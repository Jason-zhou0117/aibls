# aibls/services/gift_service.py
import os
import uuid


from flask import current_app

from aibls.models.database import db, GiftInfo, GiftVideo



class GiftService:
    """礼物特效服务类"""

    @staticmethod
    def get_active_gifts():
        """获取上架的礼物列表（is_active='1'）"""
        gifts = GiftInfo.query.filter_by(is_active='1').order_by(
            GiftInfo.has_video.desc(),
            GiftInfo.gift_id.asc()
        ).all()
        return [g.to_list_dict() for g in gifts]

    @staticmethod
    def get_inactive_gifts():
        """获取下架的礼物列表（is_active='0'）"""
        gifts = GiftInfo.query.filter_by(is_active='0').order_by(
            GiftInfo.gift_id.asc()
        ).all()
        return [g.to_list_dict() for g in gifts]

    @staticmethod
    def get_all_gifts():
        """获取所有礼物（已废弃，建议用上面两个方法）"""
        gifts = GiftInfo.query.order_by(
            GiftInfo.is_active.desc(),
            GiftInfo.has_video.desc(),
            GiftInfo.gift_id.asc()
        ).all()
        return [g.to_list_dict() for g in gifts]

    @staticmethod
    def move_gift_to_active(gift_id):
        """将礼物移动到上架列表"""
        try:
            gift = GiftInfo.query.get(gift_id)
            if not gift:
                return False, "礼物不存在"
            gift.is_active = '1'
            db.session.commit()
            return True, "已移动到上架列表"
        except Exception as e:
            db.session.rollback()
            return False, str(e)

    @staticmethod
    def move_gift_to_inactive(gift_id):
        """将礼物移动到下架列表"""
        try:
            gift = GiftInfo.query.get(gift_id)
            if not gift:
                return False, "礼物不存在"
            gift.is_active = '0'
            db.session.commit()
            return True, "已移动到下架列表"
        except Exception as e:
            db.session.rollback()
            return False, str(e)

    @staticmethod
    def get_gift_by_id(gift_id):
        """根据礼物ID获取礼物"""
        return GiftInfo.query.get(gift_id)

    @staticmethod
    def get_gift_videos(gift_id):
        """获取礼物的特效视频列表"""
        gift = GiftInfo.query.get(gift_id)
        if not gift:
            return [], "礼物不存在"
        return [v.to_dict() for v in gift.videos], None

    @staticmethod
    def add_gift(data):
        """添加礼物"""
        logger = current_app.logger
        try:
            # 检查是否已存在
            existing = GiftInfo.query.get(data.get('gift_id'))
            if existing:
                return None, f"礼物ID {data.get('gift_id')} 已存在"
            gift_icon = data.get('gif') or data.get('img_basic') or ''
            gift = GiftInfo(
                gift_id=data['id'],
                gift_name=data['name'],
                gift_icon=gift_icon,
                price_origin=data.get('price', 0),
                price_gold=data.get('price', 0) / 100,
                price_cny=data.get('price', 0) / 1000,
                is_blind_box='0',
                blind_box_id=0,
                has_video='0',
                is_active='0'
            )
            db.session.add(gift)
            db.session.commit()
            return gift.to_dict(), None
        except Exception as e:
            logger.error(f"添加礼物失败: {e}",exc_info=True)
            db.session.rollback()
            return None, str(e)

    @staticmethod
    def update_gift(gift_id, data):
        """更新礼物信息"""
        logger = current_app.logger
        try:
            gift = GiftInfo.query.get(gift_id)
            if not gift:
                return None, "礼物不存在"

            if 'is_blind_box' in data:
                gift.is_blind_box = data['is_blind_box']
            if 'blind_box_id' in data:
                gift.blind_box_id = data['blind_box_id']

            db.session.commit()
            return gift.to_dict(), None
        except Exception as e:
            logger.error(f"更新礼物失败: {e}",exc_info=True)
            db.session.rollback()
            return None, str(e)

    @staticmethod
    def delete_gift(gift_id):
        """删除礼物（级联删除关联视频）"""
        logger = current_app.logger
        try:
            gift = GiftInfo.query.get(gift_id)
            if not gift:
                return False, "礼物不存在"

            # 删除关联的视频文件
            for video in gift.videos:
                if video.path and os.path.exists(video.path):
                    try:
                        os.remove(video.path)
                    except Exception as e:
                        logger.error(f"删除视频文件失败: {e}",exc_info=True)

            db.session.delete(gift)
            db.session.commit()
            return True, "删除成功"
        except Exception as e:
            logger.error(f"删除礼物失败: {e}",exc_info=True)
            db.session.rollback()
            return False, str(e)

    @staticmethod
    def add_video(gift_id, video_id, title, url, path):
        """添加礼物特效视频"""
        logger = current_app.logger
        try:
            gift = GiftInfo.query.get(gift_id)
            if not gift:
                return None, "礼物不存在"

            video_uuid = str(uuid.uuid4())[:8]
            video = GiftVideo(
                id=video_uuid,
                video_id=video_id,
                gift_id=gift_id,
                title=title,
                url=url,
                path=path
            )
            db.session.add(video)

            # 更新礼物的 has_video 标记
            gift.has_video = '1'

            db.session.commit()
            return video.to_dict(), None
        except Exception as e:
            logger.error(f"添加视频失败: {e}",exc_info=True)
            db.session.rollback()
            return None, str(e)

    @staticmethod
    def delete_video(video_uuid):
        """删除特效视频"""
        logger = current_app.logger
        try:
            video = GiftVideo.query.filter_by(id=video_uuid).first()
            if not video:
                return False, "视频不存在"

            gift_id = video.gift_id

            # 删除视频文件
            if video.path and os.path.exists(video.path):
                try:
                    os.remove(video.path)
                except Exception as e:
                    logger.error(f"删除视频文件失败: {e}",exc_info=True)

            db.session.delete(video)

            # 检查该礼物是否还有其他视频
            remaining = GiftVideo.query.filter_by(gift_id=gift_id).count()
            if remaining == 0:
                gift = GiftInfo.query.get(gift_id)
                if gift:
                    gift.has_video = '0'

            db.session.commit()
            return True, "删除成功"
        except Exception as e:
            logger.error(f"删除视频失败: {e}",exc_info=True)
            db.session.rollback()
            return False, str(e)

    @staticmethod
    def is_gift_abandoned(gift: dict) -> tuple:
        """
        判断一个礼物条目是否已被废弃。

        Args:
            gift: 礼物的字典数据

        Returns:
            tuple: (是否废弃, 废弃原因)
        """
        # 1. 最高置信度：名字直接为"废弃"
        if gift.get('name') == '废弃' or '废弃' in gift.get('name') :
            return True, "礼物名为'废弃'"

        # 2. 辅助特征组合判断（提高准确率）
        name = gift.get('name', '')
        price = gift.get('price', 0)
        coin_type = gift.get('coin_type', '')
        gift_type = gift.get('gift_type', 0)
        bind_room_id = gift.get('bind_roomid', 0)

        reasons = []

        # 礼物名称含作废字样
        if '作废' in name:
            reasons.append("礼物名称含作废字样")

        # 价格异常低（但排除正常的低价礼物如辣条100银瓜子）
        if price == 0 :
            reasons.append("价格为0")

        # 银瓜子且价格较高（非正常消费品）
        if coin_type == 'silver':
            reasons.append("银瓜子高价礼物")

        # 特定活动类型且价格异常
        if gift_type == 5 and price == 0:
            reasons.append("活动类型且价格为0")

        # 绑定特定房间（通常是活动直播间）
        if bind_room_id != 0:
            reasons.append(f"绑定特定房间 {bind_room_id}")

        # 描述中可能出现"已结束"等关键词（可扩展）
        desc = gift.get('desc', '')
        if any(keyword in desc for keyword in ['已结束', '活动已结束', '过期']):
            reasons.append(f"描述包含过期关键词: {desc}")

        # 综合判断：有2个以上辅助特征视为高概率废弃
        if len(reasons) >= 1:
            return True, f"辅助特征判断: {', '.join(reasons)}"

        return False, ""

    @staticmethod
    def sync_from_bili(gifts_data):
        """从B站同步礼物数据（批量）"""
        logger = current_app.logger
        try:
            list_gifts = gifts_data.get("list",[])
            logger.debug(f'同步的禮物數量：{len(list_gifts)}')
            for g in list_gifts:
                is_abandoned, reason = GiftService.is_gift_abandoned(g)
                if is_abandoned:
                    continue
                else:
                    existing = GiftInfo.query.get(g.get('id'))
                    # 判断是否是盲盒
                    gift_name = g.get('name', "")
                    gift_type = g.get('gift_type', "0")

                    is_blind_box = '1' if ('盲盒' in str(gift_name) or '6' == gift_type) else '0'
                    #礼物图片
                    gift_icon = g.get('gif') or g.get('img_basic') or ''
                    if existing:
                        # 更新
                        existing.gift_name = gift_name
                        existing.gift_icon = gift_icon
                        existing.price_origin = g.get('price', existing.price_origin)
                        existing.price_gold = existing.price_origin / 100
                        existing.price_cny = existing.price_origin / 1000
                        existing.is_blind_box = is_blind_box
                    else:
                        # 新增
                        gift = GiftInfo(
                            gift_id=g['id'],
                            gift_name=gift_name,
                            gift_icon=gift_icon,
                            price_origin=g.get('price', 0),
                            price_gold=g.get('price', 0) / 100,
                            price_cny=g.get('price', 0) / 1000,
                            is_blind_box=is_blind_box,
                            blind_box_id=0,
                            has_video='0',
                            is_active='0'
                        )
                        db.session.add(gift)

            db.session.commit()
            return True, "同步成功"
        except Exception as e:
            logger.error(f"同步礼物失败: {e}",exc_info=True)
            db.session.rollback()
            return False, str(e)


gift_service = GiftService()