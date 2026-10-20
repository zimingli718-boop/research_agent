import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import re
from dotenv import load_dotenv
from openai import OpenAI

from models.database import SessionLocal, Paper

load_dotenv()


class FutureWorkAnalyzer:
    """Future Work 提取与去重：提炼真正有价值的未来研究方向"""

    def __init__(self):
        self.client = OpenAI(
            api_key=os.getenv("DEEPSEEK_API_KEY"),
            base_url=os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com"),
            timeout=300,
        )
        self.model = "deepseek-chat"

    def _extract_future_work(self, markdown: str) -> str:
        """从 Markdown 提取 Future Work / Conclusion 段落"""
        # 找 Conclusion 或 Future Work 章节
        pattern = re.compile(
            r'^#+\s*(Conclusion|Conclusions|Future Work|Discussion|总结|结论|未来工作)\s*$',
            re.MULTILINE | re.IGNORECASE
        )
        match = pattern.search(markdown)
        if not match:
            # 兜底：找最后 20% 的文本
            lines = markdown.split("\n")
            start = int(len(lines) * 0.8)
            return "\n".join(lines[start:])[:2000]

        section = markdown[match.end():]
        # 截断到下一个一级标题
        next_heading = re.search(r'^#\s+', section, re.MULTILINE)
        if next_heading:
            section = section[:next_heading.start()]

        return section.strip()[:2000]

    def analyze(self) -> dict:
        """分析所有论文的 Future Work"""
        db = SessionLocal()
        try:
            papers = db.query(Paper).filter(Paper.markdown_path != None).all()
        finally:
            db.close()

        if not papers:
            return {"error": "库中没有论文"}

        # 1. 逐篇提取 Future Work
        future_works = []
        for p in papers:
            if not p.markdown_path or not os.path.exists(p.markdown_path):
                continue

            with open(p.markdown_path, "r", encoding="utf-8") as f:
                markdown = f.read()

            fw_text = self._extract_future_work(markdown)
            if fw_text and len(fw_text) > 100:
                future_works.append({
                    "paper_title": p.title,
                    "year": p.created_at.year if p.created_at else None,
                    "future_work": fw_text,
                })
                print(f"[FutureWork] 提取到: {p.title[:40]}（{len(fw_text)} 字符）")

        if not future_works:
            return {"error": "没有提取到 Future Work 内容"}

        # 2. 组装上下文，调用 LLM 去重 + 时效性分析
        context = ""
        for i, fw in enumerate(future_works, 1):
            context += f"\n\n[论文 {i}] {fw['paper_title']}（{fw['year']}）\n{fw['future_work']}"

        prompt = f"""你是一位学术前沿分析专家。以下是多篇论文的"结论/未来工作"段落。请提炼出真正有探索价值的未来研究方向。

要求：
1. **合并相似方向**：把不同论文提到的同类 future work 合并
2. **去重**：如果某方向已在后续论文中被解决，标注"（已被后续工作解决）"
3. **时效性排序**：越新提出的方向越优先
4. 输出 3-5 个真正有探索价值的方向，每个方向说明：
   - 方向名称
   - 提出该方向的论文（标注年份）
   - 为什么有价值

论文信息：
{context}

请输出结构化的分析结果（Markdown 格式）："""

        print("[FutureWork] 调用 DeepSeek 分析...")
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.5,
            max_tokens=2500,
        )

        return {
            "analysis": response.choices[0].message.content,
            "paper_count": len(future_works),
            "papers": [
                {"title": fw["paper_title"], "year": fw["year"]}
                for fw in future_works
            ],
        }