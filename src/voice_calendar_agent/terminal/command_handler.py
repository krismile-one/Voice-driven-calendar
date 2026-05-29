"""
命令处理器

解析和执行用户输入的命令。
"""

from typing import Callable, Dict, List, Optional
from dataclasses import dataclass


@dataclass
class Command:
    """
    命令数据类

    属性：
    - name: 命令名称
    - description: 命令描述
    - handler: 命令处理函数
    - aliases: 命令别名列表
    """
    name: str
    description: str
    handler: Callable
    aliases: List[str] = None


class CommandHandler:
    """
    命令处理器类

    功能：注册、解析和执行用户命令

    属性：
    - commands: 已注册的命令字典
    """

    def __init__(self):
        """
        初始化命令处理器

        输入：无
        输出：无
        """
        self.commands: Dict[str, Command] = {}

    def register(self, name: str, description: str, handler: Callable, aliases: List[str] = None):
        """
        注册命令

        输入：
            name: 命令名称
            description: 命令描述
            handler: 命令处理函数
            aliases: 命令别名列表（可选）
        输出：无
        """
        pass

    def execute(self, input_text: str) -> Optional[str]:
        """
        执行命令

        输入：
            input_text: 用户输入的完整命令文本
        输出：
            Optional[str] - 命令执行结果，无结果返回None
        """
        pass

    def get_help(self) -> str:
        """
        获取所有命令的帮助信息

        输入：无
        输出：
            str - 格式化的帮助信息
        """
        pass

    def _parse_input(self, input_text: str) -> tuple:
        """
        解析用户输入

        输入：
            input_text: 用户输入文本
        输出：
            tuple - (命令名, 参数列表)
        """
        pass
