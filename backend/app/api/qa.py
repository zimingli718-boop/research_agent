import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
import asyncio
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Optional

from agents.rag_agent import RAGAgent
from agents.graph_router import GraphRouter

router = APIRouter()

rag_agent = RAGAgent()
graph_router = GraphRouter()
graph_router.retriever = rag_agent.retriever


class QARequest(BaseModel):
    query: str
    top_k: int = 5
    paper_ids: Optional[List[str]] = None


@router.post("/qa")
async def qa(request: QARequest):
    """RAG 问答（非流式）"""
    return rag_agent.answer(
        query=request.query,
        top_k=request.top_k,
        paper_ids=request.paper_ids,
    )


@router.post("/qa/stream")
async def qa_stream(request: QARequest):
    """RAG 问答（SSE 真 Token 级流式输出）"""
    async def event_generator():
        try:
            # 1. 异步执行 LangGraph 编排（加上 to_thread 防止阻塞主线程）
            state = await asyncio.to_thread(graph_router.run, request.query)
            
            intent = state.get("intent", "rag")
            is_valid = state.get("is_valid_whitelist", True)
            
            # 发送真实的意图状态给前端
            yield f"data: {json.dumps({'type': 'status', 'message': f'LangGraph 意图路由: {intent}'})}\n\n"
            
            # 如果是 RAG 且白名单校验失败，直接拦截
            if intent == "rag" and not is_valid:
                yield f"data: {json.dumps({'type': 'error', 'message': '白名单校验失败：检索内容不合法'})}\n\n"
                return

            # 2. 真正的 RAG 生成逻辑
            for event_type, data in rag_agent.answer_stream(
                query=request.query,
                top_k=request.top_k,
                paper_ids=request.paper_ids,
            ):
                if event_type == "status":
                    payload = {"type": "status", "message": data}
                elif event_type == "token":
                    payload = {"type": "token", "content": data}
                elif event_type == "sources":
                    payload = {"type": "sources", "sources": data}
                elif event_type == "guardrails":
                    payload = {"type": "guardrails", "guardrails": data}
                elif event_type == "done":
                    payload = {"type": "done"}
                else:
                    continue

                yield f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"

        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)}, ensure_ascii=False)}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )