# aibls/services/box_stat_service.py
"""盲盒统计服务 - 基于数据库动态判断"""
import logging
import re
from datetime import datetime, timedelta
from typing import Optional, Tuple, Dict, Any
from logging import Logger

from aibls.models.database import db, SendGiftDetail, GiftInfo


class BoxStatService:
    """盲盒统计服务"""

    # 时间词映射
    TIME_KEYWORDS = ["今日", "今天", "昨日", "昨天", "前日", "前天", "本月", "上月"]

    # 房间前缀词
    ROOM_PREFIXES = ["播间", "本播间", "房间"]

    def __init__(self):
        self.logger = None

    def set_logger(self, logger: Logger):
        self.logger = logger

    def _is_valid_box_name(self, name: str) -> bool:
        """查询数据库，判断是否为有效的盲盒名称"""
        if not name:
            return False
        try:
            exists = db.session.query(GiftInfo).filter(
                GiftInfo.is_blind_box == '1',
                GiftInfo.gift_name.like(f"%{name}%")
            ).first() is not None
            return exists
        except Exception as e:
            if self.logger:
                self.logger.debug(f"查询盲盒名称失败: {e}")
            return False


    def _should_trigger_stats(self, text: str) -> Tuple[bool, Optional[str]]:
        """
        判断是否应该触发盲盒统计
        返回: (是否触发, 提取出的盲盒名称)
        """
        text_lower = text.lower()

        # 情况1：明确包含"盲盒"关键词，直接触发
        if "盲盒" in text_lower:
            return True, None

        # 情况2：匹配时间模式，提取剩余部分判断是否为盲盒名称
        rest_text = ""
        matched = False

        # 匹配日期格式 yyyymmdd
        date_match = re.match(r'^(\d{8})\s*(.+)?$', text_lower)
        if date_match:
            matched = True
            rest_text = date_match.group(2) or ""

        # 匹配月份格式 yyyymm
        if not matched:
            month_match = re.match(r'^(\d{6})\s*(.+)?$', text_lower)
            if month_match:
                matched = True
                rest_text = month_match.group(2) or ""

        # 匹配时间关键词
        if not matched:
            for keyword in self.TIME_KEYWORDS:
                if text_lower.startswith(keyword):
                    matched = True
                    rest_text = text_lower[len(keyword):]
                    break

        # 特殊处理："我的盲盒"（包含盲盒，上面已处理）

        # 如果没有匹配到时间模式，不触发
        if not matched:
            return False, None

        # 如果没有剩余文本（如只发了"今日"），不触发
        if not rest_text:
            return False, None

        # 提取盲盒名称（去掉可能的"盲盒"后缀）
        box_name = rest_text.strip()
        if box_name.endswith("盲盒"):
            box_name = box_name[:-2]

        # 查询数据库确认是否为有效盲盒名称
        if self._is_valid_box_name(box_name):
            return True, box_name

        return False, None

    def parse_command(self, danmu_data: Dict[str, Any], room_info: Dict[str, Any]) -> Tuple[
        Optional[str], Optional[Dict], Optional[str]]:
        """
        解析盲盒统计指令
        返回: (scope, time_range, box_name)
        """
        text = danmu_data.get("message", "").strip()
        sender_uid = danmu_data.get("sender_uid", 0)
        fans_level = danmu_data.get("fans_level", 0)
        owner_uid = room_info.get("owner_id", 0)
        room_id = room_info.get("id", 0)

        # 先判断是否应该触发统计
        should_trigger, extracted_box_name = self._should_trigger_stats(text)
        if not should_trigger:
            return None, None, None

        text_lower = text.lower()
        remaining_text = text_lower

        # 判断统计范围
        scope = None

        # 1. 检查房间前缀（高等级粉丝 >20级 或 任何人用了前缀）
        for prefix in self.ROOM_PREFIXES:
            if text_lower.startswith(prefix):
                scope = "room"
                remaining_text = text_lower[len(prefix):]
                break

        # 2. 主播按房间统计
        if scope is None and sender_uid == owner_uid:
            scope = "room"

        # 3. 默认个人统计
        if scope is None:
            scope = "user"

        # 特殊处理：我的盲盒 -> 本月盲盒
        if "我的盲盒" in remaining_text:
            remaining_text = remaining_text.replace("我的盲盒", "本月盲盒")

        # 解析时间和盲盒名称
        time_range = None
        box_name = extracted_box_name  # 使用前面提取的盲盒名称

        # 1. 尝试匹配日期格式 yyyymmdd
        date_match = re.match(r'^(\d{8})\s*(.+)?$', remaining_text)
        if date_match:
            date_str = date_match.group(1)
            try:
                dt = datetime.strptime(date_str, "%Y%m%d")
                time_range = {"type": "day", "date": dt.strftime("%Y-%m-%d")}
                # 如果没有提取到盲盒名称，从剩余部分再提取
                if not box_name:
                    rest = date_match.group(2) or ""
                    if rest:
                        box_name = self._extract_box_name_from_rest(rest)
                return scope, time_range, box_name
            except ValueError:
                pass

        # 2. 尝试匹配月份格式 yyyymm
        month_match = re.match(r'^(\d{6})\s*(.+)?$', remaining_text)
        if month_match:
            month_str = month_match.group(1)
            try:
                dt = datetime.strptime(month_str, "%Y%m")
                time_range = {"type": "month", "month": dt.strftime("%Y-%m")}
                if not box_name:
                    rest = month_match.group(2) or ""
                    if rest:
                        box_name = self._extract_box_name_from_rest(rest)
                return scope, time_range, box_name
            except ValueError:
                pass

        # 3. 匹配时间关键词
        for keyword in self.TIME_KEYWORDS:
            if remaining_text.startswith(keyword):
                time_range = self._get_time_range(keyword)
                if time_range:
                    # 如果还没有盲盒名称，尝试从剩余部分提取
                    if not box_name:
                        rest = remaining_text[len(keyword):]
                        if rest:
                            box_name = self._extract_box_name_from_rest(rest)
                    return scope, time_range, box_name

        return None, None, None

    def _extract_box_name_from_rest(self, text: str) -> Optional[str]:
        """从剩余文本中提取盲盒名称"""
        if not text:
            return None
        text = text.strip()
        if text.endswith("盲盒"):
            text = text[:-2]
        # 验证是否为有效盲盒名称
        if self._is_valid_box_name(text):
            return text
        return None

    def _get_time_range(self, keyword: str) -> Optional[Dict]:
        """根据关键词获取时间范围"""
        today = datetime.now().date()

        if keyword in ["今日", "今天"]:
            return {"type": "day", "date": today.strftime("%Y-%m-%d")}
        elif keyword in ["昨日", "昨天"]:
            yesterday = today - timedelta(days=1)
            return {"type": "day", "date": yesterday.strftime("%Y-%m-%d")}
        elif keyword in ["前日", "前天"]:
            before_yesterday = today - timedelta(days=2)
            return {"type": "day", "date": before_yesterday.strftime("%Y-%m-%d")}
        elif keyword == "本月":
            return {"type": "month", "month": today.strftime("%Y-%m")}
        elif keyword == "上月":
            first_of_month = today.replace(day=1)
            last_month = first_of_month - timedelta(days=1)
            return {"type": "month", "month": last_month.strftime("%Y-%m")}
        return None

    def get_stats(self, danmu_data: Dict[str, Any], room_info: Dict[str, Any],
                  scope: str, time_range: Dict, box_name: Optional[str]) -> Optional[Dict[str, Any]]:
        """查询统计数据"""
        try:
            sender_uid = danmu_data.get("sender_uid", 0)
            room_id = room_info.get("id", 0)

            from sqlalchemy import func

            # 直接使用 db.session，不需要 with current_app.app_context()
            # 因为 db.session 是全局的，在应用启动时已经绑定
            query = db.session.query(
                func.sum(SendGiftDetail.gift_num).label('total_num'),
                func.sum(SendGiftDetail.blind_gift_total).label('total_input'),
                func.sum(SendGiftDetail.total_scope).label('total_scope')
            ).filter(
                SendGiftDetail.blind_gift_id > 0
            )

            if scope == "user":
                query = query.filter(SendGiftDetail.sender_uid == sender_uid)
            else:
                query = query.filter(SendGiftDetail.room_id == room_id)

            if time_range["type"] == "day":
                query = query.filter(SendGiftDetail.send_date == time_range["date"])
            else:
                query = query.filter(SendGiftDetail.send_month == time_range["month"])

            if box_name:
                query = query.filter(SendGiftDetail.blind_gift_name.like(f"%{box_name}%"))

            stats = query.first()

            return {
                'gift_num': int(stats[0] or 0),
                'blind_gift_total': float(stats[1] or 0),
                'total_scope': float(stats[2] or 0)
            }

        except Exception as e:
            if self.logger:
                self.logger.error(f"查询盲盒统计失败: {e}")
            return None

    def _get_profit_level(self, amount_cny: float) -> Tuple[str, str]:
        """根据盈亏金额(元)返回 (emoji, 描述)"""
        if amount_cny == 0:
            return "😐", "不赚不亏"
        elif 0 < amount_cny <= 50:
            return "🙂", "小赚"
        elif 50 < amount_cny < 520:
            return "😊", "赚"
        elif 520 < amount_cny < 1000:
            return "🎉", "大赚"
        elif amount_cny >= 1000:
            return "👑", "欧皇"
        elif -50 < amount_cny < 0:
            return "😔", "小亏"
        elif -520 < amount_cny <= -50:
            return "😢", "亏"
        elif -1000 < amount_cny <= -520:
            return "😭", "大亏"
        else:
            return "💀", "亏麻"

    def format_reply(self, stats: Optional[Dict]) -> Optional[str]:
        """格式化回复消息"""
        if not stats or stats['gift_num'] == 0:
            return "结果：很遗憾，你不给力呀，无！"

        gift_num = stats['gift_num']
        total_input = stats['blind_gift_total']  # 投喂电池数
        total_scope = stats['total_scope']  # 盈亏电池数

        input_cny = total_input / 1000  # 消费金额(元)
        scope_cny = total_scope / 1000  # 盈亏金额(元)

        if scope_cny == 0:
            return "结果：运气不错，不赚不亏！"

        emoji, level = self._get_profit_level(scope_cny)
        abs_amount = abs(scope_cny)

        gift_num_str = self._format_number(gift_num)
        input_str = self._format_number(input_cny)
        amount_str = self._format_number(abs_amount)

        return f"结果：{gift_num_str}个，消费{input_str}元，{emoji}{level}{amount_str}元"


    def _format_number(self, num: float) -> str:
        """格式化数字，添加千位分隔符"""
        if num == int(num):
            return f"{int(num):,}"
        else:
            return f"{num:,.1f}"

box_stat_service = BoxStatService()