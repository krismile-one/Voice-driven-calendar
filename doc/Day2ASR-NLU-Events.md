# Day 2 - ASR→NLU→日历操作 全链路开发记录

## 一、开发目标

完成从语音输入到日历操作的完整链路：

```
录音 → ASR → 文本 → NLU → 结构化指令 → CalendarService → 数据库
```

## 二、涉及文件

| 文件 | 修改内容 |
|------|----------|
| `nlu_service.py` | 新增 `get_nlu_service()` 工厂函数；prompt 增加同音字纠正规则 |
| `voice.py` | 修改 `NLUResponse` 模型（删除 `date`，新增 `reminder_minutes`、`description`）；实现 `/parse` 端点 |
| `events.py` | 实现全部 CRUD 端点 + `/execute` 语音指令执行端点 |

未修改：`voice_service.py`、`calendar_service.py`、`config.py`、`time_parser.py`

## 三、关键技术

### 3.1 /parse 端点

接收 ASR 输出的纯文本，调用 `NLUService.parse_command()` 返回结构化 JSON。

```
POST /api/voice/parse?text=帮我创建一个明天下午三点的团队会议

→ {"intent":"add_event", "title":"团队会议", "time":"2026-05-31T15:00:00", ...}
```

### 3.2 同音字纠正

百度 ASR 将"会议"识别为"回忆"，在 NLU prompt 中配置同音字映射表：

```
语音识别可能产生同音字错误，请根据日历场景语义自动修正：
- "回忆""会意""回议" → "会议"
- "周灰""周辉""周惠" → "周会"
```

DeepSeek 根据上下文自动纠正，实测生效。

### 3.3 /execute 端点

接收 NLUResponse，将 ISO8601 时间字符串转为 datetime，根据 intent 分发到 CalendarService。

```
NLU: time="2026-05-31T15:00:00" (str)
  ↓ datetime.fromisoformat()
CalendarService: start_time=datetime(2026, 5, 31, 15, 0, 0)
```

### 3.4 ORM → Pydantic 转换

CalendarService 返回 SQLAlchemy Event 对象，用 `model_validate(event, from_attributes=True)` 转为 EventResponse。

## 四、客户端调用流程

```
Step 1: POST /api/voice/upload    → ASR 识别音频，返回文本
Step 2: POST /api/voice/parse     → NLU 解析文本，返回结构化指令
Step 3: POST /api/events/execute  → 执行指令，返回操作结果
```

三步各司其职：ASR 负责识别，/parse 负责解析，/execute 负责执行。

## 五、测试结果

| 测试 | 用例数 | 通过 | 耗时 |
|------|--------|------|------|
| 单元测试 - NLU 服务 | 4 | 4/4 | 0.89s |
| 单元测试 - 日历服务 | 4 | 4/4 | 0.09s |
| 集成测试 - 语音识别 | 7 | 7/7 | 4.03s |
| 端到端 - 全链路 | 2 | 2/2 | 7.09s |

端到端测试覆盖：

- 语音添加事件：录音 → ASR → NLU → 创建事件 → 验证数据库
- 语音查询 + 删除：前置创建 → 语音查询 → 语音删除 → 验证已删除

## 六、待完善

- [✅] `/execute` 的 `update_event` 分支（当前提示用 REST 接口）
- [✅] `/execute` 的 `delete_event` 按标题模糊匹配的精确度
- [✅] 测试中 NLU 调用真实 API，后续可加 mock 选项