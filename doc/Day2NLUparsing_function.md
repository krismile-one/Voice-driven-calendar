# Day 2 - NLU 解析功能开发记录

> 说明：日期编号按需调整。本记录对应 NLU（自然语言理解）解析服务的实现。

## 一、功能概述

实现语音日历助手的 NLU 解析功能：把语音识别出的自然语言文本，转换成结构化的日历操作指令（增/删/查），并由大模型直接输出 ISO 绝对时间。

### 已实现功能

- NLU 解析服务 `parse_command`，把口语文本解析为结构化指令
- 支持 OpenAI 格式（DeepSeek / Mimo 等）与 Anthropic 格式（Claude），通过配置切换
- 大模型直接输出 ISO8601 绝对时间（以当前时间为锚点换算"明天/下周三/三点一刻"等）
- 结构化输出：`intent / title / time / reminder / reminder_minutes / description`
- 健壮的响应解析：去除 ```` ``` ```` 代码块包裹、正则提取 JSON、补默认值
- 异常兜底：模型返回非法内容时降级为 `intent=unknown`，不崩溃
- 单元测试（mock 模型返回，4 个用例全部通过）

---

## 二、实现方案

### 2.1 修改文件清单

| 文件 | 路径 | 修改内容 |
|------|------|----------|
| nlu_service.py | `src/voice_calendar_agent/backend/core/nlu_service.py` | 实现 NLUService 全部方法 |
| test_nlu_service.py | `tests/unit/test_nlu_service.py` | 填充 4 个单元测试（mock 模型） |
| test_nlu.py | `（项目根目录）` | 新增真 API 手动测试脚本（可选） |

### 2.2 配置说明

NLU 复用已有的 `LLM_*` 配置字段（与 ASR 的 `ASR_*` 相互独立）：

```
LLM_PROVIDER   →  openai | anthropic（DeepSeek/Mimo 走 openai 格式）
LLM_API_KEY    →  大模型 API 密钥
LLM_MODEL      →  模型名（如 deepseek-chat）
LLM_BASE_URL   →  API 基础地址（openai 兼容时用，如 https://api.deepseek.com）
```

### 2.3 依赖变更

无新增依赖。NLU 使用的 `openai`、`anthropic`、`httpx` 在基础依赖中已存在。

### 2.4 关键技术点

- **供应商分流**：`LLMProvider` 枚举 + `_init_client()` 懒加载，按 `provider` 只建一个客户端
- **时间锚点**：`_build_prompt()` 用 `datetime.now()` 取当前时间注入提示词，模型据此把相对/口语时间换算成 ISO 绝对时间（模型自身没有可靠实时时钟，必须由代码提供"现在")
- **强制 JSON 输出**：提示词要求只输出 JSON、不带解释；`temperature=0` 保证稳定
- **健壮解析**：`_parse_response()` 去 ```` ``` ```` 包裹 → 正则取第一个 `{...}` → `json.loads` → 补默认值
- **兜底**：`parse_command()` 全程 try/except，异常返回 `intent=unknown` 的稳定结构

---

## 三、运行逻辑

### 3.1 整体架构

```
                        ┌──────────────┐
                        │   .env 配置   │
                        │ LLM_PROVIDER │
                        │ LLM_API_KEY  │
                        │ LLM_MODEL    │
                        │ LLM_BASE_URL │
                        └──────┬───────┘
                               │ 读取
                               ▼
   识别出的文字 ──────▶ ┌─────────────────┐
   "明天下午三点开会"    │   NLUService    │
                       │  parse_command  │
                       └────────┬────────┘
                                │
              ┌─────────────────┼──────────────────┐
              ▼                 ▼                  ▼
        _build_prompt    _call_openai /      _parse_response
        (注入当前时间)    _call_anthropic     (解析 JSON + 兜底)
                                │
                       ┌────────┴────────┐
                       ▼                 ▼
                 OpenAI 格式 API     Anthropic API
                 (DeepSeek/Mimo)       (Claude)
                                │
                                ▼
              结构化 dict {intent, title, time(ISO), reminder, ...}
```

### 3.2 初始化流程

```
1. 上层（API / 终端）用 Settings 的 LLM_* 字段构造 NLUService
   NLUService(provider, api_key, model, base_url)
2. 首次调用 parse_command 时触发 _init_client()
   ├── provider == "anthropic" → Anthropic(api_key)
   └── provider == "openai"    → OpenAI(api_key, base_url)   # base_url 为空则用默认
3. 客户端缓存在 self._client，后续复用
```

### 3.3 parse_command 流程

```
parse_command(text)
├── 文本为空 → 直接返回 intent=unknown 的默认结构
├── _init_client()                      → 懒加载客户端
├── _build_prompt(text)                 → 拼提示词（含当前时间锚点）
├── 按 provider 分流
│   ├── anthropic → _call_anthropic(prompt)
│   └── openai    → _call_openai(prompt)
├── _parse_response(raw)                → 解析模型返回的 JSON 文本
└── 异常 → 捕获并返回 intent=unknown（不抛出，保证稳定）
```

### 3.4 时间解析机制

```
代码取当前时间 datetime.now()
        ↓ 写进提示词："当前时间是 2026-05-30T..（周六）"
模型据此换算
        ↓ "明天下午三点一刻" → "2026-05-31T15:15:00"
返回 time 字段（ISO 字符串）
        ↓ 交给下游 / time_parser 转成 datetime 对象
```

> 设计要点：NLU 只负责"算出"绝对时间（产出 ISO **字符串**）；把字符串转成 `datetime` **对象** 由 `time_parser` 负责。

### 3.5 供应商切换机制

```
.env:
  LLM_PROVIDER=openai     → _call_openai  （DeepSeek / Mimo）
  LLM_PROVIDER=anthropic  → _call_anthropic（Claude）

切换只改 .env，代码无需改动；两条调用路径输出都归一到 _parse_response。
```

### 3.6 返回格式契约（与协作者对接的关键）

`parse_command` 固定返回以下结构，供下游（time_parser / calendar_service）消费：

```json
{
    "intent": "add_event",              // add_event/delete_event/update_event/query_events/unknown
    "title": "开会",                     // 删除/查询时为关键词，可为空串
    "time": "2026-05-31T15:15:00",      // ISO 绝对时间字符串，可能为 null
    "reminder": true,                   // 是否提醒
    "reminder_minutes": 30,             // 提前提醒分钟数
    "description": ""                   // 备注，可为空串
}
```

> **重点：`time` 已是 ISO 绝对时间**，下游直接 `datetime.fromisoformat(time)` 转换即可，无需再解析中文。

---

## 四、调用说明

### 4.1 配置 .env

```env
# 用 DeepSeek
LLM_PROVIDER=openai
LLM_API_KEY=你的DeepSeek密钥
LLM_MODEL=deepseek-chat
LLM_BASE_URL=https://api.deepseek.com

# 用 Claude
LLM_PROVIDER=anthropic
LLM_API_KEY=你的Anthropic密钥
LLM_MODEL=（当前 Claude 模型名）
```

### 4.2 直接调用 NLUService（不通过 API）

```python
from voice_calendar_agent.backend.core.nlu_service import NLUService

nlu = NLUService(
    provider="openai",
    api_key="你的密钥",
    model="deepseek-chat",
    base_url="https://api.deepseek.com",
)

result = nlu.parse_command("明天下午3点一刻开会，提前半小时提醒我")
print(result)
```

### 4.3 返回示例

```json
{
    "intent": "add_event",
    "title": "开会",
    "time": "2026-05-31T15:15:00",
    "reminder": true,
    "reminder_minutes": 30,
    "description": ""
}
```

---

## 五、测试用例

### 5.1 单元测试方法（mock 模型返回，不联网、不花钱）

| 测试方法 | mock 的模型返回 | 预期结果 |
|----------|----------------|----------|
| test_parse_add_event | add_event 的 JSON | intent=add_event、title=开会、time 为 ISO、reminder_minutes=30 |
| test_parse_query_events | query_events 的 JSON | intent=query_events、time 为当天 ISO |
| test_parse_delete_event | delete_event 的 JSON（time=null） | intent=delete_event、title=会议 |
| test_parse_invalid_returns_unknown | 非法字符串 | intent=unknown（兜底，不崩溃） |

> 测试用 `@patch.object(NLUService, "_call_openai")` 把模型调用替换为假返回，因此**只验证解析逻辑**，不依赖真实模型/密钥。

### 5.2 运行测试

```bash
# 首次需安装 dev 依赖（含 pytest）
uv sync --extra dev

# 运行 NLU 单元测试
uv run pytest tests/unit/test_nlu_service.py -v
```

### 5.3 真 API 手动验证（可选，需密钥）

```bash
# .env 配好 LLM_* 后
uv run python test_nlu.py
```

---

## 六、测试结果

测试时间：2026-05-30

### 6.1 单元测试结果

```
collected 4 items
test_parse_add_event ............... PASSED
test_parse_query_events ............ PASSED
test_parse_delete_event ............ PASSED
test_parse_invalid_returns_unknown . PASSED
================= 4 passed in 14.52s =================
```

### 6.2 结果分析

| 指标 | 结果 |
|------|------|
| 单元测试通过率 | 4/4（100%） |
| 解析逻辑正确性 | ✅ 三种意图均正确解析 |
| 健壮性兜底 | ✅ 非法返回降级为 unknown，不崩溃 |
| 是否依赖真实 API | 否（mock），无需密钥即可通过 |

**说明：**
- 14.52s 主要为首次加载 openai/anthropic 等库的启动开销，非测试本身耗时
- 真模型对句子的理解准确性需用 `test_nlu.py` 调真 API 验证（待拿到密钥后补充）

---

## 七、待完善 / 与协作者对接

- [ ] 实现 `time_parser.py`：把 NLU 输出的 ISO 字符串转成 `datetime` 对象 + 兜底
- [ ] 真 API 端到端验证：拿到 DeepSeek/Claude 密钥后跑 `test_nlu.py`，记录真实识别准确率
- [ ] 与上游对接：`voice_service` 识别出的文字 → `parse_command(text)`
- [ ] 与下游对接：`parse_command` 返回的 dict → `calendar_service.add_event(...)`（`time` 已是 ISO，下游直接转 datetime）
- [ ] 多轮对话：支持"把刚才那个会改到四点"这类上下文修改
- [ ] 复述确认：解析结果回显确认后再落库