from flask import Flask
from flask_restx import Api
from flask_cors import CORS
from .config import Config
from .extensions import jwt
from .api.hello import hello_bp

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    CORS(app, supports_credentials=True)
    jwt.init_app(app)
    api = Api(app, doc="/api/doc/")
    api.add_namespace(hello_bp)
    return app