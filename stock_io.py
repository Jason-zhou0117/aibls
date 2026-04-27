import queue

from flask import Flask
from flask_socketio import SocketIO



app = Flask(__name__, static_folder='web/static',  # 静态文件目录
                template_folder='web/templates')


# 创建 SocketIO 实例但不初始化 app
socketio = SocketIO()

# 创建消息队列
message_queue = queue.Queue()