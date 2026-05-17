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
        """动态生成热词要求"""
        return f"使用{self.current_year}年近期网络热词（如尊嘟假嘟、硬控、破防、我真的会谢、绝绝子、家人们谁懂啊等），自然融入回复中"

    def _call_api(self, messages: List[Dict[str, str]], temperature: float = 0.9, max_tokens: int = 60) -> Optional[
        str]:
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
                # 去除可能的标点符号和换行
                content = re.sub(r'[\n\r]', '', content)
                # 限制40字
                if len(content) > 40:
                    content = content[:40]
                return content
            else:
                print(f"[ERROR] API 调用失败: {response.status_code}")
                return None
        except Exception as e:
            print(f"[ERROR] API 请求异常: {e}")
            return None

    async def chat(self, system_prompt: str, user_prompt: str, temperature: float = 0.9) -> Optional[str]:
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
            user_name: str,
            user_text: str
    ) -> Optional[str]:
        """生成文字弹幕回复（有记忆）"""
        context_str = "\n".join(context[-10:]) if context else "（暂无历史弹幕）"

        user_prompt = f"""对话历史：
{context_str}

用户「{user_name}」说：{user_text}

请根据对话历史回复，要求：
1. {personality_style}
2. {self._get_hotword_prompt()}
3. 结尾引导用户继续发弹幕互动
4. 严格40字以内，只回复内容本身"""

        return await self.chat(personality, user_prompt, temperature=0.9)

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
        """生成礼物回复（无记忆）"""
        tier_map = {
            "small": "小礼物（<100瓜子）→ 简短感谢即可",
            "medium": "中礼物（100-500瓜子）→ 热情感谢，用1-2个热词",
            "large": "大礼物（500-2000瓜子）→ 炸裂式感谢，用2-3个热词，要破防感",
            "luxury": "豪礼（>2000瓜子）→ 震惊式感谢，用3个热词，强调'你有矿'、'排面'"
        }

        user_prompt = f"""用户「{user_name}」送了【{gift_name} x{gift_num}】（价值{price}瓜子）

档次：{tier_map.get(tier, tier_map['small'])}

要求：
1. {personality_style}
2. {self._get_hotword_prompt()}
3. 热情感谢，匹配档次热情程度
4. 结尾引导："发弹幕"或"快夸我"或"点歌"
5. 严格40字以内，只回复内容本身"""

        return await self.chat(personality, user_prompt, temperature=0.9)

    async def generate_guard_reply(
            self,
            personality: str,
            personality_style: str,
            user_name: str,
            guard_name: str,  # 舰长/提督/总督
            guard_level: int,
            num: int
    ) -> Optional[str]:
        """生成上舰回复（专属）"""
        guard_level_names = {1: "总督", 2: "提督", 3: "舰长"}
        guard_display = guard_level_names.get(guard_level, guard_name)

        user_prompt = f"""【重磅】用户「{user_name}」开通了【{guard_display} x{num}个月】！

要求：
1. {personality_style}
2. {self._get_hotword_prompt()}
3. 炸裂式庆祝，要有"排面"、"大佬"感
4. 引导用户发弹幕点歌或提要求
5. 严格40字以内，只回复内容本身"""

        return await self.chat(personality, user_prompt, temperature=0.95)

    async def generate_super_chat_reply(
            self,
            personality: str,
            personality_style: str,
            user_name: str,
            message: str,
            price: int
    ) -> Optional[str]:
        """生成醒目留言回复（专属）"""
        # 截取留言前20字
        msg_preview = message[:20] + "..." if len(message) > 20 else message

        user_prompt = f"""【醒目留言】用户「{user_name}」付费{price}元说：「{msg_preview}」

要求：
1. {personality_style}
2. {self._get_hotword_prompt()}
3. 引用他的话并评价
4. 引导其他观众讨论（"大家觉得呢？弹幕扣1/2"）
5. 严格40字以内，只回复内容本身"""

        return await self.chat(personality, user_prompt, temperature=0.9)

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

        user_prompt = f"""用户「{user_name}」进入直播间{guard_info}{medal_info}

要求：
1. {personality_style}
2. {self._get_hotword_prompt()}
3. 热情欢迎，如果是舰长要特别捧
4. 结尾引导发弹幕互动
5. 严格40字以内，只回复内容本身"""

        return await self.chat(personality, user_prompt, temperature=0.8)


# 全局实例
deepseek_bot = DeepSeekBotService()