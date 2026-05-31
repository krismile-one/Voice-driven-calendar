# Day 2 - 日历服务（CalendarService）开发记录

> 说明：日期编号按需调整。本记录对应日历事件业务逻辑层（CalendarService）的实现。

## 一、功能概述

实现语音日历助手的**日历业务逻辑层**：把上游（NLU 解析结果 / API 层）传来的事件数据，落到 SQLite 数据库，并提供事件的增、删、查、改与提醒查询。

### 已实现功能

- `add_event` —— 添加事件
- `delete_event` —— 按 ID 删除事件（不存在返回 False）
- `get_events` —— 按 day / week / month 范围查询事件，按开始时间排序
- `get_event` —— 按 ID 查询单个事件（不存在返回 None）
- `update_event` —— 按 ID 更新事件字段（不存在返回 None）
- `get_upcoming_reminders` —— 获取即将提醒的事件（方式 A：所有“开启提醒且未开始”的未来事件）
- 单元测试（连真实测试数据库，4 个用例全部通过）

---

## 二、实现方案

### 2.1 修改文件清单

| 文件 | 路径 | 修改内容 |
|------|------|----------|
| calendar_service.py | `src/voice_calendar_agent/backend/core/calendar_service.py` | 实现 CalendarService 的 6 个方法 |
| test_calendar_service.py | `tests/unit/test_calendar_service.py` | 填充 4 个单元测试 |

### 2.2 数据库与配置

- 数据库：**SQLite**，路径由 `DATABASE_URL`（默认 `sqlite:///data/calendar.db`）控制
- ORM：**同步 SQLAlchemy**（`Session` / `query` / `commit`），与 `database.py`、`conftest.py` 一致
- 表：`events`（见 `models/event.py`）

### 2.3 依赖变更

无新增依赖。`sqlalchemy`、`aiosqlite` 已在基础依赖中；实际使用**同步 Session**（`database.py` 用 `create_engine` + `sessionmaker`）。

### 2.4 关键技术点

- **同步写法**：所有方法走 `self.db`（同步 `Session`），无 async/await
- **添加事件**：`add` → `commit` → `refresh`（refresh 用于拿到自增 `id` 等数据库生成字段）
- **按日期查询**：用**时间区间 `[start, end)`** 比较（如当天 00:00 到次日 00:00），而非 `Event.start_time.date() == ...`（后者在 SQL 中不可用）
- **不存在的处理**：按骨架注释，`delete_event` 返回 `False`，`get_event` / `update_event` 返回 `None`
- **更新**：只对事件对象上**真实存在的字段**执行 `setattr`，忽略无关键值
- **提醒（方式 A）**：返回所有 `reminder=True` 且 `start_time > now` 的事件，把“到点没到点”的判断留给以后的提醒循环
- **测试隔离**：用 `conftest.py` 的 `db_session` 夹具，每个测试函数独立建表、跑完清表（连真实临时 SQLite，非 mock）

---

## 三、运行逻辑

### 3.1 整体架构

```
   上游调用方（NLU 解析结果 / API 层）
            │ 调用
            ▼
   ┌─────────────────────────┐
   │     CalendarService      │
   │  add / delete / get /    │
   │  update / reminders      │
   └───────────┬─────────────┘
               │ self.db（同步 Session）
               ▼
   ┌─────────────────────────┐
   │     SQLAlchemy ORM       │
   └───────────┬─────────────┘
               ▼
   ┌─────────────────────────┐
   │    SQLite（events 表）   │
   └─────────────────────────┘
```

### 3.2 初始化流程

```
1. 上层构造数据库会话
   ├── 正式运行：database.py 的 sessionmaker（get_db / get_db_session）
   └── 测试：conftest.py 的 TestingSessionLocal（db_session 夹具）
2. CalendarService(db=session)  →  self.db = session
3. 调用各方法时复用同一个 session
```

### 3.3 各方法流程

```
add_event(title, start_time, ...)
└── 构造 Event → self.db.add → commit → refresh → 返回 Event（含 id）

delete_event(event_id)
└── 按 id 查 → 不存在返回 False；存在则 delete → commit → 返回 True

get_events(date, range)
├── date 为 None → 返回全部，按 start_time 排序
└── date 不为 None → 按 range 算时间窗口 [start, end)
        day  : 当天 00:00 → 次日 00:00
        week : 本周一 00:00 → 下周一 00:00
        month: 本月 1 号 00:00 → 下月 1 号 00:00
    → filter(start_time >= start, < end) → 按 start_time 排序

get_event(event_id)
└── 按 id 查 → 返回 Event 或 None

update_event(event_id, **kwargs)
└── 按 id 查 → 不存在返回 None；存在则对已有字段 setattr → commit → refresh → 返回 Event

get_upcoming_reminders()
└── filter(reminder == True, start_time > now) → 按 start_time 排序 → 返回列表
```

### 3.4 与上下游的关系

```
NLU 解析结果 {title, time(ISO字符串), reminder, reminder_minutes, ...}
        ↓ time 需先转 datetime（ISO → datetime，由 time_parser / 胶水层负责）
CalendarService.add_event(title, start_time=datetime, ...)
        ↓
SQLite events 表
```

---

## 四、调用说明

### 4.1 直接调用示例

```python
from voice_calendar_agent.backend.core.calendar_service import CalendarService
from voice_calendar_agent.backend.models.database import init_db, get_db_session
from datetime import datetime

init_db("sqlite:///data/calendar.db")
db = get_db_session()
service = CalendarService(db)

# 添加
event = service.add_event(
    title="团队会议",
    start_time=datetime(2026, 5, 31, 15, 15),
    reminder_minutes=30,
)

# 查询当天
events = service.get_events(date=datetime(2026, 5, 31), range="day")

# 更新
service.update_event(event.id, title="团队会议（已改）")

# 删除
service.delete_event(event.id)
```

### 4.2 方法返回一览

| 方法 | 返回 |
|------|------|
| add_event | Event（含自增 id） |
| delete_event | bool（成功 True / 不存在 False） |
| get_events | List[Event]（按开始时间排序） |
| get_event | Event 或 None |
| update_event | Event 或 None |
| get_upcoming_reminders | List[Event] |

---

## 五、测试用例

### 5.1 单元测试方法（连真实测试数据库，非 mock）

| 测试方法 | 操作 | 预期结果 |
|----------|------|----------|
| test_add_event | 添加一条事件 | 返回对象有自增 id，字段正确（title/start_time/reminder/reminder_minutes） |
| test_delete_event | 删除存在 / 不存在的事件 | 存在返回 True 且查不到；不存在返回 False |
| test_get_events_by_date | 同一天加 2 条、隔天加 1 条，按天查 | 只返回当天 2 条，按开始时间排序 |
| test_update_event | 更新存在 / 不存在的事件 | 存在返回更新后对象；不存在返回 None |

> 测试用 `conftest.py` 的 `db_session` 夹具：每个测试函数独立建表、跑完清表，互不影响。

### 5.2 运行测试

```bash
# 首次需安装 dev 依赖（含 pytest）
uv sync --extra dev

# 运行日历服务单元测试
uv run pytest tests/unit/test_calendar_service.py -v
```

---

## 六、测试结果

测试时间：2026-05-30

### 6.1 单元测试结果

```
collected 4 items
test_add_event ............ PASSED
test_delete_event ......... PASSED
test_get_events_by_date ... PASSED
test_update_event ......... PASSED
================= 4 passed in 0.85s =================
```

### 6.2 结果分析

| 指标 | 结果 |
|------|------|
| 单元测试通过率 | 4/4（100%） |
| 增删查改正确性 | ✅ 均正确 |
| 不存在处理 | ✅ delete 返回 False、update 返回 None |
| 按日期查询 | ✅ 只返回当天且按时间排序 |
| 测试方式 | 连真实临时 SQLite（非 mock），跑后自动清理 |

---