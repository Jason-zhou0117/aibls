# aibls/views/room_route.py
import logging

from bilibili_api import Credential
from flask import session, request, jsonify, current_app

from aibls.decorators import check_session_2api_decorator
from aibls.models import LoginCookie
from aibls.services import room_service_file
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

@room_api.route('/api/updateroom', methods=['GET', 'POST'])
@check_session_2api_decorator
def update_room():
    """更新房间信息"""

    logger = current_app.logger
    try:
        room_id = _get_room_id_from_request()
        if room_id is None:
            return jsonify({"code": 2102, "message": "请输入房间号"})

        credential = _get_login_credential()
        resp = room_service_file.save_room(credential, str(room_id))
        logger.info(f"保存房间数据结果: {resp}")

        return jsonify(resp.to_dict())

    except Exception as e:
        logger.error(f"更新房间信息失败: {e}")
        return jsonify({"code": -210001, "message": str(e)})


@room_api.route("/api/searchrooms")
@check_session_2api_decorator
def search_room_list():
    """搜索房间列表"""

    logger = current_app.logger
    try:
        login_user = session.get("login_user")
        filters = {"login_id": login_user["login_id"]}

        # 添加筛选条件
        room_id = request.args.get("room_id")
        if room_id:
            filters["room_id"] = room_id

        result_data = room_service_file.load_rooms_by_filter(filters)

        return jsonify({
            "code": 0,
            "message": "查询成功",
            "rooms": result_data["items"],
            "count": result_data["count"]
        })

    except Exception as e:
        logger.error(f"搜索房间列表失败: {e}")
        return jsonify({"code": -210002, "message": str(e)})


@room_api.route('/api/updatefav', methods=['GET', 'POST'])
@check_session_2api_decorator
def update_fav():
    """更新收藏状态"""

    logger = current_app.logger

    try:
        room_id = request.form.get("room_id")
        is_fav = request.form.get("is_favorites")

        if not room_id:
            return jsonify({"code": 2102, "message": "请输入房间号"})
        if is_fav is None:
            return jsonify({"code": 2103, "message": "请输入收藏信息"})

        login_user = session.get("login_user")
        resp = room_service_file.set_favorites(room_id, login_user["login_id"], is_fav)

        return jsonify(resp.to_dict())

    except Exception as e:
        logger.error(f"更新收藏状态失败: {e}")
        return jsonify({"code": -210001, "message": str(e)})

