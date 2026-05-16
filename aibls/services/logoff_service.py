from datetime import datetime, time
import json
from typing import List

from flask import current_app
from sqlalchemy import or_, and_, Time, cast

from aibls import db
from aibls.models import LogOffUser, RoomInfo, LogOffRoom
from aibls.utils import snowflake


class LogoffService:

    @staticmethod
    def get_all_users():
        """获取所有Session中（列表格式）"""
        users = LogOffUser.query.all()
        return [u.to_dict() for u in users]


    @staticmethod
    def get_opened_users() -> List[LogOffUser]:
        """获取所有Session中（列表格式）"""
        users = LogOffUser.query.filter_by(is_open='Y').all()
        return users

    @staticmethod
    def get_user_by_uid(uid:int) -> LogOffUser:
        """根据UID获取用户"""
        return LogOffUser.query.filter_by(user_id=uid).first()



    @staticmethod
    def add_user(logoff_user,is_open = "Y"):
        """添加VIP用户"""
        # 检查是否已存在
        existing:LogOffUser = LogOffUser.query.filter_by(user_id=logoff_user.get("login_id")).first()
        credential = {
            "sess_data": logoff_user.get("sess_data"),
            "buvid3": logoff_user.get("buvid3"),
            "bili_jct": logoff_user.get("bili_jct"),
            "ac_time_value": logoff_user.get("ac_time_value"),
            "dede_user_id": logoff_user.get("dede_user_id"),
        }
        if existing:
            # 更新现有 Session
            existing.user_name = logoff_user.get("nick_name")
            existing.user_face = logoff_user.get("user_face")
            existing.user_face = logoff_user.get("user_face")
            existing.is_open = is_open
            existing.credential = json.dumps(credential, ensure_ascii=False)
        else:
            existing = LogOffUser(
                user_id= logoff_user.get("login_id"),
                user_name=logoff_user.get("nick_name"),
                user_face=logoff_user.get("user_face"),
                is_open= is_open,
                credential= json.dumps(credential, ensure_ascii=False)
            )
            db.session.add(existing)
        db.session.commit()
        return existing.to_dict(), None

    @staticmethod
    def update_user(uid, name=None, face=None,is_open=None):
        """更新登录用户信息"""
        user = LogOffUser.query.filter_by(user_id=int(uid)).first()
        if not user:
            return None, "用户不存在"

        if name:
            user.user_name = name
        if is_open:
            user.is_open = is_open
        if face:
            user.face = face

        db.session.commit()
        return user.to_dict(), None

    @staticmethod
    def delete_user(uid):
        logger = current_app.logger
        """删除登录用户（级联删除关联挂机房间）"""
        user = LogOffUser.query.filter_by(user_id=int(uid)).first()
        if not user:
            return False, "用户不存在"

        db.session.delete(user)
        db.session.commit()
        return True, "删除成功"

    @staticmethod
    def get_user_logoff(uid):
        """获取用户的挂机房间列表"""
        user = LogOffUser.query.filter_by(user_id=int(uid)).first()
        if not user:
            return [], "用户不存在"

        return [v.to_dict() for v in user.logoffs], None

    @staticmethod
    def add_logoff(uid:int,room_id:int,start_time:str,end_time:str):
        """为VIP用户添加入场视频"""
        logger = current_app.logger
        user:LogOffUser = LogOffUser.query.filter_by(user_id=uid).first()
        if not user:
            return None, "用户不存在"
        room:RoomInfo = RoomInfo.query.filter_by(id=room_id).first()
        if not room:
            return None, "房间不存在"
        try:
            logoff = LogOffRoom(
                id= snowflake.next_id(),
                user_id=uid,
                room_id=room.id,
                title=room.title,
                cover_url=room.cover_url,
                owner_id=room.owner_id,
                owner_name=room.owner_name,
                owner_face=room.owner_face,
                start_time=time.fromisoformat(start_time),
                end_time=time.fromisoformat(end_time)
            )
            db.session.add(logoff)
            db.session.commit()
            return logoff.to_dict(), None
        except Exception as e:
            logger.error(f"添加视频失败: {e}")
            db.session.rollback()
            return None, str(e)

    @staticmethod
    def update_logoff(id_key,room_id:int,start_time:str,end_time:str):
        """更新挂机房间"""
        logoff:LogOffRoom = LogOffRoom.query.filter_by(id=id_key).first()
        if not logoff:
            return False, "挂机房间不存在"
        logoff.start_time = time.fromisoformat(start_time)
        logoff.end_time = time.fromisoformat(end_time)
        logoff.room_id = room_id
        db.session.commit()

        return logoff.to_dict(), None

    @staticmethod
    def delete_logoff(id_key):
        """删除挂机房间"""
        logoff = LogOffRoom.query.filter_by(id=id_key).first()
        if not logoff:
            return False, "挂机房间不存在"

        db.session.delete(logoff)
        db.session.commit()
        return True, "删除成功"

    @staticmethod
    def get_logoff_by_id(logoff_id):
        """根据ID获取挂机房间"""
        return LogOffRoom.query.get(logoff_id)

    @staticmethod
    def get_user_logoff_times(uid, current_time: time = None):
        """获取用户的挂机房间（返回第一个符合条件的）"""
        from sqlalchemy import and_, or_, cast, Time
        from datetime import datetime, time as dt_time

        if current_time is None:
            current_time = datetime.now().time()

        # 使用 with_entities 明确指定要查询的字段
        query = LogOffRoom.query.filter(
            LogOffRoom.user_id == uid,
            or_(
                and_(
                    LogOffRoom.start_time <= LogOffRoom.end_time,
                    cast(LogOffRoom.start_time, Time) <= cast(current_time, Time),
                    cast(LogOffRoom.end_time, Time) >= cast(current_time, Time)
                ),
                and_(
                    LogOffRoom.start_time > LogOffRoom.end_time,
                    or_(
                        cast(LogOffRoom.start_time, Time) <= cast(current_time, Time),
                        cast(LogOffRoom.end_time, Time) >= cast(current_time, Time)
                    )
                )
            )
        )

        # 执行查询
        room = query.first()
        # 调试：打印实际类型
        if not room:
            return None, "没有合适挂机房间"

        return room, None

logoff_service = LogoffService()