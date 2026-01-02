from flask_jwt_extended import JWTManager
from redis import Redis

jwt = JWTManager()
redis_client = Redis.from_url("redis://localhost:6379/0", decode_responses=True)