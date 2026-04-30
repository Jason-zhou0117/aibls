# aibls/__init__.py
"""
BiliMon 核心包
"""

from .settings import (
    APP_ROOT,
    SESSION_DIR,
    IS_EMBEDDED,
    DEBUG_MODE,
    STATIC_DIR,
    TEMPLATE_DIR,
    LOG_DIR,
    VIDEO_DIR,
    CONFIG_DIR
)

from .config import get_app_config
from .stock_io import socketio, message_queue
from .db_init import init_db
from .models import db, VIPUser, UserVideo,VideoInfo,LoginCookie
from .views import user_api,room_api,live_api,vip_api

__all__ = [
    'APP_ROOT',
    'SESSION_DIR',
    'IS_EMBEDDED',
    'DEBUG_MODE',
    'STATIC_DIR',
    'TEMPLATE_DIR',
    'LOG_DIR',
    'VIDEO_DIR',
    'CONFIG_DIR',
    'get_app_config',      # 改为导出函数，不是实例
    'socketio',
    'message_queue',
    'init_db',
    'db',                  # 添加
    'VIPUser',             # 添加
    'UserVideo'   ,             # 添加
    'VideoInfo' ,             # 添加
    'LoginCookie',
    'user_api',
    'room_api',
    'live_api',
    'vip_api'              # 添加
]