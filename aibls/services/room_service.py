import asyncio
import logging
from typing import Any, List

from bilibili_api import Credential, live, user

from aibls.daos.room_dao import RoomDAO
from aibls.exceptions.BLSException import BLSException
from aibls.models.rooms import RoomInfo
from aibls.services.response import ResponseResult

logger = logging.getLogger(__name__)

class RoomService:

    def __init__(self):
        self.room_dao = RoomDAO()

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

    def save_room(self, login_user_credential:Credential,room_id:str) -> ResponseResult:
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
                    room_key = f"{room_info["room_info"]["room_id"]}_{login_user_credential.dedeuserid}"
                    # 构建需要更新到数据库的房间信息
                    room_data: dict[str, Any] = self.__from_dict_to_db(room_info, room_owner,
                                                                       login_user_credential.dedeuserid,room_key)
                    logger.info("保存的房間信息為：{}".format(room_data))
                    # 保存房间数据
                    self.room_dao.save(room_key,room_data)
                    #更新其他用户同样room_id的信息
                    self.room_dao.update_batch(login_user_credential.dedeuserid,room_info["room_info"]["room_id"],room_data)

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

    def load_rooms_by_filter(self,filters: dict) -> dict:
        """
        根据筛选条件获取房间信息
        :param filters: 筛选条件
        :return: 数据字典，带count,items中是房间信息的数据字典
        """
        room_datas : List[RoomInfo] = self.room_dao.find_by_dict_orderby(filters)
        out_items = [roomInfo.to_dict() for roomInfo in room_datas]
        return {
            "count": len(out_items),
            "items": out_items
        }

    def set_favorites(self,room_id:str,login_id:str,is_favorites:str) -> ResponseResult:
        """
        更新收藏涨停
        :param room_id: 房间号
        :param login_id: 当前登录用户ID
        :param is_favorites: 是否收藏
        :return:
        """
        try:
            room_key = f"{room_id}_{login_id}"
            room_data = {"is_favorites":is_favorites}
            # 保存房间数据
            self.room_dao.save(room_key, room_data)

            return ResponseResult(code=0, message="更新收藏信息成功！")
        except Exception as e:
            logger.info(f"更新收藏信息失败:{e}")
            return ResponseResult(code=-20001, message=f"更新收藏信息失败:{e}")
