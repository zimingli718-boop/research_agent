import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
from openai import OpenAI

from models.database import SessionLocal, Paper
from services.hybrid_retriever import HybridRetriever

load_dotenv()


class WriterAgent:
    def __init__(self):
        self.client = OpenAI(
            api_key=os.getenv("DEEPSEEK_API_KEY"),
            base_url=os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com"),
            timeout=300,
        )
        self.model = "deepseek-chat"
        self.retriever = HybridRetriever()

    def generate_outline(self, idea: str) -> dict:
        """10月17日上午：论文框架生成（LLM + 真实引用）"""
        db = SessionLocal()
        try:
            papers = db.query(Paper).all()
        finally:
            db.close()

        real_refs = [f"- {p.title} ({p.authors[:50] if p.authors else 'Unknown'})" for p in papers if p.title]
        refs_context = "\n".join(real_refs)

        prompt = f"""你是一位学术写作专家。请基于以下研究 idea，生成一份论文框架（Abstract、Introduction、Related Work）。

**研究 Idea**：{idea}

**可用真实参考文献库**：
{refs_context}

严格要求：
1. Related Work 部分**必须引用上面提供的真实文献**。
2. **严禁编造不存在的参考文献**。
3. 以 Markdown 格式输出，包含 `## Abstract`、`## Introduction`、`## Related Work`。

请生成："""

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.4,
            max_tokens=2500,
        )

        return {
            "outline": response.choices[0].message.content,
            "available_refs": real_refs,
        }

    def generate_diagram(self, description: str, diagram_type: str = "mermaid") -> str:
        """10月17日下午：拓扑图脚本生成（支持 Mermaid / Graphviz / TikZ）"""
        prompt = f"""你是一位技术绘图专家。请根据以下描述，生成一个 {diagram_type} 格式的架构图代码。

**描述**：{description}

要求：
1. 只输出可运行的 {diagram_type} 代码。
2. 不要输出 Markdown 标记（不要 ``` 包裹），直接输出纯代码。
3. 排版紧凑，节点清晰。

代码："""

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
        )
        code = response.choices[0].message.content.strip()
        if code.startswith("```"):
            lines = code.split("\n")
            code = "\n".join(lines[1:-1])
        return code.strip()

    def translate_academic(self, text: str, target_lang: str = "en") -> str:
        """10月17日晚上：学术翻译（全文翻译 + 术语一致）"""
        lang_name = "英文" if target_lang == "en" else "中文"
        prompt = f"""你是一位学术翻译专家。请将以下学术文本翻译为{lang_name}。

要求：
1. 保持学术规范，用词准确，术语前后一致。
2. 公式和代码（如 $x$、`code`）保留原文不翻译。
3. 只输出翻译结果，不要添加任何解释。

原文：
{text}

翻译："""
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
        )
        return response.choices[0].message.content.strip()