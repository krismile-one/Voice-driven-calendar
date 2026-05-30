"""
NLU 解析服务测试脚本
使用方法: uv run python test_nlu.py
"""

import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

from voice_calendar_agent.config import Settings
from voice_calendar_agent.backend.core.nlu_service import NLUService


def main():
    settings = Settings()

    nlu = NLUService(
        provider=settings.LLM_PROVIDER,
        api_key=settings.LLM_API_KEY,
        model=settings.LLM_MODEL,
        base_url=settings.LLM_BASE_URL,
    )

    tests = [
        "帮我创建一个明天下午三点的团队会议",
        "今天有什么安排",
        "取消明天上午的会议",
        "下周一上午9点有个周会，提前10分钟提醒我",
        "帮我查一下这周五有什么安排",
    ]

    print(f"NLU 提供商: {settings.LLM_PROVIDER}")
    print(f"模型: {settings.LLM_MODEL}")
    print(f"API 地址: {settings.LLM_BASE_URL}")
    print(f"\n{'='*60}")

    for text in tests:
        print(f"\n输入: {text}")
        result = nlu.parse_command(text)
        print(f"  intent  : {result['intent']}")
        print(f"  title   : {result['title']}")
        print(f"  time    : {result['time']}")
        print(f"  reminder: {result['reminder']}")
        print(f"  提前分钟: {result['reminder_minutes']}")

    print(f"\n{'='*60}")
    print("测试完成")


if __name__ == "__main__":
    main()
