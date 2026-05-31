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

### 工具脚本（2026-05-31）

| 文件 | 用途 | 用法 |
|------|------|------|
| `clean.py` | 清理工具 | 默认：清理端口 8000；`--reset`：同时删除数据库 |
| `addData.py` | 测试数据注入 | NLU 模式：自然语言 → parse → execute；`--direct`：绕过 NLU 直调 API |

### 特殊日期 + 农历 + UI 优化（2026-05-31）

#### 新增文件

| 文件 | 说明 |
|------|------|
| `frontend/web/static/js/special_dates.js` | 58 条特殊日期配置（节假日/调休/补班/节气），2026 全年覆盖，2027-2028 可扩展 |
| `frontend/web/static/images/jieri/` | 节日背景图目录（元旦/春节/清明/劳动/端午/中秋/国庆/元宵/情人/妇女等） |
| `frontend/web/static/images/24_jieqi/` | 二十四节气背景图目录（立春→大寒，24 张） |

#### index.html CSS 变更（11 处）

| # | 选择器 | 旧值 | 新值 | 说明 |
|---|--------|------|------|------|
| 1 | `.bg-default-layer` | `linear-gradient(135deg, #FF626E, #FFBE71)` | `linear-gradient(45deg, #BC95C6, #7DC4CC)` | 渐变方向 135°→45°（左下→右上），颜色换为紫→青 |
| 2 | `.bg-special-layer` | `background-size: cover` | `115%` | 放大避免水印进入可视区 |
| 3 | `.bg-special-layer` | `background-position: center top` | `center center` | 居中显示 |
| 4 | `.date-number` | （新增） | `display:flex; align-items:center; justify-content:center; height:1.35em` | 固定高度容器，数字与标签解耦 |
| 5 | `.date-label` | `margin-top: 2px` | 删除 | 避免挤占高度 |
| 6 | `.lunar-text` | （新增） | `font-size:9px; color:rgba(255,255,255,0.35)` | 农历日期半透明白色 |
| 7 | `.event-badge` | `margin-top: 3px` | 删除 | 避免挤占高度 |
| 8 | `.date-cell` | （不变） | — | 保留 `aspect-square flex flex-col items-center justify-center` |
| 9 | 卡片容器 | `max-w-[480px]` | `max-w-[560px]` | 日历面板加宽 |
| 10 | 日期网格 | `gap-0.5 md:gap-1` | `gap-1 md:gap-1.5` | 间距加大 |
| 11 | 日期数字 | `text-base md:text-lg` | `text-lg md:text-xl` | 字号加大 |

#### index.html 模板变更（4 处）

| # | 位置 | 变更 | 说明 |
|---|------|------|------|
| 1 | 日期格结构 | 数字 → 标签 → 红点 三层 → 数字（`date-number`）→ 标签(v-if) / 农历(v-else-if) → 红点(v-if) | 新增农历行，严格优先级 |
| 2 | 农历标签 | `v-else-if="cell.isCurrentMonth"` → `{{ getLunarText(cell.dateStr) }}` | 无特殊标签时显示农历 |
| 3 | 日程面板 | 新增 `<p>农历{{ getLunarFullText(selectedDateStr) }}</p>` | 详情页显示完整农历 |
| 4 | 特殊标签注释 | `Q6` 注释标记移除 | 清理 |

#### index.html JS 变更（8 处）

| # | 变更 | 说明 |
|---|------|------|
| 1 | `<script>` → `<script type="module">` | 支持 ESM import |
| 2 | `import { lunisolar } from 'https://unpkg.com/tinylunar/dist/index.js'` | 引入农历库（v1.0.2，~50KB） |
| 3 | 新增 `lunarCache` + `queryLunar(dateStr)` | 带缓存的农历查询，避免重复计算 |
| 4 | 新增 `getLunarText(dateStr)` | 返回农历日（如"十五"），用于日期格 |
| 5 | 新增 `getLunarFullText(dateStr)` | 返回完整农历（如"四月十五"），用于日程详情 |
| 6 | `onMounted` 新增自动背景 | 检测 `todayStr` 是否在 SPECIAL_DATES 中，有则 `switchBackground()` |
| 7 | return 对象新增 | `getLunarText`, `getLunarFullText` 暴露给模板 |
| 8 | `queryLunar` 异常保护 | try/catch + null 返回，农历加载失败不影响其他功能 |

#### voice.py 音频格式修复

| # | 变更 | 说明 |
|---|------|------|
| 1 | 新增 `import shutil, subprocess` | ffmpeg 调用所需 |
| 2 | 新增 `FFMPEG_AVAILABLE` | 启动时检测 ffmpeg 是否安装 |
| 3 | 新增 `_needs_conversion(path)` | 判断是否为非 ASR 兼容格式（webm/mp3 等） |
| 4 | 新增 `_convert_to_wav(path)` | ffmpeg 转码：`pcm_s16le, 16kHz, mono` |
| 5 | 修改 `upload_audio()` | 自动检测 → 按需转码 → 识别 → finally 清理双文件 |
| 6 | `RuntimeError` 独立捕获 | ffmpeg 缺失/失败返回明确错误信息 |

#### special_dates.js 修复

- 节日图片扩展名 `.jpg` → `.png`（6 处），匹配文件系统实际格式

## 模块框架

```
src/voice_calendar_agent/
├── app.py、config.py、__main__.py
├── backend/
│   ├── api/          events.py、voice.py（含 ffmpeg 转码层）
│   ├── core/         calendar_service.py、nlu_service.py、voice_service.py
│   ├── models/       database.py、event.py
│   └── utils/        time_parser.py (stub)
├── frontend/
│   └── web/          index.html（~1035 行）、static/{js/special_dates.js, images/{jieri/, 24_jieqi/}}
└── terminal/         全部 stub
tests/ — 17 条测试全部通过
```

### NLU 跨月日期溢出修复（2026-05-31）

**问题**：每月最后一天（31日/28日/30日）NLU 解析必然崩溃，报 `day is out of range for month`。语音识别成功、文本正确，但 parse 阶段直接抛异常。

**根因**：`nlu_service.py#L186` 提示词示例 2 用了 `now.replace(day=now.day+1)` 计算"明天"的日期。当今天是 5 月 31 日时，`now.day+1 = 32`，`datetime.replace(day=32)` 在 5 月只有 31 天的情况下抛出 `ValueError`。虽然异常被 `parse_command()` 的 `except` 兜底捕获并降级为 `unknown`，但导致整个 NLU 链中断。

**场景复现**：

```
当前日期: 2026-05-31
执行路径: startRecording → upload → parse → _build_prompt
崩溃点:   now.replace(day=31+1) → day=32 → ValueError("day is out of range for month")
影响范围: 每月 28/29/30/31 日 — 所有触发"明天"相关提示词的请求
```

**为什么语音识别成功但 NLU 失败？**

```
语音链路:  浏览器录音 → ffmpeg 转码 → 百度 ASR → 文本 ✅ 成功
NLU 链路:  文本 → _build_prompt → 构建示例时 now.replace(day=32) → 💥
```

两条链路独立，ASR 正常返回文本后，NLU 在构建提示词阶段就崩了，根本没到调用大模型那一步。

**修复方案**：

| # | 位置 | 旧代码 | 新代码 | 说明 |
|---|------|--------|--------|------|
| 1 | `nlu_service.py` L12 | `from datetime import datetime` | `from datetime import datetime, timedelta` | 引入 timedelta |
| 2 | `nlu_service.py` L186 | `now.replace(day=now.day+1)` | `(now + timedelta(days=1))` | 用标准日期运算替代手动 replace |

`timedelta` 会正确处理跨月/跨年/闰年，不会出现非法日期。

**教训总结**：

- `datetime.replace(day=...)` 对越界值不安全，**永远用 `datetime + timedelta(days=N)` 做日期加减**
- 提示词中的动态示例也会成为崩溃点 — 示例不是"死文字"，里面的 Python 代码照样会执行
- 跨月边界是典型盲区 — 开发时恰好是 30 号，没触发 31 号的 bug；需要刻意在月末/年初/2 月底测试

### 修复记录

| 日期 | 问题 | 修改文件 | 修改内容 |
|------|------|----------|----------|
| 05-30 | /execute 删除逻辑只删首个匹配 → 可能误删 | `events.py` | 精确匹配 → 唯一删；模糊匹配多结果 → 提示确认 |
| 05-30 | "明天上午"未按时间段过滤 | `nlu_service.py`, `voice.py`, `events.py` | 新增 `time_range` 字段（morning/afternoon/evening/day） |
| 05-31 | `navigator.mediaDevices` undefined 白屏 | `index.html` | `startRecording()` 增加双重预检 + 中文提示 |
| 05-31 | 数据库为空无法验证前端 | 临时脚本 | Python 注入 8 条测试事件（5月3条 + 6月5条） |
| 05-31 | jieri 图片 `.jpg` 引用实际为 `.png` | `special_dates.js` | 6 处扩展名修正 |
| 05-31 | 浏览器 webm/opus → 百度 ASR 格式不匹配 | `voice.py` | 新增 ffmpeg 转码层（webm→16kHz PCM WAV） |
| 05-31 | 服务器部署后麦克风被浏览器阻止 | `config.py`, `app.py`, `main.py`, `index.html` 等 7 个文件 | 新增 `--ssl` 自签名证书 + HTTPS 启动 |
| 05-31 | 每月最后一天 NLU 崩溃：`now.replace(day=32)` 跨月溢出 | `nlu_service.py` L12, L186 | `replace(day=day+1)` → `+ timedelta(days=1)` |

### 服务器 HTTPS 部署修复（2026-05-31）

**问题**：部署到服务器后，浏览器阻止麦克风 — `getUserMedia()` 仅在安全上下文（`localhost` 或 `https://`）下可用，通过 `http://IP:8000` 访问时 `navigator.mediaDevices` 不可用。

**根因**：浏览器安全策略，非 localhost 的 HTTP 页面不是安全上下文。

#### 修改文件

| # | 文件 | 变更 | 说明 |
|---|------|------|------|
| 1 | `config.py` | 新增 `SSL_CERTFILE`、`SSL_KEYFILE` | 可在 `.env` 预设 SSL 路径 |
| 2 | `app.py` | `run()` 新增 `ssl_certfile`/`ssl_keyfile` 参数 | 传给 uvicorn 启用 HTTPS |
| 3 | `main.py` | 新增 `--ssl`、`--ssl-certfile`、`--ssl-keyfile` CLI 参数 | 三选一启用 HTTPS |
| 4 | `utils/ssl_helper.py` | **新文件** | 纯 Python 自签名证书生成（cryptography），自动 fallback openssl |
| 5 | `pyproject.toml` | 新增 `cryptography` 依赖 | 确保证书生成跨平台可用 |
| 6 | `index.html` | 错误提示改用 `window.isSecureContext` | 动态显示正确 HTTPS 地址替代硬编码 localhost |
| 7 | `README.md` | 新增"生产部署（HTTPS）"章节 | 三种部署方式 + 麦克风权限说明 |

#### 使用方式

```bash
# 自动生成自签名证书并启动 HTTPS（内网 / 开发用）
uv run python main.py --api --ssl
# → 访问 https://<服务器IP>:8000
# → 浏览器提示不安全 → ＂高级 → 继续访问＂即可

# 指定已有证书
uv run python main.py --api --ssl-certfile cert.pem --ssl-keyfile key.pem

# .env 预设（省去每次传参）
SSL_CERTFILE=/path/to/cert.pem
SSL_KEYFILE=/path/to/key.pem
```

## 测试结果

| 类别 | 数量 | 通过 |
|------|------|------|
| 单元 - 日历服务 | 4 | 4/4 |
| 单元 - NLU | 4 | 4/4 |
| 集成 - 语音识别 | 7 | 7/7 |
| E2E - 全链路 | 2 | 2/2 |
| **合计** | **17** | **100%** |
