# =============================================================================
# 功能：创建 Flask 扩展实例（延迟初始化模式），避免循环导入
# 归属：week7-8 服务层任务（扩展管理）
# 上游：无（独立创建实例）
# 下游：__init__.py（init_app 绑定）、api 模块（使用扩展）
# =============================================================================

from flask_jwt_extended import JWTManager   # JWT 扩展：处理令牌生成、验证、刷新
from redis import Redis # Redis 客户端库，用于缓存和会话存储
import os

jwt = JWTManager()
# 创建 JWTManager 实例（未绑定应用）
# 采用"延迟初始化"模式：先创建实例，后在 create_app 中绑定
# 好处：避免 extensions.py 导入 app 导致循环导入

redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
redis_client = Redis.from_url(redis_url, decode_responses=True)
