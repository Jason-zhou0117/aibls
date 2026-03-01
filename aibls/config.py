import logging
import os
from functools import lru_cache
from os import urandom

from pydantic.v1 import BaseSettings, Field

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AppConfig(BaseSettings):
    """数据库配置"""
    DB_HOST: str = str(os.getenv('DB_HOST', "localhost"))
    DB_PORT: int = int(os.getenv('DB_PORT', 3306))
    DB_USER: str = str(os.getenv('DB_USER', "root"))
    DB_PASSWORD: str = str(os.getenv('DB_PASSWORD', ""))
    DB_NAME: str = str(os.getenv('DB_NAME', "test_db"))

    SQLALCHEMY_DATABASE_URI = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}?charset=utf8mb4"

    # 连接池配置
    SQLALCHEMY_ENGINE_OPTIONS = {
        # 连接池大小
        "pool_size":  int(os.getenv('DB_POOL_SIZE', 20)),
        # 最大溢出连接数
        "max_overflow": int(os.getenv('DB_MAX_OVERFLOW', 10)),
        # 连接池回收时间（秒）
        "pool_recycle": int(os.getenv('DB_POOL_RECYCLE', 3600)),
        # 连接池预处理时间
        "pool_pre_ping": bool(os.getenv('DB_POOL_PRE_PING', True)),
        # 连接池超时时间
        "pool_timeout": int(os.getenv('DB_POOL_TIMEOUT', 30)),
        # 回显SQL语句（开发环境开启）
        "echo": True,
        # 连接池的持久性
        "pool_reset_on_return": "rollback"
    }
    # 是否追踪修改（建议关闭以提高性能）
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    #Session设置
    SESSION_FILE_THRESHOLD: int = int(os.getenv('SESSION_FILE_THRESHOLD', 500))
    SESSION_FILE_MODE: int = int(os.getenv('SESSION_FILE_MODE', 384))
    SESSION_PERMANENT: bool = bool(os.getenv('SESSION_PERMANENT', False))
    SESSION_USE_SIGNER: bool = bool(os.getenv('SESSION_USE_SIGNER', False))
    SESSION_KEY_PREFIX: str = str(os.getenv('SESSION_KEY_PREFIX', "session"))
    SESSION_TYPE: str = str(os.getenv('SESSION_TYPE', "filesystem"))

    SECRET_KEY= urandom(24)

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False  # 环境变量不区分大小写
        validate_all = True  # 验证所有字段

@lru_cache()
def get_app_settings() -> AppConfig:
    """获取异步数据库配置（缓存单例）"""
    return AppConfig()