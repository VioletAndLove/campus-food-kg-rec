# =============================================================================
# 功能：集中管理 Flask 应用配置，支持环境变量覆盖
# 归属：week7-8 服务层任务（配置管理）
# 上游：系统环境变量（.env 文件或 export 设置）
# 下游：__init__.py（加载配置）、各模块读取数据库连接等
# =============================================================================

import os
from datetime import timedelta  # 时间差类，用于设置 Session 过期时间


class Config:  # 配置类，使用类变量存储配置项（Flask 标准做法）
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-2024")
    # Session 加密密钥，用于签名 session cookie

    # Session 配置
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)  # Session 有效期7天
    SESSION_TYPE = 'filesystem'  # 使用文件系统存储session

    NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
    NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "wwj@51816888")
    REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")