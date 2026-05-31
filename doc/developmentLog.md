# 语音日历助手 - 开发日志

## Day 1: 后端核心 + 语音识别

- √ FastAPI 项目结构：`app.py`、`config.py`
- √ SQLite + SQLAlchemy ORM：`models/event.py`、`models/database.py`
- √ 事件 CRUD：`core/calendar_service.py`、`api/events.py`
- √ 语音识别：`core/voice_service.py`（百度 + 讯飞，通过 `ASR_PROVIDER` 切换）
- √ NLU 解析：`core/nlu_service.py`（DeepSeek，含同音字纠正，输出 ISO8601）

## Day 2: 语音交互 + 接口联调

- √ 全链路：`upload` → `parse` → `execute` 三步串联，端到端通过
- √ 测试用例：17 条全部通过（单元 8 + 集成 7 + E2E 2）

## Day 3: Web 前端 + 部署（2026-05-30 ~ 2026-05-31）

### 新增文件

| 文件 | 说明 |
|------|------|
| `frontend/web/index.html` | Vue 3 CDN + Tailwind 单文件应用（~1050 行），三状态交互、3D 倾斜、月份切换、录音全链路 |
| `frontend/web/static/js/special_dates.js` | 58 条特殊日期（节假日/调休/补班/节气），2026 全年覆盖 |
| `frontend/web/static/images/jieri/` + `24_jieqi/` | 节日 + 节气背景图 |
| `clean.py` | 端口清理；`--reset` 删库 |
| `addData.py` | 测试数据注入：NLU 模式 / `--direct` 直调 API |
| `setup.py` | 环境检查：`python setup.py [--fix]` |
| `utils/ssl_helper.py` | 纯 Python 自签名证书生成（cryptography + openssl fallback） |

### 主要变更

| 类别 | 文件 | 内容 |
|------|------|------|
| 前端 UI | `index.html` | Apple 液态玻璃（blur + saturate + 浅白底色）、卡片 680px、字体放大、紫→青渐变 |
| 农历 | `index.html` | `<script type="module">` 引入 `tinylunar`，带缓存查询，日期格 + 详情页双处展示 |
| 特殊日期 | `index.html` + `special_dates.js` | 日期格三层：数字 → 标签/农历 → 红点，自动切换背景图 |
| 录音链路 | `index.html` → `voice.py` | MediaRecorder(webm/opus) → ffmpeg 转 16kHz PCM WAV → 百度 ASR → NLU → execute |
| 音频健壮 | `voice.py` | `fsync` 强制刷盘 + EBML 魔数校验 + 空文件拒绝；前端 0.8s 最小录音时长 |
| 部署 | `main.py`, `app.py`, `config.py` | `--ssl` 自签名证书 + HTTPS，解决浏览器安全上下文限制 |
| 服务端 | `app.py` | StaticFiles 挂载 + `/` 根路由 |
| 依赖 | `pyproject.toml` | 新增 `cryptography`（证书生成） |
| 图片修复 | `special_dates.js` | `.jpg` → `.png`（6 处），"节日" → "jieri" 目录修正 |

### 代码清理

- 删除 `backend/utils/time_parser.py`、`terminal/command_handler.py`、`terminal/operation_interface.py` 等纯 stub
- 删除 `frontend/gui/` 整个目录（PyQt6 预留，未实现）
- 重写 `__main__.py`（53 行废弃代码 → 7 行委托 `main.py`）

## 修复记录

| 日期 | 问题 | 文件 | 修改 |
|------|------|------|------|
| 05-30 | /execute 删除可能误删 | `events.py` | 精确匹配 → 唯一删；模糊匹配多结果 → 提示确认 |
| 05-30 | "明天上午"未按时间段过滤 | `nlu_service.py`, `voice.py`, `events.py` | 新增 `time_range` 字段 |
| 05-31 | `navigator.mediaDevices` undefined 白屏 | `index.html` | `startRecording()` 双重预检 + 中文提示 |
| 05-31 | 数据库为空无法验证前端 | 临时脚本 | Python 注入 8 条测试事件 |
| 05-31 | 节日图片 `.jpg` 引用实际 `.png` | `special_dates.js` | 6 处扩展名修正 + 目录名修正 |
| 05-31 | webm/opus → 百度 ASR 格式不匹配 | `voice.py` | ffmpeg 转码层（webm→16kHz PCM WAV） |
| 05-31 | 服务器部署麦克风被浏览器阻止 | `config.py`, `app.py`, `main.py`, `index.html` 等 7 个文件 | `--ssl` 自签名证书 + HTTPS + `isSecureContext` 检测 |
| 05-31 | NLU 每月最后一天崩溃 | `nlu_service.py` | `now.replace(day=day+1)` → `timedelta(days=1)` |
| 05-31 | 服务器 ffmpeg EBML header 解析失败 | `voice.py`, `index.html` | `fsync` + EBML 魔数校验 + 0.8s 最小录音时长 |

> **教训**：`datetime.replace(day=N)` 对越界值不安全，永远用 `timedelta`。提示词中的动态示例不是"死文字"，跨月边界是典型盲区。

## 模块框架

```
src/voice_calendar_agent/
├── __main__.py        → 委托 main.py
├── app.py             FastAPI 应用
├── config.py          配置加载
├── backend/
│   ├── api/            events.py、voice.py（含 ffmpeg 转码）
│   ├── core/           calendar_service.py、nlu_service.py、voice_service.py
│   └── models/         database.py、event.py
├── frontend/
│   └── web/            index.html、static/{js/special_dates.js, images/}
├── terminal/           terminal_app.py (stub)
└── utils/              ssl_helper.py
tests/ — 17 条测试全部通过
```

## 服务器部署

```bash
uv run python main.py --api --ssl          # 自动生成证书，访问 https://<IP>:8000
uv run python main.py --api --ssl-certfile cert.pem --ssl-keyfile key.pem   # 指定证书
```

## 测试结果

| 类别 | 数量 | 通过 |
|------|------|------|
| 单元 - 日历服务 | 4 | 4/4 |
| 单元 - NLU | 4 | 4/4 |
| 集成 - 语音识别 | 7 | 7/7 |
| E2E - 全链路 | 2 | 2/2 |
| **合计** | **17** | **100%** |

## Day 3: 天气背景集成（2026-05-31）

### 新增文件

| 文件 | 说明 |
|------|------|
| `backend/api/weather.py` | `/api/weather` 端点，wttr.in 代理 + WWO 码映射 + 日出日落昼夜判断 + 30min 内存缓存 |

### 主要变更

| 类别 | 文件 | 内容 |
|------|------|------|
| 后端 | `app.py` | 注册 weather router（+5 行） |
| 前端 CSS | `index.html` | 12 种天气 × 昼夜渐变（body 属性选择器）+ 雨滴/雪花/星星/闪电 CSS 动画 |
| 前端 JS | `index.html` | geolocation → `/api/weather` → 设置 `body[data-weather-category][data-daynight]`，30min 刷新，`onUnmounted` 清理 |
| 前端 HTML | `index.html` | `.bg-effects-layer` 粒子层（z:-1，介于渐变与特殊日期之间） |

### 背景层优先级

```
z-index: -2  天气渐变（body 属性触发 CSS）/ 默认紫→青渐变
z-index: -1  天气特效粒子（雨滴/雪花/星星/闪电）
z-index: -1  特殊日期背景图（hover/选中时覆盖上面两层）
```

### 降级链

```
geolocation 允许 → 本地坐标查天气
       ↓ 拒绝/超时
不传坐标 → 默认北京（39.9, 116.4）
       ↓ wttr.in 挂了
返回旧缓存 → 返回默认晴天 → 前端静默保留默认渐变
```

### 关键设计决策

- **数据源**：选 wttr.in（零配置、免费、支持中文），未选 和风天气（需实名注册）或 OpenWeatherMap（需绑信用卡）
- **昼夜判断**：用 wttr.in 返回的日出日落天文数据（`astronomy.sunrise/sunset`），比固定 6-18 点更准确
- **纬度优先**：天气渐变（`body[data-weather-category]`）在默认层，特效粒子（`.bg-effects-layer`）在中间层，特殊日期背景图（`.bg-special-layer`）在最上层——三层层叠互不干扰
- **零侵入**：天气 API 异步加载不阻塞 UI，所有降级路径保留默认渐变，不影响原有录音/日历/日程逻辑

## 修复记录

| 日期 | 问题 | 文件 | 修改 |
|------|------|------|------|
| 05-30 | /execute 删除可能误删 | `events.py` | 精确匹配 → 唯一删；模糊匹配多结果 → 提示确认 |
| 05-30 | "明天上午"未按时间段过滤 | `nlu_service.py`, `voice.py`, `events.py` | 新增 `time_range` 字段 |
| 05-31 | `navigator.mediaDevices` undefined 白屏 | `index.html` | `startRecording()` 双重预检 + 中文提示 |
| 05-31 | 数据库为空无法验证前端 | 临时脚本 | Python 注入 8 条测试事件 |
| 05-31 | 节日图片 `.jpg` 引用实际 `.png` | `special_dates.js` | 6 处扩展名修正 + 目录名修正 |
| 05-31 | webm/opus → 百度 ASR 格式不匹配 | `voice.py` | ffmpeg 转码层（webm→16kHz PCM WAV） |
| 05-31 | 服务器部署麦克风被浏览器阻止 | `config.py`, `app.py`, `main.py`, `index.html` 等 7 个文件 | `--ssl` 自签名证书 + HTTPS + `isSecureContext` 检测 |
| 05-31 | NLU 每月最后一天崩溃 | `nlu_service.py` | `now.replace(day=day+1)` → `timedelta(days=1)` |
| 05-31 | 服务器 ffmpeg EBML header 解析失败 | `voice.py`, `index.html` | `fsync` + EBML 魔数校验 + 0.8s 最小录音时长 |
| 05-31 | 天气背景集成 | `weather.py`, `app.py`, `index.html` | 新增 wttr.in 天气 API + 动态渐变/特效前端 |
