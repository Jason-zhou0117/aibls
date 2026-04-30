# aibls/views/live_route.py
"""弹幕API的蓝图定义"""
import logging
import random
import threading
import time
from datetime import datetime

from bilibili_api import Credential
from flask import session, render_template, request
from flask_socketio import emit

from aibls.decorators import check_session_2api_decorator, check_session_go_login_decorator
from aibls.models import LoginCookie
from aibls.services import message_consumer,room_service_file
from aibls.views import live_api
from aibls.stock_io import socketio, message_queue

logger = logging.getLogger(__name__)

# live_route.py
from aibls.generator_manager import get_generator, reset_generator

# 使用
generator = get_generator()

# 启动消费者线程
consumer_thread = threading.Thread(target=message_consumer.run, daemon=True, name="MessageConsumer")
consumer_thread.start()
print(f"[{datetime.now().strftime('%H:%M:%S')}] 消费者线程已启动")


# ==================== 路由 ====================

@live_api.route('/')
@check_session_go_login_decorator
def danmu_page():
    """弹幕监控主页"""
    global generator

    # 重新获取生成器（确保是最新的）
    generator = get_generator()
    if generator is None:
        return "系统未就绪，请稍后重试", 503

    # ✅ 重置生成器（停止旧的，创建新的）
    generator = reset_generator()

    login_user = session.get("login_user")
    user_credential:Credential = LoginCookie.dic_to_credential(login_user)

    room_data = room_service_file.get_default_live_room()
    room_id = "000000"
    room_owner = "未设置房间"

    if room_data:
        room_id = room_data["room_id"]
        room_owner = room_data["room_user_name"]
        generator.connect(user_credential, room_id)
        generator.start()
        print(f"✅ 生成器已启动，房间: {room_id}")

    return render_template('danmu.html',
                           nick_name=login_user["nick_name"],
                           user_face=login_user["user_face"],
                           room_id=room_id,
                           room_owner=room_owner)


@live_api.route('/danmu/start/<int:room_id>')
@check_session_2api_decorator
def start_generator(room_id: int):
    """启动消息生成器"""
    try:
        login_user = session.get("login_user")
        user_credential:Credential = LoginCookie.dic_to_credential(login_user)
        generator.connect(user_credential, room_id)

        if generator.start():
            return {
                'code': 0,
                'message': f'正在监听[{room_id}]',
                'type': 1,
                'generator_id': generator.generator_id,
                'timestamp': datetime.now().isoformat()
            }
        else:
            return {
                'code': 0,
                'type': 1,
                'message': f'已停止监听[{room_id}]',
                'generator_id': generator.generator_id,
                'timestamp': datetime.now().isoformat()
            }
    except Exception as e:
        return {'code': -1, 'message': str(e)}


@live_api.route('/danmu/stop/<int:room_id>')
@check_session_2api_decorator
def stop_generator(room_id: int):
    """停止消息生成器"""
    try:
        generator.stop()
        return {
            'code': 0,
            'type': 0,
            'message': f'关闭监听[{room_id}]',
            'timestamp': datetime.now().isoformat()
        }
    except Exception as e:
        return {'code': -1, 'message': str(e)}


@live_api.route('/api/status')
def get_status():
    """获取系统状态"""
    return {
        'generator_running': generator.running,
        'consumer_running': consumer_thread.is_alive(),
        'queue_size': message_queue.qsize(),
        'generator_id': generator.generator_id,
        'timestamp': datetime.now().isoformat()
    }


@live_api.route('/api/clear')
def clear_queue():
    """清空消息队列"""
    cleared = 0
    while not message_queue.empty():
        try:
            message_queue.get_nowait()
            cleared += 1
        except:
            break

    return {
        'status': 'success',
        'message': f'已清空 {cleared} 条消息',
        'cleared': cleared,
        'timestamp': datetime.now().isoformat()
    }


@live_api.route('/api/test')
def test_message():
    """发送测试消息"""
    test_msg = {
        'id': random.randint(1000, 9999),
        'type': 'info',
        'content': '这是一条测试消息',
        'timestamp': datetime.now().isoformat(),
        'generator_id': 'test',
        'value': random.randint(1, 100)
    }
    socketio.emit('new_message', test_msg)

    return {
        'status': 'success',
        'message': '测试消息已发送',
        'timestamp': datetime.now().isoformat()
    }


# ==================== SocketIO 事件 ====================

@socketio.on('connect')
def handle_connect():
    """客户端连接"""
    print(f'✅ 客户端连接成功: {request.sid}')

    emit('connected', {
        'message': '成功连接到服务器',
        'timestamp': datetime.now().isoformat(),
        'sid': request.sid
    })

    emit('new_message', {
        'id': 0,
        'type': 'success',
        'content': '欢迎连接到服务器！',
        'timestamp': datetime.now().isoformat(),
        'generator_id': 'system',
        'value': 0
    })


@socketio.on('disconnect')
def handle_disconnect():
    """客户端断开"""
    print(f'❌ 客户端断开连接: {request.sid}')


@socketio.on('request_status')
def handle_status_request():
    """状态请求"""
    emit('status_update', {
        'generator_running': generator.running,
        'queue_size': message_queue.qsize(),
        'timestamp': datetime.now().isoformat()
    })