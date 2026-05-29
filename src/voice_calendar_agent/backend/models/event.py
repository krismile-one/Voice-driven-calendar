"""
事件数据模型

定义日历事件的数据库表结构。
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean


# 注意：Base 在 database.py 中定义，此处使用延迟导入
# 实际使用时通过 from voice_calendar_agent.backend.models.database import Base


def get_base():
    """
    获取SQLAlchemy Base类

    输入：无
    输出：
        declarative_base实例
    """
    from voice_calendar_agent.backend.models.database import Base
    return Base


class Event(get_base()):
    """
    日历事件数据模型

    功能：定义events表的结构

    属性：
    - id: 主键，自增
    - title: 事件标题（最长200字符）
    - description: 事件描述（可选）
    - start_time: 开始时间
    - end_time: 结束时间（可选）
    - reminder: 是否提醒（默认True）
    - reminder_minutes: 提前提醒分钟数（默认15）
    - created_at: 创建时间
    - updated_at: 更新时间
    """
    __tablename__ = "events"

    id = Column(Integer, primary_key=True, index=True, comment="事件ID")
    title = Column(String(200), nullable=False, comment="事件标题")
    description = Column(Text, nullable=True, comment="事件描述")
    start_time = Column(DateTime, nullable=False, comment="开始时间")
    end_time = Column(DateTime, nullable=True, comment="结束时间")
    reminder = Column(Boolean, default=True, comment="是否提醒")
    reminder_minutes = Column(Integer, default=15, comment="提前提醒分钟数")
    created_at = Column(DateTime, default=datetime.now, comment="创建时间")
    updated_at = Column(
        DateTime,
        default=datetime.now,
        onupdate=datetime.now,
        comment="更新时间"
    )

    def __repr__(self):
        """返回事件的字符串表示"""
        return f"<Event(id={self.id}, title='{self.title}', start_time={self.start_time})>"
