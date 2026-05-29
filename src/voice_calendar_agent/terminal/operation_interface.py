"""
操作层接口定义

定义操作层的抽象接口，方便后续实现GUI或其他操作层。
"""

from abc import ABC, abstractmethod
from typing import List, Optional
from datetime import datetime


class OperationInterface(ABC):
    """
    操作层抽象接口

    功能：定义操作层必须实现的方法，确保服务层与操作层解耦

    实现此接口可以创建不同的操作层：
    - TerminalApp: 终端操作层（当前实现）
    - GUIApp: 图形界面操作层（后续实现）
    - WebApp: Web界面操作层（后续实现）
    """

    @abstractmethod
    def display_message(self, message: str):
        """
        显示消息

        输入：
            message: 要显示的消息文本
        输出：无
        """
        pass

    @abstractmethod
    def display_error(self, error: str):
        """
        显示错误消息

        输入：
            error: 错误消息文本
        输出：无
        """
        pass

    @abstractmethod
    def display_events(self, events: List[dict]):
        """
        显示事件列表

        输入：
            events: 事件字典列表
        输出：无
        """
        pass

    @abstractmethod
    def get_user_input(self, prompt: str) -> str:
        """
        获取用户输入

        输入：
            prompt: 输入提示文本
        输出：
            str - 用户输入的文本
        """
        pass

    @abstractmethod
    def get_confirmation(self, message: str) -> bool:
        """
        获取用户确认

        输入：
            message: 确认提示消息
        输出：
            bool - 用户是否确认
        """
        pass

    @abstractmethod
    def display_reminder(self, event: dict):
        """
        显示事件提醒

        输入：
            event: 事件字典
        输出：无
        """
        pass

    @abstractmethod
    def run(self):
        """
        启动操作层

        输入：无
        输出：无
        """
        pass

    @abstractmethod
    def stop(self):
        """
        停止操作层

        输入：无
        输出：无
        """
        pass
