
"""弹幕API的蓝图定义"""
import logging
from typing import Any

from bilibili_api import Credential
from flask import session, render_template

from aibls.decorators.decorator import check_session_go_login_decorator, check_session_2api_decorator
from aibls.models.users import LoginCookie
from aibls.services.danmu_listener import DanmuListener, BilibiliDanmuListener
from aibls.services.danmu_service import DanmuService
from aibls.views import live_api
from stock_io import socketio

"""日志对象的记录"""
logger = logging.getLogger(__name__)

# 存储当前活动的弹幕监听线程
active_danmu_threads = {}

danmu_service = DanmuService()

@live_api.route('/danmu/<int:room_id>')
@check_session_go_login_decorator
def danmu_form(room_id: int):
    """
    更新房间信息的API
    :return:
    """
    login_user: dict[str, Any] = session.get("login_user")
    return render_template('danmu.html', nick_name=login_user["nick_name"],
                           user_face=login_user["user_face"],room_id=room_id)


@live_api.route('/danmu/start/<int:room_id>')
@check_session_2api_decorator
def start_listener(room_id: int):
    """
    开始监听指定直播间
    前端通过这个接口启动监听
    """

    # 检查是否已经在监听该房间
    if room_id in active_danmu_threads and active_danmu_threads[room_id].is_running:
        return {'code': 0, 'message': f'已在监听房间 {room_id}'}

    login_user: dict[str, Any] = session.get("login_user")
    user_credential: Credential = LoginCookie.dic_to_credential(login_user)
    # 创建并启动新的监听线程
    listener = BilibiliDanmuListener(user_credential,room_id, message_to_client)
    listener.start()
    logger.debug("已开始监听房间")
    active_danmu_threads[room_id] = listener

    return {'code': 0, 'message': f'开始监听房间 {room_id}'}


@live_api.route('/danmu/stop/<int:room_id>')
def stop_listener(room_id: int):
    """停止监听"""
    logger.debug("已开始停止监听房间……")
    #如果房间号存在 且 正在执行
    if room_id in active_danmu_threads and active_danmu_threads[room_id].is_running:
        #停止
        active_danmu_threads[room_id].stop()
        del active_danmu_threads[room_id]
        return {'code': 0, 'message': f'停止监听房间{room_id}'}

    return {'code': 0, 'message': f'未监听房间{room_id}'}

@socketio.on('connect')
def handle_connect():
    """处理客户端连接"""
    print('客户端已连接')

@socketio.on('disconnect')
def handle_disconnect():
    """处理客户端断开"""
    print('客户端已断开')


def message_to_client(message_type:str, message:dict[str, Any]):
    """
    对客户端进行推送
    :param message_type: 消息类型
    :param message: 消息内容
    :return:
    """
    socketio.emit(message_type, message)