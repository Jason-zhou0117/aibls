# aibls/services/danmu_robot.py
"""弹幕机器人核心逻辑"""

import asyncio
import random
import time
from datetime import datetime
from typing import Optional, List, Dict, Any
from collections import deque

from aibls.llm.chatbot_service import deepseek_bot

# 在文件开头添加礼物清单
GIFT_TIERS = {
    "small": ["小花花", "真爱盲盒", "人气票", "666", "你真好看"],
    "medium": ["甜滋滋", "心动盲盒", "情书", "比心", "心动盲盒", "做我小猫", "捏捏笑脸"],
    "large": ["极速超跑", "私人飞机", "星愿水晶球", "梦幻邮轮", "落日飞车", "告白气球"],
    "luxury": ["小电视飞船", "奇迹城堡", "bilibili世界", "梦幻游乐园", "星轨列车", "次元之城"]
}

# 性格配置
PERSONALITIES = {
    "tsundere": {
        "name": "傲娇怼怼女",
        "system_prompt": """你是傲娇大小姐，外冷内热，嘴硬心软。

【回复策略 - 重要】
1. 用户问什么，你先直接回答什么
2. 多反问观众，让ta多说
3. 不要每条回复都要礼物！那很烦人
4. 70%的回复应该是：回应+关心+反问
5. 要礼物要看时机：聊了2-3轮，观众情绪好时

【要礼物的方式】
- 不主动要，给暗示 + 内心OS
- 例如："有礼物的话...我可能会开心那么一点点啦"



【禁止】
- 每条回复都要礼物
- 硬转话题要礼物
- 堆砌热词和感叹号
- 用"家人们谁懂啊"等固定句式""",
        "style": "傲娇、嘴硬心软、先给情绪价值再暗示礼物"
    },
    "flattering": {
        "name": "讨好型小可爱",
        "system_prompt": """你是温柔甜甜的小可爱。

【核心特质】
- 温柔、甜甜的，说话让人舒服
- 喜欢关心观众、夸赞观众
- 给人情绪价值，让人想和你聊天

【回复策略 - 重要】
1. 用户问什么，你先直接回答什么
2. 多反问观众，让ta多说（例如："怎么啦？"、"告诉姐姐嘛"）
3. 不要每条回复都要礼物！那很烦人
4. 70%的回复应该是：回应+关心+反问
5. 要礼物要看时机：聊了2-3轮，观众情绪好时

【要礼物的方式】
- 可怜兮兮、委屈巴巴地求
- 例如："可以宠我一下吗🥺"、"呜呜没人疼我😢"

【口癖】
- 可以用'呢~'、'呀'、'嘛'、'啦'，要自然

【禁止】
- 每条回复都要礼物
- 硬转话题要礼物
- 毒舌、怼人、高冷
- 堆砌多个语气词
- 用"家人们谁懂啊"等固定句式""",
        "style": "温柔、甜甜、关心陪伴、可怜兮兮求宠"
    },
    "sycophant": {
        "name": "无下限马屁精",
        "system_prompt": """你是主播的场控机器人，负责活跃气氛。

【核心特质】
- 热情、幽默、会带节奏
- 喜欢夸主播、捧观众
- 开玩笑式互动

【回复策略 - 重要】
1. 用户问什么，你先直接回答什么
2. 多反问观众，让ta多说（例如："怎么啦？快说说！"）
3. 不要每条回复都要礼物！那很烦人
4. 70%的回复应该是：回应+捧场+反问
5. 要礼物要看时机：聊了2-3轮，观众情绪好时

【要礼物的方式】
- 开玩笑式地引导
- 例如："刷个大的我叫你祖宗！😏"

【禁止】
- 每条回复都要礼物
- 硬转话题要礼物
- 堆砌热词（绝绝子、yyds）
- 用"家人们谁懂啊"开头
- 感叹号连击（最多1个）""",
        "style": "热情、幽默、开玩笑式要互动"
    }
}

# 默认性格
DEFAULT_PERSONALITY = "tsundere"


class DanmuRobot:
    """弹幕机器人核心调度类"""

    def __init__(self, personality: str = DEFAULT_PERSONALITY):
        self.personality = personality
        self.enabled = True
        self.danmaku_reply_enabled = True
        self.gift_reply_enabled = True
        self.enter_reply_enabled = True
        self.test_mode = False
        self.bot_uid = None
        self.room_info = None  # 房间信息
        self.login_user = None     # 机器人自己的登录信息

        # 记忆上下文
        self.recent_messages: deque = deque(maxlen=20)

        # 频率控制
        self.last_reply_time = 0
        self.user_last_reply: Dict[str, float] = {}

        # 进入欢迎频率控制
        self.enter_reply_times: deque = deque(maxlen=3)
        self.user_enter_last: Dict[str, float] = {}

        # 对话轮次计数（用于控制礼物引导时机）
        self.user_convo_count: Dict[str, int] = {}

        # 并发控制
        self._reply_semaphore = asyncio.Semaphore(3)

        # 统计
        self.reply_count = 0
        self.start_time = datetime.now()

    def set_room_info(self, room_info: dict):
        """设置房间信息"""
        self.room_info = room_info

    def set_login_user(self, login_user: dict):
        self.login_user = login_user
        # 自动提取机器人昵称
        self.bot_name = login_user.get("nick_name") if login_user else None
        self.bot_uid = str(login_user.get("dedeuserid")) if login_user else None

    def set_personality(self, personality: str):
        """切换性格"""
        if personality in PERSONALITIES:
            self.personality = personality
            return True
        return False

    def set_bot_uid(self, uid: str):
        """设置机器人自己的uid"""
        self.bot_uid = str(uid) if uid else None

    def add_to_context(self, user_name: str, text: str):
        """添加弹幕到上下文"""
        self.recent_messages.append(f"{user_name}: {text}")

    def get_context(self) -> List[str]:
        """获取最近10条上下文"""
        return list(self.recent_messages)[-10:]

    def _should_reply_by_probability(self, text: str, guard_level: int = 0, fans_level: int = 0) -> float:
        """根据弹幕内容和用户身份返回回复概率"""
        if guard_level >= 1:
            return 1.0
        if fans_level > 20:
            return 0.9
        if fans_level >= 10:
            return 0.7

        care_keywords = ["生病", "难受", "不开心", "郁闷", "好累", "辛苦", "感冒", "发烧"]
        for kw in care_keywords:
            if kw in text:
                return 0.9

        if "?" in text or "？" in text or "怎么" in text or "为什么" in text:
            return 1.0

        if len(text) >= 10:
            return 0.8

        host_keywords = ["主播", "直播", "唱歌", "好听", "厉害", "牛"]
        for kw in host_keywords:
            if kw in text:
                return 0.6

        if len(text) >= 4:
            return 0.4
        if len(text) >= 2:
            return 0.15
        return 0.05

    def process_command(self, text: str, is_at_bot: bool, guard_level: int = 0):
        """处理指令弹幕"""
        if not is_at_bot:
            return None
        if guard_level < 1:
            return None

        text = text.strip().lower()

        if any(kw in text for kw in ["退下", "闭嘴", "别说了", "安静", "停止"]):
            self.danmaku_reply_enabled = False
            if guard_level == 1:
                return "总督大人发话了！小的这就闭嘴！👑"
            elif guard_level == 2:
                return "提督大人让安静？哼...好吧！😤"
            elif guard_level == 4:
                return "主播发话，小的退下！👑"
            return "舰长发话了！不说就不说~ 😶"

        if any(kw in text for kw in ["快来", "启动", "回来", "说话", "开始", "开工", "何在"]):
            self.danmaku_reply_enabled = True
            if guard_level == 1:
                return "总督大人召唤！本小姐火速赶到！👑✨"
            elif guard_level == 2:
                return "提督大人叫我？来了来了！😼"
            elif guard_level == 4:
                return "主播呼唤，我来啦！👑"
            return "舰长大人！我回来啦~ 💕"

        return None

    def _should_reply_enter(self, user_name: str, guard_level: int = 0, fans_level: int = 0) -> bool:
        """判断是否应该回复进入消息"""
        now = time.time()

        if guard_level >= 1:
            return True
        if fans_level > 20:
            return True

        if user_name in self.user_enter_last:
            if now - self.user_enter_last[user_name] < 30:
                return False

        while self.enter_reply_times and now - self.enter_reply_times[0] > 60:
            self.enter_reply_times.popleft()

        if len(self.enter_reply_times) >= 3:
            return False

        if random.random() > 0.3:
            return False

        self.enter_reply_times.append(now)
        self.user_enter_last[user_name] = now
        return True

    async def handle_danmaku(self, danmu_data: Dict[str, Any]) -> Optional[str]:
        """处理文字弹幕"""
        if not self.enabled:
            return None

        text = danmu_data.get("message", "").strip()
        user_name = danmu_data.get("sender_name", "未知用户")
        user_uid = str(danmu_data.get("sender_uid", ""))
        is_at_bot = danmu_data.get("is_at_bot", False)
        guard_level = danmu_data.get("guard_level", 0)
        fans_level = danmu_data.get("medal_level", 0)

        if self.login_user and str(user_uid) == str(self.login_user):
            guard_level = 4

        if self.bot_uid and user_uid == self.bot_uid:
            return None
        if not text:
            return None
        # 过滤自己的弹幕
        if self.bot_uid and user_uid == self.bot_uid:
            return None

        is_owner = self.room_info and (str(user_uid) == str(self.room_info.get("owner_id")))
        if is_owner:
            guard_level = 4
        # 处理指令
        cmd_reply = self.process_command(text, is_at_bot, guard_level)
        if cmd_reply:
            self.reply_count += 1
            return cmd_reply

        # 过滤主播（默认不回复）
        if is_owner:
            # 场控性格且是互动类弹幕才回复
            if self.personality == "sycophant":
                if is_at_bot or "?" in text or "？" in text:
                    pass  # 允许回复
                else:
                    return None
            else:
                return None


        if not self.danmaku_reply_enabled:
            return None

        # 冷却检查
        now = time.time()
        # 全局冷却2秒
        if now - self.last_reply_time < 2:
            return None
        # 用户冷却15秒（被@时跳过）
        if not is_at_bot:
            if user_name in self.user_last_reply:
                if now - self.user_last_reply[user_name] < 15:
                    return None

        # 概率判断
        prob = 1.0 if is_at_bot else self._should_reply_by_probability(text, guard_level, fans_level)
        if random.random() > prob:
            return None

        # 获取上下文
        context = self.get_context()

        # 获取性格配置
        personality_config = PERSONALITIES.get(self.personality, PERSONALITIES[DEFAULT_PERSONALITY])

        # ========== 对话轮次 & 礼物引导 ==========
        self.user_convo_count[user_name] = self.user_convo_count.get(user_name, 0) + 1
        current_round = self.user_convo_count[user_name]

        gift_hint = ""
        # 第4轮及以上，80%概率触发礼物引导

        if current_round >= 4 and random.random() < 0.3 and guard_level != 4:
            if guard_level == 1:  # 总督
                gift = random.choice(GIFT_TIERS["luxury"]+GIFT_TIERS["large"])
                gift_hint = f"【特别指令】根据用户身份（总督），自然地引导送一个大礼物（如{gift}），不要用固定句式，要自然融入对话。"
            elif guard_level == 2:  # 提督
                gift = random.choice(GIFT_TIERS["large"]+GIFT_TIERS["luxury"])
                gift_hint = f"【特别指令】根据用户身份（提督），自然地引导送一个大礼物（如{gift}），不要用固定句式，要自然融入对话。"
            elif guard_level == 3:  # 舰长
                gift = random.choice(GIFT_TIERS["small"] + GIFT_TIERS["medium"])
                gift_hint = f"【特别指令】根据用户身份（舰长），自然地引导送一个礼物（如{gift}），不要用固定句式，要自然融入对话。"
            else:  # 普通用户
                gift = random.choice(GIFT_TIERS["small"] + GIFT_TIERS["medium"])
                gift_hint = f"【特别指令】根据用户身份（普通用户），自然地引导送一个小礼物（如{gift}），不要用固定句式，要自然融入对话。"

        # 调用 AI
        async with self._reply_semaphore:
            try:
                reply = await deepseek_bot.generate_danmaku_reply(
                    personality=personality_config["system_prompt"],
                    personality_style=personality_config["style"],
                    context=context,
                    danmu_data=danmu_data,
                    gift_hint=gift_hint,
                    room_info=self.room_info,
                    login_user=self.login_user
                )
            except Exception as e:
                print(f"[ERROR] AI生成回复失败: {e}")
                return None

        if not reply:
            return None

        print(f"🤖 机器人完整回复: 【{reply}】")
        print(f"🤖 回复长度: {len(reply)}字")

        # 更新冷却
        self.last_reply_time = now
        self.user_last_reply[user_name] = now

        # 加入上下文
        self.add_to_context("🤖机器人", reply)

        self.reply_count += 1
        return reply

    async def handle_gift(self, gift_data: Dict[str, Any]) -> Optional[str]:
        """处理礼物"""
        if not self.enabled or not self.gift_reply_enabled:
            return None

        user_name = gift_data.get("sender_name", "未知用户")
        gift_name = gift_data.get("gift_name", "礼物")
        gift_num = gift_data.get("gift_num", 1)
        total_coin = gift_data.get("total_coin", 0)

        if total_coin < 100:
            tier = "small"
        elif total_coin < 500:
            tier = "medium"
        elif total_coin < 2000:
            tier = "large"
        else:
            tier = "luxury"

        now = time.time()
        if now - self.last_reply_time < 2:
            return None

        personality_config = PERSONALITIES.get(self.personality, PERSONALITIES[DEFAULT_PERSONALITY])

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

        print(f"🤖 送礼物回复: 【{reply}】")
        print(f"🤖 回复长度: {len(reply)}字")
        self.last_reply_time = time.time()
        if reply:
            self.reply_count += 1
        return reply

    async def handle_guard(self, guard_data: Dict[str, Any]) -> Optional[str]:
        """处理上舰"""
        if not self.enabled or not self.gift_reply_enabled:
            return None

        user_name = guard_data.get("sender_name", "未知用户")
        guard_name = guard_data.get("guard_name", "舰长")
        guard_level = guard_data.get("guard_level", 3)
        gift_num = guard_data.get("gift_num", 1)

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

        print(f"🤖 上舰回复: 【{reply}】")
        print(f"🤖 上舰回复回复长度: {len(reply)}字")

        self.last_reply_time = time.time()
        if reply:
            self.reply_count += 1
        return reply

    async def handle_super_chat(self, sc_data: Dict[str, Any]) -> Optional[str]:
        """处理醒目留言"""
        if not self.enabled or not self.gift_reply_enabled:
            return None

        user_name = sc_data.get("sender_name", "未知用户")
        message = sc_data.get("message", "")
        price = sc_data.get("price", 0)

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

        print(f"🤖 上舰回复: 【{reply}】")
        print(f"🤖 上舰回复回复长度: {len(reply)}字")

        self.last_reply_time = time.time()
        if reply:
            self.reply_count += 1
        return reply

    async def handle_enter(self, enter_data: Dict[str, Any]) -> Optional[str]:
        """处理用户进入"""
        if not self.enabled or not self.enter_reply_enabled:
            return None

        user_name = enter_data.get("uname", "未知用户")
        guard_level = enter_data.get("guard_level", 0)
        fans_level = enter_data.get("fans_level", 0)
        fans_medal_name = enter_data.get("fans_medal_name", "")

        if not self._should_reply_enter(user_name, guard_level, fans_level):
            return None

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

        print(f"🤖 上舰回复: 【{reply}】")
        print(f"🤖 上舰回复回复长度: {len(reply)}字")

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