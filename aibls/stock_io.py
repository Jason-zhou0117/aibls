import queue

from flask import Flask
from flask_socketio import SocketIO

# 创建 SocketIO 实例但不初始化 app
socketio = SocketIO()

# 创建消息队列
message_queue = queue.Queue()