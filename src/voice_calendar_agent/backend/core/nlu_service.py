"""
NLU解析服务

使用大模型API将自然语言转换为标准化指令。
支持OpenAI格式（deepseek/mimo等）和Anthropic格式。
"""

import json
import logging
from typing import Optional
from enum import Enum

logger = logging.getLogger(__name__)


class LLMProvider(Enum):
    """
    大模型提供商枚举

    属性：
    - OPENAI: OpenAI格式（包括deepseek、mimo等兼容接口）
    - ANTHROPIC: Anthropic格式
    """
    OPENAI = "openai"
    ANTHROPIC = "anthropic"


class NLUService:
    """
    NLU解析服务类

    功能：将语音识别出的自然语言文本转换为结构化的日历操作指令

    属性：
    - provider: 大模型提供商
    - api_key: API密钥
    - model: 模型名称
    - base_url: API基础URL（用于兼容deepseek/mimo等）
    """

    def __init__(
        self,
        provider: str = "openai",
        api_key: str = "",
        model: str = "deepseek-chat",
        base_url: Optional[str] = None,
    ):
        """
        初始化NLU服务

        输入：
            provider: 大模型提供商（openai/anthropic）
            api_key: API密钥
            model: 模型名称
            base_url: API基础URL（可选，用于兼容deepseek/mimo等）
        输出：无
        """
        self.provider = LLMProvider(provider)
        self.api_key = api_key
        self.model = model
        self.base_url = base_url
        self._client = None

    def _init_client(self):
        """
        初始化大模型客户端

        输入：无
        输出：无
        """
        pass

    def parse_command(self, text: str) -> dict:
        """
        解析语音指令

        输入：
            text: 语音识别后的文本
        输出：
            dict - 解析结果，包含以下字段：
                - intent: 意图类型 (add_event/delete_event/update_event/query_events/unknown)
                - title: 事件标题（可选）
                - time: 时间描述（可选）
                - date: 日期描述（可选）
                - reminder: 是否提醒（默认True）
                - description: 事件描述（可选）
        """
        pass

    def _build_prompt(self, text: str) -> str:
        """
        构建NLU解析提示词

        输入：
            text: 用户输入文本
        输出：
            str - 格式化的提示词
        """
        pass

    def _call_openai(self, prompt: str) -> str:
        """
        调用OpenAI格式API

        输入：
            prompt: 提示词
        输出：
            str - 模型返回的文本
        """
        pass

    def _call_anthropic(self, prompt: str) -> str:
        """
        调用Anthropic格式API

        输入：
            prompt: 提示词
        输出：
            str - 模型返回的文本
        """
        pass

    def _parse_response(self, response_text: str) -> dict:
        """
        解析模型响应

        输入：
            response_text: 模型返回的原始文本
        输出：
            dict - 结构化的解析结果
        """
        pass
