"""
NLU服务单元测试
"""

import pytest
from unittest.mock import patch

from voice_calendar_agent.backend.core.nlu_service import NLUService


class TestNLUService:
    """
    NLU服务测试类

    功能：测试NLU解析服务的功能
    说明：用 mock 把大模型的调用替换成"假返回"，这样测试不联网、不花钱，
          只验证我们自己的解析逻辑（_parse_response）是否正确。
    """

    def _make_service(self) -> NLUService:
        """构造一个测试用的 NLU 服务（provider 默认 openai）"""
        return NLUService(provider="openai", api_key="test-key", model="deepseek-chat")

    @patch.object(NLUService, "_call_openai")
    def test_parse_add_event(self, mock_call):
        """
        测试解析添加事件指令

        输入：无
        输出：无
        """
        # 模拟大模型返回的 JSON 文本（time 为 ISO 绝对时间）
        mock_call.return_value = (
            '{"intent":"add_event","title":"开会",'
            '"time":"2026-05-31T15:15:00","reminder":true,'
            '"reminder_minutes":30,"description":""}'
        )

        nlu = self._make_service()
        result = nlu.parse_command("明天下午3点一刻开会，提前半小时提醒我")

        assert result["intent"] == "add_event"
        assert result["title"] == "开会"
        assert result["time"] == "2026-05-31T15:15:00"
        assert result["reminder"] is True
        assert result["reminder_minutes"] == 30

    @patch.object(NLUService, "_call_openai")
    def test_parse_query_events(self, mock_call):
        """
        测试解析查询事件指令

        输入：无
        输出：无
        """
        mock_call.return_value = (
            '{"intent":"query_events","title":"",'
            '"time":"2026-05-31T00:00:00","reminder":false,'
            '"reminder_minutes":0,"description":""}'
        )

        nlu = self._make_service()
        result = nlu.parse_command("查一下我明天有什么安排")

        assert result["intent"] == "query_events"
        assert result["time"] == "2026-05-31T00:00:00"

    @patch.object(NLUService, "_call_openai")
    def test_parse_delete_event(self, mock_call):
        """
        测试解析删除事件指令

        输入：无
        输出：无
        """
        mock_call.return_value = (
            '{"intent":"delete_event","title":"会议",'
            '"time":null,"reminder":false,'
            '"reminder_minutes":0,"description":""}'
        )

        nlu = self._make_service()
        result = nlu.parse_command("删除明天的会议")

        assert result["intent"] == "delete_event"
        assert result["title"] == "会议"

    @patch.object(NLUService, "_call_openai")
    def test_parse_invalid_returns_unknown(self, mock_call):
        """
        测试模型返回非法内容时，能兜底成 unknown 而不崩溃

        输入：无
        输出：无
        """
        mock_call.return_value = "这不是合法的JSON"

        nlu = self._make_service()
        result = nlu.parse_command("乱七八糟的一句话")

        assert result["intent"] == "unknown"
