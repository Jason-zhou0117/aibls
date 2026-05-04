from datetime import datetime

from flask import current_app

from aibls.models.database import SendGiftDetail, db
from aibls.utils import snowflake


class SendGiftService:

    @staticmethod
    def add_send_gift(send_gift:dict):
        """添加投喂礼物的日志"""
        logger = current_app.logger
        logger.debug(f"添加投喂礼物详情：{send_gift}")
        try:
            # 获取当前日期时间
            now = datetime.now()
            # 获取 yyyy-mm-dd 格式
            date_ymd = now.strftime('%Y-%m-%d') # 例如: 2026-05-02
            # 获取 yyyy-mm 格式
            date_ym = now.strftime('%Y-%m') # 例如: 2026-05

            send_gift_data = SendGiftDetail(
                id= snowflake.next_id(),
                room_id = send_gift.get('room_id'),
                send_month = date_ym,
                send_date = date_ymd,
                sender_uid = send_gift.get('sender_uid'),
                sender_name = send_gift.get('sender_name'),
                sender_face = send_gift.get('sender_face'),
                receiver_uid = send_gift.get('receiver_uid'),
                receiver_name = send_gift.get('receiver_name'),
                receiver_face = send_gift.get('receiver_face'),
                gift_id = send_gift.get('gift_id'),
                gift_type = send_gift.get('gift_type'),
                gift_name = send_gift.get('gift_name'),
                gift_num = send_gift.get('gift_num'),
                gift_price_origin = send_gift.get('price'),
                gift_total_coin = send_gift.get('total_coin'),
                blind_gift_id = send_gift.get('blind_gift_id'),
                blind_gift_name = send_gift.get('blind_gift_name'),
                blind_gift_price = send_gift.get('blind_gift_price'),
                blind_gift_total = send_gift.get('blind_gift_total'),
                total_scope = send_gift.get('total_scope')
            )

            db.session.add(send_gift_data)
            db.session.commit()
            return True, f"已添加投喂日志 {send_gift_data.id} "
        except Exception as e:
            db.session.rollback()
            logger.error(f"更换默认房间时出错：{e}")
            return False, str(e)

send_gift_service = SendGiftService()