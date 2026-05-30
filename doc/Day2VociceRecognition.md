#   Day2实现语音API接口的方案总结
##  需要实现的内容
###  组件	实现内容
config.py	将 BAIDU_* 重命名为通用命名 ASR_APP_ID / ASR_API_KEY / ASR_SECRET_KEY，新增 ASR_PROVIDER 配置项（值为 baidu 或 xunfei）  
voice_service.py	实现百度语音识别（HTTP API）+ 讯飞语音识别（WebSocket API），通过配置切换  
voice.py	实现 /upload（文件识别）和 /stream（WebSocket 中转实时识别）端点  
.env.example	同步更新配置字段名  
pyproject.toml	新增 websocket-client 依赖（讯飞 WebSocket API 需要）  
##  不修改的内容
所有现有注释不动
函数签名和输入输出格式不动
nlu_service.py、calendar_service.py 等其他文件不动
Vosk 相关代码保持 stub
##  关键技术点
百度：使用 baidu-aip SDK 的 AipSpeech.asr() 方法，发送完整音频 bytes
讯飞：使用 WebSocket 协议，需要 HMAC-SHA256 签名鉴权，将音频分片发送
通用配置：ASR_APP_ID、ASR_API_KEY、ASR_SECRET_KEY 三个字段，百度和讯飞共用
/stream 端点：客户端 WebSocket → 我们的 FastAPI → 讯飞 WebSocket API → 结果原路返回
配置示例（.env）

### 使用百度
ASR_PROVIDER=baidu  
ASR_APP_ID=你的百度APP_ID  
ASR_API_KEY=你的百度API_KEY  
ASR_SECRET_KEY=你的百度SECRET_KEY  

### 使用讯飞
ASR_PROVIDER=xunfei  
ASR_APP_ID=讯飞APPID  
ASR_API_KEY=讯飞APIKey  
ASR_SECRET_KEY=讯飞APISecret  


# 语音识别功能 - 测试用例分析

## 1. 相关测试用例总览

测试文档中涉及语音识别功能的测试分布在 3 个区域：

| 区域 | 文件路径 | 测试方法数 | 当前状态 |
|------|----------|-----------|----------|
| 4.2 语音识别集成测试 | `tests/integration/test_voice_service.py` | 2 | 文件不存在 |
| 5.1 端到端测试 | `tests/e2e/test_full_flow.py` | 1（间接） | 存在，方法体为 `pass` |
| 6 语音识别准确率测试 | `tests/voice/test_accuracy.py` | 1 | 文件不存在 |

---

## 2. 语音识别集成测试（第 4.2 节）

### 2.1 fixture 定义

```python
@pytest.fixture
def voice_service(self):
    model_path = os.getenv("VOSK_MODEL_PATH", "models/vosk/vosk-model-small-cn-0.22")
    return VoiceService(model_path)
```

> **注意**：fixture 将 `model_path` 字符串作为位置参数传给 `VoiceService()`，但当前 `__init__` 签名为 `VoiceService(mode, baidu_app_id, baidu_api_key, baidu_secret_key, vosk_model_path)`，第一个参数是 `mode: ASRMode`。此处存在签名不匹配问题。

### 2.2 测试方法详情

#### test_recognize_audio_file

| 项目 | 内容 |
|------|------|
| 目的 | 测试识别音频文件功能 |
| 输入 | 音频文件路径 `tests/fixtures/test_audio.wav` |
| 调用方法 | `VoiceService.recognize_file(audio_path)` |
| 断言 1 | `isinstance(result, str)` — 返回值必须是字符串类型 |
| 断言 2 | `len(result) > 0` — 返回值不能为空字符串 |
| 前置条件 | 测试音频文件存在（不存在则跳过） |

#### test_real_time_recognition

| 项目 | 内容 |
|------|------|
| 目的 | 测试实时语音识别 |
| 前置条件 | Vosk 模型文件存在 |
| 跳过条件 | `models/vosk/vosk-model-small-cn-0.22` 目录不存在时 `@pytest.mark.skipif` |
| 当前实现 | `pass`（需要手动验证） |

---

## 3. 语音识别准确率测试（第 6 节）

### 3.1 测试数据集

```python
VOICE_TEST_CASES = [
    {
        "input_audio": "test_add_meeting.wav",
        "expected_text": "帮我创建一个明天下午3点的团队会议",
        "expected_intent": "add_event",
        "expected_title": "团队会议"
    },
    {
        "input_audio": "test_query_today.wav",
        "expected_text": "今天有什么安排",
        "expected_intent": "query_events"
    },
    {
        "input_audio": "test_delete_meeting.wav",
        "expected_text": "取消明天的会议",
        "expected_intent": "delete_event"
    }
]
```

### 3.2 测试流程

| 步骤 | 操作 | 输出 |
|------|------|------|
| 1 | `voice_service.recognize_file(case["input_audio"])` | 识别文本 `text` |
| 2 | `nlu_service.parse_command(text)` | 结构化结果 `result`（dict） |
| 3 | 比较 `result["intent"]` 与 `case["expected_intent"]` | 是否匹配 |

### 3.3 通过条件

| 意图类型 | 匹配逻辑 |
|----------|----------|
| `add_event` | `result["intent"] == "add_event"` **且** `case["expected_title"] in result.get("title", "")` |
| 其他意图 | `result["intent"] == case["expected_intent"]` |
| 准确率 | `correct / total >= 0.7`（70%） |

---

## 4. 端到端测试（第 5 节，间接相关）

### 4.1 test_voice_to_event_flow

| 步骤 | 操作 | 说明 |
|------|------|------|
| 1 | `voice_text = "帮我创建一个明天下午3点的团队会议"` | 语音识别被跳过，直接使用文本 |
| 2 | 调用 NLU 解析（使用 mock） | NLU 服务被 mock |
| 3 | `POST /api/events` 创建事件 | 断言 `status_code == 201` |
| 4 | `GET /api/events` 验证事件存在 | 断言标题匹配 |

> **关键观察**：端到端测试中语音识别被 mock 掉，不直接测试 `VoiceService`，仅验证下游链路。

### 4.2 test_query_and_delete_flow

与语音识别无直接关联，不涉及 `VoiceService`。

---

## 5. 语音识别功能需要满足的通过条件

### 5.1 recognize_file(audio_path: str) -> str

| # | 条件 | 来源 |
|---|------|------|
| 1 | 接受文件路径字符串作为输入参数 | `test_recognize_audio_file` |
| 2 | 返回值必须是 `str` 类型 | `assert isinstance(result, str)` |
| 3 | 返回值不能为空字符串 | `assert len(result) > 0` |
| 4 | 读取音频文件并调用 ASR API 执行识别 | `test_recognize_audio_file` |
| 5 | 识别文本应尽可能准确，使 NLU 能解析出正确意图 | `test_recognition_accuracy` |

### 5.2 recognize_audio_data(audio_data: bytes) -> str

测试文档中未直接测试此方法，但 `voice.py` 的 `/upload` 端点会调用它：

| # | 条件 | 来源 |
|---|------|------|
| 1 | 接受 PCM/WAV 格式的 bytes 数据 | `voice.py` upload 端点 |
| 2 | 返回 str 类型的识别文本 | 与 `recognize_file` 一致 |

### 5.3 VoiceService 构造函数

| # | 条件 | 来源 |
|---|------|------|
| 1 | `VoiceService(model_path)` 能正常构造 | `voice_service` fixture |

---

## 6. 可能的失败原因

| # | 失败场景 | 原因 | 影响的测试 |
|---|----------|------|------------|
| 1 | fixture 构造崩溃 | fixture 传 `VoiceService(model_path)` 但 `__init__` 第一个参数是 `mode: ASRMode` | `test_recognize_audio_file` |
| 2 | 百度 API 鉴权失败 | `.env` 中凭证为空，调用 SDK 时抛异常 | `test_recognize_audio_file` |
| 3 | 网络不可达 | 无网络或 API 地址不可达，SDK 超时或抛连接异常 | `test_recognize_audio_file` |
| 4 | 音频格式不符 | 百度 API 要求 PCM/WAV/AMR，采样率 16000；测试文件不满足则识别失败 | `test_recognize_audio_file`、`test_recognition_accuracy` |
| 5 | 讯飞 WebSocket 鉴权失败 | HMAC-SHA256 签名逻辑错误导致连接被拒 | `/stream` 端点 |
| 6 | 异常未处理返回空串 | 识别失败时 `return ""`，违反 `len(result) > 0` | `test_recognize_audio_file` |
| 7 | 返回值类型错误 | 实现返回 dict 而非 str，`isinstance` 断言失败 | `test_recognize_audio_file` |
| 8 | 准确率不达标 | 识别结果偏差大，NLU 解析出错误意图，准确率 < 70% | `test_recognition_accuracy` |
| 9 | 测试音频文件缺失 | `tests/fixtures/*.wav` 不存在，测试被跳过不实际验证 | `test_recognize_audio_file`、`test_recognition_accuracy` |

---

## 7. 对实现的约束总结

| # | 约束 | 说明 |
|---|------|------|
| 1 | `recognize_file()` 必须返回非空字符串 | 识别失败时应抛异常或返回错误提示文本（如 `"识别失败"`），不能返回 `""` 或 `None` |
| 2 | 构造函数需兼容测试 fixture 调用方式 | 文档 fixture 写法与当前签名不匹配，需确认修改 fixture 还是调整 `__init__` |
| 3 | 需准备测试音频文件 | `tests/fixtures/test_audio.wav` 及准确率测试的 3 个 WAV 文件 |
| 4 | 异常处理不能静默吞错 | API 调用失败时应抛出有意义的异常，不能返回空字符串 |