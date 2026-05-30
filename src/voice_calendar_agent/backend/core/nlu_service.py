"""
NLU解析服务
使用大模型API将自然语言转换为标准化指令。
支持OpenAI格式（deepseek/mimo等）和Anthropic格式。
"""
import re
import json
import logging
from enum import Enum
from typing import Optional
from datetime import datetime

logger = logging.getLogger(__name__)

# 中文星期，用于在提示词里告诉大模型“今天是周几”
_WEEKDAYS = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]


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

        根据 provider 懒加载对应的客户端，只建一次。
        输入：无
        输出：无
        """
        if self._client is not None:
            return

        if self.provider == LLMProvider.ANTHROPIC:
            # Claude
            from anthropic import Anthropic
            self._client = Anthropic(api_key=self.api_key)
        else:
            # OpenAI 兼容格式（DeepSeek / Mimo 等）
            from openai import OpenAI
            kwargs = {"api_key": self.api_key}
            if self.base_url:
                kwargs["base_url"] = self.base_url
            self._client = OpenAI(**kwargs)

    def parse_command(self, text: str) -> dict:
        """
        解析语音指令

        输入：
            text: 语音识别后的文本
        输出：
            dict - 解析结果，包含以下字段：
                - intent: 意图类型 (add_event/delete_event/update_event/query_events/unknown)
                - title: 事件标题（可选）
                - time: ISO8601 绝对时间字符串，如 "2026-05-30T15:15:00"（可能为 None）
                - reminder: 是否提醒（默认True）
                - reminder_minutes: 提前提醒分钟数（默认0）
                - description: 事件描述（可选）
        """
        if not text or not text.strip():
            return {"intent": "unknown", "title": "", "time": None,
                    "reminder": True, "reminder_minutes": 0, "description": ""}

        try:
            self._init_client()
            prompt = self._build_prompt(text)

            if self.provider == LLMProvider.ANTHROPIC:
                raw = self._call_anthropic(prompt)
            else:
                raw = self._call_openai(prompt)

            return self._parse_response(raw)
        except Exception as e:
            logger.error(f"NLU 解析失败: {e}")
            return {"intent": "unknown", "title": "", "time": None,
                    "reminder": True, "reminder_minutes": 0, "description": ""}

    def _build_prompt(self, text: str) -> str:
        """
        构建NLU解析提示词

        输入：
            text: 用户输入文本
        输出：
            str - 格式化的提示词
        """
        now = datetime.now()
        now_str = now.strftime("%Y-%m-%dT%H:%M:%S")
        weekday = _WEEKDAYS[now.weekday()]

        return f"""你是日历指令解析助手。当前时间是 {now_str}（{weekday}）。
请把用户的一句话解析成 JSON，只输出 JSON，不要 markdown、不要任何解释。

字段说明：
- intent: 意图，取值 add_event / delete_event / update_event / query_events / unknown
- title: 事件标题；删除或查询时填关键词，可为空字符串
- time: ISO8601 绝对时间字符串，如 "2026-05-30T15:15:00"。
        把"明天""下周三""三点一刻(=15分)""下午三点"等换算成绝对时间；
        查询某一天但没有具体时刻时，用当天的 00:00:00；
        完全没有时间则填 null
- reminder: 是否需要提醒，true 或 false
- reminder_minutes: 提前多少分钟提醒，整数，没提到则填 0
- description: 备注说明，没有则空字符串

示例：
输入："明天下午3点一刻开会，提前半小时提醒我"
输出：{{"intent":"add_event","title":"开会","time":"{now.strftime('%Y-%m-%d')}T15:15:00","reminder":true,"reminder_minutes":30,"description":""}}

用户的话：{text}"""

    def _call_openai(self, prompt: str) -> str:
        """
        调用OpenAI格式API（DeepSeek/Mimo 等）

        输入：
            prompt: 提示词
        输出：
            str - 模型返回的文本
        """
        resp = self._client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
        )
        return resp.choices[0].message.content

    def _call_anthropic(self, prompt: str) -> str:
        """
        调用Anthropic格式API（Claude）

        输入：
            prompt: 提示词
        输出：
            str - 模型返回的文本
        """
        resp = self._client.messages.create(
            model=self.model,
            max_tokens=1024,
            temperature=0,
            messages=[{"role": "user", "content": prompt}],
        )
        # content 是内容块列表，把所有文本块拼起来
        return "".join(
            block.text for block in resp.content
            if getattr(block, "type", None) == "text"
        )

    def _parse_response(self, response_text: str) -> dict:
        """
        解析模型响应

        输入：
            response_text: 模型返回的原始文本
        输出：
            dict - 结构化的解析结果
        """
        text = (response_text or "").strip()

        # 去掉可能的 ```json ... ``` 代码块包裹
        if text.startswith("```"):
            text = text.strip("`")
            text = re.sub(r"^json", "", text, flags=re.IGNORECASE).strip()

        # 容错：只取第一个 { ... } JSON 对象
        match = re.search(r"\{.*\}", text, re.S)
        if match:
            text = match.group(0)

        data = json.loads(text)

        # 补默认值，保证返回结构稳定
        return {
            "intent": data.get("intent", "unknown"),
            "title": data.get("title", ""),
            "time": data.get("time"),                       # ISO 字符串或 None
            "reminder": data.get("reminder", True),
            "reminder_minutes": data.get("reminder_minutes", 0),
            "description": data.get("description", ""),
        }
