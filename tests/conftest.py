"""
测试配置

提供测试夹具和通用测试工具。
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from voice_calendar_agent.backend.models.database import Base


# 测试数据库URL
TEST_DATABASE_URL = "sqlite:///./test.db"

# 创建测试引擎
engine = create_engine(TEST_DATABASE_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db_session():
    """
    每个测试函数独立的数据库会话

    输入：无
    输出：
        Session - 测试数据库会话
    """
    # 创建所有表
    Base.metadata.create_all(bind=engine)

    # 创建会话
    session = TestingSessionLocal()
    yield session

    # 清理
    session.close()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db_session):
    """
    FastAPI测试客户端

    输入：
        db_session: 数据库会话夹具
    输出：
        TestClient - 测试客户端实例
    """
    from fastapi.testclient import TestClient
    from voice_calendar_agent.app import create_app
    from voice_calendar_agent.config import Settings
    from voice_calendar_agent.backend.models.database import get_db

    # 创建测试配置
    settings = Settings(DATABASE_URL=TEST_DATABASE_URL)

    # 创建应用
    app = create_app(settings).fastapi_app

    # 覆盖数据库依赖
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db

    # 创建测试客户端
    with TestClient(app) as c:
        yield c

    # 清理
    app.dependency_overrides.clear()
