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

## Day 3: Web 前端主页（2026-05-30 ~ 2026-05-31）

### 任务进度

- √ 实现 Web 前端主页 — 单文件 Vue 3 + Tailwind CSS 应用
  - `frontend/web/index.html` — ~750 行，零构建单文件应用
  - `frontend/web/static/` — FastAPI StaticFiles 挂载目录

- √ 集成 FastAPI 静态文件服务
  - `app.py` 新增 StaticFiles 挂载 + 根路由 `/` 返回 index.html
  - 前后端同源，无需处理跨域

- √ 日历月视图
  - 周日~周六表头，6×7 日期矩阵，当前月灰色区分
  - 今天高亮（淡黄背景），事件蓝色小圆点标记（最多 4 个 + "+N" 溢出）

- √ 三状态交互
  - Home：日历居中，click 背景 → 录音，click 日期 → 日程模式
  - Recording：红色呼吸边框动画，click 背景 → 停止录音 → 全链路 → 返回 Home
  - Schedule：日历缩小 62% 左移，右侧面板滑入，click 日期 → 切换日，click 背景 → Home

- √ 3D 倾斜效果 — JS mousemove → `perspective(1200px) rotateX/Y(±8deg)`，mouseleave 平滑回正

- √ 液态玻璃风格 — `backdrop-blur-2xl bg-white/[0.04] border-white/[0.08]`

- √ 实时时钟 — 底部居中 `2026年5月31日 22:16`，每秒更新

- √ 月份切换 — 鼠标滚轮 + 触屏滑动，带方向感知滑入淡出动画

- √ 录音全链路 — MediaRecorder → upload → parse → execute → 刷新事件列表

- √ 录音安全上下文检查 — 检测 `navigator.mediaDevices` 和 `MediaRecorder` 可用性，非安全上下文给出中文提示

- √ 移动端响应式 — 触屏滑动、全屏日程面板、自适应字号

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
│   └── web/
│       ├── index.html                  # √ Vue 3 + Tailwind 单文件应用（~750 行）
│       └── static/                     # FastAPI StaticFiles 挂载目录
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

### 2026-05-31 前端主页实现

**新增文件：**
- `frontend/web/index.html` — Vue 3 CDN + Tailwind CSS CDN 单文件应用（~750 行）
- `frontend/web/static/` — FastAPI StaticFiles 挂载目录

**修改文件：**
- `app.py` — 新增 `StaticFiles` 挂载 + 根路由 `/` 返回 `FileResponse`

**技术要点：**
- Vue 3 Composition API (`reactive`)，零构建
- 三状态管理：home / recording / schedule
- 日历算法：周日起始，6×7 网格，前后月填充
- API 调用均使用相对路径，前后端同源无跨域
- 录音全链路：MediaRecorder → `/api/voice/upload` → `/api/voice/parse` → `/api/execute`
- Glassmorphism 液态玻璃 + 3D 倾斜 + Vue Transition 动画

### 2026-05-31 麦克风安全上下文检查

**问题：** `startRecording()` 直接调用 `navigator.mediaDevices.getUserMedia()`，当页面不在安全上下文（非 localhost/HTTPS）或浏览器不支持时，报错 `Cannot read properties of undefined` 白屏。

**修改文件：** `frontend/web/index.html` — `startRecording()` 函数

**修改内容：**
```javascript
// 调用前增加两重检查
if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
  addToast('麦克风不可用：请通过 http://localhost:8000 访问', 'error')
  state.mode = 'home'
  return
}
if (!window.MediaRecorder) {
  addToast('当前浏览器不支持录音功能，请使用 Chrome 或 Edge', 'error')
  state.mode = 'home'
  return
}
```

### 2026-05-31 测试数据注入

**背景：** 前端开发完成后需验证日历显示和日程面板功能，数据库原本为空。

**操作：** 通过 Python 脚本直接向 SQLite 写入 8 条测试事件，覆盖 5 月（2 天）和 6 月（4 天）。

**插入的测试数据：**

| id | title | start_time | end_time | 日期 |
|----|-------|-----------|----------|------|
| 1 | 团队晨会 | 2026-05-31T09:00 | 10:00 | 今天 |
| 2 | 项目评审 | 2026-05-31T14:00 | 16:00 | 今天 |
| 3 | 晚餐聚会 | 2026-05-31T19:00 | — | 今天 |
| 4 | 产品需求讨论 | 2026-06-01T10:00 | 11:30 | |
| 5 | 技术分享会 | 2026-06-03T15:00 | 17:00 | |
| 6 | 团建活动 | 2026-06-05T09:00 | 18:00 | |
| 7 | 牙医预约 | 2026-06-10T08:00 | 09:00 | |
| 8 | 月度总结 | 2026-05-28T10:00 | 11:00 | 本月已过
