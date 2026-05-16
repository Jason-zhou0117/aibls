from typing import Any

from bilibili_api import Credential, live, Danmaku
from bilibili_api.live import LiveRoom
from flask import current_app


class BiliLiveService:

    @staticmethod
    async def get_live_info( room_id: str, login_user_credential: Credential) -> dict[str, Any] | None:
        logger = current_app.logger
        try:
            # 根据房间号，获取房主的用户信息
            logger.info(f"开始获取B站房间信息：room_id={room_id}")
            # 获取房间信息
            live_obj = live.LiveRoom(int(room_id), login_user_credential)
            room_info: dict =  await live_obj.get_room_info()

            logger.info(f"获取B站房间信息如下：是Room_ID={room_id}的信息:{room_info}")
            return room_info
        except Exception as e:
            logger.info(e)
            return None

    @staticmethod
    async def get_gif_config( room_id: str) -> dict[str, Any] | None:
        logger = current_app.logger
        try:
            # 根据房间号，获取房主的用户信息
            logger.info(f"开始获取B站房间的礼物信息：room_id={room_id}")
            # 获取房间信息
            # live_obj = live.get_gift_config(int(room_id))
            gift_common: dict = await live.get_gift_config(int(room_id))

            logger.info(f"获取B站房间的礼物信息下：是Room_ID={room_id}的信息:{gift_common}")
            return gift_common
        except Exception as e:
            logger.info(e)
            return None

    @staticmethod
    async def get_gif_common( room_id: str,login_user_credential: Credential) -> dict[str, Any] | None:
        logger = current_app.logger
        try:
            # 根据房间号，获取房主的用户信息
            logger.info(f"开始获取B站房间的礼物信息：room_id={room_id}")
            # 获取房间信息
            live_obj : LiveRoom = live.LiveRoom(int(room_id),login_user_credential)
            gift_common: dict = await live_obj.get_gift_common()

            logger.info(f"获取B站房间的礼物信息下：是Room_ID={room_id}的信息:{gift_common}")
            return gift_common
        except Exception as e:
            logger.info(e)
            return None

    @staticmethod
    async def send_danmu(room_id: int, login_user_credential: Credential,text_damnu:str):
        logger = current_app.logger
        try:
            # 根据房间号，获取房主的用户信息
            logger.info(f"发送弹幕：room_id={room_id}，弹幕：{text_damnu}")
            # 获取房间信息
            live_obj = live.LiveRoom(room_id, login_user_credential)
            danmu = Danmaku(text_damnu)
            await live_obj.send_danmaku(danmu,room_id)

        except Exception as e:
            logger.info(f"发送弹幕失败：{e}")

bili_live_service = BiliLiveService()