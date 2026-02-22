from flask_restx import Namespace, Resource
from flask_jwt_extended import jwt_required, get_jwt_identity
from py2neo import Graph
import os
import pickle
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from rec.algo.path_sampler import PathSampler

dish_bp = Namespace("dish", description="菜品详情")

NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_AUTH = (
    os.getenv("NEO4J_USER", "neo4j"),
    os.getenv("NEO4J_PASSWORD", "wwj@51816888")
)

try:
    node_map = pickle.load(open('rec/algo/cache/node_map.pkl', 'rb'))
    cont_to_neo = {int(v): int(k) for k, v in node_map.items()}
except Exception as e:
    print(f"[DISH] 加载 node_map 失败: {e}")
    cont_to_neo = {}


@dish_bp.route("/<int:dish_id>")
class DishDetail(Resource):
    @jwt_required()
    def get(self, dish_id):
        user_id_raw = get_jwt_identity()
        try:
            user_id = int(user_id_raw)
        except (ValueError, TypeError):
            return {"msg": f"无效的 user_id: {user_id_raw}"}, 422

        neo_id = cont_to_neo.get(int(dish_id))
        if not neo_id:
            return {"msg": f"找不到 dish_id {dish_id} 对应的图谱节点"}, 404

        graph = Graph(NEO4J_URI, auth=NEO4J_AUTH)

        query = """
        MATCH (d:Dish)
        WHERE id(d) = $neo_id
        OPTIONAL MATCH (d)-[:HAS_TAG]->(t:Tag)
        OPTIONAL MATCH (d)-[:CONTAINS]->(i:Ingredient)
        RETURN d.name as name, 
               d.price as price, 
               d.file as photo,
               collect(DISTINCT t.name) as tags,
               collect(DISTINCT i.name) as ingredients
        """
        result = graph.run(query, neo_id=int(neo_id)).data()

        if not result or not result[0].get('name'):
            return {"msg": "菜品未找到"}, 404

        data = result[0]

        sampler = PathSampler()
        paths = sampler.sample_paths_for_user_item(user_id, data['name'])

        if paths:
            patterns = [sampler.get_path_pattern(p) for p in paths]
            if 'HAS_TAG' in str(patterns) and 'CONTAINS' in str(patterns):
                explanation = f"基于口味标签和食材相似推荐 → {data['name']}"
            elif 'HAS_TAG' in str(patterns):
                explanation = f"同属口味标签推荐 → {data['name']}"
            elif 'CONTAINS' in str(patterns):
                explanation = f"含有相似食材推荐 → {data['name']}"
            else:
                explanation = f"基于您的历史偏好推荐 → {data['name']}"
        else:
            explanation = "基于知识图谱相似度推荐"

        return {
            "dish_id": int(dish_id),
            "name": str(data['name']),
            "price": int(data['price']) if data['price'] else 0,
            "photo": str(data['photo']) if data['photo'] else '',
            "tags": [str(t) for t in data['tags'] if t],
            "ingredients": [str(i) for i in data['ingredients'] if i],
            "explanation": explanation,
            "paths": [
                {
                    "pattern": str(sampler.get_path_pattern(p)),
                    "relations": [str(rel) for rel, _ in p],
                    "entities": [str(ent) for _, ent in p]
                } for p in paths[:3]
            ] if paths else []
        }