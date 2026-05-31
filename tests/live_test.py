"""
语音交互实时测试脚本

对着麦克风说话，自动完成：录音 → ASR → NLU → 日历操作
使用方法: uv run python live_test.py
"""

import sys
import io
import threading
import time
import urllib.parse

import httpx

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

BASE_URL = "http://localhost:8000/api"
NLU_TIMEOUT = 60

# ── 全局状态（供状态线程读取） ──
_status_lock = threading.Lock()
_current_status = "listening"       # listening | speaking | processing:N | done | no_result | error:X
_status_time = time.time()
_step_active = False                # 是否正在执行处理步骤
_spinner_chars = "⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏"
_spinner_idx = 0


def set_status(status: str):
    """更新当前状态"""
    global _current_status, _status_time, _step_active
    with _status_lock:
        _current_status = status
        _status_time = time.time()
        # speaking 不算"处理中"，processing/done/no_result/error 才算
        _step_active = status not in ("listening", "speaking")


def get_status_line() -> str:
    """根据当前状态生成终端状态行"""
    global _spinner_idx
    with _status_lock:
        status = _current_status
        elapsed = time.time() - _status_time

    _spinner_idx = (_spinner_idx + 1) % len(_spinner_chars)
    spin = _spinner_chars[_spinner_idx]

    if status == "listening":
        return f"  {spin}  🎤 等待语音输入..."
    elif status == "speaking":
        return f"  {spin}  🔴 正在录音... ({elapsed:.0f}秒)"
    elif status.startswith("processing:"):
        dur = status.split(":", 1)[1]
        return f"  {spin}  ⏳ 正在语音识别 (录制{dur}秒)..."
    elif status == "done":
        return ""   # 会被 on_recognized 的输出替代
    elif status == "no_result":
        return f"  ⚠️  未识别到语音内容（太短或空白）"
    elif status.startswith("error:"):
        err = status.split(":", 1)[1]
        return f"  ❌ ASR 错误: {err}"
    return f"  {spin}  ..."


def on_recognized(text: str):
    """ASR 识别到文本后的回调：自动调 NLU + 执行日历操作"""
    print(f"\n  📝 [ASR]  识别文本: {text}")

    if not text or text.startswith("识别失败"):
        print(f"  {'─'*40}")
        print("  继续说话，或按 Ctrl+C 停止...")
        return

    # ── NLU 解析 ──
    print(f"  🤖 [NLU]  正在解析意图...")
    try:
        encoded = urllib.parse.quote(text)
        resp = httpx.post(f"{BASE_URL}/voice/parse?text={encoded}", timeout=NLU_TIMEOUT)
        nlu = resp.json()
        print(f"  ✅ [NLU]  intent={nlu.get('intent')}, title={nlu.get('title')}, "
              f"time={nlu.get('time')}, time_range={nlu.get('time_range')}")
    except Exception as e:
        print(f"  ❌ [NLU]  解析失败: {e}")
        print(f"  {'─'*40}")
        print("  继续说话，或按 Ctrl+C 停止...")
        return

    # ── 执行日历操作 ──
    print(f"  📅 [执行] 正在操作日历...")
    try:
        resp = httpx.post(f"{BASE_URL}/execute", json=nlu, timeout=10)
        result = resp.json()
        print(f"  ✅ [执行] {result.get('message', '')}")
    except Exception as e:
        print(f"  ❌ [执行] 操作失败: {e}")

    print(f"  {'─'*40}")
    print("  继续说话，或按 Ctrl+C 停止...")


def status_reporter_thread():
    """后台线程：实时刷新状态行"""
    last_line = ""
    last_step_active = False
    while True:
        with _status_lock:
            status = _current_status
            step = _step_active

        if not step:
            line = get_status_line()
            if line and line != last_line:
                # 退格清空上一行再输出
                if last_line:
                    sys.stdout.write("\r\033[K")
                sys.stdout.write("\r" + line)
                sys.stdout.flush()
                last_line = line

        if step and not last_step_active:
            # 刚进入处理步骤，清掉状态行
            if last_line:
                sys.stdout.write("\r\033[K")
                sys.stdout.flush()
                last_line = ""

        last_step_active = step
        time.sleep(0.15)


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

    # 启动状态显示线程
    reporter = threading.Thread(target=status_reporter_thread, daemon=True)
    reporter.start()

    service = get_voice_service()

    def status_callback(status: str):
        """voice_service 的状态回调"""
        set_status(status)

    service.start_listening(callback=on_recognized, status_callback=status_callback)

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
