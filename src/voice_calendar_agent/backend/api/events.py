"""
事件管理API接口

提供事件的增删查改RESTful接口。
"""

from datetime import datetime
from typing import Optional, List
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field

from voice_calendar_agent.backend.core.calendar_service import CalendarService
from voice_calendar_agent.backend.core.nlu_service import get_nlu_service
from voice_calendar_agent.backend.models.database import get_db
from voice_calendar_agent.backend.api.voice import NLUResponse

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
async def create_event(request: EventCreateRequest, db=Depends(get_db)):
    """
    创建事件

    输入：
        request: EventCreateRequest - 事件创建请求
    输出：
        EventResponse - 创建的事件信息
    """
    service = CalendarService(db)
    event = service.add_event(
        title=request.title,
        start_time=request.start_time,
        description=request.description,
        end_time=request.end_time,
        reminder=request.reminder,
        reminder_minutes=request.reminder_minutes,
    )
    if event is None:
        raise HTTPException(status_code=500, detail="创建事件失败")
    return EventResponse.model_validate(event, from_attributes=True)


@router.get("/events", response_model=EventListResponse)
async def get_events(
    date: Optional[str] = Query(None, description="日期过滤"),
    range: str = Query("day", description="时间范围: day/week/month"),
    db=Depends(get_db),
):
    """
    获取事件列表

    输入：
        date: 日期过滤（可选，格式：YYYY-MM-DD）
        range: 时间范围（day/week/month，默认day）
    输出：
        EventListResponse - 事件列表和总数
    """
    service = CalendarService(db)
    date_obj = None
    if date:
        date_obj = datetime.fromisoformat(date)
    events = service.get_events(date=date_obj, range=range)
    event_list = [EventResponse.model_validate(e, from_attributes=True) for e in events]
    return EventListResponse(events=event_list, total=len(event_list))


@router.get("/events/{event_id}", response_model=EventResponse)
async def get_event(event_id: int, db=Depends(get_db)):
    """
    获取单个事件详情

    输入：
        event_id: 事件ID
    输出：
        EventResponse - 事件详细信息
    """
    service = CalendarService(db)
    event = service.get_event(event_id)
    if event is None:
        raise HTTPException(status_code=404, detail="事件不存在")
    return EventResponse.model_validate(event, from_attributes=True)


@router.put("/events/{event_id}", response_model=EventResponse)
async def update_event(event_id: int, request: EventUpdateRequest, db=Depends(get_db)):
    """
    更新事件

    输入：
        event_id: 事件ID
        request: EventUpdateRequest - 事件更新请求
    输出：
        EventResponse - 更新后的事件信息
    """
    service = CalendarService(db)
    # 只传用户实际提供的字段
    update_fields = {k: v for k, v in request.model_dump().items() if v is not None}
    if not update_fields:
        raise HTTPException(status_code=400, detail="没有提供需要更新的字段")
    event = service.update_event(event_id, **update_fields)
    if event is None:
        raise HTTPException(status_code=404, detail="事件不存在")
    return EventResponse.model_validate(event, from_attributes=True)


@router.delete("/events/{event_id}", response_model=MessageResponse)
async def delete_event(event_id: int, db=Depends(get_db)):
    """
    删除事件

    输入：
        event_id: 事件ID
    输出：
        MessageResponse - 删除结果消息
    """
    service = CalendarService(db)
    success = service.delete_event(event_id)
    if not success:
        raise HTTPException(status_code=404, detail="事件不存在")
    return MessageResponse(message="事件已删除", id=event_id)


# ========== 语音指令执行端点 ==========


@router.post("/execute", response_model=MessageResponse)
async def execute_command(nlu_result: NLUResponse, db=Depends(get_db)):
    """
    执行NLU解析后的结构化指令

    输入：
        nlu_result: NLUResponse - NLU解析结果
    输出：
        MessageResponse - 执行结果消息

    调用流程：
        1. 客户端调用 /api/voice/upload 获取语音文本
        2. 客户端调用 /api/voice/parse 获取结构化指令（NLUResponse）
        3. 客户端调用 /api/execute 执行指令
    """
    service = CalendarService(db)
    intent = nlu_result.intent
    title = nlu_result.title or ""

    # 将 ISO8601 字符串转为 datetime
    start_time = None
    if nlu_result.time:
        start_time = datetime.fromisoformat(nlu_result.time)

    if intent == "add_event":
        if not title:
            return MessageResponse(message="缺少事件标题")
        if not start_time:
            return MessageResponse(message="缺少事件时间")
        event = service.add_event(
            title=title,
            start_time=start_time,
            description=nlu_result.description or None,
            reminder=nlu_result.reminder,
            reminder_minutes=nlu_result.reminder_minutes,
        )
        if event is None:
            raise HTTPException(status_code=500, detail="创建事件失败")
        return MessageResponse(message=f"已添加事件：{event.title}", id=event.id)

    elif intent == "delete_event":
        events = service.get_events(date=start_time, range="day")
        matched = [e for e in events if title in e.title] if title else events
        if not matched:
            raise HTTPException(status_code=404, detail=f"未找到匹配的事件：{title}")
        event_id = matched[0].id
        success = service.delete_event(event_id)
        if not success:
            raise HTTPException(status_code=500, detail="删除事件失败")
        return MessageResponse(message=f"已删除事件：{matched[0].title}", id=event_id)

    elif intent == "update_event":
        # update_event 需要更多信息（改什么字段），NLU 当前不输出，提示用户
        return MessageResponse(message="更新事件需要更多信息，请通过 /api/events/{id} 接口操作")

    elif intent == "query_events":
        events = service.get_events(date=start_time, range="day")
        if not events:
            return MessageResponse(message="该时间段没有事件")
        titles = "、".join(e.title for e in events)
        return MessageResponse(message=f"找到 {len(events)} 个事件：{titles}")

    else:
        return MessageResponse(message=f"未知意图: {intent}")
