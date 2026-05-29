"""
语音日历助手 - 启动入口

支持两种启动模式：
1. API服务模式：启动FastAPI后端服务
2. 终端模式：启动命令行交互界面

使用方式：
    uv run python main.py              # 默认启动终端模式
    uv run python main.py --api        # 启动API服务模式
    uv run python main.py --terminal   # 启动终端模式
"""

import sys
import argparse
import logging

from voice_calendar_agent.config import Settings
from voice_calendar_agent.app import create_app
from voice_calendar_agent.terminal.terminal_app import TerminalApp


def main():
    """
    程序主入口

    功能：
    1. 解析命令行参数
    2. 加载配置
    3. 根据模式启动相应服务

    输入：无
    输出：无
    """
    # 解析命令行参数
    parser = argparse.ArgumentParser(description="语音日历助手")
    parser.add_argument(
        "--api",
        action="store_true",
        help="启动API服务模式",
    )
    parser.add_argument(
        "--terminal",
        action="store_true",
        help="启动终端交互模式（默认）",
    )
    args = parser.parse_args()

    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    logger = logging.getLogger(__name__)

    try:
        # 加载配置
        settings = Settings()

        if args.api:
            # 启动API服务模式
            logger.info("启动API服务模式...")
            app = create_app(settings)
            app.run()
        else:
            # 启动终端交互模式（默认）
            logger.info("启动终端交互模式...")
            terminal_app = TerminalApp(settings)
            terminal_app.run()

    except KeyboardInterrupt:
        logger.info("用户中断，程序退出")
        sys.exit(0)
    except Exception as e:
        logger.error(f"程序启动失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
