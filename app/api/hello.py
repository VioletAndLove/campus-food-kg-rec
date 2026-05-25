# =============================================================================
# 功能：健康检查接口，验证 API 服务正常运行
# 归属：week7-8 服务层任务（RESTful API 基础）
# 上游：Flask-RESTX Namespace, Resource
# 下游：Swagger UI 文档、前端/客户端健康检测
# =============================================================================

from flask_restx import Namespace, Resource
from flask_jwt_extended import jwt_required
from py2neo import Graph
from app.extensions import redis_client
import os
import time

hello_bp = Namespace("hello", description="系统健康检查与状态监控")

NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_AUTH = (
    os.getenv("NEO4J_USER", "neo4j"),
    os.getenv("NEO4J_PASSWORD", "wwj@51816888")
)


@hello_bp.route("/")
class Hello(Resource):
    def get(self):
        """基础健康检查"""
        return {
            "msg": "UCPR-CampusFood API 运行正常 🍜",
            "status": "ok",
            "timestamp": time.time()
        }, 200


@hello_bp.route("/health")
class HealthCheck(Resource):
    @jwt_required()
    def get(self):
        """完整系统健康检查"""
        checks = {}

        # 检查Neo4j
        try:
            graph = Graph(NEO4J_URI, auth=NEO4J_AUTH)
            result = graph.run("MATCH (n) RETURN count(n) as count").data()
            checks['neo4j'] = {
                "name": "Neo4j图数据库",
                "status": "ok",
                "detail": f"连接正常，共{result[0]['count']}个节点"
            }
        except Exception as e:
            checks['neo4j'] = {
                "name": "Neo4j图数据库",
                "status": "error",
                "detail": str(e)
            }

        # 检查Redis
        try:
            redis_client.ping()
            checks['redis'] = {
                "name": "Redis缓存",
                "status": "ok",
                "detail": "连接正常"
            }
        except Exception as e:
            checks['redis'] = {
                "name": "Redis缓存",
                "status": "error",
                "detail": str(e)
            }

        # 检查模型文件
        try:
            cache_dir = 'rec/algo/cache'
            model_files = ['ent_emb_bpr.pth', 'rel_emb_bpr.pth', 'node_map.pkl']
            missing = [f for f in model_files if not os.path.exists(os.path.join(cache_dir, f))]
            if missing:
                checks['model'] = {
                    "name": "推荐模型",
                    "status": "warning",
                    "detail": f"缺少文件: {', '.join(missing)}"
                }
            else:
                checks['model'] = {
                    "name": "推荐模型",
                    "status": "ok",
                    "detail": "模型文件完整"
                }
        except Exception as e:
            checks['model'] = {
                "name": "推荐模型",
                "status": "error",
                "detail": str(e)
            }

        # 检查数据集
        try:
            if os.path.exists('data/menu.json'):
                import json
                with open('data/menu.json', 'r', encoding='utf-8') as f:
                    dishes = json.load(f)
                checks['dataset'] = {
                    "name": "菜品数据集",
                    "status": "ok",
                    "detail": f"共{len(dishes)}道菜品"
                }
            else:
                checks['dataset'] = {
                    "name": "菜品数据集",
                    "status": "warning",
                    "detail": "数据集未找到"
                }
        except Exception as e:
            checks['dataset'] = {
                "name": "菜品数据集",
                "status": "error",
                "detail": str(e)
            }

        # 整体状态
        all_ok = all(c['status'] == 'ok' for c in checks.values())

        return {
            "status": "healthy" if all_ok else "degraded",
            "timestamp": time.time(),
            "checks": checks
        }, 200 if all_ok else 503


@hello_bp.route("/stats")
class SystemStats(Resource):
    @jwt_required()
    def get(self):
        """获取系统统计数据"""
        try:
            graph = Graph(NEO4J_URI, auth=NEO4J_AUTH)

            # 统计各类节点
            stats = {}

            # 菜品数量
            dish_result = graph.run("MATCH (d:Dish) RETURN count(d) as count").data()
            stats['dishes'] = dish_result[0]['count'] if dish_result else 0

            # 用户数量
            user_result = graph.run("MATCH (u:User) RETURN count(u) as count").data()
            stats['users'] = user_result[0]['count'] if user_result else 0

            # 交互数量
            interact_result = graph.run("""
                MATCH ()-[r:INTERACTED]->() 
                RETURN count(r) as count
            """).data()
            stats['interactions'] = interact_result[0]['count'] if interact_result else 0

            # 总节点和边
            node_result = graph.run("MATCH (n) RETURN count(n) as count").data()
            edge_result = graph.run("MATCH ()-[r]->() RETURN count(r) as count").data()
            stats['nodes'] = node_result[0]['count'] if node_result else 0
            stats['edges'] = edge_result[0]['count'] if edge_result else 0

            # 标签统计
            tag_result = graph.run("MATCH (t:Tag) RETURN count(t) as count").data()
            stats['tags'] = tag_result[0]['count'] if tag_result else 0

            # 食材统计
            ing_result = graph.run("MATCH (i:Ingredient) RETURN count(i) as count").data()
            stats['ingredients'] = ing_result[0]['count'] if ing_result else 0

            return {
                "status": "ok",
                "data": stats,
                "timestamp": time.time()
            }, 200

        except Exception as e:
            return {
                "status": "error",
                "msg": str(e)
            }, 500