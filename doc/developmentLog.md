# 语音日历助手 - 开发日志

## Day 1: 后端核心 + 语音识别

- √ FastAPI 项目结构：`app.py`、`config.py`、`__main__.py`
- √ SQLite + SQLAlchemy ORM：`models/event.py`、`models/database.py`
- √ 事件 CRUD：`core/calendar_service.py`、`api/events.py`
- √ 语音识别：`core/voice_service.py`（百度 + 讯飞，通过 `ASR_PROVIDER` 切换）
- √ NLU 解析：`core/nlu_service.py`（DeepSeek，含同音字纠正，输出 ISO8601）

## Day 2: 语音交互 + 接口联调

- √ 全链路：`upload` → `parse` → `execute` 三步串联，端到端通过
- √ 测试用例：17 条全部通过（单元 8 + 集成 7 + E2E 2）

## Day 3: Web 前端（2026-05-30 ~ 2026-05-31）

### 初始搭建
- 新增 `frontend/web/index.html` — Vue 3 CDN + Tailwind CDN 单文件应用
- 新增 `frontend/web/static/` — FastAPI StaticFiles 挂载目录
- 修改 `app.py` — StaticFiles 挂载 + `/` 根路由
- 三状态交互（home/recording/schedule）、3D 倾斜、月份切换
- 录音全链路：MediaRecorder(webm/opus) → ffmpeg 转 WAV → 百度 ASR → NLU → execute
- 麦克风安全上下文检查、移动端响应式

### 特殊日期 + 农历 + UI 优化（2026-05-31）
- 新增 `frontend/web/static/js/special_dates.js` — 58 条特殊日期（节假日/调休/补班/节气）
- 引入 `tinylunar@1.0.2` (CDN) 公历→农历转换
- 默认渐变 `#BC95C6 → #7DC4CC`（45deg，左下→右上），特殊日期背景叠加层 opacity 切换
- 日历面板 `max-w-[560px]`，日期数字固定高度严格居中，字号 `text-lg md:text-xl`
- 日期格结构：数字 → 特殊标签/农历 → 事件红点徽标
- 日程详情：公历日期 + 星期 + 特殊标签 + 农历
- 当天自动显示特殊背景，图片预加载，加载失败静默回退

## 模块框架

```
src/voice_calendar_agent/
├── app.py、config.py、__main__.py
├── backend/
│   ├── api/          events.py、voice.py
│   ├── core/         calendar_service.py、nlu_service.py、voice_service.py
│   ├── models/       database.py、event.py
│   └── utils/        time_parser.py (stub)
├── frontend/
│   └── web/          index.html、static/{js/special_dates.js, images/{jieri/, 24_jieqi/}}
└── terminal/         全部 stub
tests/ — 17 条测试全部通过
```

## 修复记录

| 日期 | 问题 | 修改 |
|------|------|------|
| 05-30 | /execute 删除逻辑只删首个匹配 → 可能误删 | `events.py`：精确匹配 → 唯一删；模糊匹配多结果 → 提示确认 |
| 05-30 | "明天上午"未按时间段过滤 | 新增 `time_range` 字段（morning/afternoon/evening/day），NLU + API 联动 |
| 05-31 | 麦克风报错 `Cannot read properties of undefined` | `startRecording()` 增加 `mediaDevices` + `MediaRecorder` 双重预检 |
| 05-31 | 数据库为空无法验证前端 | Python 脚本注入 8 条测试事件（5月3条 + 6月5条） |
| 05-31 | 节日图片 `.jpg` 引用实际为 `.png` | `special_dates.js` 全部修正 |
| 05-31 | 浏览器 webm/opus 录音 → ASR 格式不匹配 | `voice.py` 新增 ffmpeg 转码层（webm→16kHz PCM WAV），自动检测格式并按需转换 |

## 测试结果

| 类别 | 数量 | 通过 |
|------|------|------|
| 单元 - 日历服务 | 4 | 4/4 |
| 单元 - NLU | 4 | 4/4 |
| 集成 - 语音识别 | 7 | 7/7 |
| E2E - 全链路 | 2 | 2/2 |
| **合计** | **17** | **100%** |
