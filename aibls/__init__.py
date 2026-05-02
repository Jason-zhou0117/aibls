# aibls/__init__.py
"""
BiliMon 核心包
"""

from .settings import (
    APP_ROOT,
    IS_EMBEDDED,
    DEBUG_MODE,
    STATIC_DIR,
    TEMPLATE_DIR,
    LOG_DIR,
    VIDEO_DIR
)

from .config import get_app_config
from .stock_io import socketio, message_queue
from .db_init import init_db
from .models import db, VIPUser, UserVideo,GiftInfo,GiftVideo,LoginCookie
from .views import user_api,room_api,live_api,vip_api,gift_api
from .services import bili_user_service,bili_live_service,vip_service,gift_service

__all__ = [
    'APP_ROOT',
    'IS_EMBEDDED',
    'DEBUG_MODE',
    'STATIC_DIR',
    'TEMPLATE_DIR',
    'LOG_DIR',
    'VIDEO_DIR',
    'get_app_config',      # 改为导出函数，不是实例
    'socketio',
    'message_queue',
    'init_db',
    'db',                  # 添加
    'VIPUser',             # 添加
    'UserVideo'   ,             # 添加
    'GiftInfo' ,               # 添加
    'GiftVideo' ,             # 添加
    'LoginCookie',
    'user_api',
    'room_api',
    'live_api',
    'vip_api',
    'gift_api',
    'bili_user_service'  ,
    'bili_live_service'  ,
    'vip_service',
    'gift_service'           # 添加
]