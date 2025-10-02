from abc import ABC, abstractmethod
from typing import Dict, Any, AsyncGenerator, Union
from fastapi import Request

class BaseProvider(ABC):
    """所有 Provider 的抽象基类"""

    @abstractmethod
    async def chat_completion(
        self,
        request_data: Dict[str, Any],
        original_request: Request
    ) -> Union[Dict[str, Any], AsyncGenerator[str, None]]:
        """处理聊天补全请求的核心方法"""
        pass
