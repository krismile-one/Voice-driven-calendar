"""
语音识别API接口

提供语音上传识别和WebSocket实时语音流接口。
"""

import json
import logging
import os
import tempfile

from fastapi import APIRouter, File, UploadFile, WebSocket
from pydantic import BaseModel, Field
from typing import Optional

from voice_calendar_agent.backend.core.voice_service import VoiceService, get_voice_service
from voice_calendar_agent.backend.core.nlu_service import get_nlu_service

logger = logging.getLogger(__name__)

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
    - time: ISO8601绝对时间字符串
    - reminder: 是否提醒
    - reminder_minutes: 提前提醒分钟数
    - description: 事件描述
    """

    intent: str
    title: Optional[str] = None
    time: Optional[str] = None
    reminder: bool = True
    reminder_minutes: int = 0
    description: Optional[str] = None


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
    try:
        audio_bytes = await audio.read()

        suffix = ".wav"
        if audio.filename:
            ext = os.path.splitext(audio.filename)[1]
            if ext:
                suffix = ext

        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(audio_bytes)
            tmp_path = tmp.name

        try:
            service = get_voice_service()
            text = service.recognize_file(tmp_path)
            return VoiceRecognizeResponse(text=text, confidence=None)
        finally:
            os.unlink(tmp_path)

    except Exception as e:
        logger.error(f"语音识别失败: {e}")
        return VoiceRecognizeResponse(text=f"识别失败: {str(e)}", confidence=None)


@router.post("/parse", response_model=NLUResponse)
async def parse_voice_command(text: str):
    """
    解析语音指令文本

    输入：
        text: 语音识别后的文本（query参数）
    输出：
        NLUResponse - NLU解析结果（意图、标题、时间等）
    """
    try:
        nlu_service = get_nlu_service()
        result = nlu_service.parse_command(text)
        return NLUResponse(**result)
    except Exception as e:
        logger.error(f"NLU解析失败: {e}")
        return NLUResponse(intent="unknown")


@router.websocket("/stream")
async def voice_stream(websocket: WebSocket):
    """
    WebSocket实时语音流

    输入：
        websocket: WebSocket连接，客户端实时发送音频数据
    输出：
        通过WebSocket返回识别结果
    """
    await websocket.accept()
    logger.info("WebSocket语音流连接已建立")

    audio_chunks: list[bytes] = []

    try:
        while True:
            data = await websocket.receive()

            if "text" in data:
                try:
                    msg = json.loads(data["text"])
                    if msg.get("action") == "stop":
                        break
                except json.JSONDecodeError:
                    continue

            elif "bytes" in data:
                audio_chunks.append(data["bytes"])

    except Exception as e:
        logger.error(f"WebSocket接收数据异常: {e}")

    if audio_chunks:
        try:
            audio_data = b"".join(audio_chunks)
            service = get_voice_service()
            text = service.recognize_audio_data(audio_data)
            await websocket.send_json({"type": "result", "text": text})
        except Exception as e:
            logger.error(f"语音识别失败: {e}")
            await websocket.send_json({"type": "error", "message": str(e)})

    await websocket.close()
