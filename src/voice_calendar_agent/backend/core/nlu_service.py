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
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

# 中文星期，用于在提示词里告诉大模型"今天是周几"
_WEEKDAYS = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]

_nlu_service_instance: Optional["NLUService"] = None


def get_nlu_service(settings=None) -> "NLUService":
    """
    获取NLU解析服务单例

    输入：
        settings: 应用配置对象（可选，首次调用时需要）
    输出：
        NLUService - NLU解析服务实例
    """
    global _nlu_service_instance
    if _nlu_service_instance is None:
        if settings is None:
            from voice_calendar_agent.config import Settings

            settings = Settings()
        _nlu_service_instance = NLUService(
            provider=settings.LLM_PROVIDER,
            api_key=settings.LLM_API_KEY,
            model=settings.LLM_MODEL,
            base_url=settings.LLM_BASE_URL,
        )
    return _nlu_service_instance


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
                    "time_range": "day", "reminder": True, "reminder_minutes": 0, "description": ""}

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
                    "time_range": "day", "reminder": True, "reminder_minutes": 0, "description": ""}

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
        tomorrow_str = (now + timedelta(days=1)).strftime("%Y-%m-%d")

        return f"""你是日历指令解析助手。当前时间是 {now_str}（{weekday}）。
请把用户的一句话解析成 JSON，只输出 JSON，不要 markdown、不要任何解释。

字段说明：
- intent: 意图，取值 add_event / delete_event / update_event / query_events / unknown
- title: 事件标题。规则：
        · 添加事件(add_event)时，填具体事件名（"开会"、"看电影"等）
        · 删除/查询时：
          - 用户说**具体事件类型**（"会议"、"面试"、"飞机"、"约会"等）→ 填进 title，用于模糊匹配
          - 用户说**泛指词**（"事情"、"事"、"日程"、"安排"、"计划"、"东西"、"内容"）→ title 填**空字符串 ""**，表示"那一天的全部事件"
- time: ISO8601 绝对时间字符串，如 "2026-05-30T15:15:00"。
        把"明天""下周三""三点一刻(=15分)""下午三点"等换算成绝对时间；
        查询/删除某一天但没有具体时刻时，用当天的 00:00:00；
        完全没有时间则填 null
- time_range: 时间段，取值 morning(上午) / afternoon(下午) / evening(晚上) / day(全天)。
        用户说"上午"则 morning，"下午"则 afternoon，"晚上"则 evening；
        没有提到时间段则填 day
- reminder: 是否需要提醒，true 或 false
- reminder_minutes: 提前多少分钟提醒，整数，没提到则填 0
- description: 备注说明，没有则空字符串

示例 1（添加，具体时间）：
输入："明天下午3点一刻开会，提前半小时提醒我"
输出：{{"intent":"add_event","title":"开会","time":"{tomorrow_str}T15:15:00","time_range":"day","reminder":true,"reminder_minutes":30,"description":""}}

示例 2（查询，时间段）：
输入："明天上午有哪些事情"

输出：{{"intent":"query_events","title":"","time":"{tomorrow_str}T00:00:00","time_range":"morning","reminder":false,"reminder_minutes":0,"description":""}}

示例 3（删除，带具体关键词）：
输入："删除明天的会议"
输出：{{"intent":"delete_event","title":"会议","time":"{tomorrow_str}T00:00:00","time_range":"day","reminder":false,"reminder_minutes":0,"description":""}}

示例 4（删除，泛指词代表全部）：
输入："删除明天的事情"
输出：{{"intent":"delete_event","title":"","time":"{tomorrow_str}T00:00:00","time_range":"day","reminder":false,"reminder_minutes":0,"description":""}}

输出：{{"intent":"query_events","title":"","time":"{(now + timedelta(days=1)).strftime('%Y-%m-%d')}T00:00:00","time_range":"morning","reminder":false,"reminder_minutes":0,"description":""}}


语音识别可能产生同音字错误，请根据日历场景语义自动修正 title 中的错误：
- "回忆""会意""回议" → "会议"
- "灰机""飞及" → "飞机"
- "周灰""周辉""周惠" → "周会"
- "活东""活洞" → "活动"
- "面试"常为正确词，不要随意修改
如果 title 中出现了明显的同音字错误，请替换为正确的词汇。

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
            "time_range": data.get("time_range", "day"),    # morning/afternoon/evening/day
            "reminder": data.get("reminder", True),
            "reminder_minutes": data.get("reminder_minutes", 0),
            "description": data.get("description", ""),
        }
