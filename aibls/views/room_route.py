import asyncio
import logging
from typing import Any

from bilibili_api import Credential
from flask import Blueprint, session, request, jsonify, render_template

from aibls.decorators.decorator import check_session_2api_decorator, check_session_go_login_decorator
from aibls.models.users import LoginCookie
from aibls.services.response import ResponseResult
from aibls.services.room_service import RoomService
from aibls.views import room_api

"""日志对象的记录"""
logger = logging.getLogger(__name__)

room_service = RoomService()

@room_api.route('/api/updateroom', methods=['GET','POST'])
@check_session_2api_decorator
def update_room():
    """
    更新房间信息的API
    :return:
    """
    api_resp = {"code": 0, "message": "成功"}
    try:
        #获取房间号
        room_id_str = request.form["room_id"]
        if room_id_str == "":
            api_resp = {"code":2102,"text":"请输入房间号"}
        room_id :int = int(room_id_str)

        #准备当前登录用户
        login_user : dict[str,Any] = session.get("login_user")
        user_credential:Credential = LoginCookie.dic_to_credential(login_user)
        resp: ResponseResult = room_service.save_room(user_credential, room_id_str)
        logger.info("保存房间数据的结果：{}".format(resp))
        api_resp = resp.to_dict()
    except Exception as e:
        logger.error(e)
        api_resp = {"code": -210001, "message": str(e)}
    finally:
        return jsonify(api_resp)

@room_api.route("/api/searchrooms")
@check_session_2api_decorator
def search_room_list():
    api_resp = {"code": 0, "message": "查询成功"}
    try:
        login_user : dict[str,Any] = session.get("login_user")
        filters:dict = {"login_id":login_user["login_id"]}
        #如果页面传输的筛选条件
        room_id :str = request.args.get("room_id")
        if room_id and room_id != "":
            filters["room_id"] = room_id
        #查询数据
        result_data = room_service.load_rooms_by_filter(filters)
        api_resp["rooms"] = result_data["items"]
        api_resp["count"] = result_data["count"]

    except Exception as e:
        logger.error(e)
        api_resp = {"code": -210002, "text": str(e)}
    finally:
        return jsonify(api_resp)

@room_api.route('/api/updatefav', methods=['GET','POST'])
@check_session_2api_decorator
def update_fav():
    api_resp = {"code": 0, "message": "成功"}
    try:
        # 获取房间号
        room_id_str = request.form["room_id"]
        if room_id_str == "":
            api_resp = {"code": 2102, "text": "请输入房间号"}

        is_fav:str = request.form["is_favorites"]
        if is_fav == "":
            api_resp = {"code": 2103, "text": "请输入收藏信息"}

        # 准备当前登录用户
        login_user: dict[str, Any] = session.get("login_user")
        resp: ResponseResult = room_service.set_favorites(room_id_str,login_user["login_id"],is_fav)
        api_resp = resp.to_dict()
    except Exception as e:
        logger.error(e)
        api_resp = {"code": -210001, "message": str(e)}
    finally:
        return jsonify(api_resp)