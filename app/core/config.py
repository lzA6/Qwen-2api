# app/core/config.py (v7.2 最终修正版)

from pydantic_settings import BaseSettings
# ！！！确保这一行包含了 Optional ！！！
from typing import Dict, List, Optional

class Settings(BaseSettings):
    """
    应用配置 (v7.2 最终修正版)
    - 修正了因缺少 Optional 导入导致的启动崩溃问题。
    """
    # --- 服务监听端口 ---
    LISTEN_PORT: int = 8082

    # --- 应用元数据 ---
    APP_NAME: str = "Qwen Multi-Account Local API"
    APP_VERSION: str = "7.2.0"
    DESCRIPTION: str = "一个支持根据模型名称动态切换账号并具备密钥认证功能的高性能通义千问本地代理。"

    # --- 认证与安全 ---
    API_MASTER_KEY: Optional[str] = None

    # --- 模型与账号的映射关系 ---
    MODEL_TO_ACCOUNT_MAP: Dict[str, int] = {
        "Qwen3-Max-Preview": 2
    }

    # --- 全面更新的模型列表 (仅供参考，实际以你的账号支持为准) ---
    SUPPORTED_MODELS: List[str] = [
        "qwen-plus", "qwen-turbo", "qwen-max", "qwen-long", "qwen-vl-plus",
        "Qwen3-Max-Preview",
    ]

    # --- 国内站账号 1 (默认) ---
    CN_ACCOUNT_1_COOKIE: str = ""
    CN_ACCOUNT_1_XSRF_TOKEN: str = ""

    # --- 国内站账号 2 (专属) ---
    CN_ACCOUNT_2_COOKIE: str = ""
    CN_ACCOUNT_2_XSRF_TOKEN: str = ""

    # --- 国际站账号 (可选) ---
    INTL_COOKIE: str = ""
    INTL_AUTHORIZATION: str = ""
    INTL_BX_UA: str = ""

    class Config:
        env_file = ".env"
        env_file_encoding = 'utf-8'

settings = Settings()
