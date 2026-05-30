"""
语音全链路测试

三级测试：
  Level 1: 录音 → ASR 文本输出
  Level 2: 录音 → ASR → NLU 结构化输出
  Level 3: 录音 → ASR → NLU → 日历操作完成
"""

import os
import subprocess
import tempfile
import shutil

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


# ========== Level 1: 录音 → ASR 文本 ==========


class TestVoiceToASR:
    """Level 1: 音频文件 → 语音识别 → 文本输出"""

    @pytest.mark.skipif(not os.path.isdir(AUDIO_DIR), reason="测试音频目录不存在")
    @pytest.mark.skipif(not os.path.exists(FFMPEG), reason="ffmpeg 未安装")
    def test_asr_recognizes_add_event(self, client):
        """测试 ASR 识别添加事件语音"""
        tmp_dir = tempfile.mkdtemp()
        try:
            m4a = os.path.join(AUDIO_DIR, "帮我创建一个明天上午10点的周会.m4a")
            if not os.path.exists(m4a):
                pytest.skip("测试音频文件不存在")

            wav = os.path.join(tmp_dir, "test.wav")
            m4a_to_wav(m4a, wav)

            with open(wav, "rb") as f:
                resp = client.post("/api/voice/upload", files={"audio": ("test.wav", f, "audio/wav")})

            assert resp.status_code == 200
            text = resp.json()["text"]
            assert isinstance(text, str)
            assert len(text) > 0
            assert not text.startswith("识别失败")
            assert "周会" in text

        finally:
            shutil.rmtree(tmp_dir, ignore_errors=True)

    @pytest.mark.skipif(not os.path.isdir(AUDIO_DIR), reason="测试音频目录不存在")
    @pytest.mark.skipif(not os.path.exists(FFMPEG), reason="ffmpeg 未安装")
    def test_asr_recognizes_query(self, client):
        """测试 ASR 识别查询事件语音"""
        tmp_dir = tempfile.mkdtemp()
        try:
            m4a = os.path.join(AUDIO_DIR, "今天有什么安排.m4a")
            if not os.path.exists(m4a):
                pytest.skip("测试音频文件不存在")

            wav = os.path.join(tmp_dir, "test.wav")
            m4a_to_wav(m4a, wav)

            with open(wav, "rb") as f:
                resp = client.post("/api/voice/upload", files={"audio": ("test.wav", f, "audio/wav")})

            assert resp.status_code == 200
            text = resp.json()["text"]
            assert "安排" in text

        finally:
            shutil.rmtree(tmp_dir, ignore_errors=True)

    @pytest.mark.skipif(not os.path.isdir(AUDIO_DIR), reason="测试音频目录不存在")
    @pytest.mark.skipif(not os.path.exists(FFMPEG), reason="ffmpeg 未安装")
    def test_asr_recognizes_delete(self, client):
        """测试 ASR 识别删除事件语音"""
        tmp_dir = tempfile.mkdtemp()
        try:
            m4a = os.path.join(AUDIO_DIR, "取消明天上午的周会.m4a")
            if not os.path.exists(m4a):
                pytest.skip("测试音频文件不存在")

            wav = os.path.join(tmp_dir, "test.wav")
            m4a_to_wav(m4a, wav)

            with open(wav, "rb") as f:
                resp = client.post("/api/voice/upload", files={"audio": ("test.wav", f, "audio/wav")})

            assert resp.status_code == 200
            text = resp.json()["text"]
            assert "取消" in text or "周会" in text

        finally:
            shutil.rmtree(tmp_dir, ignore_errors=True)


# ========== Level 2: 录音 → ASR → NLU ==========


class TestVoiceToNLU:
    """Level 2: 音频文件 → 语音识别 → NLU 解析 → 结构化输出"""

    @pytest.mark.skipif(not os.path.isdir(AUDIO_DIR), reason="测试音频目录不存在")
    @pytest.mark.skipif(not os.path.exists(FFMPEG), reason="ffmpeg 未安装")
    def test_nlu_parses_add_event(self, client):
        """测试语音 → NLU 解析添加事件"""
        tmp_dir = tempfile.mkdtemp()
        try:
            m4a = os.path.join(AUDIO_DIR, "帮我创建一个明天上午10点的周会.m4a")
            if not os.path.exists(m4a):
                pytest.skip("测试音频文件不存在")

            wav = os.path.join(tmp_dir, "test.wav")
            m4a_to_wav(m4a, wav)

            with open(wav, "rb") as f:
                resp = client.post("/api/voice/upload", files={"audio": ("test.wav", f, "audio/wav")})
            text = resp.json()["text"]

            resp = client.post(f"/api/voice/parse?text={text}", timeout=60)
            assert resp.status_code == 200
            nlu = resp.json()

            assert nlu["intent"] == "add_event"
            assert "周会" in nlu["title"]
            assert nlu["time"] is not None

        finally:
            shutil.rmtree(tmp_dir, ignore_errors=True)

    @pytest.mark.skipif(not os.path.isdir(AUDIO_DIR), reason="测试音频目录不存在")
    @pytest.mark.skipif(not os.path.exists(FFMPEG), reason="ffmpeg 未安装")
    def test_nlu_parses_query(self, client):
        """测试语音 → NLU 解析查询事件"""
        tmp_dir = tempfile.mkdtemp()
        try:
            m4a = os.path.join(AUDIO_DIR, "今天有什么安排.m4a")
            if not os.path.exists(m4a):
                pytest.skip("测试音频文件不存在")

            wav = os.path.join(tmp_dir, "test.wav")
            m4a_to_wav(m4a, wav)

            with open(wav, "rb") as f:
                resp = client.post("/api/voice/upload", files={"audio": ("test.wav", f, "audio/wav")})
            text = resp.json()["text"]

            resp = client.post(f"/api/voice/parse?text={text}", timeout=60)
            assert resp.status_code == 200
            nlu = resp.json()

            assert nlu["intent"] == "query_events"

        finally:
            shutil.rmtree(tmp_dir, ignore_errors=True)

    @pytest.mark.skipif(not os.path.isdir(AUDIO_DIR), reason="测试音频目录不存在")
    @pytest.mark.skipif(not os.path.exists(FFMPEG), reason="ffmpeg 未安装")
    def test_nlu_parses_delete(self, client):
        """测试语音 → NLU 解析删除事件"""
        tmp_dir = tempfile.mkdtemp()
        try:
            m4a = os.path.join(AUDIO_DIR, "取消明天上午的周会.m4a")
            if not os.path.exists(m4a):
                pytest.skip("测试音频文件不存在")

            wav = os.path.join(tmp_dir, "test.wav")
            m4a_to_wav(m4a, wav)

            with open(wav, "rb") as f:
                resp = client.post("/api/voice/upload", files={"audio": ("test.wav", f, "audio/wav")})
            text = resp.json()["text"]

            resp = client.post(f"/api/voice/parse?text={text}", timeout=60)
            assert resp.status_code == 200
            nlu = resp.json()

            assert nlu["intent"] == "delete_event"
            assert "周会" in nlu["title"]

        finally:
            shutil.rmtree(tmp_dir, ignore_errors=True)


# ========== Level 3: 录音 → ASR → NLU → 日历操作 ==========


class TestVoiceToCalendar:
    """Level 3: 音频文件 → 语音识别 → NLU → 日历操作 → 数据库"""

    @pytest.mark.skipif(not os.path.isdir(AUDIO_DIR), reason="测试音频目录不存在")
    @pytest.mark.skipif(not os.path.exists(FFMPEG), reason="ffmpeg 未安装")
    def test_voice_add_event(self, client):
        """测试语音添加事件 → 数据库验证"""
        tmp_dir = tempfile.mkdtemp()
        try:
            m4a = os.path.join(AUDIO_DIR, "帮我创建一个明天上午10点的周会.m4a")
            if not os.path.exists(m4a):
                pytest.skip("测试音频文件不存在")

            wav = os.path.join(tmp_dir, "test.wav")
            m4a_to_wav(m4a, wav)

            # 1. ASR
            with open(wav, "rb") as f:
                resp = client.post("/api/voice/upload", files={"audio": ("test.wav", f, "audio/wav")})
            text = resp.json()["text"]

            # 2. NLU
            resp = client.post(f"/api/voice/parse?text={text}", timeout=60)
            nlu = resp.json()

            # 3. 执行
            resp = client.post("/api/execute", json=nlu)
            assert resp.status_code == 200
            assert "已添加" in resp.json()["message"]

            # 4. 验证数据库
            resp = client.get("/api/events")
            events = resp.json()["events"]
            assert any("周会" in e["title"] for e in events)

        finally:
            shutil.rmtree(tmp_dir, ignore_errors=True)

    @pytest.mark.skipif(not os.path.isdir(AUDIO_DIR), reason="测试音频目录不存在")
    @pytest.mark.skipif(not os.path.exists(FFMPEG), reason="ffmpeg 未安装")
    def test_voice_query_event(self, client):
        """测试语音查询事件 → 返回结果验证"""
        tmp_dir = tempfile.mkdtemp()
        try:
            m4a = os.path.join(AUDIO_DIR, "今天有什么安排.m4a")
            if not os.path.exists(m4a):
                pytest.skip("测试音频文件不存在")

            wav = os.path.join(tmp_dir, "test.wav")
            m4a_to_wav(m4a, wav)

            # 1. ASR
            with open(wav, "rb") as f:
                resp = client.post("/api/voice/upload", files={"audio": ("test.wav", f, "audio/wav")})
            text = resp.json()["text"]

            # 2. NLU
            resp = client.post(f"/api/voice/parse?text={text}", timeout=60)
            nlu = resp.json()

            # 3. 执行
            resp = client.post("/api/execute", json=nlu)
            assert resp.status_code == 200
            message = resp.json()["message"]
            assert "事件" in message  # "该时间段没有事件" 或 "找到 N 个事件：..."

        finally:
            shutil.rmtree(tmp_dir, ignore_errors=True)

    @pytest.mark.skipif(not os.path.isdir(AUDIO_DIR), reason="测试音频目录不存在")
    @pytest.mark.skipif(not os.path.exists(FFMPEG), reason="ffmpeg 未安装")
    def test_voice_delete_event(self, client):
        """测试语音删除事件 → 数据库验证"""
        tmp_dir = tempfile.mkdtemp()
        try:
            # 前置：先创建事件
            m4a_add = os.path.join(AUDIO_DIR, "帮我创建一个明天上午10点的周会.m4a")
            if not os.path.exists(m4a_add):
                pytest.skip("测试音频文件不存在")

            wav_add = os.path.join(tmp_dir, "add.wav")
            m4a_to_wav(m4a_add, wav_add)

            with open(wav_add, "rb") as f:
                resp = client.post("/api/voice/upload", files={"audio": ("test.wav", f, "audio/wav")})
            text = resp.json()["text"]

            resp = client.post(f"/api/voice/parse?text={text}", timeout=60)
            resp = client.post("/api/execute", json=resp.json())
            assert resp.status_code == 200

            # 测试：语音删除
            m4a_del = os.path.join(AUDIO_DIR, "取消明天上午的周会.m4a")
            if not os.path.exists(m4a_del):
                pytest.skip("删除测试音频不存在")

            wav_del = os.path.join(tmp_dir, "del.wav")
            m4a_to_wav(m4a_del, wav_del)

            with open(wav_del, "rb") as f:
                resp = client.post("/api/voice/upload", files={"audio": ("test.wav", f, "audio/wav")})
            text = resp.json()["text"]

            resp = client.post(f"/api/voice/parse?text={text}", timeout=60)
            nlu = resp.json()

            resp = client.post("/api/execute", json=nlu)
            assert resp.status_code == 200
            assert "已删除" in resp.json()["message"]

            # 验证数据库
            resp = client.get("/api/events")
            events = resp.json()["events"]
            assert not any("周会" in e["title"] for e in events)

        finally:
            shutil.rmtree(tmp_dir, ignore_errors=True)
