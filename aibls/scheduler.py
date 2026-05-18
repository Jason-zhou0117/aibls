# aibls/scheduler.py
import threading
import time
import random
import json
from datetime import datetime, timedelta

from aibls import LoginCookie, bili_live_service
from aibls.models import LogOffUser, LogOffRoom
from aibls.services import logoff_service
from aibls.llm import chengyu_agent


class DanmakuScheduler:
    """定时发送弹幕调度器 - 支持大模型成语接龙（持续接龙模式）"""

    def __init__(self, app=None):
        self.app = app
        self.thread = None
        self.running = False
        self._sent_count = 0

    def init_app(self, app):
        """初始化应用上下文"""
        self.app = app
        self.logger = app.logger

    def start(self):
        """启动定时任务线程"""
        if self.running:
            self.logger.warning("定时任务已在运行中")
            return

        self.running = True
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()
        self.logger.info("定时发送弹幕任务已启动")

    def stop(self):
        """停止定时任务"""
        self.running = False
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=5)
        self.logger.info("定时发送弹幕任务已停止")

    def _send_danmu(self):
        try:

            datas = logoff_service.get_opened_users()
            if not datas:
                self.logger.debug("没有可用的用户，跳过本轮")
                return

            # 遍历所有用户
            for i, data in enumerate(datas):
                # 用户之间的间隔
                interval_user = random.randint(5, 10)
                text_meditation = "修炼"
                if data.double_majoring == 'Y':
                    text_meditation = "双修"
                # 发送修仙弹幕
                self._send_meditation_danmaku(data, text_meditation)

                # 间隔后发送成语弹幕
                interval_chengyu = random.randint(5, 10)
                time.sleep(interval_chengyu)
                self._send_chengyu_danmaku(data, "突破")

                # 获取接龙结果
                # next_chengyu = chengyu_agent.get_next_chengyu(current_chengyu)

                # self.logger.info(f"成语接龙: {current_chengyu} → {next_chengyu}")

                # 更新当前成语为接龙结果
                # current_chengyu = next_chengyu

                # 用户间间隔
                if i < len(datas) - 1:
                    time.sleep(interval_user)

            # 持续接龙，不重置
            # self.logger.info(f"本轮完成，当前成语: {current_chengyu}，继续下一轮接龙")

        except Exception as e:
            self.logger.error(f"定时发送弹幕出错: {e}",exc_info=True)

    def _run(self):
        """后台线程运行 - 持续接龙模式"""
        with self.app.app_context():
            # 初始化起始成语
            # current_chengyu = chengyu_agent.get_random_chengyu()
            # self.logger.info(f"成语接龙起始成语: {current_chengyu}")

            while self.running:
                self._send_danmu()
                # 随机间隔 5-9 分钟 (300-540 秒)
                interval = random.randint(600, 800)
                # interval = random.randint(20, 30)
                self.logger.debug(f"下次发送弹幕将在 {interval // 60} 分钟后")
                time.sleep(interval)


    def _is_within_20_minutes_of_start(self,start_time):
        """
        判断当前时间是否在 start_time 的 20 分钟内

        Args:
            start_time: 数据库中的时间字段（datetime.time 对象或字符串 "HH:MM:SS"）

        Returns:
            bool: True 如果在20分钟内，False 否则
        """
        # 获取当前时间
        now = datetime.now()
        current_time = now.time()

        # 如果 start_time 是字符串，先转换
        if isinstance(start_time, str):
            start_time = datetime.strptime(start_time, '%H:%M:%S').time()

        # 计算时间差（转换为当天的时间戳）
        start_datetime = datetime.combine(now.date(), start_time)
        current_datetime = datetime.combine(now.date(), current_time)

        # 如果当前时间小于开始时间，可能是第二天的情况
        if current_datetime < start_datetime:
            # 检查是否在第二天的20分钟内（比如 23:50 检查 00:05 的情况）
            start_datetime_next = start_datetime + timedelta(days=1)
            time_diff = (current_datetime + timedelta(days=1)) - start_datetime
        else:
            time_diff = current_datetime - start_datetime

        # 判断是否在 20 分钟内（1200 秒）
        is_within = 0 <= time_diff.total_seconds() <= 1200

        return is_within

    def _send_meditation_danmaku(self, session: LogOffUser,text_meditation):
        """发送修仙弹幕"""
        from bilibili_api import sync, Credential

        if not session:
            self.logger.warning("没有已登录用户，跳过发送弹幕")
            return

        room, message = logoff_service.get_user_logoff_times(session.user_id)
        if not room:
            self.logger.debug(f"用户 {session.user_name} 没有合适时间段的房间，跳过")
            return

        credential_dict = json.loads(session.credential)
        credential: Credential = LoginCookie.dic_to_credential(credential_dict)

        # danmaku_texts = [text_meditation, "签到"]
        # text = random.choice(danmaku_texts)
        try:
            room_id = room.room_id
            if self._is_within_20_minutes_of_start(room.start_time):
                sync(bili_live_service.send_danmu(room_id, credential, "签到"))
                time.sleep(2)

            sync(bili_live_service.send_danmu(room_id, credential, text_meditation))
            self._sent_count += 1
            self.logger.info(f"[{session.user_name}] 发送修仙弹幕: {text_meditation}")
        except Exception as e:
            self.logger.error(f"发送修仙弹幕异常: {e}",exc_info=True)

    def _send_chengyu_danmaku(self, session: LogOffUser, chengyu: str):
        """发送成语弹幕"""
        from bilibili_api import sync, Credential

        if not session:
            self.logger.warning("没有已登录用户，跳过发送弹幕")
            return

        room, message = logoff_service.get_user_logoff_times(session.user_id)
        if not room:
            self.logger.debug(f"用户 {session.user_name} 没有合适时间段的房间，跳过")
            return

        credential_dict = json.loads(session.credential)
        credential: Credential = LoginCookie.dic_to_credential(credential_dict)

        # danmaku_texts = ["突破", "签到"]
        # text = random.choice(danmaku_texts)
        try:
            room_id = room.room_id
            sync(bili_live_service.send_danmu(room_id, credential, chengyu))
            self._sent_count += 1
            self.logger.info(f"[{session.user_name}] 发送成语: {chengyu} (第{self._sent_count}条)")
        except Exception as e:
            self.logger.error(f"发送成语弹幕异常: {e}",exc_info=True)

    def reset_game(self):
        """手动重置游戏"""
        chengyu_agent.reset()
        start_chengyu = chengyu_agent.get_random_chengyu()
        self.logger.info(f"成语接龙已手动重置，起始成语: {start_chengyu}")
        return start_chengyu

    def get_current_chengyu(self):
        """获取当前成语"""
        return chengyu_agent.get_current()


# 全局实例
danmaku_scheduler = DanmakuScheduler()