"""
ASR → NLU 完整链路测试脚本
使用方法:
  1. 先启动服务: uv run python main.py --api
  2. 再运行本脚本: uv run python test_pipeline.py
"""

import httpx
import os
import subprocess
import sys
import io
import tempfile
import urllib.parse

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

# 测试音频文件目录
AUDIO_DIR = r"D:\Desktop\Voice-Driven-Calendar_VoiceTest"

# ffmpeg 路径
FFMPEG = r"C:\Users\xuzhi\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-8.1.1-full_build\bin\ffmpeg.exe"

# API 地址
BASE_URL = "http://localhost:8000/api/voice"


def m4a_to_wav(m4a_path: str, wav_path: str):
    subprocess.run(
        [FFMPEG, "-y", "-i", m4a_path, "-ar", "16000", "-ac", "1",
         "-sample_fmt", "s16", "-f", "wav", wav_path],
        capture_output=True, check=True,
    )


def test_parse_only():
    """测试 1: 单独测试 /parse 端点（不经过 ASR）"""
    print(f"\n{'='*60}")
    print("测试 1: /parse 端点（直接传文本）")
    print(f"{'='*60}")

    cases = [
        ("帮我创建一个明天下午三点的团队会议", "add_event"),
        ("今天有什么安排", "query_events"),
        ("取消明天上午的会议", "delete_event"),
        ("", "unknown"),
    ]

    passed = 0
    for text, expected_intent in cases:
        try:
            encoded = urllib.parse.quote(text) if text else ""
            url = f"{BASE_URL}/parse?text={encoded}" if text else f"{BASE_URL}/parse?text="
            response = httpx.post(url, timeout=30)
            data = response.json()
        except Exception as e:
            display_text = text if text else "(空字符串)"
            print(f"  [FAIL] \"{display_text}\" 请求异常: {e}")
            continue
        intent = data.get("intent", "")

        ok = intent == expected_intent
        status = "[OK]" if ok else "[FAIL]"
        if ok:
            passed += 1

        display_text = text if text else "(空字符串)"
        print(f"  {status} \"{display_text}\"")
        print(f"        → intent={intent}, time={data.get('time')}, title={data.get('title')}")

    print(f"\n  结果: {passed}/{len(cases)} 通过")
    return passed == len(cases)


def test_full_pipeline():
    """测试 2: 完整链路 upload → ASR → parse → NLU"""
    print(f"\n{'='*60}")
    print("测试 2: 完整链路 ASR → NLU")
    print(f"{'='*60}")

    if not os.path.isdir(AUDIO_DIR):
        print("  [SKIP] 测试音频目录不存在")
        return True

    cases = [
        ("帮我创建一个明天下午三点的团队会议.m4a", "add_event", "会议"),
        ("今天有什么安排.m4a", "query_events", None),
        ("取消明天上午的会议.m4a", "delete_event", None),
    ]

    tmp_dir = tempfile.mkdtemp()
    passed = 0
    total = 0

    for filename, expected_intent, expected_keyword in cases:
        m4a_path = os.path.join(AUDIO_DIR, filename)
        if not os.path.exists(m4a_path):
            print(f"\n  [SKIP] 文件不存在: {filename}")
            continue

        total += 1
        wav_path = os.path.join(tmp_dir, filename.replace(".m4a", ".wav"))

        try:
            m4a_to_wav(m4a_path, wav_path)
        except subprocess.CalledProcessError:
            print(f"\n  [FAIL] ffmpeg 转换失败: {filename}")
            continue

        # Step 1: ASR
        try:
            with open(wav_path, "rb") as f:
                resp1 = httpx.post(f"{BASE_URL}/upload", files={"audio": ("test.wav", f, "audio/wav")}, timeout=30)
            asr_result = resp1.json()
            text = asr_result.get("text", "")
        except Exception as e:
            print(f"\n  [FAIL] ASR 请求异常: {filename} - {e}")
            continue

        if text.startswith("识别失败"):
            print(f"\n  [FAIL] ASR 失败: {filename}")
            print(f"        ASR 输出: {text}")
            continue

        # Step 2: NLU
        try:
            encoded = urllib.parse.quote(text)
            resp2 = httpx.post(f"{BASE_URL}/parse?text={encoded}", timeout=30)
            nlu_result = resp2.json()
            intent = nlu_result.get("intent", "")
        except Exception as e:
            print(f"\n  [FAIL] NLU 请求异常: {filename} - {e}")
            continue

        # 验证
        intent_ok = intent == expected_intent
        nlu_title = nlu_result.get("title", "")
        keyword_ok = expected_keyword is None or expected_keyword in nlu_title
        ok = intent_ok and keyword_ok
        if ok:
            passed += 1

        status = "[OK]" if ok else "[FAIL]"
        print(f"\n  {status} {filename}")
        print(f"        ASR: \"{text}\"")
        print(f"        NLU: intent={intent}, time={nlu_result.get('time')}, title={nlu_result.get('title')}")

    import shutil
    shutil.rmtree(tmp_dir, ignore_errors=True)

    print(f"\n  结果: {passed}/{total} 通过")
    return passed == total


def test_parse_response_format():
    """测试 3: /parse 返回格式完整性"""
    print(f"\n{'='*60}")
    print("测试 3: /parse 返回格式")
    print(f"{'='*60}")

    try:
        response = httpx.post(f"{BASE_URL}/parse?text=%E5%B8%AE%E6%88%91%E5%88%9B%E5%BB%BA%E4%B8%80%E4%B8%AA%E6%98%8E%E5%A4%A9%E4%B8%8B%E5%8D%88%E4%B8%89%E7%82%B9%E7%9A%84%E5%9B%A2%E9%98%9F%E4%BC%9A%E8%AE%AE", timeout=30)
        data = response.json()
    except Exception as e:
        print(f"  [FAIL] 请求异常: {e}")
        return False

    required_fields = ["intent", "title", "time", "reminder", "reminder_minutes", "description"]
    missing = [f for f in required_fields if f not in data]

    if not missing:
        print(f"  [OK] 所有字段齐全: {required_fields}")
        return True
    else:
        print(f"  [FAIL] 缺少字段: {missing}")
        print(f"        实际返回: {data}")
        return False


def main():
    print("ASR -> NLU 完整链路测试")

    # 检查服务
    try:
        httpx.get("http://localhost:8000/docs", timeout=5)
        print("[OK] 服务已启动")
    except Exception:
        print("[FAIL] 服务未启动，请先运行: uv run python main.py --api")
        return

    # 运行测试
    r1 = test_parse_only()
    r2 = test_full_pipeline()
    r3 = test_parse_response_format()

    # 汇总
    print(f"\n{'='*60}")
    results = [("parse 端点", r1), ("完整链路", r2), ("返回格式", r3)]
    all_pass = all(r for _, r in results)
    for name, ok in results:
        status = "[OK]" if ok else "[FAIL]"
        print(f"  {status} {name}")
    print(f"{'='*60}")
    print(f"最终结果: {'全部通过' if all_pass else '存在失败'}")


if __name__ == "__main__":
    main()
