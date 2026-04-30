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
from .response import ResponseResult
from .user_service_file import user_service_file
from .room_service_file import room_service_file
from .message_consumer import message_consumer
from .bili_user_service import bili_user_service
from .vip_service import vip_service


__all__ = [
    'AsyncMessageGenerator',
    'ResponseResult',
    'user_service_file',
    'room_service_file',
    'bili_user_service',
    'vip_service',
    'message_consumer'
]