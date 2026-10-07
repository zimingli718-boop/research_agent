import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
from openai import OpenAI

from services.hybrid_retriever import HybridRetriever

load_dotenv()


class RAGAgent:
    """RAG 问答：混合检索 → 上下文组装 → LLM 生成 → 溯源标注"""

    def __init__(self):
        print("[RAGAgent] 初始化...")
        self.retriever = HybridRetriever()
        self.client = OpenAI(
            api_key=os.getenv("DEEPSEEK_API_KEY"),
            base_url=os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com"),
        )
        self.model = os.getenv("DEEPSEEK_MODEL", "deepseek-flash")
        print(f"[RAGAgent] 使用模型: {self.model}")

    def answer(self, query: str, top_k: int = 5, paper_ids: list = None) -> dict:
        """
        完整 RAG 流程：
        1. 混合检索
        2. 组装上下文（带来源编号）
        3. LLM 生成（要求标注 [来源N]）
        4. 返回答案 + 引用来源
        """
        # 1. 检索
        hits = self.retriever.search(query, top_k=top_k, paper_ids=paper_ids)

        if not hits:
            return {
                "answer": "检索库中没有找到相关内容，无法回答。",
                "sources": [],
                "query": query,
            }

        # 2. 组装上下文
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

        # 3. LLM 生成
        prompt = f"""你是一位学术研究助手。基于以下检索到的论文内容回答用户问题。

严格要求：
1. 每个事实声明后必须标注来源编号，格式为 [来源N]
2. 只使用检索内容中的信息，不要编造
3. 如果检索内容不足以回答问题，明确说"检索内容不足以回答此问题"
4. 涉及数字、超参数、模型名称、引用信息时，必须精确引用原文

检索内容：
{context}

用户问题：{query}

请给出准确、有据可查的回答："""

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            max_tokens=1500,
        )

        answer = response.choices[0].message.content

        return {
            "answer": answer,
            "sources": sources,
            "query": query,
        }