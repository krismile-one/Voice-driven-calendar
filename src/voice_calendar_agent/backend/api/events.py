"""
事件管理API接口

提供事件的增删查改RESTful接口。
"""

from datetime import datetime
from typing import Optional, List
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field

from voice_calendar_agent.backend.core.calendar_service import CalendarService
from voice_calendar_agent.backend.models.database import get_db

router = APIRouter()


# ========== 请求/响应模型 ==========

class EventCreateRequest(BaseModel):
    """
    创建事件请求模型

    属性：
    - title: 事件标题（必填）
    - description: 事件描述（可选）
    - start_time: 开始时间（必填）
    - end_time: 结束时间（可选）
    - reminder: 是否提醒（默认True）
    - reminder_minutes: 提前提醒分钟数（默认15）
    """
    title: str = Field(..., min_length=1, max_length=200, description="事件标题")
    description: Optional[str] = Field(None, description="事件描述")
    start_time: datetime = Field(..., description="开始时间")
    end_time: Optional[datetime] = Field(None, description="结束时间")
    reminder: bool = Field(True, description="是否提醒")
    reminder_minutes: int = Field(15, ge=0, description="提前提醒分钟数")


class EventUpdateRequest(BaseModel):
    """
    更新事件请求模型

    属性：
    - title: 事件标题（可选）
    - description: 事件描述（可选）
    - start_time: 开始时间（可选）
    - end_time: 结束时间（可选）
    - reminder: 是否提醒（可选）
    - reminder_minutes: 提前提醒分钟数（可选）
    """
    title: Optional[str] = Field(None, min_length=1, max_length=200, description="事件标题")
    description: Optional[str] = Field(None, description="事件描述")
    start_time: Optional[datetime] = Field(None, description="开始时间")
    end_time: Optional[datetime] = Field(None, description="结束时间")
    reminder: Optional[bool] = Field(None, description="是否提醒")
    reminder_minutes: Optional[int] = Field(None, ge=0, description="提前提醒分钟数")


class EventResponse(BaseModel):
    """
    事件响应模型

    属性：
    - id: 事件ID
    - title: 事件标题
    - description: 事件描述
    - start_time: 开始时间
    - end_time: 结束时间
    - reminder: 是否提醒
    - reminder_minutes: 提前提醒分钟数
    - created_at: 创建时间
    - updated_at: 更新时间
    """
    id: int
    title: str
    description: Optional[str]
    start_time: datetime
    end_time: Optional[datetime]
    reminder: bool
    reminder_minutes: int
    created_at: datetime
    updated_at: datetime


class EventListResponse(BaseModel):
    """
    事件列表响应模型

    属性：
    - events: 事件列表
    - total: 事件总数
    """
    events: List[EventResponse]
    total: int


class MessageResponse(BaseModel):
    """
    消息响应模型

    属性：
    - message: 消息内容
    - id: 相关事件ID（可选）
    """
    message: str
    id: Optional[int] = None


# ========== API端点 ==========

@router.post("/events", response_model=EventResponse, status_code=201)
async def create_event(request: EventCreateRequest):
    """
    创建事件

    输入：
        request: EventCreateRequest - 事件创建请求
    输出：
        EventResponse - 创建的事件信息
    """
    pass


@router.get("/events", response_model=EventListResponse)
async def get_events(
    date: Optional[str] = Query(None, description="日期过滤"),
    range: str = Query("day", description="时间范围: day/week/month"),
):
    """
    获取事件列表

    输入：
        date: 日期过滤（可选，格式：YYYY-MM-DD）
        range: 时间范围（day/week/month，默认day）
    输出：
        EventListResponse - 事件列表和总数
    """
    pass


@router.get("/events/{event_id}", response_model=EventResponse)
async def get_event(event_id: int):
    """
    获取单个事件详情

    输入：
        event_id: 事件ID
    输出：
        EventResponse - 事件详细信息
    """
    pass


@router.put("/events/{event_id}", response_model=EventResponse)
async def update_event(event_id: int, request: EventUpdateRequest):
    """
    更新事件

    输入：
        event_id: 事件ID
        request: EventUpdateRequest - 事件更新请求
    输出：
        EventResponse - 更新后的事件信息
    """
    pass


@router.delete("/events/{event_id}", response_model=MessageResponse)
async def delete_event(event_id: int):
    """
    删除事件

    输入：
        event_id: 事件ID
    输出：
        MessageResponse - 删除结果消息
    """
    pass
