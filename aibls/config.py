import os
from datetime import timedelta
from functools import lru_cache

from aibls.settings import APP_ROOT



class AppConfig:
    """Flask 配置类"""

    # ==================== 基础配置 ====================
    SECRET_KEY = 'bili-danmu-monitor-secret-key-2024'

    # ==================== 数据库配置 ====================
    # SQLite 数据库路径
    SQLALCHEMY_DATABASE_URI = f'sqlite:///{os.path.join(APP_ROOT, "bili_mon.db")}'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = False  # 设为True可查看SQL日志

    # ==================== Session 配置（改为数据库方式） ====================
    SESSION_TYPE = 'sqlalchemy'  # 改为 sqlalchemy
    SESSION_SQLALCHEMY = None  # 稍后在 app.py 中设置
    SESSION_SQLALCHEMY_TABLE = 'sessions'  # session 表名
    SESSION_PERMANENT = True
    SESSION_USE_SIGNER = True
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)
    SESSION_KEY_PREFIX = 'bili_'
    SESSION_REFRESH_EACH_REQUEST = True

    # ==================== Cookie 配置 ====================
    SESSION_COOKIE_NAME = 'bili_session'
    SESSION_COOKIE_PATH = '/'
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    SESSION_COOKIE_SECURE = False

    # ==================== 文件上传配置 ====================
    MAX_CONTENT_LENGTH = 100 * 1024 * 1024
    UPLOAD_FOLDER = os.path.join(APP_ROOT, 'web', 'static', 'videos')



@lru_cache()
def get_app_config() -> AppConfig:
    """获取异步数据库配置（缓存单例）"""
    return AppConfig()