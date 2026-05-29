"""
语音识别API接口

提供语音上传识别和WebSocket实时语音流接口。
"""

from fastapi import APIRouter, UploadFile, File, WebSocket
from pydantic import BaseModel, Field
from typing import Optional

from voice_calendar_agent.backend.core.voice_service import VoiceService
from voice_calendar_agent.backend.core.nlu_service import NLUService

router = APIRouter()


# ========== 请求/响应模型 ==========

class VoiceRecognizeResponse(BaseModel):
    """
    语音识别响应模型

    属性：
    - text: 识别出的文本
    - confidence: 识别置信度（0-1）
    """
    text: str
    confidence: Optional[float] = None


class NLUResponse(BaseModel):
    """
    NLU解析响应模型

    属性：
    - intent: 意图类型 (add_event/delete_event/update_event/query_events/unknown)
    - title: 事件标题
    - time: 时间描述
    - date: 日期描述
    - reminder: 是否提醒
    """
    intent: str
    title: Optional[str] = None
    time: Optional[str] = None
    date: Optional[str] = None
    reminder: bool = True


# ========== API端点 ==========

@router.post("/upload", response_model=VoiceRecognizeResponse)
async def upload_audio(audio: UploadFile = File(...)):
    """
    上传音频文件进行识别

    输入：
        audio: UploadFile - WAV格式音频文件
    输出：
        VoiceRecognizeResponse - 识别结果（文本和置信度）
    """
    pass


@router.post("/parse", response_model=NLUResponse)
async def parse_voice_command(text: str):
    """
    解析语音指令文本

    输入：
        text: 语音识别后的文本
    输出：
        NLUResponse - NLU解析结果（意图、标题、时间等）
    """
    pass


@router.websocket("/stream")
async def voice_stream(websocket: WebSocket):
    """
    WebSocket实时语音流

    输入：
        websocket: WebSocket连接，客户端实时发送音频数据
    输出：
        通过WebSocket返回识别结果
    """
    pass
