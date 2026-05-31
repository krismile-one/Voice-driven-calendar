"""
测试数据注入工具

用法：
    python addData.py              通过 NLU 自然语言命令注入
    python addData.py --direct     绕过 NLU，直接调用 /api/events
    python addData.py --list       仅列出命令，不执行
    python addData.py --dry-run    解析但不执行（仅 NLU 模式）

添加/删除命令：
    NLU 模式：编辑 NLU_COMMANDS 列表（自然语言文本）
    Direct 模式：编辑 DIRECT_COMMANDS 列表（结构化事件数据）
"""

import io
import sys
import json
import urllib.request
import urllib.error
from datetime import datetime, timedelta

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

BASE_URL = "http://localhost:8000"


# ═══════════════════════════════════════════════════════════
# A. NLU 模式命令（自然语言 → parse → execute）
#    需要服务器配置了 LLM API Key 才能正常解析
# ═══════════════════════════════════════════════════════════

NLU_COMMANDS = [
    # ── 添加 ──
    "明天上午十点提醒我开会",
    "后天下午三点团队代码评审",
    "6月5日上午九点牙医预约，提前一小时提醒",
    "下周一早上八点晨跑",
    "6月15日晚上七点朋友生日聚餐",
    "6月20日全天团建活动",
    "6月3日下午两点产品需求讨论会",

    # ── 查询 ──
    # "明天有什么安排",

    # ── 删除 ──
    # "取消明天的会议",
]


# ═══════════════════════════════════════════════════════════
# B. Direct 模式命令（结构化事件 → 直接 POST /api/events）
#    不依赖 NLU，日期基于"明天"推算（可手动指定）
# ═══════════════════════════════════════════════════════════

def _tomorrow(hour: int = 9, minute: int = 0) -> str:
    """返回明天指定时刻的 ISO 时间字符串"""
    d = datetime.now() + timedelta(days=1)
    return d.replace(hour=hour, minute=minute, second=0, microsecond=0).isoformat()


def _day_after(days: int, hour: int = 9, minute: int = 0) -> str:
    """返回 N 天后的 ISO 时间字符串"""
    d = datetime.now() + timedelta(days=days)
    return d.replace(hour=hour, minute=minute, second=0, microsecond=0).isoformat()


DIRECT_COMMANDS = [
    # ── 添加 ──
    {"action": "add", "title": "团队晨会",       "start_time": _tomorrow(9, 0),  "end_time": _tomorrow(10, 0),  "description": "每日站会", "reminder": True,  "reminder_minutes": 15},
    {"action": "add", "title": "代码评审",       "start_time": _day_after(2, 15, 0), "end_time": _day_after(2, 17, 0), "description": "后端代码评审", "reminder": True,  "reminder_minutes": 30},
    {"action": "add", "title": "牙医预约",       "start_time": _day_after(5, 9, 0),  "end_time": _day_after(5, 10, 0), "description": "年度口腔检查", "reminder": True,  "reminder_minutes": 60},
    {"action": "add", "title": "晨跑",           "start_time": _day_after(1, 8, 0),  "end_time": _day_after(1, 9, 0),  "description": "晨跑锻炼", "reminder": False, "reminder_minutes": 0},
    {"action": "add", "title": "朋友生日聚餐",   "start_time": _day_after(15, 19, 0), "end_time": None, "description": "带礼物", "reminder": True,  "reminder_minutes": 120},
    {"action": "add", "title": "团建活动",       "start_time": _day_after(20, 9, 0),  "end_time": _day_after(20, 18, 0), "description": "全天户外拓展", "reminder": True,  "reminder_minutes": 1440},
    {"action": "add", "title": "产品需求讨论",   "start_time": _day_after(3, 14, 0), "end_time": _day_after(3, 16, 0), "description": "Q3需求评审", "reminder": True,  "reminder_minutes": 15},

    # ── 删除（指定 event_id，需先查） ──
    # {"action": "delete", "event_id": 1},
]


# ═══════════════════════════════════════════════════════════
# 执行逻辑
# ═══════════════════════════════════════════════════════════

def _post(url: str, data: dict | None = None, timeout: int = 30) -> dict | None:
    """通用 POST 请求"""
    body = json.dumps(data).encode("utf-8") if data else b""
    req = urllib.request.Request(
        url, data=body,
        headers={"Content-Type": "application/json"} if data else {},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        msg = e.read().decode(errors="replace")
        print(f"    [HTTP {e.code}] {msg}")
        return None
    except urllib.error.URLError as e:
        print(f"    [连接失败] {e.reason}")
        return None
    except Exception as e:
        print(f"    [异常] {e}")
        return None


def _get(url: str) -> dict | None:
    """通用 GET 请求"""
    try:
        with urllib.request.urlopen(url, timeout=30) as resp:
            return json.loads(resp.read())
    except Exception as e:
        return None


def check_server() -> bool:
    return _get(f"{BASE_URL}/api/events?date=2026-01-01&range=day") is not None


# ── NLU 模式 ──

def api_parse(text: str) -> dict | None:
    """POST /api/voice/parse"""
    url = f"{BASE_URL}/api/voice/parse?text={urllib.parse.quote(text)}"
    return _post(url)


def api_execute(nlu_result: dict) -> dict | None:
    """POST /api/execute"""
    return _post(f"{BASE_URL}/api/execute", nlu_result)


def run_nlu_command(text: str, dry_run: bool = False) -> bool:
    """NLU 模式：parse → execute"""
    print(f"\n{'─' * 55}")
    print(f"📝 命令: {text}")

    print(f"  ⏳ NLU 解析中...")
    nlu = api_parse(text)
    if nlu is None:
        print(f"  ❌ NLU 解析失败（检查服务器 LLM 配置）")
        return False

    intent = nlu.get("intent", "unknown")
    title = nlu.get("title", "")
    time = nlu.get("time", "")
    time_range = nlu.get("time_range", "day")
    reminder = nlu.get("reminder", False)
    reminder_min = nlu.get("reminder_minutes", 0)

    print(f"  📋 intent: {intent}  |  title: {title}  |  time: {time}")
    if reminder:
        print(f"       range: {time_range}  |  提前 {reminder_min} 分钟提醒")

    if intent == "unknown":
        print(f"  ⚠️  无法理解该命令，跳过")
        return False

    if dry_run:
        print(f"  🔍 [dry-run] 仅解析，不执行")
        return True

    print(f"  ⏳ 执行中...")
    result = api_execute(nlu)
    if result is None:
        print(f"  ❌ 执行失败")
        return False

    print(f"  ✅ {result.get('message', 'OK')}")
    return True


# ── Direct 模式 ──

def api_create_event(ev: dict) -> dict | None:
    """POST /api/events"""
    body = {
        "title": ev["title"],
        "start_time": ev["start_time"],
        "end_time": ev.get("end_time"),
        "description": ev.get("description", ""),
        "reminder": ev.get("reminder", True),
        "reminder_minutes": ev.get("reminder_minutes", 15),
    }
    return _post(f"{BASE_URL}/api/events", body)


def api_delete_event(event_id: int) -> dict | None:
    """DELETE /api/events/{id}"""
    url = f"{BASE_URL}/api/events/{event_id}"
    req = urllib.request.Request(url, method="DELETE")
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read())
    except Exception as e:
        print(f"    [异常] {e}")
        return None


def run_direct_command(cmd: dict) -> bool:
    """Direct 模式：直接调用 /api/events"""
    action = cmd.get("action", "add")

    if action == "add":
        print(f"\n{'─' * 55}")
        print(f"📝 添加: {cmd['title']}  @ {cmd.get('start_time', '?')}")
        result = api_create_event(cmd)
        if result:
            print(f"  ✅ 已创建 (id={result.get('id')}) — {result.get('title')}")
            return True
        else:
            print(f"  ❌ 创建失败")
            return False

    elif action == "delete":
        eid = cmd.get("event_id")
        print(f"\n{'─' * 55}")
        print(f"🗑  删除: event_id={eid}")
        result = api_delete_event(eid)
        if result:
            print(f"  ✅ {result.get('message', '已删除')}")
            return True
        else:
            print(f"  ❌ 删除失败")
            return False

    else:
        print(f"  ⚠️  未知操作: {action}")
        return False


# ── 主入口 ──

def main():
    list_only = "--list" in sys.argv
    dry_run = "--dry-run" in sys.argv
    direct = "--direct" in sys.argv

    mode = "direct" if direct else "nlu"

    print("=" * 55)
    print("  语音日历助手 - 测试数据注入")
    print("=" * 55)
    print(f"  服务器: {BASE_URL}")
    print(f"  模式:   {mode}")

    if not check_server():
        print(f"\n❌ 无法连接到 {BASE_URL}")
        print(f"   请先启动服务器: uv run python main.py --api")
        sys.exit(1)
    print(f"  ✅ 服务器已连接")

    if mode == "nlu":
        commands = NLU_COMMANDS
        print(f"  命令数: {len(commands)}")
        if dry_run:
            print(f"  [dry-run] 仅解析不执行")
        if list_only:
            print(f"\n📋 NLU 命令列表:")
            for i, c in enumerate(commands, 1):
                print(f"  {i}. {c}")
            return

        ok = fail = 0
        for cmd in commands:
            if run_nlu_command(cmd, dry_run=dry_run):
                ok += 1
            else:
                fail += 1

    else:  # direct
        commands = DIRECT_COMMANDS
        print(f"  命令数: {len(commands)}")
        if list_only:
            print(f"\n📋 Direct 命令列表:")
            for i, c in enumerate(commands, 1):
                print(f"  {i}. [{c.get('action','?')}] {c.get('title', c.get('event_id','?'))}")
            return

        ok = fail = 0
        for cmd in commands:
            if run_direct_command(cmd):
                ok += 1
            else:
                fail += 1

    print(f"\n{'=' * 55}")
    print(f"  结果: {ok} 成功, {fail} 失败, {len(commands)} 总计")
    print(f"{'=' * 55}")


if __name__ == "__main__":
    main()
