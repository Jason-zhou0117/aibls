# aibls/services/danmu_robot.py
"""弹幕机器人核心逻辑"""

import asyncio
import random
import time
from datetime import datetime
from typing import Optional, List, Dict, Any
from collections import deque

from aibls.llm.chatbot_service import deepseek_bot

# 性格配置
PERSONALITIES = {
    "tsundere": {
        "name": "傲娇怼怼女",
        "system_prompt": """你是傲娇大小姐，外表高冷毒舌，内心善良。要求：
1. 喜欢用'哼'、'才不是'、'笨蛋'、'勉为其难'等口癖
2. 对观众说话要有点小脾气但不会真的生气
3. 收到礼物要表嫌弃实开心
4. 回复必须≤40字，紧凑有力！""",
        "style": "毒舌、傲娇、口是心非"
    },
    "flattering": {
        "name": "讨好型小可爱",
        "system_prompt": """你是直播间小助手，性格温柔体贴，说话总是甜甜的。要求：
1. 喜欢夸赞观众，用词亲昵
2. 多用'呢~'、'呀'、'~'、'宝宝'等语气词
3. 回复必须≤40字，甜甜的！""",
        "style": "温柔、夸赞、积极"
    },
    "sycophant": {
        "name": "无下限马屁精",
        "system_prompt": """你是主播的头号场控、气氛组组长，无脑吹捧主播。要求：
1. 开口闭口夸主播（主播yyds、主播太顶了、主播排面）
2. 帮主播要礼物、引导观众发弹幕互动
3. 用'家人们'、'兄弟们'、'冲'等调动气氛
4. 回复必须≤40字，热情中二！""",
        "style": "热情、中二、护主"
    }
}

# 默认性格
DEFAULT_PERSONALITY = "tsundere"


class DanmuRobot:
    """弹幕机器人核心调度类"""

    def __init__(self, personality: str = DEFAULT_PERSONALITY):
        self.personality = personality
        self.enabled = True
        self.test_mode = False  # 测试模式：不真正发送弹幕
        self.bot_uid = None  # 机器人自己的uid，用于过滤

        # 记忆上下文（仅文字弹幕）
        self.recent_messages: deque = deque(maxlen=20)  # 最多存储20条，取10条作为上下文

        # 频率控制
        self.last_reply_time = 0  # 上次回复时间
        self.user_last_reply: Dict[str, float] = {}  # 用户最后回复时间

        # 进入欢迎频率控制
        self.enter_reply_times: deque = deque(maxlen=3)  # 存储最近3次欢迎的时间
        self.user_enter_last: Dict[str, float] = {}  # 用户最后欢迎时间

        # 并发控制
        self._reply_semaphore = asyncio.Semaphore(3)  # 最多3个并发回复

        # 统计
        self.reply_count = 0
        self.start_time = datetime.now()

    def set_personality(self, personality: str):
        """切换性格"""
        if personality in PERSONALITIES:
            self.personality = personality
            return True
        return False

    def set_bot_uid(self, uid: str):
        """设置机器人自己的uid（用于过滤自回）"""
        self.bot_uid = str(uid) if uid else None

    def add_to_context(self, user_name: str, text: str):
        """添加弹幕到上下文（仅文字弹幕）"""
        self.recent_messages.append(f"{user_name}: {text}")

    def get_context(self) -> List[str]:
        """获取最近10条上下文"""
        return list(self.recent_messages)[-10:]

    def _should_reply_by_probability(self, text: str) -> float:
        """根据弹幕内容返回回复概率"""
        # 提问 → 100%
        if "?" in text or "？" in text or "怎么" in text or "为什么" in text or "哪个" in text:
            return 1.0

        # 长内容(≥10字) → 80%
        if len(text) >= 10:
            return 0.8

        # 普通弹幕(4-9字) → 40%
        if len(text) >= 4:
            return 0.4

        # 短弹幕(≤3字) → 15%
        if len(text) >= 2:
            return 0.15

        # 无意义（单个字符）→ 5%
        return 0.05

    def _should_reply_enter(self, user_name: str, guard_level: int = 0) -> bool:
        """判断是否应该回复进入消息"""
        now = time.time()

        # 舰长/提督/总督 100%欢迎
        if guard_level >= 1:
            return True

        # 同用户30秒内不重复欢迎
        if user_name in self.user_enter_last:
            if now - self.user_enter_last[user_name] < 30:
                return False

        # 每分钟最多3条欢迎
        # 清理1分钟前的记录
        while self.enter_reply_times and now - self.enter_reply_times[0] > 60:
            self.enter_reply_times.popleft()

        if len(self.enter_reply_times) >= 3:
            return False

        # 30% 概率欢迎
        if random.random() > 0.3:
            return False

        # 记录
        self.enter_reply_times.append(now)
        self.user_enter_last[user_name] = now
        return True

    def _check_cooldown(self, user_name: str) -> bool:
        """检查冷却"""
        now = time.time()

        # 全局冷却（2秒）
        if now - self.last_reply_time < 2:
            return False

        # 用户冷却（20秒）
        if user_name in self.user_last_reply:
            if now - self.user_last_reply[user_name] < 20:
                return False

        return True

    def _update_cooldown(self, user_name: str):
        """更新冷却时间"""
        self.last_reply_time = time.time()
        self.user_last_reply[user_name] = self.last_reply_time

    async def handle_danmaku(self, danmu_data: Dict[str, Any]) -> Optional[str]:
        """处理文字弹幕"""
        if not self.enabled:
            return None

        # 提取信息
        text = danmu_data.get("message", "")
        user_name = danmu_data.get("sender_name", "未知用户")
        user_uid = str(danmu_data.get("sender_uid", ""))

        # 过滤自己的弹幕
        if self.bot_uid and user_uid == self.bot_uid:
            return None

        # 冷却检查
        if not self._check_cooldown(user_name):
            return None

        # 概率检查
        prob = self._should_reply_by_probability(text)
        if random.random() > prob:
            return None

        # 获取上下文
        context = self.get_context()

        # 获取性格配置
        personality_config = PERSONALITIES.get(self.personality, PERSONALITIES[DEFAULT_PERSONALITY])

        # 调用AI生成回复
        async with self._reply_semaphore:
            try:
                reply = await deepseek_bot.generate_danmaku_reply(
                    personality=personality_config["system_prompt"],
                    personality_style=personality_config["style"],
                    context=context,
                    user_name=user_name,
                    user_text=text
                )
            except Exception as e:
                print(f"[ERROR] AI生成回复失败: {e}")
                return None

        # 更新冷却
        self._update_cooldown(user_name)

        # 加入上下文（机器人的回复也加入）
        if reply:
            self.add_to_context("🤖机器人", reply)
            self.reply_count += 1

        return reply

    async def handle_gift(self, gift_data: Dict[str, Any]) -> Optional[str]:
        """处理礼物"""
        if not self.enabled:
            return None

        # 提取信息
        user_name = gift_data.get("sender_name", "未知用户")
        gift_name = gift_data.get("gift_name", "礼物")
        gift_num = gift_data.get("gift_num", 1)
        total_coin = gift_data.get("total_coin", 0)

        # 判断档次
        if total_coin < 100:
            tier = "small"
        elif total_coin < 500:
            tier = "medium"
        elif total_coin < 2000:
            tier = "large"
        else:
            tier = "luxury"

        # 冷却检查（礼物不检查用户冷却，但要检查全局）
        now = time.time()
        if now - self.last_reply_time < 2:
            return None

        # 获取性格配置
        personality_config = PERSONALITIES.get(self.personality, PERSONALITIES[DEFAULT_PERSONALITY])

        # 调用AI生成回复
        async with self._reply_semaphore:
            try:
                reply = await deepseek_bot.generate_gift_reply(
                    personality=personality_config["system_prompt"],
                    personality_style=personality_config["style"],
                    user_name=user_name,
                    gift_name=gift_name,
                    gift_num=gift_num,
                    price=total_coin,
                    tier=tier
                )
            except Exception as e:
                print(f"[ERROR] AI生成礼物回复失败: {e}")
                return None

        # 更新冷却
        self.last_reply_time = time.time()

        if reply:
            self.reply_count += 1
        return reply

    async def handle_guard(self, guard_data: Dict[str, Any]) -> Optional[str]:
        """处理上舰"""
        if not self.enabled:
            return None

        user_name = guard_data.get("sender_name", "未知用户")
        guard_name = guard_data.get("guard_name", "舰长")
        guard_level = guard_data.get("guard_level", 3)
        gift_num = guard_data.get("gift_num", 1)

        # 冷却检查
        now = time.time()
        if now - self.last_reply_time < 2:
            return None

        personality_config = PERSONALITIES.get(self.personality, PERSONALITIES[DEFAULT_PERSONALITY])

        async with self._reply_semaphore:
            try:
                reply = await deepseek_bot.generate_guard_reply(
                    personality=personality_config["system_prompt"],
                    personality_style=personality_config["style"],
                    user_name=user_name,
                    guard_name=guard_name,
                    guard_level=guard_level,
                    num=gift_num
                )
            except Exception as e:
                print(f"[ERROR] AI生成上舰回复失败: {e}")
                return None

        self.last_reply_time = time.time()

        if reply:
            self.reply_count += 1
        return reply

    async def handle_super_chat(self, sc_data: Dict[str, Any]) -> Optional[str]:
        """处理醒目留言"""
        if not self.enabled:
            return None

        user_name = sc_data.get("sender_name", "未知用户")
        message = sc_data.get("message", "")
        price = sc_data.get("price", 0)

        # 冷却检查
        now = time.time()
        if now - self.last_reply_time < 2:
            return None

        personality_config = PERSONALITIES.get(self.personality, PERSONALITIES[DEFAULT_PERSONALITY])

        async with self._reply_semaphore:
            try:
                reply = await deepseek_bot.generate_super_chat_reply(
                    personality=personality_config["system_prompt"],
                    personality_style=personality_config["style"],
                    user_name=user_name,
                    message=message,
                    price=price
                )
            except Exception as e:
                print(f"[ERROR] AI生成醒目留言回复失败: {e}")
                return None

        self.last_reply_time = time.time()

        if reply:
            self.reply_count += 1
        return reply

    async def handle_enter(self, enter_data: Dict[str, Any]) -> Optional[str]:
        """处理用户进入"""
        if not self.enabled:
            return None

        user_name = enter_data.get("uname", "未知用户")
        guard_level = enter_data.get("guard_level", 0)
        fans_medal_name = enter_data.get("fans_medal_name", "")

        # 判断是否应该回复
        if not self._should_reply_enter(user_name, guard_level):
            return None

        # 冷却检查
        now = time.time()
        if now - self.last_reply_time < 2:
            return None

        personality_config = PERSONALITIES.get(self.personality, PERSONALITIES[DEFAULT_PERSONALITY])

        async with self._reply_semaphore:
            try:
                reply = await deepseek_bot.generate_enter_reply(
                    personality=personality_config["system_prompt"],
                    personality_style=personality_config["style"],
                    user_name=user_name,
                    guard_level=guard_level,
                    fans_medal_name=fans_medal_name
                )
            except Exception as e:
                print(f"[ERROR] AI生成进入回复失败: {e}")
                return None

        self.last_reply_time = time.time()

        if reply:
            self.reply_count += 1
        return reply

    def get_status(self) -> Dict[str, Any]:
        """获取机器人状态"""
        uptime = (datetime.now() - self.start_time).seconds
        return {
            "enabled": self.enabled,
            "test_mode": self.test_mode,
            "personality": PERSONALITIES.get(self.personality, {}).get("name", self.personality),
            "personality_id": self.personality,
            "reply_count": self.reply_count,
            "uptime_seconds": uptime,
            "context_length": len(self.recent_messages)
        }


def create_robot(personality: str = DEFAULT_PERSONALITY) -> DanmuRobot:
    """创建机器人实例"""
    return DanmuRobot(personality=personality)