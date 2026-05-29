"""
语音识别服务

支持在线（百度）和离线（Vosk，可选）语音识别，可通过配置切换。
"""

import logging
from typing import Optional, Callable
from enum import Enum

logger = logging.getLogger(__name__)


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


class VoiceService:
    """
    语音识别服务类

    功能：提供语音识别能力，支持在线和离线模式切换

    属性：
    - mode: 识别模式（online/offline/hybrid）
    - baidu_app_id: 百度语音应用ID
    - baidu_api_key: 百度语音API Key
    - baidu_secret_key: 百度语音Secret Key
    - vosk_model_path: Vosk模型路径（离线模式）
    - is_listening: 是否正在监听
    """

    def __init__(
        self,
        mode: ASRMode = ASRMode.ONLINE,
        baidu_app_id: str = "",
        baidu_api_key: str = "",
        baidu_secret_key: str = "",
        vosk_model_path: str = "models/vosk/vosk-model-small-cn-0.22",
    ):
        """
        初始化语音识别服务

        输入：
            mode: 识别模式
            baidu_app_id: 百度语音应用ID
            baidu_api_key: 百度语音API Key
            baidu_secret_key: 百度语音Secret Key
            vosk_model_path: Vosk模型路径（仅离线模式）
        输出：无
        """
        self.mode = mode
        self.baidu_app_id = baidu_app_id
        self.baidu_api_key = baidu_api_key
        self.baidu_secret_key = baidu_secret_key
        self.vosk_model_path = vosk_model_path
        self.is_listening = False
        self._baidu_client = None
        self._vosk_recognizer = None

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
        pass

    def stop_listening(self):
        """
        停止监听

        输入：无
        输出：无
        """
        pass

    def recognize_file(self, audio_path: str) -> str:
        """
        识别音频文件

        输入：
            audio_path: 音频文件路径（支持PCM、WAV格式）
        输出：
            str - 识别出的文本
        """
        pass

    def recognize_audio_data(self, audio_data: bytes) -> str:
        """
        识别音频数据

        输入：
            audio_data: 音频数据（bytes，PCM格式）
        输出：
            str - 识别出的文本
        """
        pass

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
