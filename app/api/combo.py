# =============================================================================
# 功能：智能套餐组合推荐 API
# 归属：weekX 套餐推荐模块
# 上游：rec/algo/combo_recommender.py（推荐引擎）
# 下游：frontend/src/views/DishDetail.vue（前端展示）
# =============================================================================

from flask_restx import Namespace, Resource, fields
from flask import session
from py2neo import Graph
import os
import pickle
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from rec.algo.combo_recommender import ComboRecommender, get_cont_id

combo_bp = Namespace("combo", description="智能套餐组合推荐")

NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_AUTH = (
    os.getenv("NEO4J_USER", "neo4j"),
    os.getenv("NEO4J_PASSWORD", "wwj@51816888")
)

try:
    node_map = pickle.load(open('rec/algo/cache/node_map.pkl', 'rb'))
    cont_to_neo = {int(v): int(k) for k, v in node_map.items()}
    neo_to_cont = {int(k): int(v) for k, v in node_map.items()}
except Exception as e:
    print(f"[COMBO] 加载 node_map 失败: {e}")
    cont_to_neo = {}
    neo_to_cont = {}

# API 模型定义
combo_item = combo_bp.model('ComboItem', {
    'dish_id': fields.Integer(description='菜品连续ID'),
    'name': fields.String(description='菜品名称'),
    'price': fields.Integer(description='价格'),
    'photo': fields.String(description='图片文件名'),
    'tags': fields.List(fields.String, description='口味标签'),
    'avg_rating': fields.Float(description='平均评分'),
    'reason': fields.String(description='推荐理由'),
    'path_pattern': fields.String(description='知识图谱路径模式'),
    'co_occurrence': fields.Integer(description='协同出现次数'),
    'score': fields.Float(description='综合得分'),
})

combo_response = combo_bp.model('ComboResponse', {
    'main_dish': fields.Raw(description='主菜信息'),
    'combo_items': fields.List(fields.Nested(combo_item), description='推荐配菜列表'),
    'total_price': fields.Integer(description='套餐总价'),
    'budget': fields.Integer(description='预算上限'),
    'explanation': fields.String(description='套餐整体推荐理由'),
})


@combo_bp.route("/<int:dish_id>/combo")
class DishCombo(Resource):
    @combo_bp.marshal_with(combo_response)
    def get(self, dish_id):
        """获取某菜品的智能套餐搭配推荐"""
        neo_id = cont_to_neo.get(int(dish_id))
        if not neo_id:
            combo_bp.abort(404, f"找不到 dish_id {dish_id}")

        graph = Graph(NEO4J_URI, auth=NEO4J_AUTH)

        # 获取主菜名称
        query = "MATCH (d:Dish) WHERE id(d) = $neo_id RETURN d.name as name"
        result = graph.run(query, neo_id=int(neo_id)).data()
        if not result or not result[0]['name']:
            combo_bp.abort(404, "菜品未找到")

        main_dish_name = result[0]['name']

        # 获取当前用户ID（可能未登录）
        user_id = session.get('user_id')

        # 调用推荐引擎
        recommender = ComboRecommender()
        rec_result = recommender.recommend_combo(
            main_dish_name=main_dish_name,
            user_id=user_id,
            budget=25,
            top_k=3
        )

        if "error" in rec_result:
            combo_bp.abort(404, rec_result["error"])

        # 将菜名映射为 cont_id
        main_dish = rec_result['main_dish']
        main_cont_id = get_cont_id(main_dish['name'], graph)

        combo_items = []
        for item in rec_result['combo_items']:
            cont_id = get_cont_id(item['name'], graph)
            combo_items.append({
                'dish_id': int(cont_id) if cont_id else -1,
                'name': item['name'],
                'price': item['price'],
                'photo': item['photo'],
                'tags': item['tags'],
                'avg_rating': item['avg_rating'],
                'reason': item['reason'],
                'path_pattern': item['path_pattern'],
                'co_occurrence': item['co_occurrence'],
                'score': item['score'],
            })

        return {
            'main_dish': {
                'dish_id': int(main_cont_id) if main_cont_id else dish_id,
                'name': main_dish['name'],
                'price': main_dish['price'],
                'photo': main_dish['photo'],
            },
            'combo_items': combo_items,
            'total_price': rec_result['total_price'],
            'budget': rec_result['budget'],
            'explanation': rec_result['explanation'],
        }
