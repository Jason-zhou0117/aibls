
"""弹幕API的蓝图定义"""
import asyncio
import logging
import queue
import random
import threading
import time
from datetime import datetime
from typing import Any

from bilibili_api import Credential, live, sync
from flask import session, render_template, request
from flask_socketio import emit

from aibls.decorators.decorator import check_session_2api_decorator, check_session_go_login_decorator
from aibls.models.users import LoginCookie
from aibls.services.danmu_handler import AsyncMessageGenerator

from aibls.views import live_api
from aibls.views.room_route import room_service

from stock_io import socketio, app, message_queue

"""日志对象的记录"""
logger = logging.getLogger(__name__)


# 创建生成器实例
generator = AsyncMessageGenerator(message_queue)

def message_consumer():
    """消息消费者函数 - 独立线程运行"""
    print(f"[{datetime.now().strftime('%H:%M:%S')}] 消息消费者线程已启动")

    stats = {
        'total_pushed': 0,
        'last_push_time': None,
        'queue_size_history': []
    }

    while True:
        try:
            # 从队列获取消息，设置超时
            try:
                if message_queue.empty():
                    time.sleep(0.1)
                    logger.debug("消息队列为空，不做处理")
                    continue

                message = message_queue.get(timeout=0.5)

                # 推送消息到前端
                try:
                    # 添加处理时间戳
                    message['pushed_at'] = datetime.now().isoformat()
                    logger.info(f"从消息队列中获取消息：{message},并准备推送……")
                    # 根据消息类型推送到前端
                    msg_type = message.get("type")

                    if msg_type == "video_command":
                        # 视频指令使用独立事件名
                        socketio.emit('video_command', message)
                        logger.info(f"已推送视频指令: {message.get('uname')}")
                    else:
                        # 其他消息类型（danmaku,gift,welcome,guard,super_chat）
                        socketio.emit(msg_type, message)

                    logger.info(
                        f"[{datetime.now().strftime('%H:%M:%S')}] 消息队列剩余: {message_queue.qsize()}")

                    # 更新统计
                    stats['total_pushed'] += 1
                    stats['last_push_time'] = datetime.now().isoformat()
                    stats['queue_size_history'].append(message_queue.qsize())

                    # 保持历史记录在合理范围
                    if len(stats['queue_size_history']) > 50:
                        stats['queue_size_history'].pop(0)

                except Exception as e:
                    logger.error(f"推送消息错误: {e}")

                # 标记任务完成
                message_queue.task_done()

            except queue.Empty:
                # 队列为空，继续循环
                time.sleep(0.1)
                continue

        except Exception as e:
            logger.error(f"消费消息错误: {e}")
            time.sleep(0.5)






# 启动消费者线程
consumer_thread = threading.Thread(target=message_consumer, daemon=True, name="MessageConsumer")
consumer_thread.start()
print(f"[{datetime.now().strftime('%H:%M:%S')}] 消费者线程已启动")


@live_api.route('/')
@check_session_go_login_decorator
def danmu_page():
    """主页"""
    global generator  # 添加这一行

    # 完全销毁旧的
    if generator:
        generator.stop()
        # 等待线程完全结束
        time.sleep(0.5)
        generator = None

    # 创建全新的
    generator = AsyncMessageGenerator(message_queue)

    login_user = session.get("login_user")
    user_credential = LoginCookie.dic_to_credential(login_user)

    room_data = room_service.get_default_live_room()
    room_id="000000"
    room_owner="未设置房间"

    if room_data is not None:
        room_id = room_data["room_id"]
        room_owner = room_data["room_user_name"]
        generator.connect(user_credential, room_id)
        generator.start()
        print(f"🎉 全新 generator 创建完成，房间: {room_id}")

    # if generator.running:
    #     generator.stop()
    #
    # login_user: dict[str, Any] = session.get("login_user")
    # user_credential: Credential = LoginCookie.dic_to_credential(login_user)
    #
    # room_data = room_service.get_default_live_room()
    # room_id="000000"
    # room_owner="未设置房间"
    #
    # if room_data is not None:
    #     room_id = room_data["room_id"]
    #     room_owner=room_data["room_user_name"]
    #     generator.connect(user_credential,room_id)
    #     generator.start()

    return render_template('danmu.html',nick_name=login_user["nick_name"],
                           user_face=login_user["user_face"],room_id=room_id,room_owner=room_owner)


@live_api.route('/danmu/start/<int:room_id>')
@check_session_2api_decorator
def start_generator(room_id:int):
    try:
        """启动消息生成器"""
        login_user: dict[str, Any] = session.get("login_user")
        user_credential: Credential = LoginCookie.dic_to_credential(login_user)
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
                'message': f'正在监听[{room_id}]',
                'generator_id': generator.generator_id,
                'timestamp': datetime.now().isoformat()
            }
    except Exception as e:
        return {
            'code': -1,
            'message': str(e)
        }


@live_api.route('/danmu/stop/<int:room_id>')
@check_session_2api_decorator
def stop_generator(room_id:int):
    try:
        """停止消息生成器"""
        generator.stop()
        return {
            'code': 0,
            'type': 0,
            'message': f'关闭监听[{room_id}]',
            'timestamp': datetime.now().isoformat()
        }
    except Exception as e:
        return {
            'code': -1,
            'message': str(e)
        }


@live_api.route('/api/status')
def get_status():
    """获取系统状态"""
    # 获取消费者线程状态
    consumer_running = consumer_thread.is_alive() if consumer_thread else False

    return {
        'generator_running': generator.running,
        'consumer_running': consumer_running,
        'queue_size': message_queue.qsize(),
        'generator_id': generator.generator_id,
        'timestamp': datetime.now().isoformat()
    }


@live_api.route('/api/clear')
def clear_queue():
    """清空消息队列"""
    size = message_queue.qsize()
    cleared = 0

    while not message_queue.empty():
        try:
            message_queue.get_nowait()
            cleared += 1
        except queue.Empty:
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

    # 直接推送到前端
    socketio.emit('new_message', test_msg)

    return {
        'status': 'success',
        'message': '测试消息已发送',
        'timestamp': datetime.now().isoformat()
    }


@socketio.on('connect')
def handle_connect():
    """处理客户端连接"""
    print(f'客户端连接成功: {request.sid}')

    # 发送连接成功消息
    emit('connected', {
        'message': '成功连接到服务器',
        'timestamp': datetime.now().isoformat(),
        'sid': request.sid
    })

    # 发送一条欢迎消息
    welcome_msg = {
        'id': 0,
        'type': 'success',
        'content': '欢迎连接到服务器！消息推送系统已启动。',
        'timestamp': datetime.now().isoformat(),
        'generator_id': 'system',
        'value': 0
    }
    emit('new_message', welcome_msg)


@socketio.on('disconnect')
def handle_disconnect():
    """处理客户端断开连接"""
    print(f'客户端断开连接: {request.sid}')


@socketio.on('request_status')
def handle_status_request():
    """处理状态请求"""
    status = {
        'generator_running': generator.running,
        'queue_size': message_queue.qsize(),
        'timestamp': datetime.now().isoformat()
    }
    emit('status_update', status)





