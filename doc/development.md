# 语音日历助手 - 开发文档

## 1. 项目结构

```
voice-calendar-agent/
├── doc/
│   ├── proposal.md          # 需求文档
│   ├── development.md       # 开发文档（本文件）
│   └── test.md              # 测试文档
├── src/
│   └── voice_calendar_agent/
│       ├── __init__.py
│       ├── __main__.py      # 入口点（python -m voice_calendar_agent）
│       ├── app.py           # FastAPI应用入口
│       ├── config.py        # 配置管理
│       ├── backend/
│       │   ├── __init__.py
│       │   ├── api/
│       │   │   ├── __init__.py
│       │   │   ├── events.py    # 事件CRUD接口
│       │   │   └── voice.py     # 语音识别接口
│       │   ├── core/
│       │   │   ├── __init__.py
│       │   │   ├── calendar_service.py  # 日历业务逻辑
│       │   │   ├── voice_service.py     # 语音识别服务
│       │   │   └── nlu_service.py       # NLU解析服务
│       │   ├── models/
│       │   │   ├── __init__.py
│       │   │   ├── event.py     # 事件数据模型
│       │   │   └── database.py  # 数据库连接
│       │   └── utils/
│       │       ├── __init__.py
│       │       └── time_parser.py  # 时间解析工具
│       ├── terminal/            # 终端操作层
│       │   ├── __init__.py
│       │   ├── terminal_app.py  # 终端应用主程序
│       │   ├── command_handler.py # 命令处理器
│       │   └── operation_interface.py # 操作层抽象接口
│       └── frontend/
│           ├── __init__.py
│           ├── gui/
│           │   ├── __init__.py
│           │   ├── app.py       # GUI主程序
│           │   ├── main_window.py
│           │   └── widgets/
│           │       ├── event_list.py
│           │       ├── voice_input.py
│           │       └── status_bar.py
│           └── web/             # Web端（预留）
├── models/
│   └── vosk/                # Vosk模型文件
├── data/
│   └── calendar.db          # SQLite数据库
├── tests/                   # 测试目录
├── pyproject.toml           # 项目配置（uv管理）
├── main.py                  # 启动入口（支持 --api 和 --terminal 模式）
├── .env.example
├── .gitignore
└── README.md
```

---

## 2. 技术栈与依赖

### 2.1 Python版本

**要求**: Python 3.11+

### 2.2 包管理

使用 **uv** 进行包管理，项目配置在 `pyproject.toml` 中。

### 2.3 核心依赖

```toml
# pyproject.toml

[project]
name = "voice-calendar-agent"
version = "0.1.0"
description = "语音日历助手 - 以语音交互为核心的日历管理工具"
readme = "README.md"
requires-python = ">=3.11"
dependencies = [
    # 后端框架
    "fastapi>=0.104.1",
    "uvicorn[standard]>=0.24.0",
    "python-dotenv>=1.0.0",

    # 语音识别（在线）
    "baidu-aip>=4.16.0",

    # 数据库
    "sqlalchemy>=2.0.23",
    "aiosqlite>=0.19.0",

    # NLU - 大模型调用
    "openai>=1.6.1",
    "anthropic>=0.18.0",
    "httpx>=0.25.2",

    # 工具
    "pydantic>=2.5.2",
    "pydantic-settings>=2.1.0",
    "python-multipart>=0.0.6",
]

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

gui = [
    "PyQt6>=6.6.1",
]

# 离线语音识别（可选，不支持 macOS ARM64）
vosk = [
    "vosk>=0.3.45",
    "pyaudio>=0.2.14",
]

[project.scripts]
voice-calendar = "voice_calendar_agent.__main__:main"
```

### 2.4 安装命令

```bash
# 安装项目及依赖
uv sync

# 安装开发依赖
uv sync --extra dev

# 添加新依赖
uv add <package_name>

# 添加开发依赖
uv add --dev <package_name>
```

---

## 3. 数据库设计

### 3.1 使用SQLAlchemy + SQLite

**数据库文件位置**: `data/calendar.db`

### 3.2 表结构

#### events 表

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER | 主键，自增 |
| title | VARCHAR(200) | 事件标题 |
| description | TEXT | 事件描述（可选） |
| start_time | DATETIME | 开始时间 |
| end_time | DATETIME | 结束时间（可选） |
| reminder | BOOLEAN | 是否提醒 |
| reminder_minutes | INTEGER | 提前提醒分钟数 |
| created_at | DATETIME | 创建时间 |
| updated_at | DATETIME | 更新时间 |

### 3.3 SQLAlchemy模型

```python
# src/backend/models/event.py

from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Event(Base):
    __tablename__ = "events"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=True)
    reminder = Column(Boolean, default=True)
    reminder_minutes = Column(Integer, default=15)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
```

---

## 4. 接口设计（RESTful API）

### 4.1 基础信息

- **Base URL**: `http://localhost:8000/api`
- **Content-Type**: `application/json`
- **认证**: MVP阶段无需认证

### 4.2 事件管理接口

#### 添加事件

```http
POST /api/events

Request Body:
{
    "title": "团队会议",
    "description": "讨论Q2计划",
    "start_time": "2024-01-15T15:00:00",
    "end_time": "2024-01-15T16:00:00",
    "reminder": true,
    "reminder_minutes": 15
}

Response (201):
{
    "id": 1,
    "title": "团队会议",
    "description": "讨论Q2计划",
    "start_time": "2024-01-15T15:00:00",
    "end_time": "2024-01-15T16:00:00",
    "reminder": true,
    "reminder_minutes": 15,
    "created_at": "2024-01-14T10:00:00"
}
```

#### 获取事件列表

```http
GET /api/events?date=2024-01-15&range=day

Query Parameters:
- date: 日期过滤（可选）
- range: day/week/month（可选）

Response (200):
{
    "events": [
        {
            "id": 1,
            "title": "团队会议",
            "start_time": "2024-01-15T15:00:00",
            ...
        }
    ],
    "total": 1
}
```

#### 删除事件

```http
DELETE /api/events/{event_id}

Response (200):
{
    "message": "事件已删除",
    "id": 1
}
```

#### 修改事件

```http
PUT /api/events/{event_id}

Request Body:
{
    "title": "团队会议（更新）",
    "start_time": "2024-01-15T16:00:00"
}

Response (200):
{
    "id": 1,
    "title": "团队会议（更新）",
    "start_time": "2024-01-15T16:00:00",
    ...
}
```

### 4.3 语音识别接口

#### 上传语音识别

```http
POST /api/voice/upload

Content-Type: multipart/form-data

Form Data:
- audio: 音频文件（WAV格式）

Response (200):
{
    "text": "帮我创建一个明天下午3点的团队会议",
    "confidence": 0.95
}
```

#### WebSocket语音流（可选）

```http
GET /ws/voice/stream

WebSocket连接，实时传输音频数据
```

---

## 5. 核心模块实现

### 5.1 语音识别服务

```python
# src/backend/core/voice_service.py

import logging
from typing import Callable
from enum import Enum
from aip import AipSpeech

logger = logging.getLogger(__name__)

class ASRMode(Enum):
    """语音识别模式"""
    ONLINE = "online"    # 在线模式（百度语音）
    OFFLINE = "offline"  # 离线模式（Vosk，可选）
    HYBRID = "hybrid"    # 混合模式

class VoiceService:
    def __init__(
        self,
        mode: ASRMode = ASRMode.ONLINE,
        baidu_app_id: str = "",
        baidu_api_key: str = "",
        baidu_secret_key: str = "",
        vosk_model_path: str = "models/vosk/vosk-model-small-cn-0.22",
    ):
        self.mode = mode
        self.baidu_app_id = baidu_app_id
        self.baidu_api_key = baidu_api_key
        self.baidu_secret_key = baidu_secret_key
        self.vosk_model_path = vosk_model_path
        self.is_listening = False
        self._baidu_client = None
        self._vosk_recognizer = None

    def _init_baidu_client(self):
        """初始化百度语音客户端"""
        self._baidu_client = AipSpeech(
            self.baidu_app_id,
            self.baidu_api_key,
            self.baidu_secret_key
        )

    def _init_vosk_recognizer(self):
        """初始化Vosk离线识别器（可选，需安装vosk依赖）"""
        try:
            from vosk import Model, KaldiRecognizer
            self._vosk_model = Model(self.vosk_model_path)
            self._vosk_recognizer = KaldiRecognizer(self._vosk_model, 16000)
        except ImportError:
            logger.warning("vosk未安装，离线模式不可用")

    def start_listening(self, callback: Callable[[str], None]):
        """开始持续监听"""
        pass

    def stop_listening(self):
        """停止监听"""
        self.is_listening = False

    def recognize_file(self, audio_path: str) -> str:
        """识别音频文件"""
        pass

    def recognize_audio_data(self, audio_data: bytes) -> str:
        """识别音频数据"""
        pass

    def set_mode(self, mode: ASRMode):
        """切换识别模式"""
        pass

    def get_available_modes(self) -> list:
        """获取可用的识别模式列表"""
        pass
```

### 5.2 NLU解析服务

```python
# src/backend/core/nlu_service.py

from openai import OpenAI  # 或使用其他大模型API

class NLUService:
    def __init__(self, api_key: str):
        self.client = OpenAI(api_key=api_key)

    def parse_command(self, text: str) -> dict:
        """
        将自然语言转换为标准化指令

        输入: "帮我创建一个明天下午3点的团队会议"
        输出: {
            "intent": "add_event",
            "title": "团队会议",
            "time": "明天下午3点",
            "reminder": true
        }
        """
        prompt = f"""
        请解析以下语音指令，返回JSON格式：

        语音内容：{text}

        返回格式：
        {{
            "intent": "add_event" | "delete_event" | "query_events" | "unknown",
            "title": "事件标题",
            "time": "时间描述",
            "date": "日期描述",
            "reminder": true/false
        }}

        只返回JSON，不要其他内容。
        """

        response = self.client.chat.completions.create(
            model="gpt-3.5-turbo",  # 或使用其他便宜模型
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )

        return json.loads(response.choices[0].message.content)
```

### 5.3 日历服务

```python
# src/backend/core/calendar_service.py

from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from src.backend.models.event import Event

class CalendarService:
    def __init__(self, db: Session):
        self.db = db

    def add_event(self, title: str, start_time: datetime, **kwargs) -> Event:
        """添加事件"""
        event = Event(
            title=title,
            start_time=start_time,
            **kwargs
        )
        self.db.add(event)
        self.db.commit()
        self.db.refresh(event)
        return event

    def delete_event(self, event_id: int) -> bool:
        """删除事件"""
        event = self.db.query(Event).filter(Event.id == event_id).first()
        if event:
            self.db.delete(event)
            self.db.commit()
            return True
        return False

    def get_events(self, date: datetime = None, range: str = "day") -> list:
        """获取事件列表"""
        query = self.db.query(Event)
        if date:
            if range == "day":
                query = query.filter(Event.start_time.date() == date.date())
            elif range == "week":
                week_start = date - timedelta(days=date.weekday())
                week_end = week_start + timedelta(days=7)
                query = query.filter(
                    Event.start_time >= week_start,
                    Event.start_time < week_end
                )
        return query.order_by(Event.start_time).all()

    def update_event(self, event_id: int, **kwargs) -> Event:
        """更新事件"""
        event = self.db.query(Event).filter(Event.id == event_id).first()
        if event:
            for key, value in kwargs.items():
                setattr(event, key, value)
            self.db.commit()
            self.db.refresh(event)
        return event
```

---

## 6. 配置管理

### 6.1 环境变量

```python
# src/backend/config.py

from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # 数据库
    DATABASE_URL: str = "sqlite:///data/calendar.db"

    # 语音识别配置
    ASR_MODE: str = "online"  # online/offline/hybrid

    # 在线语音识别（百度）
    BAIDU_APP_ID: str = ""
    BAIDU_API_KEY: str = ""
    BAIDU_SECRET_KEY: str = ""

    # 离线语音识别（可选，需安装vosk）
    VOSK_MODEL_PATH: str = "models/vosk/vosk-model-small-cn-0.22"

    # NLU - 大模型API
    LLM_PROVIDER: str = "openai"  # openai/anthropic（deepseek和mimo使用openai格式）
    LLM_API_KEY: str = ""
    LLM_MODEL: str = "deepseek-chat"
    LLM_BASE_URL: Optional[str] = "https://api.deepseek.com"

    # 服务
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # 提醒配置
    REMINDER_CHECK_INTERVAL: int = 60

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
```

### 6.2 .env.example

```env
# 数据库
DATABASE_URL=sqlite:///data/calendar.db

# 语音识别模式：online（在线）/ offline（离线，需安装vosk）/ hybrid（混合）
ASR_MODE=online

# 在线语音识别配置（百度）
BAIDU_APP_ID=
BAIDU_API_KEY=
BAIDU_SECRET_KEY=

# 离线语音识别配置（可选，需安装vosk）
VOSK_MODEL_PATH=models/vosk/vosk-model-small-cn-0.22

# NLU - 大模型API
LLM_PROVIDER=openai
LLM_API_KEY=your-api-key-here
LLM_MODEL=deepseek-chat
LLM_BASE_URL=https://api.deepseek.com

# 服务
HOST=0.0.0.0
PORT=8000

# 提醒配置
REMINDER_CHECK_INTERVAL=60
```

---

## 7. GUI界面设计

### 7.1 技术选型

**PyQt6** - 成熟稳定，跨平台

### 7.2 界面布局

```
┌─────────────────────────────────────────┐
│  语音日历助手                 [─][□][×] │
├─────────────────────────────────────────┤
│  ┌─────────────────────────────────────┐│
│  │  🎤 语音输入状态: 监听中...         ││
│  │  [波形动画]                         ││
│  └─────────────────────────────────────┘│
│                                         │
│  ┌─────────────────────────────────────┐│
│  │  识别结果:                          ││
│  │  "帮我创建一个明天下午3点的会议"    ││
│  └─────────────────────────────────────┘│
│                                         │
│  ┌─────────────────────────────────────┐│
│  │  今日日程             [添加] [刷新] ││
│  ├─────────────────────────────────────┤│
│  │  09:00  团队站会                    ││
│  │  15:00  客户会议                    ││
│  │  17:00  代码评审                    ││
│  └─────────────────────────────────────┘│
│                                         │
│  状态: 已连接 | 事件数: 3               │
└─────────────────────────────────────────┘
```

### 7.3 核心组件

```python
# src/frontend/gui/main_window.py

from PyQt6.QtWidgets import QMainWindow, QWidget, QVBoxLayout
from PyQt6.QtCore import QThread, pyqtSignal

class VoiceThread(QThread):
    """语音识别后台线程"""
    text_recognized = pyqtSignal(str)

    def run(self):
        # 调用VoiceService进行持续监听
        pass

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("语音日历助手")
        self.init_ui()
        self.init_voice()

    def init_ui(self):
        """初始化界面"""
        # 实现界面布局
        pass

    def init_voice(self):
        """初始化语音服务"""
        self.voice_thread = VoiceThread()
        self.voice_thread.text_recognized.connect(self.on_text_recognized)
        self.voice_thread.start()

    def on_text_recognized(self, text: str):
        """处理识别到的文本"""
        # 调用NLU解析
        # 执行相应操作
        # 更新界面
        pass
```

---

## 8. 前后端分离架构

### 8.1 通信方式

- GUI前端通过HTTP请求调用后端API
- WebSocket用于实时语音流传输（可选）

### 8.2 调用示例

```python
# src/frontend/gui/api_client.py

import httpx

class APIClient:
    def __init__(self, base_url="http://localhost:8000/api"):
        self.base_url = base_url
        self.client = httpx.Client()

    def add_event(self, title: str, start_time: str, **kwargs):
        """添加事件"""
        response = self.client.post(f"{self.base_url}/events", json={
            "title": title,
            "start_time": start_time,
            **kwargs
        })
        return response.json()

    def get_events(self, date: str = None):
        """获取事件"""
        params = {"date": date} if date else {}
        response = self.client.get(f"{self.base_url}/events", params=params)
        return response.json()

    def delete_event(self, event_id: int):
        """删除事件"""
        response = self.client.delete(f"{self.base_url}/events/{event_id}")
        return response.json()
```

---

## 9. 部署指南

### 9.1 环境准备

```bash
# 1. 安装uv（如果未安装）
curl -LsSf https://astral.sh/uv/install.sh | sh

# 2. 克隆项目
git clone <repository-url>
cd voice-calendar-agent

# 3. 安装依赖
uv sync

# 4. 下载Vosk模型
mkdir -p models/vosk
cd models/vosk
wget https://alphacephei.com/vosk/models/vosk-model-small-cn-0.22.zip
unzip vosk-model-small-cn-0.22.zip
cd ../..

# 5. 配置环境变量
cp .env.example .env
# 编辑 .env 文件，填入API密钥等配置
```

### 9.2 启动服务

```bash
# 方式1: 使用uv运行（推荐）
uv run python main.py

# 方式2: 使用项目脚本
uv run voice-calendar

# 方式3: 直接激活虚拟环境运行
source .venv/bin/activate
python main.py
```

### 9.3 访问方式

- **API文档**: http://localhost:8000/docs
- **GUI应用**: 启动后自动显示桌面窗口

---

## 10. 代码规范

### 10.1 代码风格

- 遵循PEP8规范
- 使用Black进行代码格式化
- 使用isort进行import排序

### 10.2 命名规范

- **类名**: PascalCase（如`VoiceService`）
- **函数名**: snake_case（如`parse_command`）
- **变量名**: snake_case（如`event_list`）
- **常量名**: UPPER_CASE（如`MAX_RETRY`）

### 10.3 类型注解

所有函数参数和返回值必须添加类型注解：

```python
def add_event(title: str, start_time: datetime, reminder: bool = True) -> Event:
    pass
```

### 10.4 文档字符串

公共函数必须添加docstring：

```python
def parse_command(text: str) -> dict:
    """
    将自然语言转换为标准化指令

    Args:
        text: 语音识别后的文本

    Returns:
        包含intent、title、time等字段的字典
    """
    pass
```

---

## 11. 日志规范

### 11.1 日志级别

- **DEBUG**: 开发调试信息
- **INFO**: 关键业务流程
- **WARNING**: 非关键异常
- **ERROR**: 业务异常
- **CRITICAL**: 系统崩溃

### 11.2 日志格式

```
%(asctime)s - %(name)s - %(levelname)s - %(message)s
```

### 11.3 使用示例

```python
import logging

logger = logging.getLogger(__name__)

def add_event(title: str):
    logger.info(f"添加事件: {title}")
    # 业务逻辑
    logger.debug(f"事件保存成功: {event_id}")
```

---

## 12. 错误处理

### 12.1 统一异常处理

```python
# src/backend/api/events.py

from fastapi import HTTPException

@app.post("/api/events")
async def create_event(event: EventCreate):
    try:
        result = calendar_service.add_event(**event.dict())
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"添加事件失败: {e}")
        raise HTTPException(status_code=500, detail="服务器内部错误")
```

### 12.2 错误响应格式

```json
{
    "detail": "错误描述信息"
}
```
