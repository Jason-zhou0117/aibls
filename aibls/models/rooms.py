from typing import Any

from sqlalchemy import Column, String

from aibls.models.base import BaseModel


class RoomInfo(BaseModel):
    #表名
    __tablename__ = 'room_infos'

    # 字段
    room_key = Column(name="room_key",type_=String(100),primary_key=True,comment="房间主键")
    room_id = Column(name="room_id",type_=String(100),primary_key=False,comment="房间号")
    room_name = Column(name="room_name",type_=String(200),primary_key=False,comment="房间名称")
    room_uid = Column(name="room_uid",type_=String(100),primary_key=False,comment="房间主播UID")
    room_cover = Column(name="room_cover",type_=String(1000),primary_key=False,comment="房间封面")
    room_user_name = Column(name="room_user_name",type_=String(100),primary_key=False,comment="主播名称")
    room_user_face = Column(name="room_user_face",type_=String(1000),primary_key=False,comment="主播头像")
    login_id = Column(name="login_id", type_=String(50), primary_key=False, comment="登录用户ID")
    is_favorites = Column(name="is_favorites", type_=String(1), default='N',primary_key=False, comment="是否收藏")

    # 防止隐式I/O的配置
    __mapper_args__ = {
        "eager_defaults": True
    }

    def __repr__(self):
        return f"<RoomInfo(room_id={self.room_id}, room_uid='{self.room_uid}')>"

