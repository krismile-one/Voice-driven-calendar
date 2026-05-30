"""
语音识别服务

支持在线（百度）和在线（讯飞）语音识别，可通过配置切换。
"""

import base64
import hashlib
import hmac
import io
import json
import logging
import queue
import struct
import threading
import time
from datetime import UTC, datetime
from enum import Enum
from typing import Callable, Optional
from urllib.parse import urlencode

logger = logging.getLogger(__name__)

try:
    from aip import AipSpeech
except ImportError:
    AipSpeech = None
    logger.warning("baidu-aip 未安装，百度语音识别不可用")

try:
    import websocket

    HAS_WEBSOCKET_CLIENT = True
except ImportError:
    HAS_WEBSOCKET_CLIENT = False
    logger.warning("websocket-client 未安装，讯飞语音识别不可用")

try:
    import pyaudio

    HAS_PYAUDIO = True
except ImportError:
    HAS_PYAUDIO = False
    logger.warning("pyaudio 未安装，录音功能不可用")


# ========== 常量 ==========


class ASRMode(Enum):
    """
    语音识别模式枚举

    属性：
    - ONLINE: 在线模式（百度语音）
    - OFFLINE: 离线模式（Vosk，需安装vosk依赖）
    - HYBRID: 混合模式（优先在线，失败回退离线）
    """

    ONLINE = "online"
    OFFLINE = "offline"
    HYBRID = "hybrid"


# ========== 工厂函数 ==========

_voice_service_instance: Optional["VoiceService"] = None


def get_voice_service(settings=None) -> "VoiceService":
    """
    获取语音识别服务单例

    输入：
        settings: 应用配置对象（可选，首次调用时需要）
    输出：
        VoiceService - 语音识别服务实例
    """
    global _voice_service_instance
    if _voice_service_instance is None:
        if settings is None:
            from voice_calendar_agent.config import Settings

            settings = Settings()
        _voice_service_instance = VoiceService(
            mode=ASRMode(settings.ASR_MODE) if isinstance(settings.ASR_MODE, str) else settings.ASR_MODE,
            provider=settings.ASR_PROVIDER,
            app_id=settings.ASR_APP_ID,
            api_key=settings.ASR_API_KEY,
            secret_key=settings.ASR_SECRET_KEY,
            vosk_model_path=settings.VOSK_MODEL_PATH,
        )
    return _voice_service_instance


# ========== 语音识别服务类 ==========


class VoiceService:
    """
    语音识别服务类

    功能：提供语音识别能力，支持在线和离线模式切换

    属性：
    - mode: 识别模式（online/offline/hybrid）
    - provider: 识别服务商（baidu/xunfei）
    - app_id: 应用ID
    - api_key: API Key
    - secret_key: Secret Key
    - vosk_model_path: Vosk模型路径（离线模式）
    - is_listening: 是否正在监听
    """

    def __init__(
        self,
        mode: ASRMode = ASRMode.ONLINE,
        provider: str = "baidu",
        app_id: str = "",
        api_key: str = "",
        secret_key: str = "",
        vosk_model_path: str = "models/vosk/vosk-model-small-cn-0.22",
    ):
        """
        初始化语音识别服务

        输入：
            mode: 识别模式
            provider: 识别服务商（baidu/xunfei）
            app_id: 应用ID
            api_key: API Key
            secret_key: Secret Key
            vosk_model_path: Vosk模型路径（仅离线模式）
        输出：无
        """
        self.mode = mode
        self.provider = provider
        self.app_id = app_id
        self.api_key = api_key
        self.secret_key = secret_key
        self.vosk_model_path = vosk_model_path
        self.is_listening = False
        self._baidu_client = None
        self._vosk_recognizer = None
        self._engine = None

    def _get_engine(self):
        """获取语音识别引擎实例"""
        if self._engine is None:
            if self.provider == "baidu":
                self._engine = BaiduASREngine(self.app_id, self.api_key, self.secret_key)
            elif self.provider == "xunfei":
                self._engine = XunfeiASREngine(self.app_id, self.api_key, self.secret_key)
            else:
                raise ValueError(f"不支持的语音识别服务商: {self.provider}")
        return self._engine

    def _init_baidu_client(self):
        """
        初始化百度语音客户端

        输入：无
        输出：无
        """
        pass

    def _init_vosk_recognizer(self):
        """
        初始化Vosk离线识别器（可选，需安装vosk依赖）

        输入：无
        输出：无
        """
        pass

    def start_listening(self, callback: Callable[[str], None]):
        """
        开始持续监听

        输入：
            callback: 识别到文本后的回调函数，参数为识别结果文本
        输出：无
        """
        if not HAS_PYAUDIO:
            raise ImportError("pyaudio 未安装，请运行: uv add pyaudio")

        if self.is_listening:
            logger.warning("已经在监听中")
            return

        self.is_listening = True
        self._callback = callback

        # 录音参数
        self._chunk = 4096
        self._format = pyaudio.paInt16
        self._channels = 1
        self._rate = 16000

        # 静音检测参数
        self._silence_threshold = 500    # RMS 阈值，低于此值认为是静音
        self._silence_chunks_limit = 15  # 连续静音帧数（约 1.5 秒）后判定一句话结束
        self._max_duration = 55          # 最大录音时长（秒），百度限制 60 秒

        # 状态
        self._audio_buffer = bytearray()
        self._silence_chunks = 0
        self._is_speaking = False
        self._stream = None
        self._pa = None

        # 启动录音线程
        self._listen_thread = threading.Thread(target=self._listen_loop, daemon=True)
        self._listen_thread.start()
        logger.info("开始持续监听")

    def _listen_loop(self):
        """录音主循环"""
        try:
            self._pa = pyaudio.PyAudio()
            self._stream = self._pa.open(
                format=self._format,
                channels=self._channels,
                rate=self._rate,
                input=True,
                frames_per_buffer=self._chunk,
            )

            start_time = time.time()

            while self.is_listening:
                try:
                    data = self._stream.read(self._chunk, exception_on_overflow=False)
                except Exception:
                    continue

                rms = self._calculate_rms(data)

                if rms >= self._silence_threshold:
                    # 检测到语音
                    self._is_speaking = True
                    self._silence_chunks = 0
                    self._audio_buffer.extend(data)

                    # 检查是否超长
                    elapsed = time.time() - start_time
                    if elapsed >= self._max_duration:
                        self._process_buffer()
                        start_time = time.time()

                elif self._is_speaking:
                    # 语音中的静音
                    self._silence_chunks += 1
                    self._audio_buffer.extend(data)

                    if self._silence_chunks >= self._silence_chunks_limit:
                        self._process_buffer()
                        start_time = time.time()

            # 停止时处理剩余音频
            if self._audio_buffer:
                self._process_buffer()

        except Exception as e:
            logger.error(f"录音异常: {e}")
        finally:
            self._cleanup_audio()

    def _calculate_rms(self, data: bytes) -> float:
        """计算音频数据的 RMS（均方根）用于静音检测"""
        if not data:
            return 0
        count = len(data) // 2
        shorts = struct.unpack(f"<{count}h", data[:count * 2])
        sum_sq = sum(s * s for s in shorts)
        return (sum_sq / count) ** 0.5 if count > 0 else 0

    def _process_buffer(self):
        """处理累积的音频缓冲，调用 ASR 识别"""
        if len(self._audio_buffer) < self._rate:  # 少于 1 秒的音频忽略
            self._audio_buffer.clear()
            self._is_speaking = False
            self._silence_chunks = 0
            return

        audio_data = bytes(self._audio_buffer)
        self._audio_buffer.clear()
        self._is_speaking = False
        self._silence_chunks = 0

        try:
            text = self._get_engine().recognize_audio_data(audio_data)
            if text and self._callback:
                logger.info(f"识别结果: {text}")
                self._callback(text)
        except Exception as e:
            logger.error(f"ASR 识别失败: {e}")

    def _cleanup_audio(self):
        """清理录音资源"""
        if self._stream:
            try:
                self._stream.stop_stream()
                self._stream.close()
            except Exception:
                pass
            self._stream = None
        if self._pa:
            try:
                self._pa.terminate()
            except Exception:
                pass
            self._pa = None

    def stop_listening(self):
        """
        停止监听

        输入：无
        输出：无
        """
        if not self.is_listening:
            return
        self.is_listening = False
        logger.info("停止监听")

    def recognize_file(self, audio_path: str) -> str:
        """
        识别音频文件

        输入：
            audio_path: 音频文件路径（支持PCM、WAV格式）
        输出：
            str - 识别出的文本
        """
        return self._get_engine().recognize_file(audio_path)

    def recognize_audio_data(self, audio_data: bytes) -> str:
        """
        识别音频数据

        输入：
            audio_data: 音频数据（bytes，PCM格式）
        输出：
            str - 识别出的文本
        """
        return self._get_engine().recognize_audio_data(audio_data)

    def set_mode(self, mode: ASRMode):
        """
        切换识别模式

        输入：
            mode: 目标识别模式
        输出：无
        """
        pass

    def get_available_modes(self) -> list:
        """
        获取可用的识别模式列表

        输入：无
        输出：
            list - 可用模式列表
        """
        pass


# ========== 百度语音识别引擎 ==========


class BaiduASREngine:
    """百度语音识别引擎"""

    def __init__(self, app_id: str, api_key: str, secret_key: str):
        if AipSpeech is None:
            raise ImportError("baidu-aip 未安装，请运行: uv add baidu-aip")
        self._client = AipSpeech(app_id, api_key, secret_key)

    def recognize_file(self, audio_path: str) -> str:
        """识别音频文件"""
        with open(audio_path, "rb") as f:
            audio_data = f.read()

        fmt = audio_path.rsplit(".", 1)[-1].lower() if "." in audio_path else "pcm"
        if fmt not in ("pcm", "wav", "amr"):
            fmt = "pcm"

        result = self._client.asr(audio_data, fmt, 16000, {"dev_pid": 1537})

        if result.get("err_no") == 0:
            return "".join(result.get("result", []))
        else:
            raise Exception(f"百度语音识别错误: {result.get('err_no')} - {result.get('err_msg')}")

    def recognize_audio_data(self, audio_data: bytes) -> str:
        """识别PCM音频数据"""
        result = self._client.asr(audio_data, "pcm", 16000, {"dev_pid": 1537})

        if result.get("err_no") == 0:
            return "".join(result.get("result", []))
        else:
            raise Exception(f"百度语音识别错误: {result.get('err_no')} - {result.get('err_msg')}")


# ========== 讯飞语音识别引擎 ==========


class XunfeiASREngine:
    """讯飞语音识别引擎（WebSocket 协议）"""

    HOST_URL = "ws-api.xfyun.cn"
    PATH = "/v2/iat"

    def __init__(self, app_id: str, api_key: str, secret_key: str):
        if not HAS_WEBSOCKET_CLIENT:
            raise ImportError("websocket-client 未安装，请运行: uv add websocket-client")
        self.app_id = app_id
        self.api_key = api_key
        self.secret_key = secret_key

    def _build_auth_url(self) -> str:
        """生成带鉴权信息的 WebSocket URL"""
        now = datetime.now(UTC)
        date_str = now.strftime("%a, %d %b %Y %H:%M:%S GMT")

        signature_origin = f"host: {self.HOST_URL}\ndate: {date_str}\nGET {self.PATH} HTTP/1.1"
        signature_sha = hmac.new(
            self.secret_key.encode("utf-8"),
            signature_origin.encode("utf-8"),
            digestmod=hashlib.sha256,
        ).digest()
        signature = base64.b64encode(signature_sha).decode("utf-8")

        auth_origin = (
            f'api_key="{self.api_key}", algorithm="hmac-sha256", '
            f'headers="host date request-line", signature="{signature}"'
        )
        authorization = base64.b64encode(auth_origin.encode("utf-8")).decode("utf-8")

        return f"wss://{self.HOST_URL}{self.PATH}?{urlencode({'authorization': authorization, 'date': date_str, 'host': self.HOST_URL})}"

    def recognize_file(self, audio_path: str) -> str:
        """识别音频文件"""
        with open(audio_path, "rb") as f:
            audio_data = f.read()

        fmt = audio_path.rsplit(".", 1)[-1].lower() if "." in audio_path else "pcm"

        # WAV 格式需要提取 PCM 数据
        if fmt == "wav" and len(audio_data) > 44:
            audio_data = audio_data[44:]

        return self._send_audio(audio_data)

    def recognize_audio_data(self, audio_data: bytes) -> str:
        """识别 PCM 音频数据"""
        return self._send_audio(audio_data)

    def _send_audio(self, audio_data: bytes) -> str:
        """通过 WebSocket 发送音频数据并获取识别结果"""
        app = _XunfeiWebSocketApp(self._build_auth_url(), self.app_id)
        app.connect()
        app.send_audio(audio_data)
        results = app.get_results()
        app.close()

        if not results:
            raise Exception("讯飞语音识别无结果返回")

        return "".join(results)


class _XunfeiWebSocketApp:
    """讯飞 WebSocket 客户端封装（基于 websocket-client 线程模式）"""

    def __init__(self, url: str, app_id: str = ""):
        self.url = url
        self.app_id = app_id
        self.ws = None
        self.results: list[str] = []
        self.is_finished = False
        self.error: Optional[str] = None
        self._connected_event = threading.Event()
        self._send_queue: queue.Queue = queue.Queue()

    def connect(self):
        """建立 WebSocket 连接"""
        self.ws = websocket.WebSocketApp(
            self.url,
            on_open=self._on_open,
            on_message=self._on_message,
            on_error=self._on_error,
            on_close=self._on_close,
        )
        threading.Thread(target=self.ws.run_forever, daemon=True).start()
        if not self._connected_event.wait(timeout=10):
            raise TimeoutError("讯飞 WebSocket 连接超时")

    def _on_open(self, ws):
        self._connected_event.set()
        threading.Thread(target=self._sender, daemon=True).start()

    def _sender(self):
        """发送线程：从队列中取出数据并发送"""
        while True:
            try:
                data = self._send_queue.get(timeout=30)
            except queue.Empty:
                break
            if data is None:
                break
            try:
                self.ws.send(data)
            except Exception as e:
                self.error = str(e)
                self.is_finished = True
                break

    def _on_message(self, ws, message):
        try:
            resp = json.loads(message)

            if resp.get("code") != 0:
                self.error = resp.get("message", "未知错误")
                self.is_finished = True
                self._send_queue.put(None)
                return

            data = resp.get("data")
            if data and "result" in data:
                result = data.get("result")
                if result:
                    wss_data = result.get("ws", [])
                    text = "".join(
                        cw[0]
                        for item in wss_data
                        for cw in item.get("cw", [])
                    )
                    if text:
                        self.results.append(text)

            if data and data.get("status") == 2:
                self.is_finished = True
                self._send_queue.put(None)

        except json.JSONDecodeError:
            self.error = "解析讯飞响应失败"
            self.is_finished = True
            self._send_queue.put(None)

    def _on_error(self, ws, error):
        self.error = str(error)
        self.is_finished = True
        self._connected_event.set()
        self._send_queue.put(None)

    def _on_close(self, ws, close_status_code, close_msg):
        self.is_finished = True
        self._connected_event.set()
        self._send_queue.put(None)

    def send_audio(self, audio_data: bytes):
        """发送音频数据（分片）"""
        chunk_size = 1280
        status = 0
        offset = 0

        while offset < len(audio_data):
            chunk = audio_data[offset : offset + chunk_size]
            offset += chunk_size

            if offset >= len(audio_data):
                status = 2

            frame = {
                "common": {"app_id": self.app_id},
                "business": {"language": "zh_cn", "domain": "iat", "accent": "mandarin"},
                "data": {
                    "status": status,
                    "format": "audio/L16;rate=16000",
                    "encoding": "raw",
                    "audio": base64.b64encode(chunk).decode("utf-8"),
                },
            }
            self._send_queue.put(json.dumps(frame))

            if status == 0:
                status = 1

    def get_results(self) -> list[str]:
        """等待识别完成并返回结果"""
        start_time = time.time()
        while not self.is_finished:
            if time.time() - start_time > 30:
                raise TimeoutError("讯飞语音识别超时")
            time.sleep(0.1)

        if self.error:
            raise Exception(f"讯飞语音识别错误: {self.error}")

        return self.results

    def close(self):
        """关闭连接"""
        self._send_queue.put(None)
        if self.ws:
            self.ws.close()
