"""
应用主模块

负责初始化和启动整个应用，包括后端服务和操作层。
"""

import logging
import os
import uvicorn
from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

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

        # ── 前端静态文件服务 ──
        frontend_dir = os.path.join(os.path.dirname(__file__), "frontend", "web")
        static_dir = os.path.join(frontend_dir, "static")
        os.makedirs(static_dir, exist_ok=True)

        self.fastapi_app.mount(
            "/static", StaticFiles(directory=static_dir), name="static"
        )

        @self.fastapi_app.get("/")
        async def root():
            return FileResponse(os.path.join(frontend_dir, "index.html"))

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

    def run(self, ssl_certfile=None, ssl_keyfile=None):
        """
        启动应用

        输入：
            ssl_certfile: SSL 证书文件路径（可选，用于 HTTPS）
            ssl_keyfile:  SSL 私钥文件路径（可选，用于 HTTPS）
        输出：无
        """
        protocol = "https" if (ssl_certfile and ssl_keyfile) else "http"
        logger.info(f"启动服务: {protocol}://{self.settings.HOST}:{self.settings.PORT}")

        kwargs = dict(host=self.settings.HOST, port=self.settings.PORT)
        if ssl_certfile and ssl_keyfile:
            kwargs["ssl_certfile"] = ssl_certfile
            kwargs["ssl_keyfile"] = ssl_keyfile
            logger.info("已启用 HTTPS（SSL 证书已加载）")

        uvicorn.run(self.fastapi_app, **kwargs)


def create_app(settings: Settings) -> Application:
    """
    创建应用实例

    输入：
        settings: 应用配置对象
    输出：
        Application实例
    """
    return Application(settings)
