# aibls/llm/chatbot_service.py
"""弹幕机器人 LLM 服务 - 基于 DeepSeek"""

import os
import re
from datetime import datetime
from typing import Optional, List, Dict, Any

import requests



class DeepSeekBotService:
    """DeepSeek 弹幕机器人服务"""

    def __init__(self, api_key: str = None, model: str = "deepseek-chat"):
        self.api_key = api_key or os.environ.get("DEEPSEEK_API_KEY", "")
        print(f"API Key 已设置: {bool(self.api_key)}")
        self.base_url = "https://api.deepseek.com/v1"
        self.model = model
        self.current_year = datetime.now().year

    def _get_hotword_prompt(self) -> str:
        """动态生成热词和热点要求"""
        return f"""【网络热词】
如果当前话题有合适的近期热词（{self.current_year}年流行），可以自然融入（最多1个）
如果没有合适的，就不要硬加

【B站热点】
如果你知道 B站 最近（{self.current_year}年）的热门事件、热门视频、热门梗，可以适当融入回复
不知道就说没有，不要瞎编

【重要】
保持回复自然流畅，不要为了用热词而破坏通顺度"""

    def _call_api(self, messages: List[Dict[str, str]], temperature: float = 0.65, max_tokens: int = 35) -> Optional[str]:
        """调用 DeepSeek API"""
        if not self.api_key:
            print("[ERROR] DeepSeek API Key 未设置！")
            return None

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }

        data = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens
        }

        try:
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=data,
                timeout=10
            )

            if response.status_code == 200:
                result = response.json()
                content = result['choices'][0]['message']['content'].strip()
                content = re.sub(r'[\n\r]', '', content)
                return content
            else:
                print(f"[ERROR] API 调用失败: {response.status_code}")
                return None
        except Exception as e:
            print(f"[ERROR] API 请求异常: {e}")
            return None

    async def chat(self, system_prompt: str, user_prompt: str, temperature: float = 0.65) -> Optional[str]:
        """通用对话接口"""
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        return self._call_api(messages, temperature)

    async def generate_danmaku_reply(
            self,
            personality: str,
            personality_style: str,
            context: List[str],
            danmu_data: Dict[str, Any],
            gift_hint: str = "",
            room_info: dict = None,
            login_user:dict = None
    ) -> Optional[str]:
        context_str = "\n".join(context[-10:]) if context else "（暂无历史弹幕）"

        user_name = danmu_data.get("sender_name", "未知用户")
        user_text = danmu_data.get("message", "")
        guard_level = danmu_data.get("guard_level", 0)

        if guard_level == 1:
            user_title = "总督大佬"
        elif guard_level == 2:
            user_title = "提督大佬"
        elif guard_level == 3:
            user_title = "舰长大佬"
        else:
            user_title = "普通用户"
        # 机器人信息
        bot_info = ""
        print(f"生成模板前，登录用户信息：{login_user}")
        if login_user:
            bot_name = login_user.get("nick_name")
            if bot_name:
                bot_info = f"你的昵称是「{bot_name}」。用户可能会用完整昵称、昵称的一部分、或者@符号来称呼你。请根据上下文判断是否在叫你。"

        # 构建主播信息
        host_info = ""
        if room_info:
            host_name = room_info.get("owner_name")
            if host_name:
                host_info = f"当前主播是「{host_name}」。用户可能会用简称、外号或昵称的一部分来称呼主播，请根据上下文判断是否指主播本人。主播是唱歌的不会跳舞等其他才艺。"

        user_prompt = f"""最重要：回复必须 10-20 字，你写完后自己数一下，超过重新生成
    
    {bot_info}
        
    【弹幕历史】
    {context_str}

    【当前弹幕】
    {user_name}（{user_title}）：{user_text}

    {host_info}

    【最重要的规则】
    回复必须10-20字，一句话！先直接回答用户的问题。

    {self._get_hotword_prompt()}

    【互动策略】
    - 多反问观众，让ta多说
    - 70%的回复应该是：回应+关心+反问
    - 不要每条回复都要礼物

    {gift_hint}

    【性格要求】
    {personality_style}

    请直接回复："""

        return await self.chat(personality, user_prompt, temperature=0.65)

    async def generate_gift_reply(
            self,
            personality: str,
            personality_style: str,
            user_name: str,
            gift_name: str,
            gift_num: int,
            price: int,
            tier: str
    ) -> Optional[str]:
        tier_map = {
            "small": "小礼物",
            "medium": "中礼物",
            "large": "大礼物",
            "luxury": "豪礼"
        }

        battery_price = price // 100  # 金瓜子转电池

        user_prompt = f"""最重要：回复必须 10-20 字，你写完后自己数一下，超过重新生成.
        用户「{user_name}」送了【{gift_name} x{gift_num}】（价值{battery_price}电池，{tier_map.get(tier, '礼物')}）

    【要求】
    1. 热情感谢，匹配礼物档次
    2. 自然地说，不要用固定句式
    3. 结尾可以引导互动（点歌或发弹幕），注意：点歌要100人气票或1个心动盲盒
    4. 回复10-20字

    【性格】
    {personality_style}

    请直接回复："""

        return await self.chat(personality, user_prompt, temperature=0.7)

    async def generate_guard_reply(
            self,
            personality: str,
            personality_style: str,
            user_name: str,
            guard_name: str,
            guard_level: int,
            num: int
    ) -> Optional[str]:
        guard_display = {1: "总督", 2: "提督", 3: "舰长"}.get(guard_level, guard_name)

        user_prompt = f"""用户「{user_name}」开通了【{guard_display} x{num}个月】！

    【要求】
    1. 炸裂式庆祝，要有排面感
    2. 自然地说，不要用固定句式
    3. 引导用户发弹幕点歌，注意：点歌要100人气票或1个心动盲盒
    4. 回复10-20字

    【性格】
    {personality_style}

    请直接回复："""

        return await self.chat(personality, user_prompt, temperature=0.7)

    async def generate_super_chat_reply(
            self,
            personality: str,
            personality_style: str,
            user_name: str,
            message: str,
            price: int
    ) -> Optional[str]:
        msg_preview = message[:20] + "..." if len(message) > 20 else message

        user_prompt = f"""最重要：回复必须 10-20 字，你写完后自己数一下，超过重新生成。
        
        用户「{user_name}」付费{price}元说：「{msg_preview}」

    【要求】
    1. 引用他的话并评价
    2. 引导其他观众讨论
    3. 自然地说，不要用固定句式
    4. 回复10-20字

    【性格】
    {personality_style}

    请直接回复："""

        return await self.chat(personality, user_prompt, temperature=0.7)

    async def generate_enter_reply(
            self,
            personality: str,
            personality_style: str,
            user_name: str,
            guard_level: int = 0,
            fans_medal_name: str = ""
    ) -> Optional[str]:
        """生成进入直播间回复"""
        guard_info = ""
        if guard_level == 3:
            guard_info = "（舰长大佬）"
        elif guard_level == 2:
            guard_info = "（提督大佬）"
        elif guard_level == 1:
            guard_info = "（总督大佬）"

        medal_info = f" 粉丝牌「{fans_medal_name}」" if fans_medal_name else ""

        user_prompt = f"""最重要：回复必须 10-20 字，你写完后自己数一下，超过重新生成。
        
        用户「{user_name}」进入直播间{guard_info}{medal_info}

要求：
1. {personality_style}
2. {self._get_hotword_prompt()}
3. 热情欢迎，如果是大佬要特别捧
4. 结尾引导发弹幕互动
5. 严格40字以内，只回复内容本身"""

        return await self.chat(personality, user_prompt, temperature=0.8)


# 全局实例
deepseek_bot = DeepSeekBotService()