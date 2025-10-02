# main.py (v7.2 终极版 - 包含模型列表接口)

import traceback
import time
from typing import Optional, List, Dict, Any

from fastapi import FastAPI, Request, HTTPException, Depends, Header

from app.core.config import settings
from app.providers.text_provider import TextProvider

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description=settings.DESCRIPTION
)

# 只需一个全能的 Provider
text_provider = TextProvider()


# --- 认证依赖项 (保持不变) ---
async def verify_api_key(authorization: Optional[str] = Header(None)):
    """
    检查 API 密钥的依赖项。
    如果设置了 API_MASTER_KEY，则请求头中必须包含正确的密钥。
    """
    # 如果 .env 或 docker-compose.yml 中没有配置 API_MASTER_KEY，则跳过认证
    if not settings.API_MASTER_KEY:
        print("警告：未配置 API_MASTER_KEY，服务将对所有请求开放。")
        return

    # 如果配置了密钥，但请求头中没有 Authorization，则拒绝
    if authorization is None:
        raise HTTPException(
            status_code=401,
            detail="Unauthorized: Missing Authorization header.",
        )
    
    # 检查认证方案和密钥是否正确
    try:
        scheme, token = authorization.split()
        if scheme.lower() != "bearer":
            raise ValueError("Invalid scheme")
    except ValueError:
        raise HTTPException(
            status_code=401,
            detail="Invalid authentication scheme. Use 'Bearer <your_api_key>'.",
        )
    
    # 核心验证：将传入的 token 与我们的主密钥进行安全比较
    if token != settings.API_MASTER_KEY:
        raise HTTPException(
            status_code=403,
            detail="Forbidden: Invalid API Key.",
        )
    # 认证通过，请求将继续被处理


# --- 核心聊天接口 (保持不变) ---
@app.post("/v1/chat/completions", dependencies=[Depends(verify_api_key)])
async def chat_completions(request: Request):
    """
    终极路由：所有请求都交给全能的 TextProvider 处理。
    在处理前会先通过 verify_api_key 进行认证。
    """
    try:
        request_data = await request.json()
        print("接收到聊天请求，认证通过，路由到全能的 TextProvider...")
        return await text_provider.chat_completion(request_data, request)
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"主路由发生内部服务器错误: {str(e)}")


# --- 【⭐ 新增功能 ⭐】模型列表接口 ---
@app.get("/v1/models", dependencies=[Depends(verify_api_key)])
async def list_models():
    """
    新增的接口，用于返回兼容OpenAI格式的模型列表。
    它会读取 config.py 中的 SUPPORTED_MODELS 列表。
    """
    print("接收到模型列表请求，认证通过...")
    
    # 从我们的配置文件中获取模型列表
    model_names: List[str] = settings.SUPPORTED_MODELS
    
    # 将模型列表包装成OpenAI API兼容的格式
    model_data: List[Dict[str, Any]] = []
    for name in model_names:
        model_data.append({
            "id": name,
            "object": "model",
            "created": int(time.time()),
            "owned_by": "system"
        })
        
    return {
        "object": "list",
        "data": model_data
    }


# --- 根路由 (保持不变) ---
@app.get("/")
def root():
    """根路由，提供服务基本信息，无需认证。"""
    return {"message": f"Welcome to {settings.APP_NAME}", "version": settings.APP_VERSION}