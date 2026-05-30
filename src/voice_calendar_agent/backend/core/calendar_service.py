"""
日历业务逻辑服务

负责事件的增删查改和提醒管理。
"""

from datetime import datetime, timedelta
from typing import List, Optional
from sqlalchemy.orm import Session

from voice_calendar_agent.backend.models.event import Event


class CalendarService:
    """
    日历服务类

    功能:提供事件管理的核心业务逻辑

    属性:
    - db: 数据库会话
    """

    def __init__(self, db: Session):
        """
        初始化日历服务

        输入:
            db: SQLAlchemy数据库会话
        输出:无
        """
        self.db = db

    def add_event(
        self,
        title: str,
        start_time: datetime,
        description: Optional[str] = None,
        end_time: Optional[datetime] = None,
        reminder: bool = True,
        reminder_minutes: int = 15,
    ) -> Event:
        """
        添加事件

        输入:
            title: 事件标题
            start_time: 开始时间
            description: 事件描述(可选)
            end_time: 结束时间(可选)
            reminder: 是否提醒(默认True)
            reminder_minutes: 提前提醒分钟数(默认15)
        输出:
            Event - 创建的事件对象
        """
        event = Event(
            title=title,
            start_time=start_time,
            description=description,
            end_time=end_time,
            reminder=reminder,
            reminder_minutes=reminder_minutes,
        )
        self.db.add(event)
        self.db.commit()
        self.db.refresh(event)  # 刷新以拿到自增的 id 等数据库生成字段
        return event

    def delete_event(self, event_id: int) -> bool:
        """
        删除事件

        输入:
            event_id: 事件ID
        输出:
            bool - 删除成功返回True,事件不存在返回False
        """
        event = self.db.query(Event).filter(Event.id == event_id).first()
        if event is None:
            return False
        self.db.delete(event)
        self.db.commit()
        return True

    def get_events(
        self,
        date: Optional[datetime] = None,
        range: str = "day",
    ) -> List[Event]:
        """
        获取事件列表

        输入:
            date: 日期过滤(可选)
            range: 时间范围(day/week/month,默认day)
        输出:
            List[Event] - 事件列表,按开始时间排序
        """
        query = self.db.query(Event)

        if date is not None:
            # 以传入日期的零点为基准计算时间窗口 [start, end)
            day_start = datetime(date.year, date.month, date.day)

            if range == "week":
                # 本周一 00:00 到下周一 00:00
                start = day_start - timedelta(days=date.weekday())
                end = start + timedelta(days=7)
            elif range == "month":
                # 本月 1 号 00:00 到下月 1 号 00:00
                start = datetime(date.year, date.month, 1)
                if date.month == 12:
                    end = datetime(date.year + 1, 1, 1)
                else:
                    end = datetime(date.year, date.month + 1, 1)
            else:
                # 默认按天:当天 00:00 到次日 00:00
                start = day_start
                end = day_start + timedelta(days=1)

            query = query.filter(Event.start_time >= start, Event.start_time < end)

        return query.order_by(Event.start_time).all()

    def get_event(self, event_id: int) -> Optional[Event]:
        """
        获取单个事件

        输入:
            event_id: 事件ID
        输出:
            Optional[Event] - 事件对象,不存在返回None
        """
        return self.db.query(Event).filter(Event.id == event_id).first()

    def update_event(self, event_id: int, **kwargs) -> Optional[Event]:
        """
        更新事件

        输入:
            event_id: 事件ID
            **kwargs: 需要更新的字段和值
        输出:
            Optional[Event] - 更新后的事件对象,不存在返回None
        """
        event = self.db.query(Event).filter(Event.id == event_id).first()
        if event is None:
            return None

        # 只更新事件对象上真实存在的字段，忽略无关键值
        for key, value in kwargs.items():
            if hasattr(event, key):
                setattr(event, key, value)

        self.db.commit()
        self.db.refresh(event)
        return event

    def get_upcoming_reminders(self) -> List[Event]:
        """
        获取即将提醒的事件

        输入:无
        输出:
            List[Event] - 需要提醒的事件列表
        """
        # 方式 A：返回所有“开启了提醒、且还没开始”的未来事件，
        # 由调用方（提醒循环）自行判断到点没到点。按开始时间排序。
        now = datetime.now()
        return (
            self.db.query(Event)
            .filter(Event.reminder.is_(True), Event.start_time > now)
            .order_by(Event.start_time)
            .all()
        )