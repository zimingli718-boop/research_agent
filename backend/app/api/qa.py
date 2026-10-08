import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Optional

from agents.rag_agent import RAGAgent

router = APIRouter()

rag_agent = RAGAgent()


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