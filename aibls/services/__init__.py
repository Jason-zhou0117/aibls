# aibls/services/__init__.py
"""
服务层模块
==========

提供以下服务：
- danmu_handler: B站弹幕消息处理
- response: API响应结果封装
- user_service_file: 用户信息服务
- room_service_file: 房间信息服务
"""

from .danmu_handler import AsyncMessageGenerator
from .bili_user_service import bili_user_service
from .bili_live_service import bili_live_service
from .user_service_file import user_service_file
from .room_service_file import room_service_file
from .message_consumer import message_consumer
from .vip_service import vip_service
from .gift_service import gift_service
from .room_service import room_service


__all__ = [
    'AsyncMessageGenerator',
    'user_service_file',
    'room_service_file',
    'bili_user_service',
    'bili_live_service',
    'vip_service',
    'gift_service',
    'room_service',
    'message_consumer'
]