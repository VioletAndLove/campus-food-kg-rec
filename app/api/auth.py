from flask_restx import Namespace, Resource, fields
from flask import session, request
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
    'user_id': fields.Integer(description='用户ID'),
    'username': fields.String(description='用户名'),
    'msg': fields.String(description='消息')
})

user_response = auth_bp.model('UserResponse', {
    'user_id': fields.Integer(description='用户ID'),
    'username': fields.String(description='用户名'),
    'is_logged_in': fields.Boolean(description='登录状态'),
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


def get_current_user():
    """获取当前登录用户"""
    if 'user_id' in session:
        return {
            'user_id': session.get('user_id'),
            'username': session.get('username')
        }
    return None


def login_required():
    """检查是否登录的装饰器辅助函数"""
    if 'user_id' not in session:
        return False
    return True


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

        if len(username) < 3 or len(password) < 6:
            auth_bp.abort(400, "用户名至少3位，密码至少6位")

        user, msg = create_user(username, password)
        if not user:
            auth_bp.abort(400, msg)

        # 自动登录
        session.permanent = True
        session['user_id'] = user['user_id']
        session['username'] = user['username']

        return {
            'user_id': user['user_id'],
            'username': user['username'],
            'msg': '注册成功并自动登录'
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

        # 设置Session
        session.permanent = True
        session['user_id'] = user['user_id']
        session['username'] = user['username']

        return {
            'user_id': user['user_id'],
            'username': user['username'],
            'msg': '登录成功'
        }


@auth_bp.route("/logout")
class Logout(Resource):
    def post(self):
        """退出登录"""
        session.clear()
        return {'msg': '已退出登录'}


@auth_bp.route("/status")
class AuthStatus(Resource):
    @auth_bp.marshal_with(user_response)
    def get(self):
        """检查当前登录状态"""
        user = get_current_user()
        if user:
            # 获取历史记录数量
            graph = Graph(NEO4J_URI, auth=NEO4J_AUTH)
            query = """
            MATCH (u:User {user_id: $user_id})-[:INTERACTED]->(d:Dish)
            RETURN count(d) as history_count
            """
            result = graph.run(query, user_id=user['user_id']).data()
            history_count = result[0]['history_count'] if result else 0

            return {
                'user_id': user['user_id'],
                'username': user['username'],
                'is_logged_in': True,
                'history_count': history_count
            }

        return {
            'user_id': 0,
            'username': '',
            'is_logged_in': False,
            'history_count': 0
        }