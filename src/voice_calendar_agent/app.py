"""
应用主模块

负责初始化和启动整个应用，包括后端服务和操作层。
"""

import logging
import uvicorn
from fastapi import FastAPI

from voice_calendar_agent.config import Settings
from voice_calendar_agent.backend.models.database import init_db
from voice_calendar_agent.backend.api.events import router as events_router
from voice_calendar_agent.backend.api.voice import router as voice_router


logger = logging.getLogger(__name__)


class Application:
    """
    应用主类

    功能：管理应用生命周期，协调各模块启动

    属性：
    - settings: 应用配置
    - fastapi_app: FastAPI实例
    """

    def __init__(self, settings: Settings):
        """
        初始化应用

        输入：
            settings: 应用配置对象
        输出：无
        """
        self.settings = settings
        self.fastapi_app = FastAPI(
            title="语音日历助手",
            description="以语音交互为核心的日历管理工具",
            version="0.1.0",
        )
        self._setup_routes()
        self._setup_events()

    def _setup_routes(self):
        """
        注册API路由

        输入：无
        输出：无
        """
        self.fastapi_app.include_router(
            events_router,
            prefix="/api",
            tags=["事件管理"],
        )
        self.fastapi_app.include_router(
            voice_router,
            prefix="/api/voice",
            tags=["语音识别"],
        )

    def _setup_events(self):
        """
        注册应用生命周期事件

        输入：无
        输出：无
        """

        @self.fastapi_app.on_event("startup")
        async def startup():
            """应用启动时初始化数据库"""
            logger.info("正在初始化数据库...")
            init_db(self.settings.DATABASE_URL)
            logger.info("数据库初始化完成")

        @self.fastapi_app.on_event("shutdown")
        async def shutdown():
            """应用关闭时清理资源"""
            logger.info("正在清理资源...")

    def run(self):
        """
        启动应用

        输入：无
        输出：无
        """
        logger.info(f"启动服务: {self.settings.HOST}:{self.settings.PORT}")
        uvicorn.run(
            self.fastapi_app,
            host=self.settings.HOST,
            port=self.settings.PORT,
        )


def create_app(settings: Settings) -> Application:
    """
    创建应用实例

    输入：
        settings: 应用配置对象
    输出：
        Application实例
    """
    return Application(settings)
