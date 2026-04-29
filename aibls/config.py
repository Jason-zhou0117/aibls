import logging
import os
from functools import lru_cache
from os import urandom

#from pydantic.v1 import BaseSettings, Field

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AppConfig:
  
    #Session设置
    SESSION_FILE_THRESHOLD: int = int(os.getenv('SESSION_FILE_THRESHOLD', 500))
    SESSION_FILE_MODE: int = int(os.getenv('SESSION_FILE_MODE', 384))
    SESSION_PERMANENT: bool = bool(os.getenv('SESSION_PERMANENT', False))
    SESSION_USE_SIGNER: bool = bool(os.getenv('SESSION_USE_SIGNER', False))
    SESSION_KEY_PREFIX: str = str(os.getenv('SESSION_KEY_PREFIX', "session"))
    SESSION_TYPE: str = str(os.getenv('SESSION_TYPE', "filesystem"))

    SECRET_KEY= 'bilibili-danmu-monitor-secret-key-2024'

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False  # 环境变量不区分大小写
        validate_all = True  # 验证所有字段

@lru_cache()
def get_app_settings() -> AppConfig:
    """获取异步数据库配置（缓存单例）"""
    return AppConfig()