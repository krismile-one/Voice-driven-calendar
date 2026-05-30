# Web 前端技术方案

> 2026-05-30

## 一、技术选型

| 项 | 选型 | 原因 |
|----|------|------|
| 框架 | Vue 3 (CDN) | 内置 Transition/TransitionGroup，零构建 |
| 样式 | Tailwind CSS (CDN) | 液态玻璃(`backdrop-blur`)、暗色主题 |
| 动画 | Vue `<Transition>` + CSS keyframes | 框架级动画编排，不手写 JS 动画 |
| 录音 | MediaRecorder API | 浏览器原生，WebM/Opus → blob |
| HTTP | fetch (原生) | 不需要 axios，API 简单 |
| 部署 | FastAPI StaticFiles | 和现有服务同一进程，不拆服务 |

## 二、结构

```
src/voice_calendar_agent/frontend/web/
├── index.html          # 单文件应用（Vue SFC 风格，单文件 ~500 行）
└── static/             # FastAPI mount 目录（可选，按需拆分）
```

路由注册（app.py 加两行）：

```python
from fastapi.staticfiles import StaticFiles
app.mount("/static", StaticFiles(directory="frontend/web/static"), name="static")

@app.get("/")
async def index():
    return FileResponse("frontend/web/index.html")
```

启动后访问 `http://localhost:8000` 即完整应用。

## 三、API 对接

### 3.1 端点映射

| 前端操作 | HTTP 调用 | 请求体 | 响应类型 |
|----------|-----------|--------|----------|
| 上传录音文件 | `POST /api/voice/upload` | FormData(audio=blob) | `{text, confidence}` |
| 文字解析（跳过录音） | `POST /api/voice/parse?text=...` | query string | `{intent, title, time, time_range, ...}` |
| 执行 NLU 指令 | `POST /api/execute` | NLUResponse JSON | `{message, id}` |
| 获取事件列表 | `GET /api/events?date=...&range=...` | - | `{events[], total}` |
| 获取单个事件 | `GET /api/events/{id}` | - | `EventResponse` |
| 创建事件（手动） | `POST /api/events` | `{title, start_time, ...}` | `EventResponse` |
| 更新事件 | `PUT /api/events/{id}` | 部分字段 | `EventResponse` |
| 删除事件 | `DELETE /api/events/{id}` | - | `{message, id}` |

### 3.2 两条调用链

**链路 A：语音输入（完整）**

```
MediaRecorder 录音
  ↓ blob (WebM)
POST /api/voice/upload  (FormData)
  ↓ {text: "帮我创建..."}
POST /api/voice/parse?text=...
  ↓ {intent, title, time, ...}
POST /api/execute
  ↓ {message: "已添加事件：周会"}
刷新事件列表
```

**链路 B：文字输入（快捷）**

```
<input> 文字输入
  ↓ "帮我创建明天下午3点的团队会议"
POST /api/voice/parse?text=...
  ↓
POST /api/execute
  ↓
刷新事件列表
```

### 3.3 错误处理策略

```
HTTP 状态码：
  200 → 正常
  404 → "事件不存在" toast
  422 → "输入格式不对" toast
  500 → "服务异常，请重试" toast
  
网络异常 (fetch catch)：
  → "无法连接服务，请确认已启动" toast
```

### 3.4 接口数据模型（前端侧 TypeScript 参考）

```typescript
// 与后端 Pydantic 一一对应，手工同步

interface NLUResponse {
  intent: "add_event" | "delete_event" | "query_events" | "update_event" | "unknown"
  title: string | null
  time: string | null          // ISO8601
  time_range: "morning" | "afternoon" | "evening" | "day"
  reminder: boolean
  reminder_minutes: number
  description: string | null
}

interface EventResponse {
  id: number
  title: string
  description: string | null
  start_time: string           // ISO8601
  end_time: string | null
  reminder: boolean
  reminder_minutes: number
  created_at: string
  updated_at: string
}

interface MessageResponse {
  message: string
  id: number | null
}
```

## 四、Vue 组件树

```
App
├── GlassBackground          # 动态渐变背景
├── VoicePanel               # 语音输入面板（液态玻璃卡片）
│   ├── RecordButton         # 录音按钮（脉冲光圈动画）
│   ├── StatusTransition     # 状态切换（idle→recording→processing→done）
│   └── TextInput            # 文字输入备用（回车发送）
├── CalendarView             # 日历视图（3D tilt 卡片）
│   ├── DateNavigator        # 日期切换
│   └── EventList            # TransitionGroup 动画列表
│       └── EventItem[]       # 单个事件（hover 微移，删除滑出）
└── ToastContainer           # 全局消息提示
```

## 五、关键动画方案

| 效果 | 技术 |
|------|------|
| 状态切换淡入淡出 | `<Transition name="fade" mode="out-in">` |
| 事件列表增删位移 | `<TransitionGroup name="list" move-class="list-move">` |
| 录音按钮脉冲光圈 | `@keyframes pulse-ring` + `box-shadow` 扩散 |
| 液态玻璃卡片 | `bg-white/5 backdrop-blur-2xl border border-white/10` |
| 卡片 3D 倾斜 | `@mousemove` → `transform: perspective(800px) rotateX/Y(±5deg)` + CSS transition |
| 动态渐变背景 | `@keyframes gradient-shift` → `background-position` 循环 |
| 识别文字逐字浮现 | CSS `animation-delay` stagger（可选） |

## 六、录音流程状态机

```
idle ──点击──→ recording ──静音1.5s──→ processing ──API返回──→ done ──2s后自动──→ idle
  │               │                      │                    │
  │               │                      │                    └─ 显示结果 + 刷新列表
  │               │                      └─ ⏳ 正在识别...
  │               └─ 🔴 录音中... (按钮脉冲)
  └─ 🎤 点击开始录音 (按钮静态)
  
error 任何阶段发生 → "识别失败" toast → idle
```

## 七、部署不变

```
uv run python main.py --api

访问 http://localhost:8000 → Web 应用
访问 http://localhost:8000/docs → Swagger（调试用）
```

前后端同进程，无跨域问题，无额外端口。
