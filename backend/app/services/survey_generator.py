import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import re
from dotenv import load_dotenv
from openai import OpenAI

from models.database import SessionLocal, Paper

load_dotenv()


class SurveyGenerator:
    """自动综述生成：基于论文摘要和图谱结构，调用 LLM 生成领域综述"""

    def __init__(self):
        self.client = OpenAI(
            api_key=os.getenv("DEEPSEEK_API_KEY"),
            base_url=os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com"),
            timeout=300,
        )
        self.model = "deepseek-chat"

    def generate_survey(self, graph_data: dict = None) -> dict:
        """
        生成领域综述
        graph_data: 引用图谱数据（可选，用于提供上下文）
        """
        # 1. 从数据库拿所有论文的标题和摘要
        db = SessionLocal()
        try:
            papers = db.query(Paper).filter(Paper.abstract != None).all()
        finally:
            db.close()

        if not papers:
            return {"error": "库中没有论文"}

        print(f"[Survey] 从 {len(papers)} 篇论文生成综述")

        # 2. 准备上下文
        paper_infos = []
        for p in papers:
            paper_infos.append({
                "title": p.title or "Untitled",
                "abstract": (p.abstract or "")[:500],  # 限制长度
                "year": p.created_at.year if p.created_at else "未知",
            })

        # 3. 如果传了图谱数据，加上 PageRank 信息
        graph_info = ""
        if graph_data:
            nodes = graph_data.get("nodes", [])
            # 按 pagerank 排序
            sorted_nodes = sorted(nodes, key=lambda x: x.get("pagerank", 0), reverse=True)
            if sorted_nodes:
                graph_info = "\n\n【图论分析结果（按 PageRank 排序）】\n"
                for i, node in enumerate(sorted_nodes[:5], 1):
                    graph_info += f"{i}. {node.get('label', '')}（PageRank: {node.get('pagerank', 0):.3f}）\n"

        # 4. 组装论文信息
        context = ""
        for i, p in enumerate(paper_infos, 1):
            context += f"\n[论文 {i}]\n标题: {p['title']}\n年份: {p['year']}\n摘要: {p['abstract']}...\n"

        # 5. 调用 LLM 生成综述
        prompt = f"""你是一位学术综述专家。请基于以下论文信息，为该研究领域撰写一段简短的学术综述（400-600字）。

要求：
1. 使用学术综述的规范格式（如"近年来，xxx领域取得了..."）
2. 概述领域发展脉络和核心方法
3. 如果有图论分析结果，指出核心文献的地位
4. **必须标注引用来源**，格式为 [论文 N]
5. 不要编造信息，只基于提供的摘要内容

论文信息：
{context}
{graph_info}

请撰写综述："""

        print("[Survey] 调用 DeepSeek 生成综述...")
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.5,
            max_tokens=2000,
        )

        survey_text = response.choices[0].message.content

        # 6. 返回综述 + 引用论文列表
        return {
            "survey": survey_text,
            "papers": [
                {
                    "index": i + 1,
                    "title": p["title"],
                    "year": p["year"],
                }
                for i, p in enumerate(paper_infos)
            ],
            "paper_count": len(paper_infos),
        }