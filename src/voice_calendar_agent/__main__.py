"""
入口点模块

支持以下启动方式：
- python -m voice_calendar_agent
- uv run voice-calendar
"""

import sys
import logging

from voice_calendar_agent.app import create_app
from voice_calendar_agent.config import Settings


def main():
    """
    程序主入口

    功能：
    1. 加载配置
    2. 初始化应用
    3. 启动服务

    输入：无
    输出：无
    """
    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    logger = logging.getLogger(__name__)

    try:
        # 加载配置
        settings = Settings()

        # 创建并启动应用
        app = create_app(settings)
        app.run()

    except KeyboardInterrupt:
        logger.info("用户中断，程序退出")
        sys.exit(0)
    except Exception as e:
        logger.error(f"程序启动失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
