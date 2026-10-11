import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import re
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()


class Translator:
    """学术翻译：保护公式和代码，调用 LLM 翻译"""

    def __init__(self):
        self.client = OpenAI(
            api_key=os.getenv("DEEPSEEK_API_KEY"),
            base_url=os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com"),
        )
        self.model = os.getenv("DEEPSEEK_MODEL", "deepseek-flash")

    def _protect_formulas(self, text: str) -> tuple:
        """用占位符替换公式和代码，避免被翻译"""
        placeholders = {}
        counter = [0]

        def replace(match):
            key = f"__PROTECTED_{counter[0]}__"
            placeholders[key] = match.group(0)
            counter[0] += 1
            return key

        # 保护 LaTeX 行内公式 $...$
        text = re.sub(r'\$[^\$]+\$', replace, text)
        # 保护 LaTeX 块公式 $$...$$
        text = re.sub(r'\$\$[^\$]+\$\$', replace, text)
        # 保护代码块 ```...```
        text = re.sub(r'```[\s\S]*?```', replace, text)
        # 保护行内代码 `...`
        text = re.sub(r'`[^`]+`', replace, text)

        return text, placeholders

    def _restore_formulas(self, text: str, placeholders: dict) -> str:
        """恢复被保护的公式和代码"""
        for key, value in placeholders.items():
            text = text.replace(key, value)
        return text

    def translate(self, text: str, target_lang: str = "zh") -> str:
        """翻译文本，保护公式和代码"""
        if not text.strip():
            return ""

        protected_text, placeholders = self._protect_formulas(text)

        lang_name = "中文" if target_lang == "zh" else "英文"
        prompt = f"""你是一位学术翻译专家。请将以下学术文本翻译为{lang_name}。

要求：
1. 保持学术规范，用词准确
2. 不要翻译占位符（形如 __PROTECTED_N__ 的内容），原样保留
3. 保持原文的段落结构
4. 只输出翻译结果，不要添加任何解释

原文：
{protected_text}

翻译："""

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=4000,
        )

        translated = response.choices[0].message.content
        return self._restore_formulas(translated, placeholders)