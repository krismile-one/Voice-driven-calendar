# 语音日历助手 - 开发文档

## 1. 项目结构

```
voice-calendar-agent/
├── main.py                  # 启动入口（--api / --terminal / --ssl）
├── pyproject.toml           # uv 包管理
├── .env.example             # 配置模板
├── setup.py                 # 环境检查（python setup.py --fix）
├── clean.py                 # 端口清理 + 数据库重置
├── addData.py               # 测试数据注入（NLU / direct 两种模式）
├── doc/                     # 文档
├── tests/                   # 测试（17 条）
├── data/
│   ├── calendar.db          # SQLite 数据库
│   └── ssl/                 # 自签名证书
└── src/voice_calendar_agent/
    ├── __main__.py          # → 委托 main.py
    ├── app.py               # FastAPI 应用 + StaticFiles + 根路由
    ├── config.py            # pydantic-settings 配置
    ├── utils/
    │   └── ssl_helper.py    # 自签名证书生成（cryptography）
    ├── backend/
    │   ├── api/
    │   │   ├── events.py    # 事件 CRUD + /api/execute
    │   │   └── voice.py     # 语音上传 + ffmpeg 转码 + /api/voice/parse
    │   ├── core/
    │   │   ├── calendar_service.py
    │   │   ├── voice_service.py    # 百度 / 讯飞 / Vosk 三种 ASR
    │   │   └── nlu_service.py      # DeepSeek / Claude NLU 解析
    │   └── models/
    │       ├── event.py
    │       └── database.py
    ├── frontend/
    │   └── web/              # Vue 3 CDN 单文件应用 + 静态资源
    └── terminal/
        └── terminal_app.py   # 命令行交互（stub）
```

## 2. 运行逻辑与模块交互

### 2.1 分层架构

```
┌──────────────────────────────────────────────────┐
│                   操作层 (Frontend)                │
│  index.html  ←── 用户点击/录音/浏览日历            │
│  (Vue 3 CDN + Tailwind + MediaRecorder)           │
└────────────────────┬─────────────────────────────┘
                     │  HTTP REST / FormData
                     ▼
┌──────────────────────────────────────────────────┐
│                  接口层 (API)                      │
│  events.py  ←── 事件 CRUD + NLU 执行              │
│  voice.py   ←── 音频上传 + ffmpeg 转码 + NLU 解析  │
│  (FastAPI Router, 路由 /api/*)                    │
└────────────────────┬─────────────────────────────┘
                     │  单例 get_*_service()
                     ▼
┌──────────────────────────────────────────────────┐
│                  核心层 (Core)                     │
│  voice_service.py  ←── ASR 供应商路由              │
│  nlu_service.py    ←── LLM 提示词 + 响应解析       │
│  calendar_service.py ←── CRUD 业务逻辑             │
└────────────────────┬─────────────────────────────┘
                     │  SQLAlchemy Session
                     ▼
┌──────────────────────────────────────────────────┐
│                  数据层 (Models)                   │
│  database.py  ←── 引擎 / 会话 / init_db()         │
│  event.py     ←── ORM 映射                        │
│  (SQLite, 文件: data/calendar.db)                 │
└──────────────────────────────────────────────────┘
```

### 2.2 语音全链路（核心路径）

```
用户点击录音 → MediaRecorder(webm/opus)
      │
      ▼  点击停止 → Blob → FormData
POST /api/voice/upload
      │
      ▼  voice.py: upload_audio()
1. 读取音频字节 → 写入临时文件
2. fsync 强制刷盘 → EBML 魔数校验(1A 45 DF A3)
3. ffmpeg: webm → 16kHz mono PCM WAV
4. voice_service.recognize_file(wav) → 文本
      │
      ▼  返回 {"text": "帮我创建明天上午十点的会议"}
POST /api/voice/parse?text=...
      │
      ▼  voice.py → nlu_service.parse_command(text)
1. _build_prompt(text) → 拼接当前时间 + 指令模板
2. _call_openai() / _call_anthropic() → LLM 返回 JSON
3. _parse_response() → 规整字段 + 同音字纠错
      │
      ▼  返回 NLUResponse {intent, title, time, ...}
POST /api/execute  (body: NLUResponse)
      │
      ▼  events.py → calendar_service
1. datetime.fromisoformat(nlu.time) → 绝对时间
2. calendar_service.add_event(title, start_time, ...)
3. 写入 SQLite → 返回 MessageResponse
      │
      ▼  前端刷新月视图
GET /api/events?date=YYYY-MM-01&range=month
```

### 2.3 模块依赖图

```
main.py
  ├─→ config.Settings          (.env / 环境变量)
  ├─→ app.create_app()
  │     ├─→ api/events          (CalendarService → models)
  │     ├─→ api/voice           (VoiceService + NLUService + ffmpeg)
  │     └─→ StaticFiles         (/static, /)
  └─→ terminal/terminal_app     (stub)

单例获取:
  get_voice_service() → VoiceService(ASR_MODE, BAIDU_*, ...)
  get_nlu_service()   → NLUService(LLM_PROVIDER, LLM_API_KEY, ...)
  get_db_session()    → SQLAlchemy Session (每请求新建)
```

### 2.4 ASR 供应商路由

```
voice_service.recognize_file(path)
  │
  ├─ ASR_MODE=online  —→ BaiduASR.recognize(path)          # 百度云端
  ├─ ASR_MODE=offline —→ VoskModel.recognize(path)         # 本地模型
  └─ ASR_MODE=hybrid  —→ BaiduASR 优先 → 失败则 Vosk 兜底
```

### 2.5 NLU 供应商路由

```
nlu_service.parse_command(text)
  │
  ├─ LLM_PROVIDER=openai    —→ OpenAI(api_key, base_url)    # DeepSeek / Mimo 等
  └─ LLM_PROVIDER=anthropic —→ Anthropic(api_key)           # Claude
```

### 2.6 前端状态机

```
HOME ──(点击日期)──→ SCHEDULE ──(点击空白)──→ HOME
  │                      │
  │                   (点其他日期)
  │                      │
  │                      ▼
  │                   SCHEDULE (切换日期, 刷新日程列表)
  │
  └──(点击空白)──→ RECORDING ──(点击空白)──→ 上传 → 解析 → 执行 → HOME
```

## 3. 技术栈

| 层 | 选型 |
|----|------|
| 语言 / 包管理 | Python 3.11+ · uv |
| 后端 | FastAPI · Uvicorn |
| 数据库 | SQLite（SQLAlchemy + aiosqlite） |
| 在线 ASR | 百度语音（baidu-aip） |
| 离线 ASR | Vosk（可选） |
| NLU | DeepSeek / Anthropic Claude |
| 前端 | Vue 3 CDN · Tailwind CSS CDN · tinylunar |
| 音频处理 | ffmpeg（webm→16kHz PCM WAV） |
| 配置 | pydantic-settings · python-dotenv |

## 4. 系统依赖

| 依赖 | 用途 | 安装 |
|------|------|------|
| Python 3.11+ | 运行环境 | https://python.org |
| ffmpeg | 浏览器录音 webm→WAV 转码 | `sudo apt install ffmpeg` / `brew install ffmpeg` / `winget install ffmpeg` |
| uv | 包管理 | `pip install uv` |

```bash
python setup.py          # 检查所有依赖
python setup.py --fix    # 自动修复（uv sync + 创建 .env）
```

## 5. 数据库

**SQLite**: `data/calendar.db`

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER | 主键 |
| title | VARCHAR(200) | 标题 |
| description | TEXT | 描述 |
| start_time | DATETIME | 开始时间 |
| end_time | DATETIME | 结束时间 |
| reminder | BOOLEAN | 是否提醒 |
| reminder_minutes | INTEGER | 提前提醒分钟数 |
| created_at | DATETIME | 创建时间 |
| updated_at | DATETIME | 更新时间 |

## 6. API 接口

Base: `http://localhost:8000`

### 事件管理

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/events?date=YYYY-MM-DD&range=day\|week\|month` | 查询事件 |
| POST | `/api/events` | 创建事件 |
| PUT | `/api/events/{id}` | 更新事件 |
| DELETE | `/api/events/{id}` | 删除事件 |
| POST | `/api/execute` | 执行 NLU 解析结果 |

### 语音识别

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/voice/upload` | 上传音频（FormData），自动检测格式并 ffmpeg 转码 |
| POST | `/api/voice/parse?text=...` | NLU 解析语音文本 |
| WS | `/api/voice/stream` | WebSocket 实时流 |

### 前端

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/` | 前端主页 |
| GET | `/static/...` | 静态资源（JS / 图片） |

## 7. NLU 解析

全链路：`浏览器录音(webm/opus)` → `POST /api/voice/upload` → `ffmpeg 转 WAV` → `百度 ASR` → `POST /api/voice/parse?text=` → `LLM 解析` → `POST /api/execute` → `写入数据库`

### 解析目标格式

```json
{
  "intent": "add_event",
  "title": "开会",
  "time": "2026-05-30T15:15:00",
  "time_range": "morning|afternoon|evening|day",
  "reminder": true,
  "reminder_minutes": 30,
  "description": ""
}
```

LLM 自动处理：相对时间换算（"明天""下周三"）、同音字纠错（"回议"→"会议"）、时间段识别。

## 8. 配置说明（.env）

| 变量 | 说明 |
|------|------|
| `DATABASE_URL` | 数据库地址，默认 `sqlite:///data/calendar.db` |
| `ASR_MODE` | `online` / `offline` / `hybrid` |
| `ASR_PROVIDER` | `baidu` / `xunfei` |
| `BAIDU_APP_ID` / `BAIDU_API_KEY` / `BAIDU_SECRET_KEY` | 百度语音凭据 |
| `VOSK_MODEL_PATH` | Vosk 离线模型路径 |
| `LLM_PROVIDER` | `openai` / `anthropic` |
| `LLM_API_KEY` | 大模型 API 密钥 |
| `LLM_MODEL` | 模型名（如 `deepseek-chat`） |
| `LLM_BASE_URL` | API 地址（如 `https://api.deepseek.com`） |
| `HOST` / `PORT` | 监听地址与端口 |
| `SSL_CERTFILE` / `SSL_KEYFILE` | SSL 证书路径（可选，预设后无需每次传参） |
| `REMINDER_CHECK_INTERVAL` | 提醒检查间隔（秒），默认 60 |

## 9. 启动命令

```bash
# 本地开发（HTTP + localhost 麦克风可用）
uv run python main.py --api

# 服务器部署（HTTPS，自动生成自签名证书）
uv run python main.py --api --ssl

# 指定证书
uv run python main.py --api --ssl-certfile /path/to/cert.pem --ssl-keyfile /path/to/key.pem

# 终端交互模式
uv run python main.py --terminal
```

> **麦克风权限**：浏览器要求安全上下文（localhost 或 HTTPS），部署到服务器必须用 `--ssl`。

## 10. 代码规范

- Python: Black · isort · ruff · 类型注解 · docstring（Google 风格）
- 日志格式: `%(asctime)s - %(name)s - %(levelname)s - %(message)s`
- 前端: Vue 3 Options API · Tailwind utility-first · 录音 > 0.8s 最短保护
