import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import re
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()


class Translator:
    """学术翻译：保护公式和代码，长文本按段落分段"""

    MAX_SEGMENT_CHARS = 2000

    def __init__(self):
        self.client = OpenAI(
            api_key=os.getenv("DEEPSEEK_API_KEY"),
            base_url=os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com"),
            timeout=300,
        )
        self.model = "deepseek-chat"

    def _protect_formulas(self, text: str) -> tuple:
        placeholders = {}
        counter = [0]

        def replace(match):
            key = f"__PROTECTED_{counter[0]}__"
            placeholders[key] = match.group(0)
            counter[0] += 1
            return key

        text = re.sub(r'\$\$[\s\S]+?\$\$', replace, text)
        text = re.sub(r'\$[^\$\n]+?\$', replace, text)
        text = re.sub(r'```[\s\S]*?```', replace, text)
        text = re.sub(r'`[^`\n]+?`', replace, text)

        return text, placeholders

    def _restore_formulas(self, text: str, placeholders: dict) -> str:
        for key, value in placeholders.items():
            text = text.replace(key, value)
        return text

    def _split_by_paragraph(self, text: str, max_chars: int) -> list:
        paragraphs = [p.strip() for p in text.split("\n") if p.strip()]
        segments = []
        current = ""

        for p in paragraphs:
            if len(p) > max_chars:
                if current:
                    segments.append(current)
                    current = ""
                sentences = re.split(r'(?<=[.!?])\s+', p)
                for sent in sentences:
                    if len(current) + len(sent) + 1 > max_chars:
                        if current:
                            segments.append(current)
                        current = sent
                    else:
                        current = current + " " + sent if current else sent
                continue

            if len(current) + len(p) + 1 > max_chars:
                if current:
                    segments.append(current)
                current = p
            else:
                current = current + "\n" + p if current else p

        if current:
            segments.append(current)

        return segments

    def _translate_single(self, text: str, target_lang: str) -> str:
        protected_text, placeholders = self._protect_formulas(text)

        lang_name = "中文" if target_lang == "zh" else "英文"
        prompt = f"""你是一位学术翻译专家。请将以下学术文本翻译为{lang_name}。

要求：
1. 保持学术规范，用词准确
2. 保持原文的段落结构（用空行分隔段落）
3. 不要翻译占位符（形如 __PROTECTED_N__），原样保留
4. 只输出翻译结果，不要添加任何解释

原文：
{protected_text}

翻译："""

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=8000,
        )

        translated = response.choices[0].message.content or ""
        return self._restore_formulas(translated, placeholders)

    def translate(self, text: str, target_lang: str = "zh") -> str:
        if not text.strip():
            return ""

        if len(text) <= self.MAX_SEGMENT_CHARS:
            return self._translate_single(text, target_lang)

        segments = self._split_by_paragraph(text, self.MAX_SEGMENT_CHARS)
        print(f"[Translator] 分段：{len(segments)} 段")

        translated_segments = []
        for i, seg in enumerate(segments):
            print(f"[Translator] 翻译第 {i+1}/{len(segments)} 段（{len(seg)} 字符）")
            translated = self._translate_single(seg, target_lang)
            if translated:
                translated_segments.append(translated)
            else:
                translated_segments.append(f"[第 {i+1} 段失败]")

        return "\n\n".join(translated_segments)