"""
配置管理模块

负责加载和管理应用配置，支持从环境变量和 .env 文件读取配置。
"""

from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional


class Settings(BaseSettings):
    """
    应用配置类

    功能：集中管理所有配置项，支持环境变量覆盖

    配置项说明：
    - DATABASE_URL: 数据库连接地址
    - ASR_MODE: 语音识别模式（online/offline/hybrid）
    - BAIDU_APP_ID: 百度语音应用ID
    - BAIDU_API_KEY: 百度语音API Key
    - BAIDU_SECRET_KEY: 百度语音Secret Key
    - VOSK_MODEL_PATH: Vosk语音模型路径（离线模式可选）
    - LLM_PROVIDER: 大模型提供商 (openai/anthropic)
    - LLM_API_KEY: 大模型API密钥
    - LLM_MODEL: 大模型名称
    - LLM_BASE_URL: 大模型API基础URL（用于兼容deepseek/mimo等）
    - HOST: 服务监听地址
    - PORT: 服务监听端口
    """

    # 数据库配置
    DATABASE_URL: str = Field(
        default="sqlite:///data/calendar.db",
        description="数据库连接地址"
    )

    # 语音识别配置
    ASR_MODE: str = Field(
        default="online",
        description="语音识别模式 (online/offline/hybrid)"
    )

    # 在线语音识别配置（百度）
    BAIDU_APP_ID: str = Field(
        default="",
        description="百度语音应用ID"
    )
    BAIDU_API_KEY: str = Field(
        default="",
        description="百度语音API Key"
    )
    BAIDU_SECRET_KEY: str = Field(
        default="",
        description="百度语音Secret Key"
    )

    # 离线语音识别配置（可选）
    VOSK_MODEL_PATH: str = Field(
        default="models/vosk/vosk-model-small-cn-0.22",
        description="Vosk语音模型路径（仅离线模式需要）"
    )

    # NLU大模型配置
    LLM_PROVIDER: str = Field(
        default="openai",
        description="大模型提供商 (openai/anthropic，deepseek和mimo使用openai格式)"
    )
    LLM_API_KEY: str = Field(
        default="",
        description="大模型API密钥"
    )
    LLM_MODEL: str = Field(
        default="deepseek-chat",
        description="大模型名称"
    )
    LLM_BASE_URL: Optional[str] = Field(
        default="https://api.deepseek.com",
        description="大模型API基础URL（用于兼容deepseek/mimo等）"
    )

    # 服务配置
    HOST: str = Field(default="0.0.0.0", description="服务监听地址")
    PORT: int = Field(default=8000, description="服务监听端口")

    # 提醒配置
    REMINDER_CHECK_INTERVAL: int = Field(
        default=60,
        description="提醒检查间隔（秒）"
    )

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
