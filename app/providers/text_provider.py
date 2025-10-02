# app/providers/text_provider.py (v11.0 终极版 - 健壮的增量转换)

import httpx
import json
import uuid
import time
import traceback
import asyncio
from typing import Dict, Any, AsyncGenerator, Union, List

from fastapi import Request
from fastapi.responses import StreamingResponse, JSONResponse

from app.providers.base import BaseProvider
from app.core.config import settings

import logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


class TextProvider(BaseProvider):
    """
    通义千问全能提供商 (v11.0 终极版)
    - 采用最终修正的状态化解析器，逻辑清晰，确保将官网的“全量累积流”正确转换为客户端所需的“增量流”。
    - 彻底解决所有场景下的内容重复问题。
    - 保留了会话预热和国际站功能。
    """

    # --------------------------------------------------------------------------
    # 核心入口
    # --------------------------------------------------------------------------
    async def chat_completion(self, request_data: Dict[str, Any], original_request: Request) -> Union[StreamingResponse, JSONResponse]:
        model_name = request_data.get("model", "qwen-plus")
        task_type = self._get_task_type(model_name, request_data)
        try:
            if task_type in ["image", "video"]:
                logger.info(f"检测到 '{task_type}' 任务，强制使用国际站(INTL)模式...")
                return await self._handle_long_polling_task(request_data)
            else:
                account_id = settings.MODEL_TO_ACCOUNT_MAP.get(model_name, 1)
                logger.info(f"检测到模型 '{model_name}'，任务类型 '{task_type}'，将使用国内站账号 {account_id}...")
                return await self._handle_stream_task(request_data, account_id)
        except Exception as e:
            logger.error(f"处理任务时出错: {type(e).__name__}: {e}")
            traceback.print_exc()
            return JSONResponse(content={"error": {"message": f"处理任务时出错: {e}", "type": "provider_error"}}, status_code=500)

    # --------------------------------------------------------------------------
    # 国内站流式任务处理
    # --------------------------------------------------------------------------
    async def _handle_stream_task(self, request_data: Dict[str, Any], account_id: int) -> StreamingResponse:
        headers = self._prepare_cn_headers(account_id)
        await self._prewarm_session(headers)
        payload = self._prepare_cn_payload(request_data)
        model_name_for_client = request_data.get("model", "qwen-plus")
        url = "https://api.tongyi.com/dialog/conversation"
        logger.info(f"   [CN-Account-{account_id}] 正在向模型 '{model_name_for_client}' 发送流式请求...")
        return StreamingResponse(self._stream_generator(url, headers, payload, model_name_for_client), media_type="text/event-stream")

    async def _prewarm_session(self, headers: Dict[str, Any]):
        try:
            logger.info("   [Pre-warm] 正在发送会话预热请求...")
            url = "https://api.tongyi.com/assistant/api/record/list"
            payload = {
                "pageNo": 1, "terminal": "web", "pageSize": 10000, "module": "uploadhistory",
                "fileTypes": ["file", "audio", "video"], "recordSources": ["chat", "zhiwen", "tingwu"],
                "status": [20, 30, 40, 41], "taskTypes": ["local", "net_source", "doc_read", "paper_read", "book_read"]
            }
            async with httpx.AsyncClient() as client:
                prewarm_headers = headers.copy()
                prewarm_headers['Accept'] = 'application/json, text/plain, */*'
                response = await client.post(url, headers=prewarm_headers, json=payload, timeout=10)
                response.raise_for_status()
                logger.info("   [Pre-warm] ✅ 会话预热成功！")
        except Exception as e:
            logger.warning(f"   [Pre-warm] ⚠️ 会话预热失败: {e}。继续尝试...")

    # --------------------------------------------------------------------------
    # 终极版高级流式解析器 (v11.0) - 核心修改
    # --------------------------------------------------------------------------
    async def _stream_generator(self, url: str, headers: Dict, payload: Dict, model_name: str) -> AsyncGenerator[str, None]:
        """
        健壮的状态化流式生成器，将通义千问的“全量累积流”转换为标准的“增量流”。
        """
        chat_id = f"chatcmpl-{uuid.uuid4().hex}"
        is_first_chunk = True
        full_content_so_far = "" # 关键(1) 🧠: 状态变量在生成器函数的顶层作用域，确保在循环中持久存在

        try:
            async with httpx.AsyncClient(timeout=60) as client:
                async with client.stream("POST", url, headers=headers, json=payload) as response:
                    response.raise_for_status()
                    
                    async for line in response.aiter_lines():
                        if not line.startswith('data:'):
                            continue
                        
                        raw_data_str = line.strip()[len('data:'):]
                        if not raw_data_str or "[DONE]" in raw_data_str:
                            continue
                        
                        try:
                            qwen_data = json.loads(raw_data_str)
                            
                            # 从所有内容块中筛选出 'text' 类型的内容块
                            text_blocks = [block for block in qwen_data.get("contents", []) if block.get("contentType") == "text"]
                            if not text_blocks:
                                continue

                            # 通常我们只关心最后一个text块，因为它包含了最新的完整内容
                            latest_text_block = text_blocks[-1]
                            new_full_content = latest_text_block.get("content", "")
                            
                            if new_full_content is None:
                                continue

                            # 关键(2) 💡: 基于持久化的状态，精确计算增量
                            delta_content = ""
                            if new_full_content.startswith(full_content_so_far):
                                delta_content = new_full_content[len(full_content_so_far):]
                            else:
                                logger.warning(f"   [Stream Reset] 流内容不连续，将发送全部新内容。")
                                delta_content = new_full_content

                            # 如果没有实际的新内容，就跳过
                            if not delta_content:
                                continue

                            # 关键(3) ✅: 发送增量前，先发送角色信息（仅一次）
                            if is_first_chunk:
                                role_chunk = {
                                    "id": chat_id, "object": "chat.completion.chunk", "created": int(time.time()), "model": model_name,
                                    "choices": [{"index": 0, "delta": {"role": "assistant"}, "finish_reason": None}]
                                }
                                yield f"data: {json.dumps(role_chunk, ensure_ascii=False)}\n\n"
                                is_first_chunk = False

                            # 发送真正的增量内容块
                            openai_chunk = {
                                "id": chat_id, "object": "chat.completion.chunk", "created": int(time.time()), "model": model_name,
                                "choices": [{"index": 0, "delta": {"content": delta_content}, "finish_reason": None}]
                            }
                            yield f"data: {json.dumps(openai_chunk, ensure_ascii=False)}\n\n"
                            
                            # 关键(4) 🔄: 更新状态，为处理下一个 data: 消息做准备
                            full_content_so_far = new_full_content
                                
                        except json.JSONDecodeError:
                            logger.warning(f"   [Warning] JSON 解析失败: {raw_data_str}")
                            continue
            
            # 流结束，发送终止块
            final_chunk = {
                "id": chat_id, "object": "chat.completion.chunk", "created": int(time.time()), "model": model_name,
                "choices": [{"index": 0, "delta": {}, "finish_reason": "stop"}]
            }
            yield f"data: {json.dumps(final_chunk, ensure_ascii=False)}\n\n"
        
        except Exception as e:
            logger.error(f"   [Error] 流式生成器发生错误: {e}")
            traceback.print_exc()
        
        finally:
            logger.info("   [Stream] 流式传输结束。")
            yield "data: [DONE]\n\n"

    # --------------------------------------------------------------------------
    # 辅助函数 (保持不变)
    # --------------------------------------------------------------------------
    def _get_task_type(self, model_name: str, request_data: Dict[str, Any]) -> str:
        model_name_lower = model_name.lower()
        if "wanx" in model_name_lower: return "image"
        if "animate" in model_name_lower: return "video"
        if "vl" in model_name_lower or "qvq" in model_name_lower: return "vision"
        return "text"

    def _prepare_cn_headers(self, account_id: int) -> Dict[str, str]:
        try:
            cookie = getattr(settings, f"CN_ACCOUNT_{account_id}_COOKIE")
            xsrf_token = getattr(settings, f"CN_ACCOUNT_{account_id}_XSRF_TOKEN")
        except AttributeError: raise ValueError(f"国内站账号 {account_id} 的配置不完整。")
        if not cookie or not xsrf_token: raise ValueError(f"国内站账号 {account_id} 的认证信息为空。")
        safe_cookie = cookie.encode('utf-8').decode('latin-1')
        return {'Origin': 'https://www.tongyi.com', 'Referer': 'https://www.tongyi.com/', 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36', 'Cookie': safe_cookie, 'x-xsrf-token': xsrf_token, 'x-platform': 'pc_tongyi', 'Accept': 'text/event-stream', 'Content-Type': 'application/json;charset=UTF-8'}

    def _prepare_cn_payload(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        messages: List[Dict[str, Any]] = request_data.get("messages", [])
        if not messages: messages = [{"role": "user", "content": request_data.get("prompt", "你好")}]
        qwen_contents = []
        for msg in messages:
            content = msg.get("content")
            if isinstance(content, str): qwen_contents.append({"role": msg.get("role"), "content": content, "contentType": "text"})
        model_in_payload = request_data.get("model", "")
        return {"action": "next", "contents": qwen_contents, "model": model_in_payload, "parentMsgId": "", "requestId": str(uuid.uuid4()), "sessionId": "", "sessionType": "text_chat", "userAction": "new_top", "feature_config": {"search_enabled": False, "thinking_enabled": False}}

    # --------------------------------------------------------------------------
    # 国际站相关函数 (保留)
    # --------------------------------------------------------------------------
    def _prepare_intl_headers(self) -> Dict[str, str]:
        if not settings.INTL_AUTHORIZATION or not settings.INTL_COOKIE or not settings.INTL_BX_UA:
            raise ValueError("国际站(intl)认证信息不完整，请检查.env文件。")
        safe_cookie = settings.INTL_COOKIE.encode('utf-8').decode('latin-1')
        return {'Origin': 'https://chat.qwen.ai', 'Referer': 'https://chat.qwen.ai/', 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36', 'Authorization': settings.INTL_AUTHORIZATION, 'Cookie': safe_cookie, 'bx-ua': settings.INTL_BX_UA}

    async def _handle_long_polling_task(self, request_data: Dict[str, Any]) -> JSONResponse:
        headers = self._prepare_intl_headers()
        headers['Accept'] = 'application/json, text/event-stream'
        headers['Content-Type'] = 'application/json;charset=UTF-8'
        completions_url = "https://chat.qwen.ai/api/v2/chat/completions"
        task_status_url_template = "https://chat.qwen.ai/api/v1/tasks/status/{task_id}"
        prompt = request_data.get("prompt", "一只猫")
        model_name = "wanx-v1" if "wanx" in request_data.get("model", "") else "animate-v1"
        msg_type = "t2i" if model_name == "wanx-v1" else "t2v"
        payload = {"action": "next", "contents": [{"content": prompt, "contentType": "text", "role": "user"}], "msg_type": msg_type, "mode": "chat", "model": model_name, "parentMsgId": "", "requestId": str(uuid.uuid4())}
        async with httpx.AsyncClient(timeout=60) as client:
            logger.info(f"   [INTL] 正在启动 '{model_name}' 任务...")
            response = await client.post(completions_url, headers=headers, json=payload)
            response.raise_for_status()
            task_id = None
            async for line in response.aiter_lines():
                if line.startswith('data:'):
                    try:
                        data = json.loads(line[len('data:'):])
                        if data.get("taskIds"):
                            task_id = data["taskIds"][0]
                            break
                    except json.JSONDecodeError: continue
            if not task_id: raise ValueError(f"{model_name} 任务启动失败。")
            logger.info(f"   [INTL] 成功获取任务 ID: {task_id}")
            for i in range(120):
                await asyncio.sleep(3)
                status_url = task_status_url_template.format(task_id=task_id)
                status_response = await client.get(status_url, headers=headers)
                if status_response.status_code == 200:
                    data = status_response.json()
                    if data.get("status") == "succeeded":
                        logger.info(f"   [INTL] {model_name} 任务成功！")
                        return self._format_media_response(data, request_data, model_name)
                    if data.get("status") == "failed":
                        raise RuntimeError(f"任务失败: {data.get('result', '未知错误')}")
            raise TimeoutError("任务超时。")

    def _format_media_response(self, task_result: Dict[str, Any], request_data: Dict[str, Any], task_type: str) -> JSONResponse:
        model_name = request_data.get("model")
        items = task_result.get("result", {}).get("images" if "wanx" in task_type else "videos", [])
        urls = [item.get("url") for item in items if item.get("url")]
        content = "\n".join(f"!image({url})" for url in urls) if "wanx" in task_type else "\n".join(f"视频链接: {url}" for url in urls)
        response_data = {"id": f"chatcmpl-{uuid.uuid4().hex}", "object": "chat.completion", "created": int(time.time()), "model": model_name, "choices": [{"index": 0, "message": {"role": "assistant", "content": content or "生成完成，但未能获取链接。"}, "finish_reason": "stop"}], "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}}
        return JSONResponse(content=response_data)