# aibls/services/gift_stat_service.py
import logging
from datetime import datetime

from flask import current_app

from aibls.models.database import db, SendGiftDetail, RoomReceiveGifts
from aibls.services.room_service import room_service
from aibls.utils import snowflake


class GiftStatService:
    """礼物统计服务类"""

    @staticmethod
    def to_cny(coin_value):
        """金瓜子转人民币（元）"""
        if coin_value is None:
            return 0.0
        return round(coin_value / 1000, 2)

    @staticmethod
    def get_available_months():
        """获取有数据的月份列表"""
        logger = current_app.logger
        try:
            months = db.session.query(
                SendGiftDetail.send_month
            ).distinct().order_by(SendGiftDetail.send_month.desc()).all()
            return [m[0] for m in months]
        except Exception as e:
            logger.error(f"获取月份列表失败: {e}")
            return []

    @staticmethod
    def get_default_room():
        """获取默认房间ID"""
        room_data = room_service.get_default_room()
        if room_data:
            return room_data.get('id')
        return None

    @staticmethod
    def ensure_monthly_data(room_id, month):
        """确保指定月份的数据已汇总到 RoomReceiveGifts"""
        logger = current_app.logger
        try:
            # 从 SendGiftDetail 统计汇总
            stats = GiftStatService._calculate_monthly_stats(room_id, month)

            if not stats:
                return None

            # 检查是否已有数据
            existing = RoomReceiveGifts.query.filter_by(
                room_id=room_id,
                send_month=month
            ).first()

            if existing:
                # 更新现有记录
                existing.gift_total_num = stats['gift_total_num']
                existing.gift_total_coin = stats['gift_total_coin']
                existing.blind_gift_num = stats['blind_gift_num']
                existing.blind_gift_total = stats['blind_gift_total']
                existing.blind_gift_scope = stats['blind_gift_scope']
                existing.first_uid = stats['first_uid']
                existing.first_name = stats['first_name']
                existing.first_face = stats['first_face']
                existing.first_gift_total = stats['first_gift_total']
                existing.blind_first_uid = stats['blind_first_uid']
                existing.blind_first_name = stats['blind_first_name']
                existing.blind_first_face = stats['blind_first_face']
                existing.blind_first_scope = stats['blind_first_scope']
                existing.created_at = datetime.now()
            else:
                # 新增记录
                new_record = RoomReceiveGifts(
                    id=snowflake.next_id(),
                    room_id=room_id,
                    send_month=month,
                    gift_total_num=stats['gift_total_num'],
                    gift_total_coin=stats['gift_total_coin'],
                    blind_gift_num=stats['blind_gift_num'],
                    blind_gift_total=stats['blind_gift_total'],
                    blind_gift_scope=stats['blind_gift_scope'],
                    first_uid=stats['first_uid'],
                    first_name=stats['first_name'],
                    first_face=stats['first_face'],
                    first_gift_total=stats['first_gift_total'],
                    blind_first_uid=stats['blind_first_uid'],
                    blind_first_name=stats['blind_first_name'],
                    blind_first_face=stats['blind_first_face'],
                    blind_first_scope=stats['blind_first_scope']
                )
                db.session.add(new_record)

            db.session.commit()
            return stats

        except Exception as e:
            logger.error(f"汇总月度数据失败: {e}")
            db.session.rollback()
            return None

    @staticmethod
    def _calculate_monthly_stats(room_id, month):
        """从 SendGiftDetail 统计月度数据"""
        # 查询该房间该月份的所有记录
        records = SendGiftDetail.query.filter_by(
            room_id=room_id,
            send_month=month
        ).all()

        if not records:
            return None

        # 统计所有礼物（普通礼物：gift_type < 100，非盲盒爆出）
        normal_records = [r for r in records if r.gift_type < 100 and r.blind_gift_id == 0]
        gift_total_num = sum(r.gift_num for r in normal_records)
        gift_total_coin = sum(r.gift_total_coin for r in normal_records)

        # 统计盲盒相关（只统计 blind_gift_id > 0 的记录，即从盲盒爆出的礼物）
        blind_records = [r for r in records if r.blind_gift_id > 0]
        blind_gift_num = sum(r.gift_num for r in blind_records if r.gift_num)

        # 盲盒总投入：统计所有购买的盲盒（gift_id 是盲盒ID，且 blind_gift_id > 0）
        blind_gift_total = sum(r.blind_gift_total for r in blind_records if r.blind_gift_total)

        # 盲盒总盈亏：只统计 blind_gift_id > 0 的记录（即从盲盒爆出的礼物）
        blind_gift_scope = sum(r.total_scope for r in blind_records if r.total_scope)

        # 统计上舰（gift_type = 100）
        guard_records = [r for r in records if r.gift_type == 100]
        guard_stats = {
            'governor': {'count': 0, 'amount': 0},  # 总督 gift_id=10001
            'lieutenant': {'count': 0, 'amount': 0},  # 提督 gift_id=10002
            'captain': {'count': 0, 'amount': 0}  # 舰长 gift_id=10003
        }

        for r in guard_records:
            if r.gift_id == 10001:  # 总督
                guard_stats['governor']['count'] += r.gift_num
                guard_stats['governor']['amount'] += r.gift_total_coin
            elif r.gift_id == 10002:  # 提督
                guard_stats['lieutenant']['count'] += r.gift_num
                guard_stats['lieutenant']['amount'] += r.gift_total_coin
            elif r.gift_id == 10003:  # 舰长
                guard_stats['captain']['count'] += r.gift_num
                guard_stats['captain']['amount'] += r.gift_total_coin

        # 找出投喂礼物价值最高的用户
        user_gift_total = {}
        for r in records:
            uid = r.sender_uid
            user_gift_total[uid] = user_gift_total.get(uid, 0) + r.gift_total_coin

        if user_gift_total:
            first_uid = max(user_gift_total, key=user_gift_total.get)
            first_gift_total = user_gift_total[first_uid]
            first_record = next((r for r in records if r.sender_uid == first_uid), None)
            first_name = first_record.sender_name if first_record else ''
            first_face = first_record.sender_face if first_record else ''
        else:
            first_uid = 0
            first_name = ''
            first_face = ''
            first_gift_total = 0

        # 找出盲盒盈亏最高的用户（只统计 blind_gift_id > 0 的记录）
        user_blind_scope = {}
        for r in records:
            if r.blind_gift_id > 0:
                uid = r.sender_uid
                user_blind_scope[uid] = user_blind_scope.get(uid, 0) + r.total_scope

        if user_blind_scope:
            blind_first_uid = max(user_blind_scope, key=user_blind_scope.get)
            blind_first_scope = user_blind_scope[blind_first_uid]
            blind_first_record = next((r for r in records if r.sender_uid == blind_first_uid), None)
            blind_first_name = blind_first_record.sender_name if blind_first_record else ''
            blind_first_face = blind_first_record.sender_face if blind_first_record else ''
        else:
            blind_first_uid = 0
            blind_first_name = ''
            blind_first_face = ''
            blind_first_scope = 0

        return {
            'gift_total_num': gift_total_num,
            'gift_total_coin': gift_total_coin,
            'blind_gift_num': blind_gift_num,
            'blind_gift_total': blind_gift_total,
            'blind_gift_scope': blind_gift_scope,
            'first_uid': first_uid,
            'first_name': first_name,
            'first_face': first_face,
            'first_gift_total': first_gift_total,
            'blind_first_uid': blind_first_uid,
            'blind_first_name': blind_first_name,
            'blind_first_face': blind_first_face,
            'blind_first_scope': blind_first_scope,
            'guard_stats': guard_stats
        }

    @staticmethod
    def get_monthly_summary(room_id, month):
        """获取月度汇总数据（上部4个区域）"""
        # 确保数据已汇总
        stats = GiftStatService.ensure_monthly_data(room_id, month)

        if not stats:
            return None

        # 获取 RoomReceiveGifts 记录
        record = RoomReceiveGifts.query.filter_by(
            room_id=room_id,
            send_month=month
        ).first()

        if not record:
            return None

        # 转换上舰统计金额为人民币
        guard_stats = stats.get('guard_stats', {})
        guard_stats_cny = {
            'governor': {
                'count': guard_stats.get('governor', {}).get('count', 0),
                'amount': GiftStatService.to_cny(guard_stats.get('governor', {}).get('amount', 0))
            },
            'lieutenant': {
                'count': guard_stats.get('lieutenant', {}).get('count', 0),
                'amount': GiftStatService.to_cny(guard_stats.get('lieutenant', {}).get('amount', 0))
            },
            'captain': {
                'count': guard_stats.get('captain', {}).get('count', 0),
                'amount': GiftStatService.to_cny(guard_stats.get('captain', {}).get('amount', 0))
            }
        }

        return {
            'month': month,
            'room_id': room_id,
            'gift_total_num': stats['gift_total_num'],
            'gift_total_cny': GiftStatService.to_cny(stats['gift_total_coin']),
            'blind_gift_num': stats['blind_gift_num'],
            'blind_gift_total_cny': GiftStatService.to_cny(stats['blind_gift_total']),
            'blind_gift_scope_cny': GiftStatService.to_cny(stats['blind_gift_scope']),
            'guard_stats': guard_stats_cny,
            'first_user': {
                'uid': record.first_uid,
                'name': record.first_name,
                'face': record.first_face,
                'total_cny': GiftStatService.to_cny(record.first_gift_total)
            } if record.first_uid else None,
            'blind_first_user': {
                'uid': record.blind_first_uid,
                'name': record.blind_first_name,
                'face': record.blind_first_face,
                'scope_cny': GiftStatService.to_cny(record.blind_first_scope)
            } if record.blind_first_uid else None
        }

    @staticmethod
    def get_blind_box_groups(room_id, month):
        """获取盲盒分组汇总（列表1）"""
        records = SendGiftDetail.query.filter_by(
            room_id=room_id,
            send_month=month
        ).all()

        if not records:
            return []

        # 先找出所有盲盒ID（从 blind_gift_id > 0 的记录中获取）
        blind_box_ids = set()
        for r in records:
            if r.blind_gift_id > 0:
                blind_box_ids.add(r.blind_gift_id)

        # 按 blind_gift_id 分组统计
        blind_groups = {}
        for blind_id in blind_box_ids:
            # 总数量
            blind_total_num = sum(r.gift_num for r in records if r.gift_num and r.blind_gift_id == blind_id)
            blind_total_input_coin = sum(
                r.blind_gift_total for r in records if r.blind_gift_total and r.blind_gift_id == blind_id)
            blind_total_output_coin = sum(
                r.gift_total_coin for r in records if r.gift_total_coin and r.blind_gift_id == blind_id)

            blind_groups[blind_id] = {
                'blind_gift_id': blind_id,
                'blind_gift_name': '',
                'total_num': blind_total_num,
                'total_input_coin': blind_total_input_coin,
                'total_output_coin': blind_total_output_coin,
                'scope_coin': (blind_total_output_coin - blind_total_input_coin)
            }

        # 统计盲盒名称（从 blind_gift_id > 0 的记录中取）
        for r in records:
            if r.blind_gift_id > 0 and r.blind_gift_id in blind_groups:
                if not blind_groups[r.blind_gift_id]['blind_gift_name']:
                    blind_groups[r.blind_gift_id]['blind_gift_name'] = r.blind_gift_name

        # 计算盈亏并转换为人民币
        result = []
        for blind_id, group in blind_groups.items():
            result.append({
                'blind_gift_id': blind_id,
                'blind_gift_name': group['blind_gift_name'],
                'total_num': group['total_num'],
                'total_input_cny': GiftStatService.to_cny(group['total_input_coin']),
                'total_output_cny': GiftStatService.to_cny(group['total_output_coin']),
                'scope_cny': GiftStatService.to_cny(group['total_output_coin'] - group['total_input_coin'])
            })

        # 按盈亏从高到低排序
        return sorted(result, key=lambda x: x['scope_cny'], reverse=True)

    @staticmethod
    def get_blind_box_user_rank(room_id, month, blind_gift_id):
        """获取指定盲盒的用户投喂排名（列表2）"""
        records = SendGiftDetail.query.filter_by(
            room_id=room_id,
            send_month=month,
            blind_gift_id=blind_gift_id
        ).all()

        if not records:
            return []

        user_stats = {}

        for r in records:
            uid = r.sender_uid
            if uid not in user_stats:
                user_stats[uid] = {
                    'uid': uid,
                    'name': r.sender_name,
                    'face': r.sender_face,
                    'gift_num': 0,
                    'total_input_coin': 0,
                    'total_output_coin': 0,
                    'scope_coin': 0
                }
            user_stats[uid]['gift_num'] += r.gift_num
            user_stats[uid]['total_input_coin'] += r.blind_gift_total
            user_stats[uid]['total_output_coin'] += r.gift_total_coin
            user_stats[uid]['scope_coin'] += r.total_scope

        # 计算盈亏并转换为人民币
        result = []
        for uid, stats in user_stats.items():
            result.append({
                'uid': stats['uid'],
                'name': stats['name'],
                'face': stats['face'],
                'gift_num': stats['gift_num'],
                'total_input_cny': GiftStatService.to_cny(stats['total_input_coin']),
                'total_output_cny': GiftStatService.to_cny(stats['total_output_coin']),
                'scope_cny': GiftStatService.to_cny(stats['total_output_coin'] - stats['total_input_coin'])
            })

        # 按盈亏从高到低排序
        return sorted(result, key=lambda x: x['scope_cny'], reverse=True)


gift_stat_service = GiftStatService()