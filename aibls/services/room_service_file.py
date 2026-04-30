import asyncio
import json
import logging
import os
from typing import Any

from bilibili_api import Credential, live, user

from aibls.exceptions.BLSException import BLSException
from aibls.services.response import ResponseResult
from aibls.settings import ROOM_DIR

logger = logging.getLogger(__name__)

class RoomServiceFile:

    def get_folder_path(self)-> str:
        """
        获取默认房间信息的目录路径
        """
        logger.debug(f"获取默认房间文件路径...")

        # 目标目录
        dir_path = ROOM_DIR
        logger.debug(f"获取默认房间文件路径:{dir_path}")
        # 如果目录不存在，则生成目录
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)
        return dir_path

    def get_file_path(self) -> str:
        """
        获取默认房间信息的路径
        """
        folder_path = self.get_folder_path()
        file_name = "default_room.json"
        file_path = os.path.join(folder_path, file_name)
        return file_path

    def get_live_room_info(self,room_id:int,login_user_credential:Credential) -> dict:
        """
        实时获取房间信息
        :param room_id: 房间号
        :param login_user_credential: 当前登录用户凭据
        :return: 房间的基本信息
        """
        try:
            # 获取房间信息
            live_obj = live.LiveRoom(int(room_id), login_user_credential)
            room_info: dict = asyncio.run(live_obj.get_room_info())
            logger.info("如下是Room_ID={}的信息:{}".format(room_id, room_info))
        except Exception as e:
            logger.error(f"实时获取房间信息时出错：{e}")
            raise BLSException(-20001, "实时获取房间信息时出错")

    def get_default_live_room(self) -> Any:
        """
        获取默认需要检控官的房间信息
        :return: 房间的基本信息
        """
        try:
            #获取默认房间信息的数据
            file_path = self.get_file_path()
            logger.debug(f"获取默认房间文件路径:{file_path}")
            if not os.path.exists(file_path):
                return None

            # 方法2：直接使用json.load()（推荐）
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)  # 直接读取并转为Python对象
                return data
        except Exception as e:
            logger.error(f"获取默认房间信息时出错：{e}")
            raise BLSException(-20001, "获取默认房间信息时出错")

    def save_room(self, login_user_credential: Credential, room_id: str) -> ResponseResult:
        """
        保存房间（含房主）的信息
        :param login_user_credential: 当前登录用户的凭据
        :param room_id: 房间号
        :return: 无
        """
        try:
            # 获取房间信息
            live_obj = live.LiveRoom(int(room_id), login_user_credential)
            room_info: dict = asyncio.run(live_obj.get_room_info())
            logger.info("如下是Room_ID={}的信息:{}".format(room_id, room_info))
            try:
                # 根据房间号，获取房主的用户信息
                room_owner_user = user.User(room_info["room_info"]["uid"], credential=login_user_credential)
                room_owner: dict[str, Any] = asyncio.run( room_owner_user.get_user_info())
                logger.info("如下是Room_ID={}的房主（uid={})的信息:{}".format(room_id, room_info["room_info"]["uid"],
                                                                                room_owner))
                try:
                    room_key = f"{room_info['room_info']['room_id']}_{login_user_credential.dedeuserid}"
                    room_data: dict[str, Any] = self.__from_dict_to_db(room_info, room_owner,
                                                                       login_user_credential.dedeuserid, room_key)
                    #获取文件路径
                    file_path = self.get_file_path()
                    #保存到指定路径
                    with open(file_path, 'w', encoding='utf-8') as f:
                        json.dump(room_data, f, ensure_ascii=False, indent=2)  # indent使格式更美观

                    return ResponseResult(code=0, message="保存房间信息成功！")
                except Exception as e:
                    logger.info(e)
                    return ResponseResult(code=-20003, message="保存房间信息时出错！")
            except Exception as e:
                logger.info(e)
                return ResponseResult(code=-20002, message="获取房主信息时出错！")
        except Exception as e:
            logger.info(e)
            return ResponseResult(code=-20001, message="获取房间信息时出错！")

    def __from_dict_to_db(self,room_info: dict[str, Any], room_owner: dict[str, Any],
                          login_id: str,room_key:str) -> dict[str, Any]:
        """
        (内部）将房间信息和房主信息的字典，转换为房间的DB实体
        :param room_info: 房间的信息
        :param room_owner: 房主的信息
        :return:
        """
        return {
            "room_key": room_key,
            "room_id": room_info["room_info"]["room_id"],
            "room_name": room_info["room_info"]["title"],
            "room_uid": room_info["room_info"]["uid"],
            "room_cover": room_info["room_info"]["cover"],
            "room_user_name": room_owner["name"],
            "room_user_face": room_owner["face"],
            "login_id": login_id
        }

    def set_favorites(self, room_id: str, login_id: str, is_favorites: str) -> ResponseResult:
        return ResponseResult(code=0, message="成功")

    def load_rooms_by_filter(self, filters: dict) -> dict:
        """
        筛选房间信息
        """
        default_room = self.get_default_live_room()
        if default_room is None:
            return {
                "count": 0,
                "items": []
            }
        else:
            return {
                "count": 1,
                "items": [default_room]
            }

room_service_file = RoomServiceFile()