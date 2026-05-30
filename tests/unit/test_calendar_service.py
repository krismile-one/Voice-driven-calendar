"""
日历服务单元测试
"""

import pytest
from datetime import datetime, timedelta

from voice_calendar_agent.backend.core.calendar_service import CalendarService


class TestCalendarService:
    """
    日历服务测试类

    功能：测试日历服务的核心功能
    """

    def test_add_event(self, db_session):
        """
        测试添加事件

        输入：
            db_session: 数据库会话夹具
        输出：无
        """
        service = CalendarService(db_session)
        event = service.add_event(
            title="团队会议",
            start_time=datetime(2026, 5, 31, 15, 15),
            reminder_minutes=30,
        )

        # 添加后应拿到自增 id，字段值正确
        assert event.id is not None
        assert event.title == "团队会议"
        assert event.start_time == datetime(2026, 5, 31, 15, 15)
        assert event.reminder is True
        assert event.reminder_minutes == 30

    def test_delete_event(self, db_session):
        """
        测试删除事件

        输入：
            db_session: 数据库会话夹具
        输出：无
        """
        service = CalendarService(db_session)
        event = service.add_event(
            title="会议",
            start_time=datetime(2026, 5, 31, 10, 0),
        )

        # 删除存在的事件 → True，且查不到了
        assert service.delete_event(event.id) is True
        assert service.get_event(event.id) is None

        # 删除不存在的事件 → False
        assert service.delete_event(99999) is False

    def test_get_events_by_date(self, db_session):
        """
        测试按日期查询事件

        输入：
            db_session: 数据库会话夹具
        输出：无
        """
        service = CalendarService(db_session)
        service.add_event(title="今天上午的会", start_time=datetime(2026, 5, 31, 9, 0))
        service.add_event(title="今天下午的会", start_time=datetime(2026, 5, 31, 14, 0))
        service.add_event(title="明天的会", start_time=datetime(2026, 6, 1, 9, 0))

        events = service.get_events(date=datetime(2026, 5, 31), range="day")

        # 只应返回当天的两条，且按开始时间排序
        assert len(events) == 2
        assert events[0].title == "今天上午的会"
        assert events[1].title == "今天下午的会"

    def test_update_event(self, db_session):
        """
        测试更新事件

        输入：
            db_session: 数据库会话夹具
        输出：无
        """
        service = CalendarService(db_session)
        event = service.add_event(
            title="原标题",
            start_time=datetime(2026, 5, 31, 9, 0),
        )

        # 更新存在的事件
        updated = service.update_event(event.id, title="新标题")
        assert updated is not None
        assert updated.title == "新标题"

        # 更新不存在的事件 → None
        assert service.update_event(99999, title="随便") is None