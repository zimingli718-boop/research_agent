import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
from openai import OpenAI

from services.hybrid_retriever import HybridRetriever
from agents.guardrails import Guardrails

load_dotenv()


class RAGAgent:
    """RAG 问答：混合检索 → 上下文组装 → LLM 生成 → 溯源标注 → Guardrails 校验"""

    def __init__(self):
        print("[RAGAgent] 初始化...")
        self.retriever = HybridRetriever()
        self.guardrails = Guardrails()
        self.client = OpenAI(
            api_key=os.getenv("DEEPSEEK_API_KEY"),
            base_url=os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com"),
        )
        self.model = os.getenv("DEEPSEEK_MODEL", "deepseek-flash")
        print(f"[RAGAgent] 使用模型: {self.model}")

    def _retrieve_and_build_context(self, query: str, top_k: int, paper_ids: list):
        """公共方法：检索 + 组装上下文"""
        hits = self.retriever.search(query, top_k=top_k, paper_ids=paper_ids)
        context_parts = []
        sources = []
        for i, hit in enumerate(hits, start=1):
            meta = hit.get("metadata", {})
            content = hit["content"]
            context_parts.append(f"[来源{i}] {content}")
            sources.append({
                "index": i,
                "paper_id": meta.get("paper_id", ""),
                "chunk_index": meta.get("chunk_index", ""),
                "section_path": meta.get("section_path", ""),
                "page_number": meta.get("page_number"),
                "content_preview": content[:200],
            })
        context = "\n\n---\n\n".join(context_parts)
        return hits, context, sources

    def _build_prompt(self, context: str, query: str) -> str:
        return f"""你是一位学术研究助手。基于以下检索到的论文内容回答用户问题。

严格要求：
1. 每个事实声明后必须标注来源编号，格式为 [来源N]
2. 只使用检索内容中的信息，不要编造
3. 如果检索内容不足以回答问题，明确说"检索内容不足以回答此问题"
4. 涉及数字、超参数、模型名称、引用信息时，必须精确引用原文

检索内容：
{context}

用户问题：{query}

请给出准确、有据可查的回答："""

    def answer(self, query: str, top_k: int = 5, paper_ids: list = None) -> dict:
        """非流式 RAG 问答"""
        hits, context, sources = self._retrieve_and_build_context(query, top_k, paper_ids)

        if not hits:
            return {
                "answer": "检索库中没有找到相关内容，无法回答。",
                "sources": [],
                "query": query,
                "guardrails": {
                    "total_sentences": 0,
                    "unsupported_sentences": [],
                    "faithfulness_score": 0.0,
                    "citations_used": [],
                },
            }

        prompt = self._build_prompt(context, query)

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            max_tokens=1500,
        )

        answer = response.choices[0].message.content
        guard_result = self.guardrails.verify(answer, sources)

        return {
            "answer": answer,
            "sources": sources,
            "query": query,
            "guardrails": guard_result,
        }

    def answer_stream(self, query: str, top_k: int = 5, paper_ids: list = None):
        """
        流式 RAG 问答：逐 token yield
        yield 格式：(type, data)
        """
        # 1. 检索
        yield ("status", "正在检索...")
        hits, context, sources = self._retrieve_and_build_context(query, top_k, paper_ids)

        if not hits:
            yield ("token", "检索库中没有找到相关内容，无法回答。")
            yield ("done", None)
            return

        # 2. LLM 流式生成
        prompt = self._build_prompt(context, query)

        stream = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            max_tokens=1500,
            stream=True,
        )

        full_answer = ""
        for chunk in stream:
            delta = chunk.choices[0].delta
            if delta and delta.content:
                full_answer += delta.content
                yield ("token", delta.content)

        # 3. Guardrails 校验
        guard_result = self.guardrails.verify(full_answer, sources)

        yield ("sources", sources)
        yield ("guardrails", guard_result)
        yield ("done", None)