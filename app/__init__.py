# =============================================================================
# 功能：Flask 应用工厂函数，创建并配置 Flask 应用实例
# 归属：week7-8 服务层任务（RESTful 封装）
# 上游：config.py（配置类）、extensions.py（扩展实例）、api/hello.py（蓝图）
# 下游：run.py（调用 create_app() 启动服务）
# =============================================================================

from flask import Flask, send_from_directory, session
from flask_restx import Api
from flask_cors import CORS
from .config import Config
from .extensions import redis_client
from .api.hello import hello_bp
from .api.auth import auth_bp
from rec.api.rec_api_stub import rec_bp
from app.api.dish import dish_bp
from app.api.history import history_bp
from app.api.profile import profile_bp
from .api.feedback import feedback_bp
import os


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # 配置静态文件路由（用于照片访问）
    @app.route('/static/photos/<path:filename>')
    def serve_photo(filename):
        photo_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'raw')
        if not os.path.exists(os.path.join(photo_dir, filename)):
            return "Photo not found", 404
        return send_from_directory(photo_dir, filename)

    # Session配置
    app.secret_key = Config.SECRET_KEY

    CORS(app, supports_credentials=True, resources={
        r"/api/*": {
            "origins": ["http://localhost:5173", "http://127.0.0.1:5173"],
            "supports_credentials": True
        }
    })

    api = Api(app, doc="/api/doc/")

    # 注册命名空间
    api.add_namespace(hello_bp, path='/hello')
    api.add_namespace(dish_bp, path='/api/v1/dish')
    api.add_namespace(rec_bp, path='/api/v1/rec')
    api.add_namespace(auth_bp, path='/api/v1/auth')
    api.add_namespace(feedback_bp, path='/api/v1/feedback')
    api.add_namespace(history_bp, path='/api/v1/history')
    api.add_namespace(profile_bp, path='/api/v1/profile')

    return app