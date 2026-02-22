# =============================================================================
# 功能：Flask 应用工厂函数，创建并配置 Flask 应用实例
# 归属：week7-8 服务层任务（RESTful 封装）
# 上游：config.py（配置类）、extensions.py（扩展实例）、api/hello.py（蓝图）
# 下游：run.py（调用 create_app() 启动服务）
# =============================================================================

from flask import Flask, send_from_directory # Flask 核心类，Web 应用框架
from flask_restx import Api # Flask-RESTX：扩展 Flask 支持 RESTful API 和自动生成 Swagger 文档
from flask_cors import CORS # 跨域资源共享支持，允许前端（Vue3）从不同域名访问 API
from .config import Config  # 从当前包导入配置类（. 表示相对导入）
from .extensions import jwt # 导入 JWTManager 实例（已创建但未绑定应用）
from .api.hello import hello_bp # 导入 hello 蓝图（命名空间），目前仅包含测试接口
from .api.auth import auth_bp
from rec.api.rec_api_stub import rec_bp  # 新增导入
from app.api.dish import dish_bp  # 新增导入
from .api.feedback import feedback_bp
import os


def create_app():   # 应用工厂函数，返回配置完成的 Flask 应用实例
    app = Flask(__name__)
    app.config.from_object(Config)   # 从 Config 类加载配置项到 app.config 字典，包括密钥、JWT 设置、Neo4j/Redis 连接信息等

    # 配置静态文件路由（用于照片访问）
    @app.route('/static/photos/<path:filename>')
    def serve_photo(filename):
        # 照片实际存放路径：项目根目录/data/raw/
        photo_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'raw')
        # 如果文件不存在，返回 404
        if not os.path.exists(os.path.join(photo_dir, filename)):
            return "Photo not found", 404
        return send_from_directory(photo_dir, filename)



    CORS(app, supports_credentials=True)
    # 启用跨域支持：
    # - supports_credentials=True: 允许携带 Cookie/Authorization 头
    # - 必要：前端 axios 发送 JWT token 时需要
    jwt.init_app(app)
    # 将 JWTManager 绑定到应用，启用 @jwt_required() 装饰器支持
    api = Api(app, doc="/api/doc/")
    # 创建 RESTX API 实例：
    # - doc="/api/doc/": Swagger UI 文档地址 http://localhost:5000/api/doc/
    # 自动生成 API 文档，符合任务书 "Flask-RESTX 生成 Swagger" 要求

    # 注册命名空间
    api.add_namespace(hello_bp, path='/hello')
    api.add_namespace(dish_bp, path='/api/v1/dish')
    api.add_namespace(rec_bp, path='/api/v1/rec')  # 新增推荐接口
    api.add_namespace(auth_bp, path='/api/v1/auth')
    api.add_namespace(feedback_bp, path='/api/v1/feedback')

    return app  # 返回配置完成的应用实例，供 run.py 或 WSGI 服务器使用