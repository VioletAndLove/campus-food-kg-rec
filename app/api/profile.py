from flask_restx import Namespace, Resource, fields
from flask import session
from py2neo import Graph
from datetime import datetime
import json
import os

profile_bp = Namespace("profile", description="个人中心数据")

NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_AUTH = (
    os.getenv("NEO4J_USER", "neo4j"),
    os.getenv("NEO4J_PASSWORD", "wwj@51816888")
)

tag_stat = profile_bp.model('TagStat', {
    'tag': fields.String,
    'count': fields.Integer
})

ingredient_stat = profile_bp.model('IngredientStat', {
    'ingredient': fields.String,
    'count': fields.Integer
})

profile_response = profile_bp.model('ProfileResponse', {
    'user_id': fields.Integer,
    'username': fields.String,
    'created_at': fields.String,
    'total_interactions': fields.Integer,
    'avg_rating': fields.Float,
    'favorite_tags': fields.List(fields.Nested(tag_stat)),
    'favorite_ingredients': fields.List(fields.Nested(ingredient_stat)),
    'experiment_group': fields.String,
    'show_explanation': fields.Boolean
})


@profile_bp.route("/")
class UserProfile(Resource):
    @profile_bp.marshal_with(profile_response)
    def get(self):
        """获取用户完整画像数据（基于历史记录分析）"""
        user_id = session.get('user_id')
        if user_id is None:
            profile_bp.abort(401, "请先登录")

        graph = Graph(NEO4J_URI, auth=NEO4J_AUTH)

        # 基础用户信息
        user_query = """
        MATCH (u:User {user_id: $user_id})
        RETURN u.user_id as user_id, u.username as username, u.created_at as created_at
        """
        user_result = graph.run(user_query, user_id=user_id).data()

        if not user_result:
            profile_bp.abort(404, "用户不存在")

        user_info = user_result[0]

        # 交互统计
        stats_query = """
        MATCH (u:User {user_id: $user_id})-[r:INTERACTED]->(d:Dish)
        RETURN count(r) as total_interactions, avg(r.rating) as avg_rating
        """
        stats_result = graph.run(stats_query, user_id=user_id).data()
        stats = stats_result[0] if stats_result else {'total_interactions': 0, 'avg_rating': 0}

        # 偏好标签统计（基于历史记录中高评分菜品分析）
        tags_query = """
        MATCH (u:User {user_id: $user_id})-[r:INTERACTED]->(d:Dish)-[:HAS_TAG]->(t:Tag)
        WHERE r.rating >= 4
        RETURN t.name as tag, count(*) as count, avg(r.rating) as avg_rating
        ORDER BY count DESC, avg_rating DESC
        LIMIT 8
        """
        tags_result = graph.run(tags_query, user_id=user_id).data()

        # 偏好食材统计（基于历史记录中高评分菜品分析）
        ingredients_query = """
        MATCH (u:User {user_id: $user_id})-[r:INTERACTED]->(d:Dish)-[:CONTAINS]->(i:Ingredient)
        WHERE r.rating >= 4
        RETURN i.name as ingredient, count(*) as count, avg(r.rating) as avg_rating
        ORDER BY count DESC, avg_rating DESC
        LIMIT 8
        """
        ingredients_result = graph.run(ingredients_query, user_id=user_id).data()

        # 最近活跃分析
        recent_query = """
        MATCH (u:User {user_id: $user_id})-[r:INTERACTED]->(d:Dish)
        RETURN count(r) as recent_count
        """
        recent_result = graph.run(recent_query, user_id=user_id).data()

        # A/B测试分组
        experiment_group = 'unknown'
        show_explanation = False
        try:
            with open('data/experiment/user_group_map.json', 'r', encoding='utf-8') as f:
                group_map = json.load(f)
                group = group_map.get(str(user_id), 'unknown')
                experiment_group = f"{group}组" if group != 'unknown' else '未分组'
                show_explanation = (group == 'A')
        except:
            pass

        return {
            'user_id': user_info['user_id'],
            'username': user_info['username'],
            'created_at': str(user_info['created_at']) if user_info['created_at'] else '未知',
            'total_interactions': stats['total_interactions'] or 0,
            'avg_rating': round(float(stats['avg_rating']), 2) if stats['avg_rating'] else 0,
            'favorite_tags': [{'tag': r['tag'], 'count': r['count']} for r in tags_result],
            'favorite_ingredients': [{'ingredient': r['ingredient'], 'count': r['count']} for r in ingredients_result],
            'experiment_group': experiment_group,
            'show_explanation': show_explanation
        }


@profile_bp.route("/stats/simple")
class SimpleStats(Resource):
    def get(self):
        """获取简化统计（用于头部显示）"""
        user_id = session.get('user_id')
        if user_id is None:
            return {"msg": "请先登录"}, 401

        graph = Graph(NEO4J_URI, auth=NEO4J_AUTH)

        query = """
        MATCH (u:User {user_id: $user_id})-[r:INTERACTED]->(d:Dish)
        RETURN count(r) as total, avg(r.rating) as avg_rating
        """
        result = graph.run(query, user_id=user_id).data()

        if result:
            return {
                'total_interactions': result[0]['total'] or 0,
                'avg_rating': round(float(result[0]['avg_rating']), 1) if result[0]['avg_rating'] else 0
            }
        return {'total_interactions': 0, 'avg_rating': 0}


@profile_bp.route("/taste-analysis")
class TasteAnalysis(Resource):
    def get(self):
        """获取基于历史记录的口味分析报告"""
        user_id = session.get('user_id')
        if user_id is None:
            return {"msg": "请先登录"}, 401

        graph = Graph(NEO4J_URI, auth=NEO4J_AUTH)

        # 口味变化趋势（按月统计）
        trend_query = """
        MATCH (u:User {user_id: $user_id})-[r:INTERACTED]->(d:Dish)
        WHERE r.timestamp IS NOT NULL
        RETURN 
            substring(toString(r.timestamp), 0, 7) as month,
            count(*) as interactions,
            avg(r.rating) as avg_rating
        ORDER BY month DESC
        LIMIT 6
        """
        trend_result = graph.run(trend_query, user_id=user_id).data()

        # 价格偏好分析
        price_query = """
        MATCH (u:User {user_id: $user_id})-[r:INTERACTED]->(d:Dish)
        RETURN 
            CASE 
                WHEN d.price < 10 THEN '10元以下'
                WHEN d.price < 20 THEN '10-20元'
                WHEN d.price < 30 THEN '20-30元'
                ELSE '30元以上'
            END as price_range,
            count(*) as count
        ORDER BY count DESC
        """
        price_result = graph.run(price_query, user_id=user_id).data()

        return {
            'monthly_trend': [
                {
                    'month': r['month'],
                    'interactions': r['interactions'],
                    'avg_rating': round(float(r['avg_rating']), 2) if r['avg_rating'] else 0
                } for r in trend_result
            ],
            'price_preference': [
                {
                    'range': r['price_range'],
                    'count': r['count']
                } for r in price_result
            ]
        }