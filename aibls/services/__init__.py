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
from .user_service_file import UserServiceFile
from .room_service_file import RoomServiceFile
from .message_consumer import message_consumer


__all__ = [
    'AsyncMessageGenerator',
    'ResponseResult',
    'UserServiceFile',
    'RoomServiceFile',
    'message_consumer'
    ''
]