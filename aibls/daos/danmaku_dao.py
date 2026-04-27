from datetime import datetime, timedelta

from bilibili_api import Danmaku
from flask import current_app

from aibls.daos.base_dao import BaseDAO
from aibls.models.danmu import DanmakuInfo


class DanmakuDAO(BaseDAO[DanmakuInfo]):

    def __init__(self):
        super().__init__(DanmakuInfo)


    def get_danmakus_by_room(self,room_id, page=1, per_page= None, start_time=None, end_time=None,sort_by='send_time', sort_order='desc'):
        """
        按房间ID查询弹幕
        :param room_id: 房间ID
        :param start_time: 开始时间
        :param end_time: 结束时间
        :param page: 页码
        :param per_page: 每页数量
        :param sort_by: 排序字段
        :param sort_order: 排序方向
        :return: (弹幕列表, 总数量)
        """
        if per_page is None:
            per_page = current_app.config['DEFAULT_PAGE_SIZE']
        else:
            per_page = min(per_page, current_app.config['MAX_PAGE_SIZE'])

        # 构建查询
        query = self.session.query(self.model_class)
        query.filter(DanmakuInfo.room_id == room_id)
        if end_time is None:
            end_time = datetime.now()
        query.filter(DanmakuInfo.send_time <= end_time)

        if start_time is not None:
            query.filter(DanmakuInfo.send_time >= start_time)


        # 获取总数
        total = query.count()

        # 排序
        if sort_by == 'send_time':
            order_by = DanmakuInfo.send_time.desc() if sort_order == 'desc' else DanmakuInfo.send_time.asc()
        else:
            order_by = DanmakuInfo.send_time.desc()

        # 获取分页数据
        danmakus = query.order_by(order_by) \
            .offset((page - 1) * per_page) \
            .limit(per_page) \
            .all()

        return [d.to_dict() for d in danmakus],total


    def search_danmakus(self,keyword, room_id=None, user_id=None,page=1, per_page=None,start_time=None, end_time=None):
        """
        搜索弹幕
        :param keyword: 搜索关键词
        :param room_id: 房间ID（可选）
        :param start_time: 开始时间
        :param end_time: 结束时间
        :param page: 页码
        :param per_page: 每页数量
        :param search_type: 搜索类型（content/user/medal）
        :return: (弹幕列表, 总数量)
        """
        if per_page is None:
            per_page = current_app.config['DEFAULT_PAGE_SIZE']
        else:
            per_page = min(per_page, current_app.config['MAX_PAGE_SIZE'])

        # 构建查询
        query = self.session.query(self.model_class)
        if end_time is None:
            end_time = datetime.now()
        query.filter(DanmakuInfo.send_time <= end_time)

        if start_time is not None:
            query.filter(DanmakuInfo.send_time >= start_time)


        query = query.filter(DanmakuInfo.message.contains(keyword))
        if room_id is not None:
            query.filter(DanmakuInfo.room_id == room_id)
        if user_id is not None:
            query.filter(DanmakuInfo.room_id == room_id)

        # 获取总数
        total = query.count()

        # 排序
        order_by = DanmakuInfo.send_time.desc()

        # 获取分页数据
        danmakus = query.order_by(order_by) \
            .offset((page - 1) * per_page) \
            .limit(per_page) \
            .all()

        return [d.to_dict() for d in danmakus], total