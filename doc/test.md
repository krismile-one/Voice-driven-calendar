# 语音日历助手 - 测试文档

## 0. 测试总览

### 测试进度表

| # | 测试类别 | 测试文件 | 测试数 | 状态 | 耗时 | 通过率 | 最后测试时间 |
|---|----------|----------|--------|------|------|--------|-------------|
| 1 | 单元测试 - 日历服务 | `tests/unit/test_calendar_service.py` | 4 | ⬜ 未实现（stub） | - | - | - |
| 2 | 单元测试 - NLU服务 | `tests/unit/test_nlu_service.py` | 4 | ✅ 已完成 | 0.89s | 4/4(100%) | 2026-05-30 |
| 3 | 单元测试 - 时间解析 | `tests/unit/test_time_parser.py` | 3 | ⬜ 未实现（stub） | - | - | - |
| 4 | 集成测试 - 事件API | `tests/integration/test_api_events.py` | 4 | ⬜ 未实现（stub） | - | - | - |
| 5 | 集成测试 - 语音识别 | `tests/integration/test_voice_service.py` | 7 | ✅ 已完成 | 4.03s | 7/7 (100%) | 2026-05-30 |
| 6 | 端到端测试 | `tests/e2e/test_full_flow.py` | 2 | ⬜ 未实现（stub） | - | - | - |
| 7 | 语音准确率测试 | `tests/voice/test_accuracy.py` | 1 | ⬜ 文件不存在 | - | - | - |
| 8 | 性能测试 | `tests/performance/test_response_time.py` | 2 | ⬜ 文件不存在 | - | - | - |
| 9 | 集成测试 - ASR→NLU链路 | `test_pipeline.py` | 9 | ✅ 已完成 | - | 9/9 (100%) | 2026-05-30 |

**图例：** ✅ 已完成且通过 ｜ ❌ 已完成但有失败 ｜ ⬜ 未实现

### 已执行测试详情（集成测试 - 语音识别）

| # | 测试方法 | 输入 | 判定 |
|---|----------|------|------|
| 1 | test_recognize_audio_add_event | 帮我创建一个明天下午三点的团队会议.m4a | ✅ PASSED |
| 2 | test_recognize_audio_query_events | 今天有什么安排.m4a | ✅ PASSED |
| 3 | test_recognize_audio_delete_event | 取消明天上午的会议.m4a | ✅ PASSED |
| 4 | test_recognize_audio_silence | 空白录音.m4a | ✅ PASSED |
| 5 | test_recognize_audio_data_returns_string | 1 秒静音 PCM | ✅ PASSED |
| 6 | test_upload_endpoint_recognizes_text | 今天有什么安排.wav | ✅ PASSED |
| 7 | test_upload_endpoint_returns_correct_format | 空 bytes WAV | ✅ PASSED |

详细结果见 [第 10 节](#10-语音识别测试记录)。

---

## 1. 测试策略

### 1.1 测试类型

| 测试类型 | 范围 | 工具 | 优先级 |
|----------|------|------|--------|
| 单元测试 | 单个函数/模块 | pytest | P0 |
| 集成测试 | 模块间交互 | pytest + httpx | P0 |
| 端到端测试 | 完整流程 | pytest + 真实调用 | P1 |
| 语音测试 | 语音识别准确率 | 手动 + 自动化 | P1 |

### 1.2 测试覆盖率目标

- 核心业务逻辑：80%+
- API接口：90%+
- 工具函数：90%+

---

## 2. 测试环境

### 2.1 依赖

测试依赖已在 `pyproject.toml` 中配置为开发依赖：

```toml
[project.optional-dependencies]
dev = [
    "pytest>=7.4.3",
    "pytest-asyncio>=0.23.2",
    "pytest-cov>=4.1.0",
    "pytest-mock>=3.12.0",
    "black>=23.12.0",
    "isort>=5.13.0",
    "ruff>=0.1.0",
]
```

### 2.2 安装

```bash
# 安装开发依赖
uv sync --extra dev
```

### 2.3 测试配置

```python
# tests/conftest.py

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.backend.main import app
from src.backend.models.database import Base, get_db

# 测试数据库
TEST_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(TEST_DATABASE_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="function")
def db_session():
    """每个测试函数独立的数据库会话"""
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    yield session
    session.close()
    Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def client(db_session):
    """测试客户端"""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
```

---

## 3. 单元测试

### 3.1 日历服务测试

```python
# tests/unit/test_calendar_service.py

import pytest
from datetime import datetime, timedelta
from src.backend.core.calendar_service import CalendarService

class TestCalendarService:
    def test_add_event(self, db_session):
        """测试添加事件"""
        service = CalendarService(db_session)
        event = service.add_event(
            title="测试会议",
            start_time=datetime.now() + timedelta(days=1)
        )
        assert event.id is not None
        assert event.title == "测试会议"

    def test_delete_event(self, db_session):
        """测试删除事件"""
        service = CalendarService(db_session)
        event = service.add_event(
            title="待删除会议",
            start_time=datetime.now() + timedelta(days=1)
        )
        result = service.delete_event(event.id)
        assert result is True
        assert service.get_events() == []

    def test_get_events_by_date(self, db_session):
        """测试按日期查询事件"""
        service = CalendarService(db_session)
        today = datetime.now()
        tomorrow = today + timedelta(days=1)

        service.add_event(title="今天会议", start_time=today)
        service.add_event(title="明天会议", start_time=tomorrow)

        events = service.get_events(date=today, range="day")
        assert len(events) == 1
        assert events[0].title == "今天会议"

    def test_update_event(self, db_session):
        """测试更新事件"""
        service = CalendarService(db_session)
        event = service.add_event(
            title="原标题",
            start_time=datetime.now()
        )
        updated = service.update_event(event.id, title="新标题")
        assert updated.title == "新标题"
```

### 3.2 NLU服务测试

```python
# tests/unit/test_nlu_service.py

import pytest
from unittest.mock import patch, MagicMock
from src.backend.core.nlu_service import NLUService

class TestNLUService:
    @patch('src.backend.core.nlu_service.OpenAI')
    def test_parse_add_event(self, mock_openai):
        """测试解析添加事件指令"""
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = '''
        {
            "intent": "add_event",
            "title": "团队会议",
            "time": "下午3点",
            "date": "明天"
        }
        '''
        mock_openai.return_value.chat.completions.create.return_value = mock_response

        service = NLUService(api_key="test")
        result = service.parse_command("帮我创建一个明天下午3点的团队会议")

        assert result["intent"] == "add_event"
        assert result["title"] == "团队会议"

    @patch('src.backend.core.nlu_service.OpenAI')
    def test_parse_query_events(self, mock_openai):
        """测试解析查询事件指令"""
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = '''
        {
            "intent": "query_events",
            "date": "今天"
        }
        '''
        mock_openai.return_value.chat.completions.create.return_value = mock_response

        service = NLUService(api_key="test")
        result = service.parse_command("今天有什么安排")

        assert result["intent"] == "query_events"
```

### 3.3 时间解析测试

```python
# tests/unit/test_time_parser.py

import pytest
from datetime import datetime, timedelta
from src.backend.utils.time_parser import TimeParser

class TestTimeParser:
    def test_parse_tomorrow(self):
        """测试解析'明天'"""
        parser = TimeParser()
        result = parser.parse("明天下午3点")
        expected = datetime.now().replace(hour=15, minute=0, second=0) + timedelta(days=1)
        assert result.date() == expected.date()
        assert result.hour == 15

    def test_parse_next_week(self):
        """测试解析'下周'"""
        parser = TimeParser()
        result = parser.parse("下周三上午10点")
        assert result.weekday() == 2  # 周三
        assert result.hour == 10

    def test_parse_today(self):
        """测试解析'今天'"""
        parser = TimeParser()
        result = parser.parse("今天下午5点")
        assert result.date() == datetime.now().date()
        assert result.hour == 17
```

---

## 4. 集成测试

### 4.1 API接口测试

```python
# tests/integration/test_api_events.py

import pytest
from datetime import datetime, timedelta

class TestEventsAPI:
    def test_create_event(self, client):
        """测试创建事件API"""
        response = client.post("/api/events", json={
            "title": "测试会议",
            "start_time": (datetime.now() + timedelta(days=1)).isoformat(),
            "reminder": True,
            "reminder_minutes": 15
        })
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "测试会议"
        assert "id" in data

    def test_get_events(self, client):
        """测试获取事件列表API"""
        # 先创建事件
        client.post("/api/events", json={
            "title": "会议1",
            "start_time": datetime.now().isoformat()
        })
        client.post("/api/events", json={
            "title": "会议2",
            "start_time": datetime.now().isoformat()
        })

        # 查询
        response = client.get("/api/events")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2

    def test_delete_event(self, client):
        """测试删除事件API"""
        # 先创建事件
        create_response = client.post("/api/events", json={
            "title": "待删除会议",
            "start_time": datetime.now().isoformat()
        })
        event_id = create_response.json()["id"]

        # 删除
        response = client.delete(f"/api/events/{event_id}")
        assert response.status_code == 200

        # 验证已删除
        get_response = client.get("/api/events")
        assert get_response.json()["total"] == 0

    def test_update_event(self, client):
        """测试更新事件API"""
        # 先创建事件
        create_response = client.post("/api/events", json={
            "title": "原标题",
            "start_time": datetime.now().isoformat()
        })
        event_id = create_response.json()["id"]

        # 更新
        response = client.put(f"/api/events/{event_id}", json={
            "title": "新标题"
        })
        assert response.status_code == 200
        assert response.json()["title"] == "新标题"
```

### 4.2 语音识别集成测试

```python
# tests/integration/test_voice_service.py

import pytest
import os
from src.backend.core.voice_service import VoiceService

class TestVoiceService:
    @pytest.fixture
    def voice_service(self):
        """初始化语音服务"""
        model_path = os.getenv("VOSK_MODEL_PATH", "models/vosk/vosk-model-small-cn-0.22")
        return VoiceService(model_path)

    def test_recognize_audio_file(self, voice_service):
        """测试识别音频文件"""
        # 准备测试音频文件
        test_audio = "tests/fixtures/test_audio.wav"
        if os.path.exists(test_audio):
            result = voice_service.recognize_file(test_audio)
            assert isinstance(result, str)
            assert len(result) > 0

    @pytest.mark.skipif(
        not os.path.exists("models/vosk/vosk-model-small-cn-0.22"),
        reason="Vosk模型未下载"
    )
    def test_real_time_recognition(self, voice_service):
        """测试实时识别（需要麦克风）"""
        # 此测试需要手动验证
        pass
```

---

## 5. 端到端测试

### 5.1 完整流程测试

```python
# tests/e2e/test_full_flow.py

import pytest
from datetime import datetime, timedelta

class TestFullFlow:
    def test_voice_to_event_flow(self, client):
        """测试完整流程：语音 → 文本 → 事件"""
        # 1. 模拟语音识别结果
        voice_text = "帮我创建一个明天下午3点的团队会议"

        # 2. 调用NLU解析（使用mock）
        # 3. 调用创建事件API
        response = client.post("/api/events", json={
            "title": "团队会议",
            "start_time": (datetime.now() + timedelta(days=1)).replace(hour=15).isoformat()
        })
        assert response.status_code == 201

        # 4. 验证事件已创建
        get_response = client.get("/api/events")
        events = get_response.json()["events"]
        assert any(e["title"] == "团队会议" for e in events)

    def test_query_and_delete_flow(self, client):
        """测试查询和删除流程"""
        # 1. 创建事件
        client.post("/api/events", json={
            "title": "临时会议",
            "start_time": datetime.now().isoformat()
        })

        # 2. 查询事件
        get_response = client.get("/api/events")
        event_id = get_response.json()["events"][0]["id"]

        # 3. 删除事件
        delete_response = client.delete(f"/api/events/{event_id}")
        assert delete_response.status_code == 200

        # 4. 验证已删除
        final_response = client.get("/api/events")
        assert final_response.json()["total"] == 0
```

---

## 6. 语音识别准确率测试

### 6.1 测试数据集

```python
# tests/fixtures/voice_test_cases.py

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

### 6.2 准确率计算

```python
# tests/voice/test_accuracy.py

import pytest
from tests.fixtures.voice_test_cases import VOICE_TEST_CASES

class TestVoiceAccuracy:
    def test_recognition_accuracy(self, voice_service, nlu_service):
        """测试整体识别准确率"""
        correct = 0
        total = len(VOICE_TEST_CASES)

        for case in VOICE_TEST_CASES:
            # 1. 语音识别
            text = voice_service.recognize_file(case["input_audio"])

            # 2. NLU解析
            result = nlu_service.parse_command(text)

            # 3. 验证
            if result["intent"] == case["expected_intent"]:
                if case["expected_intent"] == "add_event":
                    if case["expected_title"] in result.get("title", ""):
                        correct += 1
                else:
                    correct += 1

        accuracy = correct / total
        assert accuracy >= 0.7, f"识别准确率低于70%: {accuracy:.2%}"
```

---

## 7. 性能测试

### 7.1 响应时间测试

```python
# tests/performance/test_response_time.py

import pytest
import time

class TestResponseTime:
    def test_api_response_time(self, client):
        """测试API响应时间"""
        start = time.time()
        client.get("/api/events")
        end = time.time()

        response_time = end - start
        assert response_time < 0.5, f"API响应时间超过500ms: {response_time:.2f}s"

    def test_nlu_response_time(self, nlu_service):
        """测试NLU解析响应时间"""
        start = time.time()
        nlu_service.parse_command("帮我创建一个明天下午3点的会议")
        end = time.time()

        response_time = end - start
        assert response_time < 2.0, f"NLU响应时间超过2s: {response_time:.2f}s"
```

---

## 8. 测试运行

### 8.1 运行所有测试

```bash
# 使用uv运行测试（推荐）
uv run pytest

# 运行并生成覆盖率报告
uv run pytest --cov=src --cov-report=html

# 运行特定类型的测试
uv run pytest tests/unit/          # 单元测试
uv run pytest tests/integration/   # 集成测试
uv run pytest tests/e2e/           # 端到端测试

# 运行代码质量检查
uv run black src/ tests/           # 代码格式化
uv run isort src/ tests/           # import排序
uv run ruff check src/ tests/      # lint检查
```

### 8.2 测试报告

```bash
# 生成HTML测试报告
uv run pytest --html=reports/test_report.html

# 生成JUnit XML报告（用于CI）
uv run pytest --junitxml=reports/test_results.xml
```

---

## 9. CI/CD集成

### 9.1 GitHub Actions配置

```yaml
# .github/workflows/test.yml

name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ["3.11", "3.12"]

    steps:
    - uses: actions/checkout@v4

    - name: Install uv
      uses: astral-sh/setup-uv@v3
      with:
        version: "latest"

    - name: Set up Python
      run: uv python install ${{ matrix.python-version }}

    - name: Install dependencies
      run: uv sync --extra dev

    - name: Run tests
      run: uv run pytest --cov=src --cov-report=xml

    - name: Upload coverage
      uses: codecov/codecov-action@v4
      with:
        file: ./coverage.xml

  lint:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v4

    - name: Install uv
      uses: astral-sh/setup-uv@v3

    - name: Set up Python
      run: uv python install 3.11

    - name: Install dependencies
      run: uv sync --extra dev

    - name: Run linting
      run: |
        uv run ruff check src/ tests/
        uv run black --check src/ tests/
        uv run isort --check-only src/ tests/
```

---

## 10. 语音识别测试记录

### 10.1 测试环境

| 项目 | 内容 |
|------|------|
| 测试日期 | 2026-05-30 |
| Python 版本 | 3.11.15 |
| pytest 版本 | 9.0.3 |
| ASR 服务商 | 百度 |
| 测试音频来源 | `D:\Desktop\Voice-Driven-Calendar_VoiceTest\` |
| 音频格式 | m4a（经 ffmpeg 转为 16kHz/16bit/mono WAV） |

### 10.2 测试用例与结果

| # | 测试方法 | 输入 | 预期结果 | 实际结果 | 判定 |
|---|----------|------|----------|----------|------|
| 1 | test_recognize_audio_add_event | 帮我创建一个明天下午三点的团队会议.m4a | 返回字符串，包含关键词 | "帮我创建一个，明天下午三点的团队**回忆**。" | ✅ PASSED |
| 2 | test_recognize_audio_query_events | 今天有什么安排.m4a | 返回字符串，包含"安排" | "今天有什么安排？" | ✅ PASSED |
| 3 | test_recognize_audio_delete_event | 取消明天上午的会议.m4a | 返回字符串，包含"取消"或"会议" | "取消明天上午的会议。" | ✅ PASSED |
| 4 | test_recognize_audio_silence | 空白录音.m4a | 抛出 Exception | 3301 - speech quality error | ✅ PASSED |
| 5 | test_recognize_audio_data_returns_string | 1 秒静音 PCM（struct 生成） | 抛出异常或返回空文本 | 返回空文本 | ✅ PASSED |
| 6 | test_upload_endpoint_recognizes_text | 今天有什么安排.wav（经 ffmpeg 转换） | 状态码 200，响应含非空 text | text="今天有什么安排？" | ✅ PASSED |
| 7 | test_upload_endpoint_returns_correct_format | 空 bytes WAV | 状态码 200，响应含 text 和 confidence | text="识别失败: ..." | ✅ PASSED |

### 10.3 测试输出

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

### 10.4 Warnings 汇总

| 类型 | 数量 | 说明 |
|------|------|------|
| PydanticDeprecatedSince20 | 1 | Settings 使用 class-based config，Pydantic V3 将移除 |
| InsecureRequestWarning | 1 | 测试客户端使用未验证的 HTTPS |
| StarletteDeprecationWarning | 1 | httpx 与 starlette.testclient 兼容性警告 |
| DeprecationWarning (on_event) | 3 | FastAPI 的 on_event 已废弃，建议改用 lifespan |

以上 warnings 均不影响功能，属于现有代码的兼容性提示。

### 10.5 识别准确率统计

| 指标 | 结果 |
|------|------|
| 有效语音识别成功率 | 3/3（100%） |
| 完全准确率 | 2/3（66.7%） |
| 同音字偏差 | 1/3（"会议" → "回忆"，百度 ASR 偏差） |
| 空白录音误识别率 | 0/1（0%，正确返回错误） |

---

## 11. ASR → NLU 链路测试记录

### 11.1 测试环境

| 项目 | 内容 |
|------|------|
| 测试日期 | 2026-05-30 |
| ASR 服务商 | 百度 |
| NLU 大模型 | DeepSeek (deepseek-chat) |
| 测试方式 | HTTP API 调用（FastAPI + httpx） |
| 测试音频来源 | `D:\Desktop\Voice-Driven-Calendar_VoiceTest\` |
| 音频格式 | m4a（经 ffmpeg 转为 16kHz/16bit/mono WAV） |

### 11.2 测试用例与结果

#### 测试 1：/parse 端点（直接传文本，不经 ASR）

| # | 输入文本 | 期望 intent | 实际 intent | 实际 title | 实际 time | 判定 |
|---|----------|------------|-------------|------------|-----------|------|
| 1 | 帮我创建一个明天下午三点的团队会议 | add_event | add_event | 团队会议 | 2026-05-31T15:00:00 | ✅ PASSED |
| 2 | 今天有什么安排 | query_events | query_events | （空） | 2026-05-30T00:00:00 | ✅ PASSED |
| 3 | 取消明天上午的会议 | delete_event | delete_event | 会议 | 2026-05-31T00:00:00 | ✅ PASSED |
| 4 | （空字符串） | unknown | unknown | （空） | null | ✅ PASSED |

#### 测试 2：完整链路 ASR → NLU

| # | 音频文件 | ASR 输出 | NLU intent | NLU title | NLU time | 判定 |
|---|----------|----------|------------|-----------|----------|------|
| 1 | 帮我创建一个明天下午三点的团队会议.m4a | 帮我创建一个，明天下午三点的团队回忆。 | add_event | **团队会议**（同音字已纠正） | 2026-05-31T15:00:00 | ✅ PASSED |
| 2 | 今天有什么安排.m4a | 今天有什么安排？ | query_events | （空） | 2026-05-30T00:00:00 | ✅ PASSED |
| 3 | 取消明天上午的会议.m4a | 取消明天上午的会议。 | delete_event | 会议 | 2026-05-31T00:00:00 | ✅ PASSED |

#### 测试 3：/parse 返回格式

| # | 验证字段 | 判定 |
|---|----------|------|
| 1 | intent, title, time, reminder, reminder_minutes, description 6 个字段齐全 | ✅ PASSED |

### 11.3 测试输出

```
============================================================
测试 1: /parse 端点（直接传文本）
============================================================
  [OK] "帮我创建一个明天下午三点的团队会议"
        → intent=add_event, time=2026-05-31T15:00:00, title=团队会议
  [OK] "今天有什么安排"
        → intent=query_events, time=2026-05-30T00:00:00, title=
  [OK] "取消明天上午的会议"
        → intent=delete_event, time=2026-05-31T00:00:00, title=会议
  [OK] "(空字符串)"
        → intent=unknown, time=None, title=
  结果: 4/4 通过

============================================================
测试 2: 完整链路 ASR → NLU
============================================================
  ASR: "帮我创建一个，明天下午三点的团队回忆。"
  NLU: intent=add_event, time=2026-05-31T15:00:00, title=团队会议
  ASR: "今天有什么安排？"
  NLU: intent=query_events, time=2026-05-30T00:00:00, title=
  ASR: "取消明天上午的会议。"
  NLU: intent=delete_event, time=2026-05-31T00:00:00, title=会议
  结果: 3/3 通过

============================================================
测试 3: /parse 返回格式
============================================================
  [OK] 所有字段齐全: ['intent', 'title', 'time', 'reminder', 'reminder_minutes', 'description']
```

### 11.4 同音字纠正验证

| ASR 原始输出 | NLU 纠正后 | 纠正是否生效 |
|--------------|-----------|-------------|
| 团队**回忆** | 团队**会议** | ✅ 生效 |

NLU 提示词中配置了同音字映射表（回忆/会意/回议 → 会议），DeepSeek 正确执行了纠正。

### 11.5 链路验证

```
m4a 录音文件
  ↓ ffmpeg 转码
16kHz/16bit/mono WAV
  ↓ POST /api/voice/upload
VoiceService.recognize_file() (百度 ASR)
  ↓
"帮我创建一个，明天下午三点的团队回忆。"
  ↓ 客户端拿到文本后调用
POST /api/voice/parse?text=...
  ↓
NLUService.parse_command() (DeepSeek)
  ↓
{"intent":"add_event", "title":"团队会议", "time":"2026-05-31T15:00:00", ...}
```

ASR → NLU 全链路运行正常，同音字纠正生效。
