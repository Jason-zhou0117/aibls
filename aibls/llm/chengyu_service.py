# aibls/llm/chengyu_service.py
import os
import re
import requests
import json
import random
from typing import Optional
from abc import ABC, abstractmethod


class BaseLLMService(ABC):
    """大模型服务基类"""

    @abstractmethod
    def get_random_chengyu(self) -> Optional[str]:
        """随机获取一个成语"""
        pass

    @abstractmethod
    def get_next_chengyu(self, previous_chengyu: str) -> Optional[str]:
        """根据上一个成语获取接龙成语"""
        pass


class OpenAIService(BaseLLMService):
    """OpenAI API 服务"""

    def __init__(self, api_key: str = None, base_url: str = None, model: str = "gpt-3.5-turbo"):
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY", "")
        self.base_url = base_url or os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1")
        self.model = model
        self._last_chengyu = None  # 只保存最近一条成语

    def _call_api(self, prompt: str) -> Optional[str]:
        """调用大模型 API"""
        if not self.api_key:
            print(f"[ERROR] API Key 未设置！")
            return None

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }

        data = {
            "model": self.model,
            "messages": [
                {"role": "system",
                 "content": "你是一个成语接龙助手。严格要求：1. 必须返回**严格四字成语**，不能是多字短语（如'夏虫不可语冰'是6字，不允许）；2. 上一个成语的最后一个字与接龙成语的第一个字必须读音相同；3. 只返回成语本身，不要有任何解释、标点、引号或多余字符。如果找不到，只返回'重置'。"},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.5,
            "max_tokens": 20
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
                # 去除可能的标点符号
                content = re.sub(r'[，,。！？;；:：""''【】《》\s]', '', content)
                print(f"[DEBUG] API 返回: '{content}'")
                return content
            else:
                print(f"[ERROR] API 调用失败: {response.status_code}")
                return None
        except Exception as e:
            print(f"[ERROR] API 请求异常: {e}")
            return None

    def get_random_chengyu(self) -> Optional[str]:
        """大模型随机选择一个成语"""
        prompt = "请随机想一个四字成语，不要有任何规律，想哪个就返回哪个。只返回成语本身，不要有任何解释或标点。"

        result = self._call_api(prompt)

        # 验证返回的是否是有效的成语（4个汉字）
        if result and len(result) == 4 and re.match(r'^[\u4e00-\u9fff]{4}$', result):
            self._last_chengyu = result
            return result

        # 备用成语库
        fallback_list = [
            "一心一意", "三心二意", "四面八方", "五光十色", "六神无主",
            "七上八下", "八仙过海", "九牛一毛", "十全十美", "百发百中",
            "千军万马", "万无一失", "气象万千", "天下无双", "双管齐下"
        ]
        self._last_chengyu = random.choice(fallback_list)
        print(f"[INFO] 使用备用成语: {self._last_chengyu}")
        return self._last_chengyu

    def get_next_chengyu(self, previous_chengyu: str) -> Optional[str]:
        """根据上一个成语获取接龙成语"""
        if not previous_chengyu:
            return self.get_random_chengyu()

        last_char = previous_chengyu[-1]

        prompt = f"""成语接龙：上一个成语是"{previous_chengyu}"，最后一个字是"{last_char}"。
请接一个成语，要求：
1. 必须返回一个**严格四字成语**，不能是多字短语
2. 接龙的成语第一个字必须与"{last_char}"读音相同（声调可以不同，字可以不同）
3. 例如："势不可挡"最后一个字是"挡"(dǎng) → 接龙成语"当仁不让"
4. 只返回成语本身，不要有任何解释、标点或多余字符
5. 如果找不到合适的四字成语，只返回"重置"二字"""

        result = self._call_api(prompt)

        # 检查是否需要重置
        if result == "重置" or "重置" in result:
            print(f"大模型返回重置，将重新获取随机成语")
            return self.get_random_chengyu()

        # 严格验证：必须是4个汉字
        if result and len(result) == 4 and re.match(r'^[\u4e00-\u9fff]{4}$', result):
            self._last_chengyu = result
            return result

        # 如果返回的不是4字成语，尝试重试一次
        print(f"大模型返回无效: {result}，尝试重试...")
        retry_prompt = f"请重新接龙：'{previous_chengyu}' 最后一个字是'{last_char}'，需要严格四字成语。只返回四字成语本身。"
        retry_result = self._call_api(retry_prompt)

        if retry_result and len(retry_result) == 4 and re.match(r'^[\u4e00-\u9fff]{4}$', retry_result):
            self._last_chengyu = retry_result
            return retry_result

        # 重试失败，重置
        print(f"重试仍无效，重新获取随机成语")
        return self.get_random_chengyu()

    def get_current(self) -> Optional[str]:
        """获取当前成语"""
        return self._last_chengyu

    def reset(self):
        """重置会话"""
        self._last_chengyu = None


class DeepSeekService(OpenAIService):
    """DeepSeek API 服务"""

    def __init__(self, api_key: str = None):
        super().__init__(
            api_key=api_key,
            base_url="https://api.deepseek.com/v1",
            model="deepseek-chat"
        )


class MoonshotService(OpenAIService):
    """月之暗面 Kimi API 服务"""

    def __init__(self, api_key: str = None):
        super().__init__(
            api_key=api_key,
            base_url="https://api.moonshot.cn/v1",
            model="moonshot-v1-8k"
        )


class SiliconFlowService(OpenAIService):
    """硅基流动 API 服务"""

    def __init__(self, api_key: str = None):
        super().__init__(
            api_key=api_key,
            base_url="https://api.siliconflow.cn/v1",
            model="deepseek-ai/DeepSeek-V3"
        )


# 配置（从环境变量读取）
LLM_PROVIDER = os.environ.get("LLM_PROVIDER", "openai")

if LLM_PROVIDER == "deepseek":
    chengyu_agent = DeepSeekService(api_key=os.environ.get("DEEPSEEK_API_KEY"))
elif LLM_PROVIDER == "moonshot":
    chengyu_agent = MoonshotService(api_key=os.environ.get("MOONSHOT_API_KEY"))
elif LLM_PROVIDER == "siliconflow":
    chengyu_agent = SiliconFlowService(api_key=os.environ.get("SILICONFLOW_API_KEY"))
else:
    chengyu_agent = OpenAIService(api_key=os.environ.get("OPENAI_API_KEY"))