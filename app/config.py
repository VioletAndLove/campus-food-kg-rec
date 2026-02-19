# =============================================================================
# 功能：集中管理 Flask 应用配置，支持环境变量覆盖
# 归属：week7-8 服务层任务（配置管理）
# 上游：系统环境变量（.env 文件或 export 设置）
# 下游：__init__.py（加载配置）、各模块读取数据库连接等
# =============================================================================

import os
from datetime import timedelta  # 时间差类，用于设置 JWT 过期时间

class Config:   # 配置类，使用类变量存储配置项（Flask 标准做法）
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret")
    # Flask 会话、表单 CSRF 等加密密钥
    # 优先从环境变量读取，否则使用默认值 "dev-secret"
    # ⚠️ 生产环境必须设置环境变量，硬编码密钥有安全风险
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "jwt-secret")  # JWT 令牌签名密钥，独立设置增强安全，同样优先环境变量，默认值为 "jwt-secret"
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=2)   # JWT 访问令牌有效期：2 小时，过期后需重新登录或使用刷新令牌
    NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687") # Neo4j 数据库连接地址，Bolt 协议默认端口 7687
    NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
    NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "wwj@51816888")
    REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")  # Redis 连接地址，默认本地 6379 端口，数据库 0，用于缓存推荐结果（15min TTL，见任务书 week7-8）