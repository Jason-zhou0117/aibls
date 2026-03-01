from typing import Any, List

from sqlalchemy import update, and_

from aibls.daos.base_dao import BaseDAO, T
from aibls.models.rooms import RoomInfo


class RoomDAO(BaseDAO[RoomInfo]):
    """房间数据访问对象"""

    def __init__(self):
        super().__init__(RoomInfo)

    def find_by_dict_orderby(self, filters:dict[str,Any]) -> List[T]:
        """根据条件查找记录"""
        query = self.session.query(self.model_class)
        if filters:
            for key, value in filters.items():
                if hasattr(self.model_class, key):
                    query = query.filter(getattr(self.model_class, key) == value)
        query = query.order_by(getattr(self.model_class, 'is_favorites').desc())
        return query.all()

    def update_batch(self,login_id:str, room_id:str,data:dict[str,Any]) -> List[T]:
        """按room_id,批量更新房间信息"""
        stmt = update(RoomInfo).where(and_(RoomInfo.room_id == room_id,
                                           RoomInfo.login_id != login_id)).values(
            room_name=data.get("room_name"),
            room_cover=data.get("room_cover"),
            room_user_name=data.get("room_user_name"),
            room_user_face=data.get("room_user_face"),
        )
        result = self.db.session.execute(stmt)
        self.db.session.commit()
        print(f"更新房间信息，更新了 {result.rowcount} 条记录")