# aibls/views/room_route.py
import asyncio

from bilibili_api import Credential
from flask import session, request, jsonify, current_app

from aibls.decorators import check_session_2api_decorator
from aibls.models import LoginCookie
from aibls.services import room_service
from aibls.views import room_api

def _get_login_credential() -> Credential:
    """获取当前登录用户的凭证"""
    login_user = session.get("login_user")
    return LoginCookie.dic_to_credential(login_user)


def _get_room_id_from_request() -> int | None:
    """从请求中获取房间号"""
    room_id_str = request.form.get("room_id", "")
    if not room_id_str:
        return None
    return int(room_id_str)


# ==================== 路由 ====================

@room_api.route('/api/update_room', methods=['GET', 'POST'])
@check_session_2api_decorator
def update_room():
    """更新房间信息"""
    logger = current_app.logger
    try:
        room_id = _get_room_id_from_request()
        if room_id is None:
            return jsonify({"code": 2102, "message": "请输入房间号"})

        credential = _get_login_credential()
        result,message = asyncio.run(room_service.set_default_room(room_id,credential))
        logger.debug(f"保存房间数据结果:result={result},message={message}")
        if result:
            return jsonify({"code": 0, "message": "更新成功"})
        else:
            return jsonify({"code": -210001, "message": message})
    except Exception as e:
        logger.error(f"更新房间信息失败: {e}",exc_info=True)
        return jsonify({"code": -210001, "message": str(e)})



@room_api.route('/api/room/<room_id>', methods=['DELETE'])
@check_session_2api_decorator
def delete_video(room_id):
    """删除房间"""
    success, message = room_service.delete_room(room_id)
    if not success:
        return jsonify({'code': -1, 'message': message})

    return jsonify({'code': 0, 'message': message})

@room_api.route("/api/searchrooms")
@check_session_2api_decorator
def search_room_list():
    """搜索房间列表"""
    logger = current_app.logger
    try:
        result_data = room_service.get_all_rooms()

        return jsonify({
            "code": 0,
            "message": "查询成功",
            "rooms": result_data,
            "count": len(result_data)
        })
    except Exception as e:
        logger.error(f"搜索房间列表失败: {e}",exc_info=True)
        return jsonify({"code": -210002, "message": str(e)})


