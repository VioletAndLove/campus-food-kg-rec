# =============================================================================
# 功能：创建 Flask 扩展实例（延迟初始化模式），避免循环导入
# 归属：week7-8 服务层任务（扩展管理）
# 上游：无（独立创建实例）
# 下游：__init__.py（init_app 绑定）、api 模块（使用扩展）
# =============================================================================

from redis import Redis
import os

redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
try:
    redis_client = Redis.from_url(redis_url, decode_responses=True)
    redis_client.ping()
except Exception:
    import fakeredis
    redis_client = fakeredis.FakeRedis(decode_responses=True)