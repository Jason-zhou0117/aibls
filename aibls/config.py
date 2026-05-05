# aibls/config.py
import os
from datetime import timedelta
from functools import lru_cache

from aibls.settings import APP_ROOT, IN_DOCKER


class AppConfig:
    """Flask 配置类"""

    # ==================== 基础配置 ====================
    SECRET_KEY = os.environ.get('SECRET_KEY', 'bili-danmu-monitor-secret-key-2024')

    # ==================== 数据库配置 ====================
    # SQLite 数据库路径
    if IN_DOCKER:
        # Docker 环境：数据库文件在挂载卷中
        db_path = os.environ.get('DATABASE_PATH', '/app/bili_mon.db')
    else:
        # 本地环境：数据库在项目根目录
        db_path = os.path.join(APP_ROOT, 'bili_mon.db')

    SQLALCHEMY_DATABASE_URI = f'sqlite:///{db_path}'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = False

    # ==================== Session 配置 ====================
    # Session 使用数据库存储，不需要文件目录
    SESSION_TYPE = 'sqlalchemy'
    SESSION_SQLALCHEMY_TABLE = 'sessions'
    SESSION_PERMANENT = True
    SESSION_USE_SIGNER = True
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)
    SESSION_KEY_PREFIX = 'bili_'

    # ==================== Cookie 配置 ====================
    SESSION_COOKIE_NAME = 'bili_session'
    SESSION_COOKIE_PATH = '/'
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    SESSION_COOKIE_SECURE = False

    # ==================== 文件上传配置 ====================
    MAX_CONTENT_LENGTH = 100 * 1024 * 1024  # 100MB
    UPLOAD_FOLDER = os.path.join(APP_ROOT, 'video') if not IN_DOCKER else '/app/video'


@lru_cache()
def get_app_config() -> AppConfig:
    """获取应用配置（缓存单例）"""
    return AppConfig()