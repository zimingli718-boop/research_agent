import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.pdf_parser import PDFParser
from services.structure_extractor import StructureExtractor

# 解析 PDF
parser = PDFParser(output_dir=r"E:\research_agent\data\parsed")
result = parser.parse_flash(r"E:\research_agent\data\1706.03762v7.pdf")

# 抽取结构
extractor = StructureExtractor()
structure = extractor.extract(result["markdown"])

print("\n=== 标题树 ===")
for h in structure["headings"][:15]:
    indent = "  " * (h["level"] - 1)
    print(f"{indent}[L{h['level']}] {h['title']}")

print(f"\n=== 摘要（前 300 字） ===")
print(structure["abstract"][:300])

print(f"\n=== 作者信息 ===")
for author in structure["authors"][:10]:
    print(f"  {author}")