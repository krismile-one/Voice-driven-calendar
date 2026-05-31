# 语音日历助手 - 测试文档

> 最后更新：2026-05-31

## 测试总览

| # | 测试类别 | 测试文件 | 数量 | 通过 | 耗时 |
|---|----------|----------|------|------|------|
| 1 | 单元测试 - 日历服务 | tests/unit/test_calendar_service.py | 4 | 4/4 | 0.09s |
| 2 | 单元测试 - NLU服务 | tests/unit/test_nlu_service.py | 4 | 4/4 | 0.89s |
| 3 | 单元测试 - 时间解析 | tests/unit/test_time_parser.py | 3 | ⬜ 未实现 | - |
| 4 | 集成测试 - 事件API | tests/integration/test_api_events.py | 4 | ⬜ 未实现 | - |
| 5 | 集成测试 - 语音识别 | tests/integration/test_voice_service.py | 7 | 7/7 | 4.03s |
| 6 | 端到端测试 | tests/e2e/test_full_flow.py | 2 | 2/2 | 7.09s |
| 7 | ASR→NLU→日历三级链路 | tests/e2e/test_voice_pipeline.py | 9 | 9/9 | 13.57s |
| 8 | 语音准确率测试 | tests/voice/test_accuracy.py | 1 | ⬜ 文件不存在 | - |
| 9 | 性能测试 | tests/performance/test_response_time.py | 2 | ⬜ 文件不存在 | - |
| 10 | 前端手动测试 | 浏览器操作验证 | 30 | ⬜ 待验证 | 手动 |

**已实现自动化测试：26 个，全部通过。前端手动测试：30 项待验证。**

---

## 1. 集成测试 - 语音识别（7 个）

**测试环境：** Python 3.11 / pytest 9.0.3 / 百度 ASR / 音频来自 `D:\Desktop\Voice-Driven-Calendar_VoiceTest\`

### 测试用例与结果

| # | 测试方法 | 输入 | 预期 | 实际 | 判定 |
|---|----------|------|------|------|------|
| 1 | test_recognize_audio_add_event | 帮我创建一个明天下午三点的团队会议.m4a | 返回文本，含关键词 | "帮我创建一个，明天下午三点的团队**回忆**。" | ✅ |
| 2 | test_recognize_audio_query_events | 今天有什么安排.m4a | 返回文本，含"安排" | "今天有什么安排？" | ✅ |
| 3 | test_recognize_audio_delete_event | 取消明天上午的会议.m4a | 返回文本，含"取消"或"会议" | "取消明天上午的会议。" | ✅ |
| 4 | test_recognize_audio_silence | 空白录音.m4a | 抛出 Exception | 3301 - speech quality error | ✅ |
| 5 | test_recognize_audio_data_returns_string | 1秒静音 PCM | 抛异常或返回空文本 | 返回空文本 | ✅ |
| 6 | test_upload_endpoint_recognizes_text | 今天有什么安排.wav | 状态码 200，text非空 | text="今天有什么安排？" | ✅ |
| 7 | test_upload_endpoint_returns_correct_format | 空 bytes WAV | 状态码 200，含 text 和 confidence | text="识别失败: ..." | ✅ |

### 测试输出

```
tests/integration/test_voice_service.py::TestVoiceServiceFileRecognition::test_recognize_audio_add_event PASSED
tests/integration/test_voice_service.py::TestVoiceServiceFileRecognition::test_recognize_audio_query_events PASSED
tests/integration/test_voice_service.py::TestVoiceServiceFileRecognition::test_recognize_audio_delete_event PASSED
tests/integration/test_voice_service.py::TestVoiceServiceFileRecognition::test_recognize_audio_silence PASSED
tests/integration/test_voice_service.py::TestVoiceServiceAudioData::test_recognize_audio_data_returns_string PASSED
tests/integration/test_voice_service.py::TestVoiceAPIEndpoint::test_upload_endpoint_recognizes_text PASSED
tests/integration/test_voice_service.py::TestVoiceAPIEndpoint::test_upload_endpoint_returns_correct_format PASSED

7 passed, 15 warnings in 4.03s
```

### 识别准确率

| 指标 | 结果 |
|------|------|
| 有效语音识别成功率 | 3/3（100%） |
| 完全准确率 | 2/3（66.7%） |
| 同音字偏差 | 1/3（"会议" → "回忆"，百度 ASR 偏差） |
| 空白录音误识别率 | 0%（正确返回错误） |

---

## 2. ASR → NLU 链路测试（4 + 3 + 1 个用例）

**测试环境：** 百度 ASR + DeepSeek (deepseek-chat) / HTTP API 调用

### /parse 端点（直接传文本）

| # | 输入文本 | 期望 intent | 实际 intent | 实际 title | 实际 time | 判定 |
|---|----------|------------|-------------|------------|-----------|------|
| 1 | 帮我创建一个明天下午三点的团队会议 | add_event | add_event | 团队会议 | 2026-05-31T15:00:00 | ✅ |
| 2 | 今天有什么安排 | query_events | query_events | （空） | 2026-05-30T00:00:00 | ✅ |
| 3 | 取消明天上午的会议 | delete_event | delete_event | 会议 | 2026-05-31T00:00:00 | ✅ |
| 4 | （空字符串） | unknown | unknown | （空） | null | ✅ |

### 完整链路 ASR → NLU

| # | 音频文件 | ASR 输出 | NLU intent | NLU title | 判定 |
|---|----------|----------|------------|-----------|------|
| 1 | 帮我创建一个明天下午三点的团队会议.m4a | 帮我创建一个，明天下午三点的团队回忆。 | add_event | **团队会议**（同音字已纠正） | ✅ |
| 2 | 今天有什么安排.m4a | 今天有什么安排？ | query_events | （空） | ✅ |
| 3 | 取消明天上午的会议.m4a | 取消明天上午的会议。 | delete_event | 会议 | ✅ |

### /parse 返回格式验证

| 验证字段 | 判定 |
|----------|------|
| intent, title, time, reminder, reminder_minutes, description 6 字段齐全 | ✅ |

### 同音字纠正

| ASR 原始 | NLU 纠正 | 生效 |
|----------|----------|------|
| 团队**回忆** | 团队**会议** | ✅ |

> NLU prompt 中配置了同音字映射表（回忆/会意/回议 → 会议），DeepSeek 正确执行了纠正。

---

## 3. 端到端测试 - 语音到日历（2 个）

**测试环境：** pytest + FastAPI TestClient / SQLite 测试实例（每个测试独立数据库）

### test_voice_to_event_flow（语音添加事件）

| 步骤 | 操作 | 输入 | 输出 | 判定 |
|------|------|------|------|------|
| 1 | ffmpeg 转码 | 帮我创建一个明天上午10点的周会.m4a | 16kHz WAV | ✅ |
| 2 | ASR 识别 | WAV | "帮我创建一个，明天上午十点的周会。" | ✅ |
| 3 | NLU 解析 | ASR 文本 | intent=add_event, title=周会, time=2026-05-31T10:00:00 | ✅ |
| 4 | 执行创建 | NLUResponse | "已添加事件：周会", id=1 | ✅ |
| 5 | 验证 | GET /api/events | events 中含"周会" | ✅ |

### test_query_and_delete_flow（语音查询+删除）

| 步骤 | 操作 | 输入 | 输出 | 判定 |
|------|------|------|------|------|
| 0 | 前置 | 语音添加"周会" | 事件创建成功 | ✅ |
| 1 | ASR 查询 | 今天有什么安排.m4a | "今天有什么安排？" | ✅ |
| 2 | NLU 解析 | ASR 文本 | intent=query_events, time=2026-05-30T00:00:00 | ✅ |
| 3 | 执行查询 | NLUResponse | "该时间段没有事件"（今天无事件） | ✅ |
| 4 | ASR 删除 | 取消明天上午的周会.m4a | "取消明天上午的周会。" | ✅ |
| 5 | NLU 解析 | ASR 文本 | intent=delete_event, title=周会 | ✅ |
| 6 | 执行删除 | NLUResponse | "已删除事件：周会", id=1 | ✅ |
| 7 | 验证 | GET /api/events | events 中不含"周会" | ✅ |

### 测试输出

```
tests/e2e/test_full_flow.py::TestFullFlow::test_voice_to_event_flow PASSED
tests/e2e/test_full_flow.py::TestFullFlow::test_query_and_delete_flow PASSED

2 passed, 14 warnings in 7.09s
```

---

## 4. 语音三级链路测试（9 个）

**测试环境：** pytest + FastAPI TestClient / 百度 ASR + DeepSeek

### Level 1：录音 → ASR 文本（3 个）

| # | 测试方法 | 音频文件 | ASR 输出 | 断言 | 判定 |
|---|----------|----------|----------|------|------|
| 1 | test_asr_recognizes_add_event | 帮我创建一个明天上午10点的周会.m4a | 帮我创建一个，明天上午十点的周会。 | 含"周会" | ✅ |
| 2 | test_asr_recognizes_query | 今天有什么安排.m4a | 今天有什么安排？ | 含"安排" | ✅ |
| 3 | test_asr_recognizes_delete | 取消明天上午的周会.m4a | 取消明天上午的周会。 | 含"取消"或"周会" | ✅ |

### Level 2：录音 → ASR → NLU（3 个）

| # | 测试方法 | ASR 输出 | NLU intent | NLU title | 判定 |
|---|----------|----------|------------|-----------|------|
| 4 | test_nlu_parses_add_event | 帮我创建一个，明天上午十点的周会。 | add_event | 周会 | ✅ |
| 5 | test_nlu_parses_query | 今天有什么安排？ | query_events | （空） | ✅ |
| 6 | test_nlu_parses_delete | 取消明天上午的周会。 | delete_event | 周会 | ✅ |

### Level 3：录音 → ASR → NLU → 日历操作（3 个）

| # | 测试方法 | 操作 | 验证方式 | 判定 |
|---|----------|------|----------|------|
| 7 | test_voice_add_event | 语音添加事件 | GET /events 含"周会" | ✅ |
| 8 | test_voice_query_event | 语音查询事件 | 返回消息含"事件" | ✅ |
| 9 | test_voice_delete_event | 语音删除事件 | GET /events 不含"周会" | ✅ |

### 测试输出

```
tests/e2e/test_voice_pipeline.py::TestVoiceToASR::test_asr_recognizes_add_event PASSED
tests/e2e/test_voice_pipeline.py::TestVoiceToASR::test_asr_recognizes_query PASSED
tests/e2e/test_voice_pipeline.py::TestVoiceToASR::test_asr_recognizes_delete PASSED
tests/e2e/test_voice_pipeline.py::TestVoiceToNLU::test_nlu_parses_add_event PASSED
tests/e2e/test_voice_pipeline.py::TestVoiceToNLU::test_nlu_parses_query PASSED
tests/e2e/test_voice_pipeline.py::TestVoiceToNLU::test_nlu_parses_delete PASSED
tests/e2e/test_voice_pipeline.py::TestVoiceToCalendar::test_voice_add_event PASSED
tests/e2e/test_voice_pipeline.py::TestVoiceToCalendar::test_voice_query_event PASSED
tests/e2e/test_voice_pipeline.py::TestVoiceToCalendar::test_voice_delete_event PASSED

9 passed, 45 warnings in 13.57s
```

---

## 5. 实时语音测试（手动）

**测试方式：** `live_test.py` / 麦克风实时录音 / 静音检测（1.5秒静音自动截断）

| # | 用户说话 | 预期 intent | 预期执行结果 | 判定 |
|---|----------|------------|-------------|------|
| 1 | 帮我创建一个明天下午3点的团队会议 | add_event | 已添加事件 | ✅ |
| 2 | 今天有什么安排 | query_events | 查询结果 | ✅ |
| 3 | 取消明天的会议 | delete_event | 已删除事件 | ✅ |

> 实时测试结果受环境噪音、麦克风质量、网络延迟影响，每次可能不同。

### 测试输出示例

```
========================================
  语音日历助手 - 实时测试
========================================
按 Ctrl+C 停止
────────────────────────────────────────
  [ASR]  帮我创建一个，明天下午3点的团队会议。
  [NLU]  intent=add_event, title=团队会议, time=2026-05-31T15:00:00
  [执行] 已添加事件：团队会议
────────────────────────────────────────
继续说话，或按 Ctrl+C 停止...
```

---

## 6. Warnings 汇总

| 类型 | 数量 | 说明 | 影响 |
|------|------|------|------|
| PydanticDeprecatedSince20 | 1 | Settings class-based config，Pydantic V3 将移除 | 无 |
| InsecureRequestWarning | 1 | 测试客户端未验证 HTTPS | 无 |
| StarletteDeprecationWarning | 1 | httpx 与 starlette.testclient 兼容性 | 无 |
| DeprecationWarning (on_event) | 3 | FastAPI on_event 已废弃 | 无 |
| DeprecationWarning (timeout) | 3 | TestClient 不应使用 timeout | 无 |

---
[toolu_vrtx_01So1Tco4...] ## 7. 前端手动测试（2026-05-31）

### 测试环境

- 浏览器：Chrome / Edge（需支持 MediaRecorder）
- 访问地址：`http://localhost:8000`（必须 localhost，安全上下文）
- 服务器：`uv run python main.py --api`

### 测试数据

数据库预注入 8 条测试事件用于验证前端显示：

| id | 日期 | 时间 | 标题 | 描述 |
|----|------|------|------|------|
| 1 | 2026-05-31 | 09:00-10:00 | 团队晨会 | 每日站会，同步进度 |
| 2 | 2026-05-31 | 14:00-16:00 | 项目评审 | Q2 项目阶段性评审 |
| 3 | 2026-05-31 | 19:00 | 晚餐聚会 | 团队聚餐，老地方见 |
| 4 | 2026-06-01 | 10:00-11:30 | 产品需求讨论 | 讨论下季度产品路线图 |
| 5 | 2026-06-03 | 15:00-17:00 | 技术分享会 | 分享微服务架构实践经验 |
| 6 | 2026-06-05 | 09:00-18:00 | 团建活动 | 全员户外拓展训练 |
| 7 | 2026-06-10 | 08:00-09:00 | 牙医预约 | 年度口腔检查 |
| 8 | 2026-05-28 | 10:00-11:00 | 月度总结 | 5月工作总结与6月规划 |

### 测试数据注入命令

```bash
uv run python -c "
import sys
sys.path.insert(0, 'src')
from voice_calendar_agent.config import Settings
from voice_calendar_agent.backend.models.database import init_db, get_db_session
from voice_calendar_agent.backend.models.event import Event
from datetime import datetime

settings = Settings()
init_db(settings.DATABASE_URL)
db = get_db_session()

events = [
    Event(title='团队晨会', description='每日站会，同步进度', start_time=datetime(2026,5,31,9,0), end_time=datetime(2026,5,31,10,0), reminder=True, reminder_minutes=15),
    Event(title='项目评审', description='Q2 项目阶段性评审', start_time=datetime(2026,5,31,14,0), end_time=datetime(2026,5,31,16,0), reminder=True, reminder_minutes=30),
    Event(title='晚餐聚会', description='团队聚餐，老地方见', start_time=datetime(2026,5,31,19,0), reminder=True, reminder_minutes=60),
    Event(title='产品需求讨论', description='讨论下季度产品路线图', start_time=datetime(2026,6,1,10,0), end_time=datetime(2026,6,1,11,30), reminder=True, reminder_minutes=15),
    Event(title='技术分享会', description='分享微服务架构实践经验', start_time=datetime(2026,6,3,15,0), end_time=datetime(2026,6,3,17,0), reminder=True, reminder_minutes=15),
    Event(title='团建活动', description='全员户外拓展训练', start_time=datetime(2026,6,5,9,0), end_time=datetime(2026,6,5,18,0), reminder=True, reminder_minutes=1440),
    Event(title='牙医预约', description='年度口腔检查', start_time=datetime(2026,6,10,8,0), end_time=datetime(2026,6,10,9,0), reminder=True, reminder_minutes=60),
    Event(title='月度总结', description='5月工作总结与6月规划', start_time=datetime(2026,5,28,10,0), end_time=datetime(2026,5,28,11,0), reminder=False),
]
for e in events:
    db.add(e)
db.commit()
db.close()
print('Inserted 8 test events')
"
```

### 前端功能验证清单

| # | 测试项 | 操作 | 预期结果 | 状态 |
|---|--------|------|----------|------|
| 1 | 页面加载 | 打开 `http://localhost:8000` | 玻璃态日历居中，当前月份，今天高亮 | ⬜ |
| 2 | 事件圆点 | 查看日历日期格子 | 5/28、5/31、6/1、6/3、6/5、6/10 有蓝色小圆点 | ⬜ |
| 3 | 今天多事件 | 查看 5/31 格子 | 3 个圆点（团队晨会、项目评审、晚餐聚会） | ⬜ |
| 4 | 实时时钟 | 查看底部中央 | 显示当前时间，每秒更新 | ⬜ |
| 5 | 鼠标滚轮切月 | 在日历上滚动滚轮 | 月份切换，带滑动动画，事件重新加载 | ⬜ |
| 6 | 3D 倾斜 | 鼠标在日历上移动 | 日历跟随鼠标方向倾斜 | ⬜ |
| 7 | 点击日期 → 日程模式 | 点击 5/31 | 日历缩小左移，右侧滑入日程面板，列出 3 条事件 | ⬜ |
| 8 | 日程模式切换日期 | 点击 6/5 | 面板切换为团建活动信息 | ⬜ |
| 9 | 日程模式返回 | 点击背景空白区域 | 日历恢复居中，面板滑出 | ⬜ |
| 10 | 录音模式 | Home 状态点击背景 | 出现红色呼吸边框动画 | ⬜ |
| 11 | 停止录音 | Recording 状态再次点击背景 | 停止录音，触发全链路，返回 Home | ⬜ |
| 12 | 日程模式禁录音 | Schedule 状态点击背景 | 直接返回 Home，不触发录音 | ⬜ |
| 13 | 麦克风安全提示 | 非 localhost 访问时点击录音 | Toast 提示"请通过 localhost 访问" | ⬜ |
| 14 | 移动端触屏 | 手机上左右滑动日历 | 月份切换 | ⬜ |
| 15 | API 错误处理 | 停止后端后操作 | Toast 提示"无法连接服务" | ⬜ |
| 16 | 默认渐变背景 | 打开页面查看背景 | 左下→右上 紫色(#BC95C6)→青色(#7DC4CC) 渐变 | ⬜ |
| 17 | 特殊日期标签 | 查看 5/1（劳动节）、6/19（端午节） | 日期格显示彩色标签（红色=节日，绿色=节气） | ⬜ |
| 18 | 农历日期显示 | 查看非特殊日期（如 5/6） | 日期格显示农历日期（如"初十"） | ⬜ |
| 19 | 节日>农历优先级 | 查看 5/1（劳动节+农历） | 显示"劳动节"标签，不显示农历 | ⬜ |
| 20 | 红点事件数 | 查看 5/31 | 日期格显示红色圆形徽标"3" | ⬜ |
| 21 | 悬停特殊日期背景 | 鼠标悬停 5/1（劳动节） | 背景平滑切换为劳动节图片，0.6s 过渡 | ⬜ |
| 22 | 悬停非特殊日期 | 鼠标悬停非特殊日期 | 背景恢复默认渐变 | ⬜ |
| 23 | 点击进入详情切换背景 | 点击 5/1（劳动节） | 日程面板滑入+背景同步切换为劳动节 | ⬜ |
| 24 | 返回主页恢复背景 | 日程模式点击背景返回 | 背景恢复默认渐变 | ⬜ |
| 25 | 当天自动显示背景 | 若今天为特殊日期时打开页面 | 自动显示对应背景图，无需悬停 | ⬜ |
| 26 | 背景图加载失败回退 | 访问缺失国庆节图的 10/1 | 静默回退到默认渐变，无破损图标 | ⬜ |
| 27 | 日程详情农历 | 点击任意日期进入详情 | 面板显示"农历X月Y日"完整信息 | ⬜ |
| 28 | 数字对齐 | 检查多个月份的所有日期格 | 所有日期数字严格垂直居中，无高低偏移 | ⬜ |
| 29 | 图片无误加载 | 查看 5/1 劳动节、6/19 端午节 | 图片正常显示，无 404 | ⬜ |
| 30 | 移动端适配 | 手机浏览器打开页面 | 日历大小自适应，触屏切月正常 | ⬜ |

### 已知问题

- **国庆节.png 缺失**：`static/images/jieri/` 目录中缺少 `国庆节.png`，10月1日背景将回退到默认渐变

### API 验证命令

```bash
# 验证 5 月事件（应返回 4 条：5/28 月度总结 + 5/31 三事件）
curl -s "http://localhost:8000/api/events?date=2026-05-01&range=month" | python -m json.tool

# 验证 6 月事件（应返回 4 条）
curl -s "http://localhost:8000/api/events?date=2026-06-01&range=month" | python -c "import sys,json; d=json.load(sys.stdin); print(f'total={d[\"total\"]}')"

# 验证 5/31 当天事件（应返回 3 条）
curl -s "http://localhost:8000/api/events?date=2026-05-31&range=day" | python -m json.tool
```

### 已知问题

| # | 问题 | 影响 | 处理 |
|---|------|------|------|
| 1 | `data/calendar.db` 被分支跟踪 | git checkout 时可能覆盖数据库 | `.gitignore` 已加 `*.db`，下次提交后生效 |
| 2 | 录音需 `localhost` 访问 | 局域网 IP 无法使用麦克风 | `startRecording()` 已加安全上下文检查并提示 |
| 3 | 非 Chrome/Edge 浏览器 | MediaRecorder 可能不支持 | 已加 `window.MediaRecorder` 检查 |

---

## 8. 测试命令

```bash
uv run pytest tests/ -v                          # 运行全部测试
uv run pytest tests/unit/ -v                     # 单元测试
uv run pytest tests/integration/ -v              # 集成测试
uv run pytest tests/e2e/ -v                      # 端到端测试
uv run pytest --cov=src --cov-report=html        # 覆盖率报告
```