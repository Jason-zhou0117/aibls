# aibls/views/live_route.py
"""弹幕API的蓝图定义"""

import random
from datetime import datetime

from bilibili_api import Credential
from flask import session, render_template, request
from flask_socketio import emit

from aibls.decorators import check_session_2api_decorator, check_session_go_login_decorator
from aibls.models import LoginCookie
from aibls.services import room_service
from aibls.views import live_api
from aibls.stock_io import socketio, message_queue
from aibls.services.danmu_robot import create_robot, PERSONALITIES


# live_route.py
from aibls.generator_manager import get_generator, reset_generator

# 使用
generator = get_generator()


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

    # 【新增】创建机器人
    from aibls.services.danmu_robot import create_robot
    robot = create_robot(personality="tsundere")  # 默认傲娇型
    robot.test_mode = False  # 生产环境关闭测试模式

    # 设置机器人uid（用于过滤自回）
    generator.set_robot(robot)
    generator.set_bot_uid(user_credential.dedeuserid)

    room_data = room_service.get_default_room()
    room_id = "000000"
    room_owner = "未设置房间"

    if room_data:
        room_id = room_data["id"]
        room_owner = room_data["owner_name"]
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
    """获取系统状态"""
    # 延迟导入，避免循环导入
    from aibls.services.message_consumer import message_consumer

    consumer_running = False
    if message_consumer:
        consumer_running = message_consumer.running

    return {
        'generator_running': generator.running if generator else False,
        'consumer_running': consumer_running,
        'queue_size': message_queue.qsize(),
        'generator_id': generator.generator_id if generator else None,
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

# ==================== 新增：机器人控制路由 ====================
@live_api.route('/robot/status')
def robot_status():
    """获取机器人状态"""
    global generator
    if generator and generator.robot:
        return generator.robot.get_status()
    return {'code': -1, 'message': '机器人未初始化'}


@live_api.route('/robot/enable')
def robot_enable():
    """启用机器人"""
    global generator
    if generator and generator.robot:
        generator.robot.enabled = True
        return {'code': 0, 'message': '机器人已启用'}
    return {'code': -1, 'message': '机器人未初始化'}


@live_api.route('/robot/disable')
def robot_disable():
    """禁用机器人"""
    global generator
    if generator and generator.robot:
        generator.robot.enabled = False
        return {'code': 0, 'message': '机器人已禁用'}
    return {'code': -1, 'message': '机器人未初始化'}


@live_api.route('/robot/set_personality/<personality_id>')
def robot_set_personality(personality_id):
    """切换性格"""
    global generator
    if generator and generator.robot:
        if generator.robot.set_personality(personality_id):
            name = PERSONALITIES.get(personality_id, {}).get('name', personality_id)
            return {'code': 0, 'message': f'已切换至{name}'}
        return {'code': -1, 'message': f'无效的性格: {personality_id}'}
    return {'code': -1, 'message': '机器人未初始化'}


@live_api.route('/robot/set_test_mode/<int:enable>')
def robot_set_test_mode(enable):
    """设置测试模式"""
    global generator
    if generator and generator.robot:
        generator.robot.test_mode = (enable == 1)
        return {'code': 0, 'message': f'测试模式已{"开启" if enable else "关闭"}'}
    return {'code': -1, 'message': '机器人未初始化'}


@live_api.route('/robot/get_personalities')
def robot_get_personalities():
    """获取所有可用性格"""
    return {
        'code': 0,
        'personalities': [
            {'id': pid, 'name': config['name']}
            for pid, config in PERSONALITIES.items()
        ]
    }