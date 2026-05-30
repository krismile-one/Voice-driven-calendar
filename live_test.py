"""
语音交互实时测试脚本

对着麦克风说话，自动完成：录音 → ASR → NLU → 日历操作
使用方法: uv run python live_test.py
"""

import sys
import io
import threading
import urllib.parse

import httpx

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

BASE_URL = "http://localhost:8000/api"
NLU_TIMEOUT = 60


def on_recognized(text: str):
    """ASR 识别到文本后的回调：自动调 NLU + 执行日历操作"""
    print(f"\n  [ASR]  {text}")

    if not text or text.startswith("识别失败"):
        return

    # NLU 解析
    try:
        encoded = urllib.parse.quote(text)
        resp = httpx.post(f"{BASE_URL}/voice/parse?text={encoded}", timeout=NLU_TIMEOUT)
        nlu = resp.json()
        print(f"  [NLU]  intent={nlu.get('intent')}, title={nlu.get('title')}, time={nlu.get('time')}, time_range={nlu.get('time_range')}")

        # 执行日历操作
        resp = httpx.post(f"{BASE_URL}/execute", json=nlu, timeout=10)
        result = resp.json()
        print(f"  [执行] {result.get('message', '')}")
    except Exception as e:
        print(f"  [错误] {e}")

    print(f"\n{'─'*40}")
    print("继续说话，或按 Ctrl+C 停止...")


def main():
    from voice_calendar_agent.backend.core.voice_service import get_voice_service, HAS_PYAUDIO

    if not HAS_PYAUDIO:
        print("[错误] pyaudio 未安装，请运行: uv add pyaudio")
        return

    # 检查服务
    try:
        httpx.get("http://localhost:8000/docs", timeout=5)
    except Exception:
        print("[错误] 服务未启动，请先运行: uv run python main.py --api")
        return

    print("=" * 40)
    print("  语音日历助手 - 实时测试")
    print("=" * 40)
    print()
    print("  说话示例：")
    print("    '帮我创建一个明天下午3点的团队会议'")
    print("    '今天有什么安排'")
    print("    '取消明天的会议'")
    print()
    print("  按 Ctrl+C 停止")
    print(f"{'─'*40}")
    print("正在启动麦克风...")

    service = get_voice_service()
    service.start_listening(callback=on_recognized)

    try:
        # 主线程等待，直到用户按 Ctrl+C
        while service.is_listening:
            threading.Event().wait(0.5)
    except KeyboardInterrupt:
        print("\n\n正在停止...")
        service.stop_listening()
        print("已停止。")


if __name__ == "__main__":
    main()