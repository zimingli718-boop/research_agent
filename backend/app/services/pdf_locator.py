import os
import re
import pymupdf


class PDFLocator:
    """用 PyMuPDF 精确定位 PDF 里的文本位置"""

    def __init__(self, pdf_path: str):
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"PDF 不存在: {pdf_path}")
        self.doc = pymupdf.open(pdf_path)
        self.pdf_path = pdf_path

    def locate_text(self, text: str, max_pages: int = None) -> list:
        """搜索文本，返回所有匹配位置的页码和坐标"""
        results = []
        end = max_pages or self.doc.page_count
        for page_num in range(end):
            page = self.doc[page_num]
            hits = page.search_for(text)
            for hit in hits:
                results.append({
                    "page": page_num + 1,
                    "x": round(hit.x0, 1),
                    "y": round(hit.y0, 1),
                })
        return results

    def locate_first(self, text: str) -> dict:
        """搜索文本，返回第一次出现的位置"""
        results = self.locate_text(text)
        return results[0] if results else None

    def locate_headings(self, headings: list) -> list:
        """批量定位标题"""
        located = []
        for h in headings:
            title = h["title"].strip()
            loc = self.locate_first(title)
            located.append({
                **h,
                "page": loc["page"] if loc else None,
                "y": loc["y"] if loc else None,
            })
        return located

    def locate_ref_section(self) -> dict:
        """定位 References 章节"""
        return self.locate_first("References")

    def locate_citations(self, max_ref_num: int = 100, exclude_pages: list = None) -> dict:
        """
        搜索所有引用位置，返回每个引用编号出现的所有位置。
        exclude_pages: 要排除的页码列表（如 References 页）
        """
        exclude_pages = exclude_pages or []
        citations = {str(n): [] for n in range(1, max_ref_num + 1)}

        for page_num in range(self.doc.page_count):
            if (page_num + 1) in exclude_pages:
                continue

            page = self.doc[page_num]
            text = page.get_text()

            # 匹配所有 [...] 格式的引用块（支持 [15]、[38, 24, 15]、[15, 16] 等）
            blocks = re.finditer(r'\[[\d,\s]+\]', text)

            for block in blocks:
                block_text = block.group(0)
                nums = re.findall(r'\d+', block_text)

                for num_str in nums:
                    num = int(num_str)
                    if 1 <= num <= max_ref_num:
                        # 用块起始字符位置估算 y 坐标（每行约 80 字符）
                        char_idx = block.start()
                        y = (char_idx // 80) * 15
                        citations[num_str].append({
                            "page": page_num + 1,
                            "y": y,
                        })

        # 去重
        for num_str in citations:
            seen = set()
            unique = []
            for loc in citations[num_str]:
                key = (loc["page"], round(loc["y"], 0))
                if key not in seen:
                    seen.add(key)
                    unique.append(loc)
            citations[num_str] = unique

        return {k: v for k, v in citations.items() if v}