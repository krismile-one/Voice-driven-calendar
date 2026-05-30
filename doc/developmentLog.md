# 语音日历助手 - 开发日志

## 项目进度总览


## Day 1: 后端核心 + 语音识别

### 任务进度

- √ 搭建 FastAPI 项目结构
  - `app.py` — FastAPI 应用入口，路由注册
  - `config.py` — pydantic-settings 配置管理，.env 读取
  - `__main__.py` — 模块入口

- √ 实现 SQLite 数据库和事件 CRUD 接口
  - `backend/models/database.py` — 引擎/会话管理
  - `backend/models/event.py` — Event ORM 模型
  - `backend/core/calendar_service.py` — 日历业务逻辑（增删改查）
  - `backend/api/events.py` — RESTful API 端点

- √ 集成百度在线语音识别
  - `backend/core/voice_service.py` — BaiduASREngine + XunfeiASREngine
  - 支持百度 HTTP API 和讯飞 WebSocket API，通过 ASR_PROVIDER 配置切换

- √ 实现 NLU 解析
  - `backend/core/nlu_service.py` — 支持 OpenAI/Anthropic 格式
  - 使用 DeepSeek 大模型，输出 ISO8601 绝对时间
  - 提示词含同音字纠正规则（回忆→会议 等）

---

## Day 2: 语音交互 + 接口联调

### 任务进度

- √ 完成语音 → 文本 → 指令 → 操作 全链路
  - `POST /api/voice/upload` — ASR 识别音频文件
  - `POST /api/voice/parse` — NLU 解析文本
  - `POST /api/events/execute` — 执行日历操作
  - 三步串联，端到端测试通过

- √ 编写测试用例
  - 语音识别集成测试 7 条
  - NLU 单元测试 4 条
  - 日历服务单元测试 4 条
  - 端到端全链路测试 2 条

- 实现持续语音监听功能（需 PyAudio）

---

## Day 3: 前端界面 + 优化

### 任务进度

- 实现简单的 GUI 或 Web 界面
- 集成前后端联调
- 优化识别准确率和响应速度
- 编写使用说明

---

## 已实现的模块框架

```
src/voice_calendar_agent/
├── __init__.py                         # 版本号
├── __main__.py                         # 模块入口
├── app.py                              # √ FastAPI 应用，路由注册
├── config.py                           # √ 配置管理（ASR/LLM/数据库）
│
├── backend/
│   ├── api/
│   │   ├── events.py                   # √ CRUD + /execute 端点
│   │   └── voice.py                    # √ /upload + /parse + /stream
│   │
│   ├── core/
│   │   ├── calendar_service.py         # √ 日历业务逻辑（增删改查）
│   │   ├── nlu_service.py              # √ NLU 解析（DeepSeek，含同音字纠正）
│   │   └── voice_service.py            # √ 语音识别（百度+讯飞）
│   │
│   ├── models/
│   │   ├── database.py                 # √ SQLAlchemy 引擎/会话
│   │   └── event.py                    # √ Event ORM 模型
│   │
│   └── utils/
│       └── time_parser.py              # 未实现（NLU 已替代其功能）
│
├── frontend/
│   ├── gui/                            # 全部 stub
│   └── web/                            # 未开始
│
└── terminal/
    ├── terminal_app.py                 # stub
    ├── command_handler.py              # stub
    └── operation_interface.py          # 抽象接口定义

tests/
├── conftest.py                         # √ 测试夹具
├── unit/
│   ├── test_calendar_service.py        # √ 4/4 通过
│   ├── test_nlu_service.py             # √ 4/4 通过
│   └── test_time_parser.py             # stub
├── integration/
│   ├── test_api_events.py              # stub
│   └── test_voice_service.py           # √ 7/7 通过
└── e2e/
    └── test_full_flow.py               # √ 2/2 通过
```

## 测试结果汇总

| 测试类别 | 测试数 | 通过率 |
|----------|--------|--------|
| 单元测试 - 日历服务 | 4 | 4/4 (100%) |
| 单元测试 - NLU 服务 | 4 | 4/4 (100%) |
| 集成测试 - 语音识别 | 7 | 7/7 (100%) |
| 端到端 - 全链路 | 2 | 2/2 (100%) |
| **合计** | **17** | **17/17 (100%)** |

---

## 修复记录

### 2026-05-30 /execute 删除逻辑优化

**问题：** 原删除逻辑对多个匹配事件只删第一个，用户说"取消明天的会议"时可能误删或漏删。

**修改文件：** `backend/api/events.py` — `/execute` 端点 `delete_event` 分支

**修改前：** 模糊匹配后直接取 `matched[0]` 删除

**修改后：**
- 精确匹配（title 完全一致）→ 唯一匹配则直接删除
- 模糊匹配（title 包含关键词）→ 唯一匹配则删除，多个匹配则提示用户确认
- 无匹配 → 返回"未找到相关事件"

### 2026-05-30 查询增加时间段过滤

**问题：** 用户说"明天上午有哪些事情"，NLU 输出 00:00:00，查询返回全天事件，没有按上午/下午过滤。

**修改文件：**
- `nlu_service.py` — prompt 新增 `time_range` 字段，fallback 返回加 `time_range`
- `voice.py` — `NLUResponse` 新增 `time_range: str = "day"`
- `events.py` — `/execute` 的 `query_events` 分支根据 `time_range` 过滤

**NLU 输出变化：**

```
用户："明天上午有哪些事情"
修改前: time="2026-05-31T00:00:00"                    → 查全天
修改后: time="2026-05-31T00:00:00", time_range="morning" → 只查上午 (hour < 12)
```

**time_range 取值：** morning(00-12) / afternoon(12-18) / evening(18-24) / day(不过滤)
