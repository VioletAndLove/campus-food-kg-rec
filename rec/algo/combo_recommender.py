# =============================================================================
# 功能：基于知识图谱的智能套餐组合推荐引擎
# 归属：weekX 套餐推荐模块
# 上游：Neo4j 知识图谱（Dish/Tag/Ingredient/User 节点及关系）
# 下游：app/api/combo.py（套餐推荐 API）
# =============================================================================

from py2neo import Graph
from collections import defaultdict
import os
import pickle

NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_AUTH = (
    os.getenv("NEO4J_USER", "neo4j"),
    os.getenv("NEO4J_PASSWORD", "wwj@51816888")
)

# 口味互补映射（双向）
TAG_COMPLEMENT = {
    "辣": ["清淡", "酸甜", "爽口"],
    "麻辣": ["清淡", "酸甜", "爽口"],
    "清淡": ["辣", "麻辣", "咸鲜", "浓郁"],
    "酸甜": ["辣", "麻辣", "咸鲜"],
    "咸鲜": ["清淡", "酸甜", "爽口"],
    "浓郁": ["清淡", "爽口"],
    "油腻": ["清淡", "爽口", "酸甜"],
    "爽口": ["浓郁", "油腻", "咸鲜"],
}

# 荤素食材分类（用于食材互补）
MEAT_INGREDIENTS = {
    "猪肉", "牛肉", "羊肉", "鸡肉", "鸭肉", "鱼肉", "虾", "鸡蛋", "排骨",
    "培根", "火腿", "香肠", "肉丸", "里脊", "五花肉", "鸡腿", "鸡翅"
}

VEG_INGREDIENTS = {
    "豆腐", "白菜", "西兰花", "番茄", "黄瓜", "土豆", "茄子", "豆角",
    "冬瓜", "南瓜", "萝卜", "芹菜", "菠菜", "生菜", "木耳", "香菇",
    "金针菇", "海带", "豆芽", "莲藕", "竹笋", "洋葱", "青椒", "红椒"
}


def _tag_complement_score(tags_main, tags_other):
    """计算口味互补得分（0~1）"""
    if not tags_main or not tags_other:
        return 0.0

    score = 0.0
    for t1 in tags_main:
        complements = TAG_COMPLEMENT.get(t1, [])
        for t2 in tags_other:
            if t2 in complements:
                score += 1.0
    # 归一化
    max_pairs = max(len(tags_main) * 2, 1)
    return min(score / max_pairs, 1.0)


def _ingredient_balance_score(ing_main, ing_other):
    """计算食材搭配均衡得分（荤素互补 + 重叠度低）"""
    if not ing_main or not ing_other:
        return 0.0

    set_main = set(ing_main)
    set_other = set(ing_other)

    # 1. 重叠度越低越好
    overlap = len(set_main & set_other)
    total_unique = len(set_main | set_other)
    distinct_score = 1.0 - (overlap / max(total_unique, 1))

    # 2. 荤素搭配奖励
    main_has_meat = any(i in MEAT_INGREDIENTS for i in set_main)
    main_has_veg = any(i in VEG_INGREDIENTS for i in set_main)
    other_has_meat = any(i in MEAT_INGREDIENTS for i in set_other)
    other_has_veg = any(i in VEG_INGREDIENTS for i in set_other)

    balance_score = 0.0
    if main_has_meat and other_has_veg:
        balance_score += 0.6
    if main_has_veg and other_has_meat:
        balance_score += 0.6
    if main_has_meat and other_has_meat:
        balance_score += 0.1  # 两荤也能接受，但不如荤素
    if main_has_veg and other_has_veg:
        balance_score += 0.2  # 两素稍微差点

    return distinct_score * 0.4 + balance_score * 0.6


def _get_avg_rating(graph, dish_name):
    """获取菜品平均评分"""
    query = """
    MATCH (d:Dish {name: $name})<-[r:RATED]-()
    RETURN avg(r.rating) as avg_rating, count(r) as cnt
    """
    result = graph.run(query, name=dish_name).data()
    if result and result[0]['avg_rating']:
        return float(result[0]['avg_rating']), int(result[0]['cnt'])
    return 0.0, 0


class ComboRecommender:
    """
    智能套餐组合推荐器

    基于知识图谱的多策略融合推荐：
    1. 协同过滤：基于用户 INTERACTED 共现频率
    2. 口味互补：基于 Tag 互补性
    3. 食材互补：基于荤素均衡 + 食材重叠度
    4. 价格约束：硬过滤
    5. 评分兜底：高评分菜品加分
    """

    def __init__(self):
        self.graph = Graph(NEO4J_URI, auth=NEO4J_AUTH)

    def recommend_combo(self, main_dish_name, user_id=None, budget=25, top_k=3):
        """
        为主菜推荐套餐配菜

        Args:
            main_dish_name: 主菜名称
            user_id: 当前用户ID（可选，用于个性化）
            budget: 套餐总价预算上限（默认25元）
            top_k: 推荐配菜数量（默认3道）

        Returns:
            dict: 包含 main_dish, combo_items, total_price, explanation
        """
        # 获取主菜信息
        main_query = """
        MATCH (d:Dish {name: $name})
        RETURN d.name as name, d.price as price, d.file as photo
        """
        main_result = self.graph.run(main_query, name=main_dish_name).data()
        if not main_result:
            return {"error": f"菜品 '{main_dish_name}' 不存在"}

        main_info = main_result[0]
        main_price = int(main_info['price'] or 0)
        remaining_budget = budget - main_price

        if remaining_budget <= 0:
            return {
                "main_dish": {
                    "name": main_info['name'],
                    "price": main_price,
                    "photo": main_info['photo'] or ''
                },
                "combo_items": [],
                "total_price": main_price,
                "explanation": "主菜价格已超出预算，建议单独享用"
            }

        # 获取主菜的 Tag 和 Ingredient
        main_meta_query = """
        MATCH (d:Dish {name: $name})
        OPTIONAL MATCH (d)-[:HAS_TAG]->(t:Tag)
        OPTIONAL MATCH (d)-[:CONTAINS]->(i:Ingredient)
        RETURN collect(DISTINCT t.name) as tags, collect(DISTINCT i.name) as ingredients
        """
        main_meta = self.graph.run(main_meta_query, name=main_dish_name).data()[0]
        main_tags = [t for t in main_meta['tags'] if t]
        main_ingredients = [i for i in main_meta['ingredients'] if i]

        # ========== 策略1：协同过滤（共现频率） ==========
        cooccur_query = """
        MATCH (main:Dish {name: $main_name})<-[:INTERACTED]-(u:User)-[:INTERACTED]->(other:Dish)
        WHERE main <> other
        RETURN other.name as name, count(u) as freq
        ORDER BY freq DESC
        LIMIT 50
        """
        cooccur_result = self.graph.run(cooccur_query, main_name=main_dish_name).data()
        cooccur_map = {r['name']: int(r['freq']) for r in cooccur_result}

        # ========== 策略2+3+5：基于属性筛选与打分 ==========
        # 先获取候选菜品（价格符合预算的）
        candidate_query = """
        MATCH (other:Dish)
        WHERE other.name <> $main_name AND other.price <= $max_price
        OPTIONAL MATCH (other)-[:HAS_TAG]->(t:Tag)
        OPTIONAL MATCH (other)-[:CONTAINS]->(i:Ingredient)
        OPTIONAL MATCH (other)<-[r:RATED]-()
        RETURN other.name as name, other.price as price, other.file as photo,
               collect(DISTINCT t.name) as tags, collect(DISTINCT i.name) as ingredients,
               avg(r.rating) as avg_rating
        LIMIT 200
        """
        candidates = self.graph.run(candidate_query,
                                     main_name=main_dish_name,
                                     max_price=remaining_budget).data()

        # 计算每道候选菜的综合得分
        scored_candidates = []
        for cand in candidates:
            name = cand['name']
            price = int(cand['price'] or 0)
            tags = [t for t in cand['tags'] if t]
            ingredients = [i for i in cand['ingredients'] if i]
            avg_rating = float(cand['avg_rating'] or 0)

            # 协同过滤得分（归一化）
            freq = cooccur_map.get(name, 0)
            max_freq = max(cooccur_map.values(), default=1)
            score_cooccur = (freq / max_freq) * 0.4

            # 口味互补得分
            score_tag = _tag_complement_score(main_tags, tags) * 0.3

            # 食材互补得分
            score_ing = _ingredient_balance_score(main_ingredients, ingredients) * 0.2

            # 评分兜底
            score_rating = (avg_rating / 5.0) * 0.1

            total_score = score_cooccur + score_tag + score_ing + score_rating

            # 确定推荐理由和路径模式
            reason_parts = []
            path_pattern = ""
            if freq >= 10:
                reason_parts.append(f"{freq}位同学同时选择")
                path_pattern = "INTERACTED->INTERACTED"
            elif score_tag >= 0.3:
                reason_parts.append("口味互补")
                path_pattern = "HAS_TAG->HAS_TAG"
            elif score_ing >= 0.4:
                reason_parts.append("食材均衡")
                path_pattern = "CONTAINS->CONTAINS"
            elif avg_rating >= 4.0:
                reason_parts.append("高分好评")
                path_pattern = "RATED->RATED"
            else:
                reason_parts.append("搭配推荐")
                path_pattern = "DISH->DISH"

            scored_candidates.append({
                "name": name,
                "price": price,
                "photo": cand['photo'] or '',
                "tags": tags,
                "ingredients": ingredients,
                "avg_rating": round(avg_rating, 1),
                "score": round(total_score, 4),
                "co_occurrence": freq,
                "reason": "、".join(reason_parts),
                "path_pattern": path_pattern
            })

        # 按综合得分排序，取 top_k
        scored_candidates.sort(key=lambda x: x['score'], reverse=True)
        combo_items = scored_candidates[:top_k]

        # 计算总价
        total_price = main_price + sum(item['price'] for item in combo_items)

        # 生成整体推荐理由
        if combo_items:
            reasons = [item['reason'] for item in combo_items]
            explanation = f"这份套餐结合了{'、'.join(reasons[:2])}，总价¥{total_price}"
        else:
            explanation = "未找到合适的搭配菜品，建议单独享用"

        return {
            "main_dish": {
                "name": main_info['name'],
                "price": main_price,
                "photo": main_info['photo'] or ''
            },
            "combo_items": combo_items,
            "total_price": total_price,
            "budget": budget,
            "explanation": explanation
        }

    def recommend_for_user(self, user_id, budget=25, top_k=3):
        """
        基于用户历史偏好，推荐一套完整套餐（含主菜）
        """
        # 获取用户最近高评分的一道菜作为主菜
        query = """
        MATCH (u:User {user_id: $user_id})-[r:INTERACTED]->(d:Dish)
        RETURN d.name as name, r.rating as rating
        ORDER BY r.rating DESC, r.timestamp DESC
        LIMIT 1
        """
        result = self.graph.run(query, user_id=user_id).data()
        if not result:
            return {"error": "用户无历史交互记录"}

        main_dish = result[0]['name']
        return self.recommend_combo(main_dish, user_id=user_id, budget=budget, top_k=top_k)


# 加载 node_map 用于 ID 映射
try:
    node_map = pickle.load(open('rec/algo/cache/node_map.pkl', 'rb'))
    cont_to_neo = {int(v): int(k) for k, v in node_map.items()}
    neo_to_cont = {int(k): int(v) for k, v in node_map.items()}
except Exception as e:
    print(f"[COMBO] 加载 node_map 失败: {e}")
    cont_to_neo = {}
    neo_to_cont = {}


def get_cont_id(dish_name, graph):
    """通过菜名获取连续ID（cont_id）"""
    query = "MATCH (d:Dish {name: $name}) RETURN id(d) as neo_id"
    result = graph.run(query, name=dish_name).data()
    if not result:
        return None
    neo_id = int(result[0]['neo_id'])
    return neo_to_cont.get(neo_id, neo_id)


if __name__ == '__main__':
    recommender = ComboRecommender()

    # 测试
    result = recommender.recommend_combo("红烧牛肉面", budget=30, top_k=3)
    print("主菜:", result['main_dish'])
    print("推荐配菜:")
    for item in result['combo_items']:
        print(f"  - {item['name']} ¥{item['price']} ({item['reason']}) 得分:{item['score']}")
    print(f"总价: ¥{result['total_price']}")
    print(f"推荐理由: {result['explanation']}")
