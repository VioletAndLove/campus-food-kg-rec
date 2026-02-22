from flask_restx import Namespace, Resource, fields
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from flask import current_app
from py2neo import Graph
import hashlib
import os

auth_bp = Namespace("auth", description="用户认证服务")

NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_AUTH = (
    os.getenv("NEO4J_USER", "neo4j"),
    os.getenv("NEO4J_PASSWORD", "wwj@51816888")
)

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
    graph = Graph(NEO4J_URI, auth=NEO4J_AUTH)
    query = """
    MATCH (u:User {username: $username})
    RETURN u.user_id as user_id, u.username as username, u.password_hash as password_hash
    """
    result = graph.run(query, username=username).data()
    return result[0] if result else None


def create_user(username, password):
    graph = Graph(NEO4J_URI, auth=NEO4J_AUTH)

    existing = get_user_by_username(username)
    if existing:
        return None, "用户名已存在"

    password_hash = hashlib.md5(password.encode()).hexdigest()

    max_id_query = "MATCH (u:User) RETURN coalesce(max(u.user_id), -1) as max_id"
    max_result = graph.run(max_id_query).data()
    new_user_id = max_result[0]['max_id'] + 1

    if new_user_id >= 500:
        return None, "用户数量已达上限（500人）"

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

        access_token = create_access_token(identity=str(user['user_id']))

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

        user = get_user_by_username(username)
        if not user:
            auth_bp.abort(401, "用户名或密码错误")

        password_hash = hashlib.md5(password.encode()).hexdigest()
        if password_hash != user['password_hash']:
            auth_bp.abort(401, "用户名或密码错误")

        access_token = create_access_token(identity=str(user['user_id']))

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
        user_id_raw = get_jwt_identity()
        try:
            user_id = int(user_id_raw)
        except (ValueError, TypeError):
            auth_bp.abort(422, f"无效的 user_id: {user_id_raw}")

        graph = Graph(NEO4J_URI, auth=NEO4J_AUTH)
        query = """
        MATCH (u:User) WHERE u.user_id = $user_id
        OPTIONAL MATCH (u)-[:INTERACTED]->(d:Dish)
        RETURN u.user_id as user_id, u.username as username, count(d) as history_count
        """
        result = graph.run(query, user_id=user_id).data()

        if not result:
            auth_bp.abort(404, "用户不存在")

        return result[0]