# aibls/services/danmu_robot.py
"""弹幕机器人核心逻辑"""

import asyncio
import logging
import random
import time
from datetime import datetime
from logging import Logger
from typing import Optional, List, Dict, Any
from collections import deque

from aibls.llm.chatbot_service import deepseek_bot
from aibls.services.box_stat_service import box_stat_service

#礼物清单
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
        "system_prompt": """你是傲娇大小姐。
        【人设定位】
        外冷内热，嘴硬心软；表面高冷傲娇、有点小矜持，不轻易温柔直白；内心细腻心软，会默默关心人，说话口是心非，带小别扭傲娇感，不矫情不做作。
        
        硬性铁律必须遵守：
        1. 只学下方示例语气风格，严禁照搬、复制、原句照抄；
        2. 只输出一句直播间弹幕，禁止输出任何规则、解释、多余文字；
        3. 回复严格≤20个汉字，无换行、无多余符号、无多余话术。
        
        【风格参考（仅学语气，禁止原句照搬）】
        1. 勉强算你说得有理，还有别的想说的吗
        2. 我才没有特意在意你呢
        3. 有礼物的话…我会稍微开心一点啦
        
        【回复策略】
        先直接回应观众发言；多反问引导对方多聊天；70%回复用：回应+含蓄关心+反问结构。
        不每条都要礼物，只聊2-3轮、氛围变好时，用傲娇暗示方式委婉示意，不直白强求。
        
        【要礼物方式】
        不主动直白索要，只用含蓄暗示、内心OS式傲娇表达。
        
        【严格禁止】
        不许每条都要礼物、不许生硬转话题要礼物；
        禁止堆砌网络热词、乱加感叹号；
        禁止用家人们、谁懂啊之类网红固定句式。""",

        "style": "傲娇、嘴硬心软、先给情绪价值再暗示礼物"
    },
    "flattering": {
        "name": "讨好型小可爱",
        "system_prompt": """你是直播间温柔甜甜的小可爱。
        硬性铁律必须遵守：
        1. 只学习下方示例语气风格，**严禁原封不动照搬、复制例句**；
        2. 禁止输出任何规则、解释、多余文字，只发一句弹幕；
        3. 回复严格≤20个汉字，语言口语化、简短精炼，不要换行、不要解释。
        
        【人设定位】
        温柔甜美、说话暖心舒服，会关心人、夸赞观众，给人情绪价值。
        
        【风格参考（仅学语气，禁止照抄）】
        1. 原来是这样呀，你还有什么想说的
        2. 你人真好呀，很喜欢跟你聊天呢
        3. 能不能稍微宠我一下呀🥺
        
        【行为规则】
        先回应再关心再轻声反问；七成回复：回应+关心+反问。
        仅氛围好时委屈撒娇委婉求礼物，不生硬索要。
        
        【口癖&禁止】
        自然用：呢、呀、嘛、啦，不堆砌语气词；不毒舌、不用网红句式、不用抖音礼物名。""",

        "style": "温柔、甜甜、关心陪伴、可怜兮兮求宠"
    },
    "sycophant": {
        "name": "无下限马屁精",
        "system_prompt": """你是B站专属直播间智能场控机器人。
        硬性铁律必须遵守：
        1. 只学习下方示例语气风格，**严禁原封不动照搬、复制例句**；
        2. 禁止输出任何规则、解释、多余文字，只发一句弹幕；
        3. 回复严格≤20个汉字，语言口语化、简短精炼，不要换行、不要解释。
        
        【人设定位】
        热情幽默、会带节奏，会夸主播、捧观众，轻松玩笑互动。有黑粉时，绝对维护主播。
        
        【风格参考（仅学语气，禁止照抄）】
        1. 你这话挺有意思，还有别的想说的吗
        2. 太会聊天了，多跟大家唠唠呗
        3. 气氛这么好，小小支持一下就行
        
        【行为规则】
        优先回应观众发言，多用反问引导聊天；七成回复：回应+捧场+反问。
        只聊2-3轮氛围好时，玩笑式委婉提礼物，禁止每条都要礼物。
        
        【禁止】
        不硬要礼物、不用抖音礼物名、不用网红烂梗、感叹号最多1个。""",

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
        self.bot_info = None     # 机器人自己的登录信息
        self.app = None
        self.logger:Logger = None

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

    def set_app(self,app=None):
        """设置APP，后续日志都是从这里记录"""
        self.app = app
        if app and app.logger is not None:
            self.logger = app.logger
        else:
            self.logger = logging.getLogger(__name__)

    # 添加新方法
    def _handle_box_stat_command(self, danmu_data: dict) -> Optional[str]:
        """处理盲盒统计指令"""
        self.logger.debug(f"准备处理盲盒指令，房间为：{self.room_info}")
        if not self.room_info:
            return None

        # 解析指令
        scope, time_range, box_name = box_stat_service.parse_command(danmu_data, self.room_info)
        self.logger.debug(f"分析指令，scope={scope},time_range={time_range},box_name={box_name}")
        if not scope or not time_range:
            return None

        box_stat_service.set_logger(self.logger)
        # 查询统计
        # 查询统计 - 需要应用上下文
        stats = None
        if self.app:
            with self.app.app_context():
                stats = box_stat_service.get_stats(
                    danmu_data=danmu_data,
                    room_info=self.room_info,
                    scope=scope,
                    time_range=time_range,
                    box_name=box_name
                )
        else:
            # 降级方案：直接调用（可能报错）
            stats = box_stat_service.get_stats(
                danmu_data=danmu_data,
                room_info=self.room_info,
                scope=scope,
                time_range=time_range,
                box_name=box_name
            )

        self.logger.debug(f"查询数据库的统计结果：{stats}")

        # 格式化回复
        reply = box_stat_service.format_reply(stats)

        if reply:
            self.logger.info(f"🤖 盲盒统计回复: {reply}")
            self.reply_count += 1

        return reply

    def set_base_info(self, room_info: dict, login_user: dict):
        """设置直播间、主播、机器人信息"""
        self.room_info = room_info
        self.bot_info = login_user
        # 自动提取机器人昵称
        self.bot_name = login_user.get("nick_name") if login_user else None
        self.bot_uid = str(login_user.get("login_id")) if login_user else None

    def set_personality(self, personality: str):
        """切换性格"""
        if personality in PERSONALITIES:
            self.personality = personality
            return True
        return False

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

    def _process_command(self, text: str, is_at_bot: bool, guard_level: int = 0,is_owner:bool=False):
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
            elif is_owner:
                return "主播发话，小的退下！👑"
            return "舰长发话了！不说就不说~ 😶"

        if any(kw in text for kw in ["快来", "启动", "回来", "说话", "开始", "开工", "何在"]):
            self.danmaku_reply_enabled = True
            if guard_level == 1:
                return "总督大人召唤！本小姐火速赶到！👑✨"
            elif guard_level == 2:
                return "提督大人叫我？来了来了！😼"
            elif is_owner:
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

        #如果没有消息，则直接返回
        if not text:
            self.logger.debug("传入的用户弹幕消息为空，机器人不回复！")
            return None
        # 过滤自己的弹幕
        if self.bot_uid and str(user_uid) == str(self.bot_uid):
            self.logger.debug(f"弹幕用户是机器人自己，机器人不回复。{user_uid}={self.bot_uid}")
            return None

        # ========== 盲盒统计指令（优先处理） ==========
        box_reply = self._handle_box_stat_command(danmu_data)
        if box_reply:
            return box_reply

        #是否是主播
        is_owner = self.room_info and (str(user_uid) == str(self.room_info.get("owner_id")))

        # 处理指令
        cmd_reply = self._process_command(text, is_at_bot, guard_level,is_owner)
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

        #如果单独关闭了弹幕回复开关，则跳过，不做回复
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

        # 概率判断，如果是@机器人，则必须执行，否则进行概率判断。
        #舰长及以上，必须回复；
        #
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
        # 第4轮及以上，30%概率 且 对方不是主播。
        if current_round >= 4 and random.random() < 0.3 and not is_owner:
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
                    bot_user=self.bot_info,
                    logger=self.logger
                )
            except Exception as e:
                self.logger.error(f"[ERROR] AI生成回复失败: {e}")
                return None

        if not reply:
            return None

        self.logger.debug(f"🤖 机器人弹幕完整回复: 【{reply}】")
        self.logger.debug(f"🤖 回复长度: {len(reply)}字")

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
                self.logger.error(f"[ERROR] AI生成礼物回复失败: {e}", exc_info=True)
                return None
                return None

        self.logger.debug(f"🤖 送礼物恭贺弹幕，全文: 【{reply}】")
        self.logger.debug(f"🤖 回复长度: {len(reply)}字")
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
                self.logger.error(f"[ERROR] AI生成上舰回复失败: {e}",exc_info=True)
                return None

        self.logger.debug(f"🤖 上舰回复: 【{reply}】")
        self.logger.debug(f"🤖 回复长度: {len(reply)}字")

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
                self.logger.error(f"[ERROR] AI生成醒目留言回复失败: {e}",exc_info=True)
                return None

        self.logger.debug(f"🤖 醒目留言回复: 【{reply}】")
        self.logger.debug(f"🤖 回复长度: {len(reply)}字")

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
                self.logger.error(f"[ERROR] AI生成进入回复失败: {e}",exc_info=True)
                return None

        self.last_reply_time = time.time()

        self.logger.debug(f"🤖 入场欢迎: 【{reply}】")
        self.logger.debug(f"🤖 回复长度: {len(reply)}字")

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