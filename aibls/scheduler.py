# aibls/scheduler.py
import threading
import time
import random
import json
from datetime import datetime

from aibls import LoginCookie, bili_live_service
from aibls.models import LogOffUser
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

    def _run(self):
        """后台线程运行 - 持续接龙模式"""
        with self.app.app_context():
            # 初始化起始成语
            current_chengyu = chengyu_agent.get_random_chengyu()
            self.logger.info(f"成语接龙起始成语: {current_chengyu}")

            while self.running:
                try:
                    # 随机间隔 5-9 分钟 (300-540 秒)
                    interval = random.randint(180, 300)
                    self.logger.debug(f"下次发送弹幕将在 {interval // 60} 分钟后")
                    time.sleep(interval)

                    datas = logoff_service.get_opened_users()
                    if not datas:
                        self.logger.debug("没有可用的用户，跳过本轮")
                        continue

                    # 遍历所有用户
                    for i, data in enumerate(datas):
                        # 用户之间的间隔
                        interval_user = random.randint(5, 10)

                        # 发送修仙弹幕
                        self._send_meditation_danmaku(data)

                        # 间隔后发送成语弹幕
                        interval_chengyu = random.randint(3, 5)
                        time.sleep(interval_chengyu)
                        self._send_chengyu_danmaku(data, current_chengyu)

                        # 获取接龙结果
                        next_chengyu = chengyu_agent.get_next_chengyu(current_chengyu)

                        self.logger.info(f"成语接龙: {current_chengyu} → {next_chengyu}")

                        # 更新当前成语为接龙结果
                        current_chengyu = next_chengyu

                        # 用户间间隔
                        if i < len(datas) - 1:
                            time.sleep(interval_user)

                    # 持续接龙，不重置
                    self.logger.info(f"本轮完成，当前成语: {current_chengyu}，继续下一轮接龙")

                except Exception as e:
                    self.logger.error(f"定时发送弹幕出错: {e}")

    def _send_meditation_danmaku(self, session: LogOffUser):
        """发送修仙弹幕"""
        from bilibili_api import sync, Credential

        if not session:
            self.logger.warning("没有已登录用户，跳过发送弹幕")
            return

        room, message = logoff_service.get_user_logoff_times(session.user_id)
        if not room:
            self.logger.debug(f"用户 {session.user_name} 没有合适时间段的房间，跳过")
            return

        danmaku_texts = ["修炼", "突破", "双修"]
        text = random.choice(danmaku_texts)

        credential_dict = json.loads(session.credential)
        credential: Credential = LoginCookie.dic_to_credential(credential_dict)

        try:
            room_id = room.room_id
            sync(bili_live_service.send_danmu(room_id, credential, text))
            self._sent_count += 1
            self.logger.info(f"[{session.user_name}] 发送修仙弹幕: {text}")
        except Exception as e:
            self.logger.error(f"发送修仙弹幕异常: {e}")

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

        try:
            room_id = room.room_id
            sync(bili_live_service.send_danmu(room_id, credential, chengyu))
            self._sent_count += 1
            self.logger.info(f"[{session.user_name}] 发送成语: {chengyu} (第{self._sent_count}条)")
        except Exception as e:
            self.logger.error(f"发送成语弹幕异常: {e}")

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