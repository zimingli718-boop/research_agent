import re


class StructureExtractor:
    """从 MinerU 输出的 Markdown 中抽取结构化信息"""

    def extract(self, markdown: str) -> dict:
        lines = markdown.split("\n")

        headings = self._extract_headings(lines)
        abstract = self._extract_abstract(lines)
        authors = self._extract_authors(lines)

        return {
            "headings": headings,
            "abstract": abstract,
            "authors": authors,
            "full_text": markdown,
        }

    def _extract_headings(self, lines: list) -> list:
        """提取标题树（一级到三级）"""
        headings = []
        for i, line in enumerate(lines):
            match = re.match(r"^(#{1,3})\s+(.+)", line)
            if match:
                headings.append({
                    "level": len(match.group(1)),
                    "title": match.group(2).strip(),
                    "line_number": i,
                })
        return headings

    def _extract_abstract(self, lines: list) -> str:
        """提取摘要（从 Abstract 标题后到下一个标题前）"""
        abstract_lines = []
        in_abstract = False

        for line in lines:
            # 检测 Abstract 标题
            if re.match(r"^#+\s*(Abstract|ABSTRACT|摘要)", line):
                in_abstract = True
                continue

            # 遇到下一个标题就结束
            if in_abstract and re.match(r"^#+\s+", line):
                break

            if in_abstract and line.strip():
                abstract_lines.append(line.strip())

        return " ".join(abstract_lines)

    def _extract_authors(self, lines: list) -> list:
        """从标题行后提取作者信息（简化版：找带 * 或 @ 的行）"""
        authors = []
        for line in lines[:50]:  
            
            if re.search(r"[\w.+-]+@[\w-]+\.[\w.-]+", line):
                authors.append(line.strip())
            elif re.match(r"^[A-Z][a-z]+\s+[A-Z][a-z]+", line) and "*" in line:
                authors.append(line.strip())
        return authors