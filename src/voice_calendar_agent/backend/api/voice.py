"""
语音识别API接口

提供语音上传识别和WebSocket实时语音流接口。
"""

import json
import logging
import os
import shutil
import subprocess
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
    - time_range: 时间段 (morning/afternoon/evening/day)
    - reminder: 是否提醒
    - reminder_minutes: 提前提醒分钟数
    - description: 事件描述
    """

    intent: str
    title: Optional[str] = None
    time: Optional[str] = None
    time_range: str = "day"
    reminder: bool = True
    reminder_minutes: int = 0
    description: Optional[str] = None


# ========== 音频格式转换 ==========

FFMPEG_AVAILABLE = shutil.which("ffmpeg") is not None
BAIDU_ACCEPT_FORMATS = {"pcm", "wav", "amr"}


def _needs_conversion(file_path: str) -> bool:
    """判断音频文件是否需要转为 WAV"""
    ext = os.path.splitext(file_path)[1].lower().lstrip(".")
    return ext not in BAIDU_ACCEPT_FORMATS


def _convert_to_wav(input_path: str) -> str:
    """
    使用 ffmpeg 将音频转为 16kHz 单声道 PCM WAV

    输入：
        input_path: 原始音频文件路径
    输出：
        str - 转换后的 WAV 文件路径
    异常：
        RuntimeError: ffmpeg 未安装或转换失败
    """
    if not FFMPEG_AVAILABLE:
        raise RuntimeError("ffmpeg 未安装，无法转换音频格式。请安装 ffmpeg 后重试。")

    output_path = input_path + ".wav"
    cmd = [
        "ffmpeg", "-y",
        "-i", input_path,
        "-f", "wav",
        "-acodec", "pcm_s16le",
        "-ar", "16000",
        "-ac", "1",
        output_path,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        logger.error(f"ffmpeg 转换失败: {result.stderr}")
        raise RuntimeError(f"音频格式转换失败: {result.stderr}")

    logger.info(f"音频已转换: {input_path} → {output_path}")
    return output_path


# ========== API端点 ==========


@router.post("/upload", response_model=VoiceRecognizeResponse)
async def upload_audio(audio: UploadFile = File(...)):
    """
    上传音频文件进行识别（支持 webm / wav / pcm 等格式）

    输入：
        audio: UploadFile - 音频文件
    输出：
        VoiceRecognizeResponse - 识别结果（文本和置信度）
    """
    tmp_path = None
    converted_path = None

    try:
        audio_bytes = await audio.read()

        # 空文件检查
        if not audio_bytes or len(audio_bytes) < 100:
            logger.warning(f"音频数据过小: {len(audio_bytes) if audio_bytes else 0} bytes")
            return VoiceRecognizeResponse(text="识别失败: 未录制到有效音频，请重试并确保说话时长 > 1 秒", confidence=None)

        suffix = ".webm"
        if audio.filename:
            ext = os.path.splitext(audio.filename)[1]
            if ext:
                suffix = ext

        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(audio_bytes)
            tmp.flush()
            os.fsync(tmp.fileno())
            tmp_path = tmp.name

        logger.info(f"收到音频: {len(audio_bytes)} bytes, 格式 {suffix}")

        # 检查 webm EBML header（1A 45 DF A3），损坏文件直接拒绝
        if suffix.lower() in (".webm", ".weba"):
            with open(tmp_path, "rb") as f:
                magic = f.read(4)
            if magic != b"\x1a\x45\xdf\xa3":
                logger.warning(f"无效的 webm 文件，magic bytes: {magic.hex()}, 大小: {len(audio_bytes)}")
                return VoiceRecognizeResponse(text="识别失败: 录音数据不完整，请重试", confidence=None)

        # 非 WAV/PCM 格式（如 webm/opus）需用 ffmpeg 转码
        recognize_path = tmp_path
        if _needs_conversion(tmp_path):
            converted_path = _convert_to_wav(tmp_path)
            recognize_path = converted_path

        service = get_voice_service()
        text = service.recognize_file(recognize_path)
        return VoiceRecognizeResponse(text=text, confidence=None)

    except RuntimeError as e:
        logger.error(f"音频处理失败: {e}")
        return VoiceRecognizeResponse(text=f"识别失败: {str(e)}", confidence=None)
    except Exception as e:
        logger.error(f"语音识别失败: {e}")
        return VoiceRecognizeResponse(text=f"识别失败: {str(e)}", confidence=None)
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.unlink(tmp_path)
        if converted_path and os.path.exists(converted_path):
            os.unlink(converted_path)


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
