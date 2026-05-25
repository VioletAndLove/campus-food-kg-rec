from flask_restx import Namespace, Resource, fields
from flask import session
from py2neo import Graph
import os
import pickle

history_bp = Namespace("history", description="用户历史交互记录")

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
    print(f"[HISTORY] 加载 node_map 失败: {e}")
    cont_to_neo = {}
    neo_to_cont = {}

history_item = history_bp.model('HistoryItem', {
    'dish_id': fields.Integer,
    'dish_name': fields.String,
    'price': fields.Integer,
    'rating': fields.Integer,
    'timestamp': fields.String,
    'photo': fields.String,
    'tags': fields.List(fields.String)
})

history_response = history_bp.model('HistoryResponse', {
    'total': fields.Integer,
    'page': fields.Integer,
    'per_page': fields.Integer,
    'pages': fields.Integer,
    'items': fields.List(fields.Nested(history_item))
})


@history_bp.route("/")
class HistoryList(Resource):
    @history_bp.marshal_with(history_response)
    def get(self):
        """获取当前用户的历史交互记录"""
        user_id = session.get('user_id')
        if user_id is None:
            history_bp.abort(401, "请先登录")

        from flask import request
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        sort_by = request.args.get('sort_by', 'time_desc')
        min_rating = request.args.get('min_rating', 0, type=int)

        page = max(1, page)
        per_page = min(50, max(1, per_page))

        graph = Graph(NEO4J_URI, auth=NEO4J_AUTH)

        query = """
        MATCH (u:User {user_id: $user_id})-[r:INTERACTED]->(d:Dish)
        WHERE r.rating >= $min_rating
        OPTIONAL MATCH (d)-[:HAS_TAG]->(t:Tag)
        WITH d, r, collect(DISTINCT t.name) as tags
        RETURN 
            id(d) as neo_id,
            d.name as dish_name,
            d.price as price,
            d.file as photo,
            r.rating as rating,
            r.timestamp as timestamp,
            tags
        """

        results = graph.run(query, user_id=user_id, min_rating=min_rating).data()

        # 排序
        if sort_by == 'time_desc':
            results.sort(key=lambda x: x['timestamp'] or '', reverse=True)
        elif sort_by == 'rating_desc':
            results.sort(key=lambda x: x['rating'] or 0, reverse=True)
        elif sort_by == 'price_asc':
            results.sort(key=lambda x: x['price'] or 0)

        total = len(results)
        start = (page - 1) * per_page
        end = start + per_page
        page_items = results[start:end]

        items = []
        for record in page_items:
            neo_id = record['neo_id']
            cont_id = neo_to_cont.get(neo_id, neo_id)

            items.append({
                'dish_id': cont_id,
                'dish_name': record['dish_name'],
                'price': record['price'] or 0,
                'rating': record['rating'] or 0,
                'timestamp': str(record['timestamp']) if record['timestamp'] else '',
                'photo': record['photo'] or '',
                'tags': [t for t in record['tags'] if t]
            })

        return {
            'total': total,
            'page': page,
            'per_page': per_page,
            'pages': (total + per_page - 1) // per_page,
            'items': items
        }


@history_bp.route("/<int:dish_id>")
class HistoryItem(Resource):
    def delete(self, dish_id):
        """删除单条历史记录"""
        user_id = session.get('user_id')
        if user_id is None:
            return {"msg": "请先登录"}, 401

        neo_id = cont_to_neo.get(dish_id)
        if not neo_id:
            return {"msg": f"找不到 dish_id {dish_id} 对应的图谱节点"}, 404

        graph = Graph(NEO4J_URI, auth=NEO4J_AUTH)

        query = """
        MATCH (u:User {user_id: $user_id})-[r:INTERACTED]->(d:Dish)
        WHERE id(d) = $neo_id
        WITH r, count(r) as cnt
        DELETE r
        RETURN cnt as deleted_count
        """

        result = graph.run(query, user_id=user_id, neo_id=neo_id).data()

        if result and result[0]['deleted_count'] > 0:
            return {"msg": "历史记录已删除"}, 200
        else:
            return {"msg": "记录不存在或已删除"}, 404