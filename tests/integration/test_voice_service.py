"""
语音识别服务集成测试
"""

import os
import subprocess
import tempfile

import httpx
import pytest

# ffmpeg 路径
FFMPEG = r"C:\Users\xuzhi\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-8.1.1-full_build\bin\ffmpeg.exe"

# 测试音频目录
AUDIO_DIR = r"D:\Desktop\Voice-Driven-Calendar_VoiceTest"


def m4a_to_wav(m4a_path: str, wav_path: str):
    """用 ffmpeg 将 m4a 转为 16kHz/16bit/mono WAV"""
    subprocess.run(
        [FFMPEG, "-y", "-i", m4a_path, "-ar", "16000", "-ac", "1",
         "-sample_fmt", "s16", "-f", "wav", wav_path],
        capture_output=True,
        check=True,
    )


@pytest.fixture
def voice_service():
    """初始化语音服务"""
    from voice_calendar_agent.backend.core.voice_service import VoiceService, ASRMode
    from voice_calendar_agent.config import Settings

    settings = Settings()
    return VoiceService(
        mode=ASRMode.ONLINE,
        provider=settings.ASR_PROVIDER,
        app_id=settings.ASR_APP_ID,
        api_key=settings.ASR_API_KEY,
        secret_key=settings.ASR_SECRET_KEY,
    )


class TestVoiceServiceFileRecognition:
    """音频文件识别测试"""

    @pytest.mark.skipif(not os.path.isdir(AUDIO_DIR), reason="测试音频目录不存在")
    @pytest.mark.skipif(not os.path.exists(FFMPEG), reason="ffmpeg 未安装")
    def test_recognize_audio_add_event(self, voice_service):
        """测试识别'添加事件'语音"""
        m4a = os.path.join(AUDIO_DIR, "帮我创建一个明天下午三点的团队会议.m4a")
        if not os.path.exists(m4a):
            pytest.skip("测试音频文件不存在")

        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            wav_path = tmp.name

        try:
            m4a_to_wav(m4a, wav_path)
            text = voice_service.recognize_file(wav_path)
            assert isinstance(text, str)
            assert len(text) > 0
            assert "明天" in text or "下午" in text or "三点" in text or "会议" in text or "回忆" in text
        finally:
            os.unlink(wav_path)

    @pytest.mark.skipif(not os.path.isdir(AUDIO_DIR), reason="测试音频目录不存在")
    @pytest.mark.skipif(not os.path.exists(FFMPEG), reason="ffmpeg 未安装")
    def test_recognize_audio_query_events(self, voice_service):
        """测试识别'查询事件'语音"""
        m4a = os.path.join(AUDIO_DIR, "今天有什么安排.m4a")
        if not os.path.exists(m4a):
            pytest.skip("测试音频文件不存在")

        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            wav_path = tmp.name

        try:
            m4a_to_wav(m4a, wav_path)
            text = voice_service.recognize_file(wav_path)
            assert isinstance(text, str)
            assert len(text) > 0
            assert "安排" in text
        finally:
            os.unlink(wav_path)

    @pytest.mark.skipif(not os.path.isdir(AUDIO_DIR), reason="测试音频目录不存在")
    @pytest.mark.skipif(not os.path.exists(FFMPEG), reason="ffmpeg 未安装")
    def test_recognize_audio_delete_event(self, voice_service):
        """测试识别'删除事件'语音"""
        m4a = os.path.join(AUDIO_DIR, "取消明天上午的会议.m4a")
        if not os.path.exists(m4a):
            pytest.skip("测试音频文件不存在")

        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            wav_path = tmp.name

        try:
            m4a_to_wav(m4a, wav_path)
            text = voice_service.recognize_file(wav_path)
            assert isinstance(text, str)
            assert len(text) > 0
            assert "取消" in text or "会议" in text
        finally:
            os.unlink(wav_path)

    @pytest.mark.skipif(not os.path.isdir(AUDIO_DIR), reason="测试音频目录不存在")
    @pytest.mark.skipif(not os.path.exists(FFMPEG), reason="ffmpeg 未安装")
    def test_recognize_audio_silence(self, voice_service):
        """测试识别空白录音（应抛出异常或返回空）"""
        m4a = os.path.join(AUDIO_DIR, "空白录音.m4a")
        if not os.path.exists(m4a):
            pytest.skip("测试音频文件不存在")

        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            wav_path = tmp.name

        try:
            m4a_to_wav(m4a, wav_path)
            # 空白录音应抛出异常
            with pytest.raises(Exception):
                voice_service.recognize_file(wav_path)
        finally:
            os.unlink(wav_path)


class TestVoiceServiceAudioData:
    """PCM 音频数据识别测试"""

    def test_recognize_audio_data_returns_string(self, voice_service):
        """测试 recognize_audio_data 返回值类型"""
        # 生成 1 秒静音 PCM 数据（仅验证代码流程）
        import struct
        pcm_data = struct.pack("<" + "h" * 16000, *([0] * 16000))

        # 静音数据应抛出异常（百度返回语音质量错误）
        with pytest.raises(Exception):
            voice_service.recognize_audio_data(pcm_data)


class TestVoiceAPIEndpoint:
    """语音识别 API 端点测试"""

    @pytest.mark.skipif(not os.path.isdir(AUDIO_DIR), reason="测试音频目录不存在")
    @pytest.mark.skipif(not os.path.exists(FFMPEG), reason="ffmpeg 未安装")
    def test_upload_endpoint_recognizes_text(self, client):
        """测试 /upload 端点返回识别文本"""
        m4a = os.path.join(AUDIO_DIR, "今天有什么安排.m4a")
        if not os.path.exists(m4a):
            pytest.skip("测试音频文件不存在")

        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            wav_path = tmp.name

        try:
            m4a_to_wav(m4a, wav_path)

            with open(wav_path, "rb") as f:
                response = client.post(
                    "/api/voice/upload",
                    files={"audio": ("test.wav", f, "audio/wav")},
                )

            assert response.status_code == 200
            data = response.json()
            assert "text" in data
            assert isinstance(data["text"], str)
            assert len(data["text"]) > 0
        finally:
            os.unlink(wav_path)

    def test_upload_endpoint_returns_correct_format(self, client):
        """测试 /upload 端点返回格式正确（不含音频时返回错误信息）"""
        # 发送空文件，验证返回格式
        response = client.post(
            "/api/voice/upload",
            files={"audio": ("empty.wav", b"", "audio/wav")},
        )

        assert response.status_code == 200
        data = response.json()
        assert "text" in data
        assert "confidence" in data
