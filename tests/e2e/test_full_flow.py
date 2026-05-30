"""
完整流程端到端测试
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


class TestFullFlow:
    """
    完整流程测试类

    功能：测试从语音输入到事件操作的完整流程
    链路：录音 → ASR → NLU → 日历操作
    """

    @pytest.mark.skipif(not os.path.isdir(AUDIO_DIR), reason="测试音频目录不存在")
    @pytest.mark.skipif(not os.path.exists(FFMPEG), reason="ffmpeg 未安装")
    def test_voice_to_event_flow(self, client):
        """
        测试完整流程：语音 → 文本 → 事件

        输入：
            client: 测试客户端夹具
        输出：无
        """
        tmp_dir = tempfile.mkdtemp()
        try:
            # 1. 转换音频格式
            m4a = os.path.join(AUDIO_DIR, "帮我创建一个明天上午10点的周会.m4a")
            if not os.path.exists(m4a):
                pytest.skip("测试音频文件不存在")

            wav = os.path.join(tmp_dir, "add.wav")
            m4a_to_wav(m4a, wav)

            # 2. ASR：上传音频，获取识别文本
            with open(wav, "rb") as f:
                resp = client.post(
                    "/api/voice/upload",
                    files={"audio": ("test.wav", f, "audio/wav")},
                )
            assert resp.status_code == 200
            asr_text = resp.json()["text"]
            assert len(asr_text) > 0
            assert not asr_text.startswith("识别失败")

            # 3. NLU：解析文本
            resp = client.post(f"/api/voice/parse?text={asr_text}", timeout=60)
            assert resp.status_code == 200
            nlu_result = resp.json()
            assert nlu_result["intent"] == "add_event"

            # 4. 执行：创建事件
            resp = client.post("/api/execute", json=nlu_result)
            assert resp.status_code == 200
            exec_result = resp.json()
            assert "已添加" in exec_result["message"]

            # 5. 验证：事件已存在
            resp = client.get("/api/events")
            assert resp.status_code == 200
            events = resp.json()["events"]
            assert any("周会" in e["title"] for e in events)

        finally:
            shutil.rmtree(tmp_dir, ignore_errors=True)

    @pytest.mark.skipif(not os.path.isdir(AUDIO_DIR), reason="测试音频目录不存在")
    @pytest.mark.skipif(not os.path.exists(FFMPEG), reason="ffmpeg 未安装")
    def test_query_and_delete_flow(self, client):
        """
        测试查询和删除流程

        输入：
            client: 测试客户端夹具
        输出：无
        """
        tmp_dir = tempfile.mkdtemp()
        try:
            # ---- 前置：先创建一个事件 ----
            m4a_add = os.path.join(AUDIO_DIR, "帮我创建一个明天上午10点的周会.m4a")
            if not os.path.exists(m4a_add):
                pytest.skip("测试音频文件不存在")

            wav_add = os.path.join(tmp_dir, "add.wav")
            m4a_to_wav(m4a_add, wav_add)

            with open(wav_add, "rb") as f:
                resp = client.post("/api/voice/upload", files={"audio": ("test.wav", f, "audio/wav")})
            asr_text = resp.json()["text"]

            resp = client.post(f"/api/voice/parse?text={asr_text}", timeout=60)
            nlu_result = resp.json()
            resp = client.post("/api/execute", json=nlu_result)
            assert resp.status_code == 200

            # ---- 测试查询 ----
            m4a_query = os.path.join(AUDIO_DIR, "今天有什么安排.m4a")
            if not os.path.exists(m4a_query):
                pytest.skip("查询测试音频不存在")

            wav_query = os.path.join(tmp_dir, "query.wav")
            m4a_to_wav(m4a_query, wav_query)

            with open(wav_query, "rb") as f:
                resp = client.post("/api/voice/upload", files={"audio": ("test.wav", f, "audio/wav")})
            asr_text = resp.json()["text"]

            resp = client.post(f"/api/voice/parse?text={asr_text}", timeout=60)
            nlu_result = resp.json()
            assert nlu_result["intent"] == "query_events"

            resp = client.post("/api/execute", json=nlu_result)
            assert resp.status_code == 200

            # ---- 测试删除 ----
            m4a_delete = os.path.join(AUDIO_DIR, "取消明天上午的周会.m4a")
            if not os.path.exists(m4a_delete):
                pytest.skip("删除测试音频不存在")

            wav_delete = os.path.join(tmp_dir, "delete.wav")
            m4a_to_wav(m4a_delete, wav_delete)

            with open(wav_delete, "rb") as f:
                resp = client.post("/api/voice/upload", files={"audio": ("test.wav", f, "audio/wav")})
            asr_text = resp.json()["text"]

            resp = client.post(f"/api/voice/parse?text={asr_text}", timeout=60)
            nlu_result = resp.json()
            assert nlu_result["intent"] == "delete_event"

            resp = client.post("/api/execute", json=nlu_result)
            assert resp.status_code == 200
            assert "已删除" in resp.json()["message"]

            # 验证事件已删除
            resp = client.get("/api/events")
            events = resp.json()["events"]
            assert not any("周会" in e["title"] for e in events)

        finally:
            shutil.rmtree(tmp_dir, ignore_errors=True)
