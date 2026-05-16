from bilibili_api import Credential
from flask import current_app

from aibls.models.database import db, RoomInfo
from aibls.services.bili_live_service import bili_live_service
from aibls.services.bili_user_service import bili_user_service


class RoomService:

    @staticmethod
    async def set_default_room(room_id,login_user_credential: Credential):
        """设置指定房间为默认房间，并确保只有一条记录为默认"""
        logger = current_app.logger
        try:
            # 1. 先将所有房间的 is_default 设为 '0'
            RoomInfo.query.update({RoomInfo.is_default: '0'})
            #获取房间信息
            bili_room = await bili_live_service.get_live_info(room_id, login_user_credential)
            if bili_room is not None:
                bili_room_info = bili_room.get("room_info")
                bili_owner_id = bili_room_info.get("uid")
                # 根据房间号，获取房主的用户信息
                room_owner = await bili_user_service.get_user_info(bili_owner_id, login_user_credential)

                # 2. 再设置指定房间为默认
                room = RoomInfo.query.get(room_id)

                if not room:
                    room = RoomInfo(
                        id=room_id,
                        title = bili_room_info.get("title"),
                        cover_url = bili_room_info.get("cover"),
                        owner_id = bili_owner_id,
                        owner_name = room_owner.get("name"),
                        owner_face = room_owner.get("face"),
                        is_default = "1",
                    )
                    db.session.add(room)
                else:
                    room.title = bili_room_info.get("title")
                    room.cover_url = bili_room_info.get("cover")
                    room.ower_name = room_owner.get("name")
                    room.owner_face = room_owner.get("face")
                    room.is_default = '1'
                db.session.commit()
                return True, f"房间 {room_id} 已设为默认"
            else:
                return False, f"房间 {room_id} 不存在"
        except Exception as e:
            db.session.rollback()
            logger.error(f"更换默认房间时出错：{e}")
            return False, str(e)

    @staticmethod
    def get_default_room():
        """获取默认房间"""
        room_data = RoomInfo.query.filter_by(is_default='1').first()
        if room_data is None:
            return None
        return room_data.to_dict()

    @staticmethod
    def get_room_data(room_id):
        """获取默认房间"""
        room_data = RoomInfo.query.filter_by(id=room_id).first()
        if room_data is None:
            return None
        return room_data.to_dict()

    @staticmethod
    def get_default_room_id():
        """获取默认房间 ID"""
        room = RoomInfo.query.filter_by(is_default='1').first()
        return room.id if room else None

    @staticmethod
    def get_all_rooms():
        """获取所有房间信息（列表格式）"""
        rooms = RoomInfo.query.all()
        return [r.to_list_dict() for r in rooms]

    @staticmethod
    def delete_room(room_id):
        """获取默认房间"""
        room_data = RoomInfo.query.filter_by(id=room_id).first()
        if room_data is None:
            return None
        db.session.delete(room_data)
        db.session.commit()
        return True, "删除成功"

room_service = RoomService()