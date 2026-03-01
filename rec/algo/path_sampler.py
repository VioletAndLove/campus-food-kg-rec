# =============================================================================
# 功能：从 Neo4j 知识图谱中采样用户-物品交互路径（UCPR 核心组件）
# 优化：支持2跳和3跳路径，提升路径多样性
# 归属：Week 5-6 算法补强（路径推理基础）
# 上游：Neo4j 图谱（Dish/Tag/Ingredient/User 节点）
# 下游：ucpr_light.py（路径特征编码）、eval.py（Diversity 评估）
# =============================================================================

from py2neo import Graph
import random
import pickle
from collections import defaultdict

NEO4J_URI = "bolt://localhost:7687"
NEO4J_AUTH = ("neo4j", "wwj@51816888")


class PathSampler:
    """
    UCPR 路径采样器：采样用户到推荐物品的多跳路径
    支持路径：2跳（Dish-Tag-Dish）和3跳（Dish-Tag-Dish-Tag-Dish）
    """

    def __init__(self):
        self.graph = Graph(NEO4J_URI, auth=NEO4J_AUTH)
        self.max_path_len = 4  # 最大路径长度（3跳=4个节点）
        self.sample_size = 10  # 每对用户-物品采样路径数

    def get_user_interacted_items(self, user_id):
        """获取用户历史交互物品（返回菜名列表）"""
        query = """
        MATCH (u:User {user_id: $user_id})-[r:INTERACTED]->(d:Dish)
        RETURN d.name as dish_name, r.rating as rating
        ORDER BY r.timestamp DESC
        """
        return self.graph.run(query, user_id=user_id).data()

    def sample_2hop_paths(self, start_dish_name, end_dish_name):
        """2跳路径：Dish-Tag-Dish 或 Dish-Ingredient-Dish"""
        query = """
        MATCH (start:Dish {name: $start_name})-[:HAS_TAG]->(t:Tag)<-[:HAS_TAG]-(end:Dish {name: $end_name})
        WHERE start <> end
        RETURN ['HAS_TAG', 'HAS_TAG'] as rels,
               [start.name, t.name, end.name] as entities,
               2 as path_len
        LIMIT 5

        UNION

        MATCH (start:Dish {name: $start_name})-[:CONTAINS]->(i:Ingredient)<-[:CONTAINS]-(end:Dish {name: $end_name})
        WHERE start <> end
        RETURN ['CONTAINS', 'CONTAINS'] as rels,
               [start.name, i.name, end.name] as entities,
               2 as path_len
        LIMIT 5
        """
        result = self.graph.run(query, start_name=start_dish_name, end_name=end_dish_name).data()

        paths = []
        for record in result:
            path = list(zip(record['rels'], record['entities'][1:]))
            paths.append(path)
        return paths

    def sample_3hop_paths(self, start_dish_name, end_dish_name):
        """3跳路径：Dish-Tag-Dish-Tag-Dish 等混合路径"""
        query = """
        // 路径1: DishA -[HAS_TAG]-> Tag1 <-[HAS_TAG]- DishB -[HAS_TAG]-> Tag2 <-[HAS_TAG]- DishC
        MATCH (start:Dish {name: $start_name})-[:HAS_TAG]->(t1:Tag)<-[:HAS_TAG]-(mid:Dish)-[:HAS_TAG]->(t2:Tag)<-[:HAS_TAG]-(end:Dish {name: $end_name})
        WHERE start <> mid AND mid <> end AND start <> end
        RETURN ['HAS_TAG', 'HAS_TAG', 'HAS_TAG', 'HAS_TAG'] as rels,
               [start.name, t1.name, mid.name, t2.name, end.name] as entities,
               4 as path_len
        LIMIT 3

        UNION

        // 路径2: DishA -[CONTAINS]-> Ing <-[CONTAINS]- DishB -[HAS_TAG]-> Tag <-[HAS_TAG]- DishC
        MATCH (start:Dish {name: $start_name})-[:CONTAINS]->(i:Ingredient)<-[:CONTAINS]-(mid:Dish)-[:HAS_TAG]->(t:Tag)<-[:HAS_TAG]-(end:Dish {name: $end_name})
        WHERE start <> mid AND mid <> end AND start <> end
        RETURN ['CONTAINS', 'CONTAINS', 'HAS_TAG', 'HAS_TAG'] as rels,
               [start.name, i.name, mid.name, t.name, end.name] as entities,
               4 as path_len
        LIMIT 3

        UNION

        // 路径3: DishA -[HAS_TAG]-> Tag <-[HAS_TAG]- DishB -[CONTAINS]-> Ing <-[CONTAINS]- DishC
        MATCH (start:Dish {name: $start_name})-[:HAS_TAG]->(t:Tag)<-[:HAS_TAG]-(mid:Dish)-[:CONTAINS]->(i:Ingredient)<-[:CONTAINS]-(end:Dish {name: $end_name})
        WHERE start <> mid AND mid <> end AND start <> end
        RETURN ['HAS_TAG', 'HAS_TAG', 'CONTAINS', 'CONTAINS'] as rels,
               [start.name, t.name, mid.name, i.name, end.name] as entities,
               4 as path_len
        LIMIT 3
        """
        result = self.graph.run(query, start_name=start_dish_name, end_name=end_dish_name).data()

        paths = []
        for record in result:
            path = list(zip(record['rels'], record['entities'][1:]))
            paths.append(path)
        return paths

    def sample_paths_by_name(self, start_dish_name, end_dish_name):
        """合并2跳和3跳路径采样"""
        paths_2hop = self.sample_2hop_paths(start_dish_name, end_dish_name)
        paths_3hop = self.sample_3hop_paths(start_dish_name, end_dish_name)

        # 合并并去重
        all_paths = paths_2hop + paths_3hop
        seen = set()
        unique_paths = []
        for p in all_paths:
            pattern = self.get_path_pattern(p)
            if pattern not in seen:
                seen.add(pattern)
                unique_paths.append(p)

        return unique_paths[:self.sample_size]

    def sample_paths_for_user_item(self, user_id, target_dish_name):
        """为特定用户-目标菜品采样解释路径"""
        history = self.get_user_interacted_items(user_id)
        if not history:
            return []

        # 去重历史菜名，优先高评分
        hist_names = []
        seen = set()
        for h in sorted(history, key=lambda x: x.get('rating', 0), reverse=True):
            name = h['dish_name']
            if name not in seen and name != target_dish_name:
                seen.add(name)
                hist_names.append(name)

        paths = []
        for hist_name in hist_names[:5]:  # 取前5个不同历史菜品
            path = self.sample_paths_by_name(hist_name, target_dish_name)
            if path:
                paths.extend(path)

        return paths[:self.sample_size]

    def get_path_pattern(self, path):
        """提取路径模式（用于 Diversity 计算）"""
        return "->".join([rel for rel, _ in path])

    def compute_path_diversity(self, paths):
        """
        计算路径多样性（Simpson's Index of Diversity）
        SID = 1 - sum(n_i * (n_i - 1)) / (N * (N - 1))
        范围0-1，越接近1多样性越高
        """
        if len(paths) < 2:
            return 0.0

        pattern_counts = defaultdict(int)
        for path in paths:
            pattern = self.get_path_pattern(path)
            pattern_counts[pattern] += 1

        N = len(paths)
        sid = 1.0 - sum(n * (n - 1) for n in pattern_counts.values()) / (N * (N - 1))
        return sid

    def compute_path_diversity_v2(self, paths):
        """
        增强版多样性：考虑路径长度和实体类型
        """
        if len(paths) < 2:
            return 0.0

        # 模式多样性
        patterns = [self.get_path_pattern(p) for p in paths]
        unique_patterns = len(set(patterns))
        pattern_diversity = unique_patterns / len(paths)

        # 长度多样性
        lengths = [len(p) for p in paths]
        avg_length = sum(lengths) / len(lengths)
        length_variance = sum((l - avg_length) ** 2 for l in lengths) / len(lengths)

        # 综合多样性（加权）
        sid = self.compute_path_diversity(paths)
        combined = 0.6 * sid + 0.4 * pattern_diversity
        return round(combined, 4)


def save_sampled_paths(user_item_pairs, output_file='rec/algo/cache/paths.pkl'):
    """为训练集中的用户-物品对预采样路径"""
    sampler = PathSampler()
    path_data = {}

    for user_id, item_id in user_item_pairs:
        key = (user_id, item_id)
        paths = sampler.sample_paths_for_user_item(user_id, item_id)
        path_data[key] = {
            'paths': paths,
            'patterns': [sampler.get_path_pattern(p) for p in paths],
            'diversity': sampler.compute_path_diversity_v2(paths)
        }

    with open(output_file, 'wb') as f:
        pickle.dump(path_data, f)

    print(f"已保存 {len(path_data)} 个用户-物品对的路径")
    avg_diversity = sum(v['diversity'] for v in path_data.values()) / len(path_data)
    print(f"平均路径多样性: {avg_diversity:.4f}")
    return path_data


if __name__ == '__main__':
    # 测试：验证3跳路径采样
    sampler = PathSampler()

    # 测试3跳路径
    paths = sampler.sample_3hop_paths("川大江安校区麻婆豆腐", "中山大学学一麻婆豆腐")
    print(f"3跳路径采样: {len(paths)} 条")
    for i, p in enumerate(paths[:3]):
        print(f"  路径{i + 1}: {sampler.get_path_pattern(p)}")

    # 测试多样性计算
    all_paths = sampler.sample_paths_by_name("川大江安校区麻婆豆腐", "中山大学学一麻婆豆腐")
    print(f"\n总路径数: {len(all_paths)}")
    print(f"路径多样性(SID): {sampler.compute_path_diversity(all_paths):.4f}")
    print(f"增强多样性: {sampler.compute_path_diversity_v2(all_paths):.4f}")