"""
数据库连接管理

负责创建数据库引擎、会话和初始化表结构。
"""

import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base, Session

logger = logging.getLogger(__name__)

# 创建Base类，所有模型继承此类
Base = declarative_base()

# 数据库引擎和会话工厂（延迟初始化）
_engine = None
_SessionLocal = None


def init_db(database_url: str):
    """
    初始化数据库

    输入：
        database_url: 数据库连接URL
    输出：无
    """
    global _engine, _SessionLocal

    logger.info(f"初始化数据库: {database_url}")

    # 创建引擎
    _engine = create_engine(
        database_url,
        echo=False,  # 设为True可查看SQL语句
        pool_pre_ping=True,
    )

    # 创建会话工厂
    _SessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=_engine,
    )

    # 导入所有模型以确保表被创建
    from voice_calendar_agent.backend.models.event import Event

    # 创建所有表
    Base.metadata.create_all(bind=_engine)
    logger.info("数据库表创建完成")


def get_db() -> Session:
    """
    获取数据库会话（用于FastAPI依赖注入）

    输入：无
    输出：
        Session - 数据库会话对象
    """
    if _SessionLocal is None:
        raise RuntimeError("数据库未初始化，请先调用 init_db()")

    db = _SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_db_session() -> Session:
    """
    获取数据库会话（用于非FastAPI场景）

    输入：无
    输出：
        Session - 数据库会话对象
    """
    if _SessionLocal is None:
        raise RuntimeError("数据库未初始化，请先调用 init_db()")

    return _SessionLocal()
