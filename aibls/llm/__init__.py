# aibls/llm/__init__.py
from .chengyu_service import chengyu_agent, BaseLLMService
from .chatbot_service import deepseek_bot

__all__ = ["chengyu_agent", "BaseLLMService", "deepseek_bot"]