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

## 修复记录

| 日期 | 问题 | 修改文件 | 修改内容 |
|------|------|----------|----------|
| 05-30 | /execute 删除逻辑只删首个匹配 → 可能误删 | `events.py` | 精确匹配 → 唯一删；模糊匹配多结果 → 提示确认 |
| 05-30 | "明天上午"未按时间段过滤 | `nlu_service.py`, `voice.py`, `events.py` | 新增 `time_range` 字段（morning/afternoon/evening/day） |
| 05-31 | `navigator.mediaDevices` undefined 白屏 | `index.html` | `startRecording()` 增加双重预检 + 中文提示 |
| 05-31 | 数据库为空无法验证前端 | 临时脚本 | Python 注入 8 条测试事件（5月3条 + 6月5条） |
| 05-31 | jieri 图片 `.jpg` 引用实际为 `.png` | `special_dates.js` | 6 处扩展名修正 |
| 05-31 | 浏览器 webm/opus → 百度 ASR 格式不匹配 | `voice.py` | 新增 ffmpeg 转码层（webm→16kHz PCM WAV） |

## 测试结果

| 类别 | 数量 | 通过 |
|------|------|------|
| 单元 - 日历服务 | 4 | 4/4 |
| 单元 - NLU | 4 | 4/4 |
| 集成 - 语音识别 | 7 | 7/7 |
| E2E - 全链路 | 2 | 2/2 |
| **合计** | **17** | **100%** |
