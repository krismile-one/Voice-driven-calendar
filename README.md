<div align="center">

# 🎙️ 语音日历助手 · Voice Calendar Agent

**动动嘴就能管理日程——说一句话，自动变成结构化的日历事件。**

以语音交互为核心的日历管理工具：通过语音添加、删除、查询日程，由大模型把口语解析成「操作 + 时间 + 标题 + 提醒」，存入本地数据库，并按时提醒。支持在线 / 离线 / 混合三种识别模式。

`Python 3.11+` · `FastAPI` · `uv` · `ASR：百度 / Vosk` · `NLU：DeepSeek` · `SQLite`

</div>

---

## ✨ 功能特性

- 🎤 **语音操作日程** —— 一句话完成添加 / 删除 / 查询，全程免打字
- 🔄 **三种识别模式** —— 在线（百度语音）、离线（Vosk 本地）、混合，可按需切换
- 🧠 **自然语言理解** —— 大模型把「明天下午3点一刻开会，提前半小时提醒」这类口语解析成结构化日程，自动换算相对时间
- 💾 **本地数据库** —— 日程存于本地 SQLite，隐私可控、离线可查
- ⏰ **定时提醒** —— 后台定时轮询，到点触发提醒
- 🖥️ **多种使用方式** —— 终端交互、HTTP API 服务、可选桌面 GUI

## 🔧 工作流程

```
语音输入 → 语音识别(ASR) → 意图解析(NLU) → 写入数据库 → 列表展示 / 定时提醒
            在线/离线/混合     大模型 → JSON       SQLite
```

解析目标格式示例：

```json
{ "action": "add", "title": "开会", "time": "2026-05-30T15:15:00", "remind_before_minutes": 30 }
```

## 🔄 三种识别模式

通过环境变量 `ASR_MODE` 切换：

| 模式 | 语音识别 | 是否联网 | 精度 | 隐私 | 成本 | 适用场景 |
|---|---|---|---|---|---|---|
| `online` | 百度语音云端 | 需要 | 高 | 音频上传 | 按量计费 | 追求最高准确率 |
| `offline` | 本地 Vosk 模型 | 不需要 | 中 | 数据不出设备 | 零 | 无网络 / 隐私敏感 |
| `hybrid` | 在线优先，离线兜底 | 部分 | 高 | 视情况 | 较低 | 兼顾精度与可用性 |

> 离线模式需安装 `vosk` 可选依赖，并下载中文模型到 `VOSK_MODEL_PATH` 指定路径。

## 🖥️ 使用方式（界面）

| 方式 | 启动命令 | 说明 |
|---|---|---|
| **终端交互**（默认） | `uv run python main.py` | 命令行里直接说话 / 输入指令，最快上手 |
| **API 服务** | `uv run python main.py --api` | 启动 FastAPI 后端（默认 `0.0.0.0:8000`），供前端或其他程序调用 |
| **桌面 GUI**（可选） | 需安装 `gui` 依赖（PyQt6） | 图形界面操作 |

## 🛠️ 技术栈

| 层 | 技术选型 |
|---|---|
| 语言 / 工具链 | Python 3.11+ · uv |
| 后端框架 | FastAPI · Uvicorn |
| 在线 ASR | 百度语音（`baidu-aip`） |
| 离线 ASR | Vosk（`vosk` + `pyaudio`） |
| 意图解析 NLU | DeepSeek / OpenAI / Anthropic（`openai`、`anthropic`、`httpx`） |
| 数据库 | SQLite（`sqlalchemy` + `aiosqlite`） |
| 配置管理 | `pydantic-settings` · `python-dotenv` |
| 桌面界面（可选） | PyQt6 |
| 测试 / 质量 | pytest · ruff · black · isort |

## 🚀 快速开始

```bash
# 1. 安装 uv（如未安装）
pip install uv

# 2. 安装依赖
uv sync
#   需要离线识别 / 桌面 GUI 时，附加可选依赖：
uv sync --extra vosk --extra gui

# 3. 配置环境变量
cp .env.example .env        # Windows: copy .env.example .env
#   编辑 .env，填入百度语音与大模型的密钥（见下方配置说明）

# 4. 运行
uv run python main.py            # 终端交互模式（默认）
uv run python main.py --api      # API 服务模式（FastAPI，端口 8000）
```

## ⚙️ 配置说明（.env）

| 变量 | 说明 |
|---|---|
| `DATABASE_URL` | 数据库地址，默认 `sqlite:///data/calendar.db` |
| `ASR_MODE` | 识别模式：`online` / `offline` / `hybrid` |
| `BAIDU_APP_ID` / `BAIDU_API_KEY` / `BAIDU_SECRET_KEY` | 百度语音凭据（在线模式需要） |
| `VOSK_MODEL_PATH` | Vosk 中文模型路径（离线模式需要） |
| `LLM_PROVIDER` | 大模型提供商：`openai` / `anthropic`（DeepSeek、Mimo 走 openai 格式） |
| `LLM_API_KEY` | 大模型 API 密钥 |
| `LLM_MODEL` | 模型名，如 `deepseek-chat` |
| `LLM_BASE_URL` | API 基础地址，如 `https://api.deepseek.com` |
| `HOST` / `PORT` | API 服务监听地址与端口 |
| `REMINDER_CHECK_INTERVAL` | 提醒检查间隔（秒），默认 60 |

> 需要自行申请的密钥：**百度语音**（在线 ASR）与 **DeepSeek 等大模型**（NLU）。真实 `.env` 不会提交到仓库。

## 📁 项目结构

```
voice-calendar-agent/
├── src/voice_calendar_agent/   # 核心代码包
│   ├── config.py               # 配置加载（Settings）
│   ├── app.py                  # FastAPI 应用（create_app）
│   ├── terminal/               # 终端交互界面（TerminalApp）
│   └── ...                     # ASR / NLU / 存储 / 提醒 等模块
├── tests/                      # 测试
├── doc/                        # 文档
├── main.py                     # 启动入口（终端 / API 模式）
├── pyproject.toml              # 项目与依赖配置
├── uv.lock                     # 依赖锁定
└── .env.example                # 配置模板
```

## 🗺️ Roadmap

- [ ] 复述确认与一句话纠错
- [ ] 多轮对话（「把刚才那个会改到四点」）
- [ ] 与系统日历 / Google Calendar 同步
- [ ] 离线模型自动下载与管理
- [ ] Web 前端界面
