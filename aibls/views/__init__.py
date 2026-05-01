# aibls/views/__init__.py
"""
蓝图定义模块 - 统一管理所有蓝图
"""

from flask import Blueprint

# ==================== 蓝图定义 ====================
user_api = Blueprint("user_api", __name__)
room_api = Blueprint("room_api", __name__)
live_api = Blueprint("live_api", __name__)
vip_api = Blueprint("vip_api", __name__)
gift_api = Blueprint("gift_api", __name__)

# ==================== 导入路由（必须在蓝图定义之后）====================
from aibls.views import login_route
from aibls.views import room_route
from aibls.views import live_route
from aibls.views import vip_config_route
from aibls.views import gift_route

__all__ = [
    'user_api',
    'room_api', 
    'live_api',
    'vip_api',
    'gift_api'
]