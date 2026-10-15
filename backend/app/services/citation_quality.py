import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import re


class CitationQualityScorer:
    """引用含金量评分：位置 × 长度 × 评价词"""

    # 引用位置权重（所在 section 的权重）
    POSITION_WEIGHTS = {
        "introduction": 1.0,
        "method": 1.0,
        "approach": 1.0,
        "model": 0.9,
        "architecture": 0.9,
        "experiment": 0.8,
        "result": 0.7,
        "discussion": 0.7,
        "related work": 0.5,
        "background": 0.5,
        "conclusion": 0.3,
        "appendix": 0.2,
    }

    # 评价性词汇（含这些词 → 高分）
    EVALUATIVE_WORDS = [
        "outperform", "state-of-the-art", "sota", "crucial", "fundamental",
        "essential", "significant", "novel", "pioneering", "breakthrough",
        "superior", "best", "effective", "powerful", "influential",
        "improve", "advance", "extend", "build on", "based on",
        "inspired by", "follow", "adopt",
    ]

    def score_citation(self, context: str, section: str = "") -> dict:
        """
        对单个引用上下文评分
        context: 引用附近的文本
        section: 引用所在的章节名（如 "Introduction"、"Related Work"）
        返回: {"score": float, "position_score": float, "length_score": float, "keyword_score": float, "level": str}
        """
        position_score = self._score_position(section)
        length_score = self._score_length(context)
        keyword_score = self._score_keywords(context)

        # 加权总分（位置 0.4，长度 0.3，评价词 0.3）
        total = position_score * 0.4 + length_score * 0.3 + keyword_score * 0.3

        # 等级
        if total >= 0.75:
            level = "high"      # 基石引用
        elif total >= 0.45:
            level = "medium"    # 重要引用
        else:
            level = "low"       # 边缘引用

        return {
            "score": round(total, 4),
            "position_score": round(position_score, 4),
            "length_score": round(length_score, 4),
            "keyword_score": round(keyword_score, 4),
            "level": level,
        }

    def _score_position(self, section: str) -> float:
        """位置评分：根据章节名判断"""
        if not section:
            return 0.5
        section_lower = section.lower()
        for key, weight in self.POSITION_WEIGHTS.items():
            if key in section_lower:
                return weight
        return 0.5

    def _score_length(self, context: str) -> float:
        """长度评分：上下文越长，讨论越深入"""
        length = len(context.strip())
        if length >= 500:
            return 1.0
        elif length >= 300:
            return 0.8
        elif length >= 150:
            return 0.6
        elif length >= 80:
            return 0.4
        else:
            return 0.2

    def _score_keywords(self, context: str) -> float:
        """评价词评分：含评价词越多，含金量越高"""
        context_lower = context.lower()
        hits = sum(1 for w in self.EVALUATIVE_WORDS if w in context_lower)
        if hits >= 3:
            return 1.0
        elif hits == 2:
            return 0.7
        elif hits == 1:
            return 0.4
        else:
            return 0.1

    def score_paper_citations(self, markdown: str, headings: list, citations: dict) -> dict:
        """
        对整篇论文的所有引用评分
        markdown: 全文 Markdown
        headings: 标题列表（含 line_number）
        citations: {ref_num: [in_text_locations], ...}
        返回: {ref_num: {"score": ..., "level": ..., "contexts": [...]}, ...}
        """
        lines = markdown.split("\n")
        results = {}

        for ref_num_str, locations in citations.items():
            ref_num = int(ref_num_str)
            contexts = []

            # 找到每个引用位置附近的文本
            for loc in locations:
                page = loc.get("page", 1)
                # 用页码估算行号
                total_pages = max([l.get("page", 1) for l in locations], default=1)
                estimated_line = int((page - 1) / total_pages * len(lines))
                context = self._extract_context(lines, estimated_line)
                section = self._find_section(headings, estimated_line)
                contexts.append({
                    "page": page,
                    "section": section,
                    "context": context,
                })

            # 对第一个位置评分（简化：只评第一个）
            if contexts:
                first = contexts[0]
                score_result = self.score_citation(first["context"], first["section"])
                results[ref_num_str] = {
                    **score_result,
                    "contexts": contexts,
                }

        return results

    def _extract_context(self, lines: list, center_line: int, window: int = 5) -> str:
        """提取某行附近 window 行的文本"""
        start = max(0, center_line - window)
        end = min(len(lines), center_line + window)
        return "\n".join(lines[start:end])

    def _find_section(self, headings: list, line_number: int) -> str:
        """找到某行所属的章节"""
        section = ""
        for h in headings:
            if h.get("line_number", 0) <= line_number:
                section = h.get("title", "")
            else:
                break
        return section