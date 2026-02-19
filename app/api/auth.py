# =============================================================================
# 功能：用户认证接口（JWT登录）
# 归属：week9-10 用户层任务
# 下游：前端登录页面、推荐接口用户识别
# =============================================================================

from flask_restx import Namespace, Resource, fields
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from flask import current_app
from py2neo import Graph
import hashlib

auth_bp = Namespace("auth", description="用户认证服务")

# Neo4j 连接（与 rec_api_stub 一致）
NEO4J_URI = "bolt://localhost:7687"
NEO4J_AUTH = ("neo4j", "wwj@51816888")

# Swagger 文档模型
login_request = auth_bp.model('LoginRequest', {
    'username': fields.String(required=True, description='用户名'),
    'password': fields.String(required=True, description='密码')
})

login_response = auth_bp.model('LoginResponse', {
    'access_token': fields.String(description='JWT访问令牌'),
    'user_id': fields.Integer(description='用户ID'),
    'username': fields.String(description='用户名'),
    'msg': fields.String(description='消息')
})

user_response = auth_bp.model('UserResponse', {
    'user_id': fields.Integer(description='用户ID'),
    'username': fields.String(description='用户名'),
    'history_count': fields.Integer(description='历史记录数量')
})


def get_user_by_username(username):
    """根据用户名查询用户"""
    graph = Graph(NEO4J_URI, auth=NEO4J_AUTH)
    query = """
    MATCH (u:User {username: $username})
    RETURN u.user_id as user_id, u.username as username, u.password_hash as password_hash
    """
    result = graph.run(query, username=username).data()
    return result[0] if result else None


def create_user(username, password):
    """创建新用户"""
    graph = Graph(NEO4J_URI, auth=NEO4J_AUTH)

    # 检查用户是否存在
    existing = get_user_by_username(username)
    if existing:
        return None, "用户名已存在"

    # 密码哈希（简单 MD5，生产环境建议 bcrypt）
    password_hash = hashlib.md5(password.encode()).hexdigest()

    # 获取当前最大 user_id（自定义字段，0-499）
    max_id_query = "MATCH (u:User) RETURN max(u.user_id) as max_id"
    max_result = graph.run(max_id_query).data()
    new_user_id = (max_result[0]['max_id'] or -1) + 1

    # 检查是否超过 499
    if new_user_id >= 500:
        return None, "用户数量已达上限（500人）"

    # 创建用户节点（使用自定义 user_id）
    query = """
    CREATE (u:User {
        user_id: $user_id,
        username: $username,
        password_hash: $password_hash,
        created_at: datetime()
    })
    RETURN u.user_id as user_id, u.username as username
    """
    result = graph.run(query, user_id=new_user_id, username=username, password_hash=password_hash).data()

    return result[0], "注册成功"


@auth_bp.route("/register")
class Register(Resource):
    @auth_bp.expect(login_request)
    @auth_bp.marshal_with(login_response)
    def post(self):
        data = auth_bp.payload
        username = data.get('username')
        password = data.get('password')

        if not username or not password:
            auth_bp.abort(400, "用户名和密码不能为空")

        user, msg = create_user(username, password)
        if not user:
            auth_bp.abort(400, msg)

        # 生成 JWT
        access_token = create_access_token(identity=user['user_id'])

        return {
            'access_token': access_token,
            'user_id': user['user_id'],
            'username': user['username'],
            'msg': '注册成功'
        }


@auth_bp.route("/login")
class Login(Resource):
    @auth_bp.expect(login_request)
    @auth_bp.marshal_with(login_response)
    def post(self):
        data = auth_bp.payload
        username = data.get('username')
        password = data.get('password')

        if not username or not password:
            auth_bp.abort(400, "用户名和密码不能为空")

        # 查询用户
        user = get_user_by_username(username)
        if not user:
            auth_bp.abort(401, "用户名或密码错误")

        # 验证密码
        password_hash = hashlib.md5(password.encode()).hexdigest()
        if password_hash != user['password_hash']:
            auth_bp.abort(401, "用户名或密码错误")

        # 生成 JWT
        access_token = create_access_token(identity=user['user_id'])

        return {
            'access_token': access_token,
            'user_id': user['user_id'],
            'username': user['username'],
            'msg': '登录成功'
        }


@auth_bp.route("/profile")
class Profile(Resource):
    @jwt_required()
    @auth_bp.marshal_with(user_response)
    def get(self):
        """获取当前用户信息（需要JWT）"""
        user_id = get_jwt_identity()

        graph = Graph(NEO4J_URI, auth=NEO4J_AUTH)
        query = """
        MATCH (u:User) WHERE id(u) = $user_id
        OPTIONAL MATCH (u)-[:INTERACTED]->(d:Dish)
        RETURN id(u) as user_id, u.username as username, count(d) as history_count
        """
        result = graph.run(query, user_id=user_id).data()

        if not result:
            auth_bp.abort(404, "用户不存在")

        return result[0]