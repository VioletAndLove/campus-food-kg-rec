# =============================================================================
# 功能：从 Neo4j 知识图谱中采样用户-物品交互路径（UCPR 核心组件）
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
    路径格式：User -(r1)-> e1 -(r2)-> e2 -> ... -> Dish
    """

    def __init__(self):
        self.graph = Graph(NEO4J_URI, auth=NEO4J_AUTH)
        self.max_path_len = 3  # 最大路径长度（UCPR 默认 T=3）
        self.sample_size = 10  # 每对用户-物品采样路径数

    def get_user_interacted_items(self, user_id):
        """获取用户历史交互物品（返回菜名列表）"""
        query = """
        MATCH (u:User {user_id: $user_id})-[r:INTERACTED]->(d:Dish)
        RETURN d.name as dish_name, r.rating as rating
        """
        return self.graph.run(query, user_id=user_id).data()

    def sample_paths_by_name(self, start_dish_name, end_dish_name, max_len=4):
        """通过菜名采样路径（显式模式）"""
        # 只查询 2 跳路径：Dish-Tag-Dish 或 Dish-Ingredient-Dish
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

        result = self.graph.run(query,
                                start_name=start_dish_name,
                                end_name=end_dish_name).data()

        paths = []
        for record in result:
            path = list(zip(record['rels'], record['entities'][1:]))
            paths.append(path)

        return paths

    def sample_paths_for_user_item(self, user_id, target_dish_name):
        """
        为特定用户-目标菜品采样解释路径
        target_dish_name: 目标菜品名（如"宫保鸡丁"）
        """
        # 获取用户历史菜品
        history = self.get_user_interacted_items(user_id)
        if not history:
            return []

        # 去重历史菜名
        hist_names = list(set([h['dish_name'] for h in history]))

        paths = []
        for hist_name in hist_names[:3]:  # 取前3个不同历史菜品
            # 从历史菜品到目标菜品的路径
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
        """
        if len(paths) < 2:
            return 0.0

        # 统计路径模式频率
        pattern_counts = defaultdict(int)
        for path in paths:
            pattern = self.get_path_pattern(path)
            pattern_counts[pattern] += 1

        N = len(paths)
        sid = 1.0 - sum(n * (n - 1) for n in pattern_counts.values()) / (N * (N - 1))
        return sid


def save_sampled_paths(user_item_pairs, output_file='rec/algo/cache/paths.pkl'):
    """
    为训练集中的用户-物品对预采样路径
    user_item_pairs: [(user_id, item_id), ...]
    """
    sampler = PathSampler()
    path_data = {}

    for user_id, item_id in user_item_pairs:
        key = (user_id, item_id)
        paths = sampler.sample_paths_for_user_item(user_id, item_id)
        path_data[key] = {
            'paths': paths,
            'patterns': [sampler.get_path_pattern(p) for p in paths],
            'diversity': sampler.compute_path_diversity(paths)
        }

    with open(output_file, 'wb') as f:
        pickle.dump(path_data, f)

    print(f"已保存 {len(path_data)} 个用户-物品对的路径")
    return path_data


if __name__ == '__main__':
    # 测试：为 user_id=0 采样到 dish_id=500 的路径
    sampler = PathSampler()
    paths = sampler.sample_paths_for_user_item(0, 500)
    print(f"采样到 {len(paths)} 条路径")
    for i, p in enumerate(paths[:3]):
        print(f"路径 {i + 1}: {p}")
        print(f"  模式: {sampler.get_path_pattern(p)}")