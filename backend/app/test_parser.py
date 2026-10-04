import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.pdf_parser import PDFParser

parser = PDFParser(output_dir=r"E:\research_agent\data\parsed")

result = parser.parse_flash(r"E:\research_agent\data\1706.03762v7.pdf")

print("\n=== 解析结果 ===")
print(f"paper_id: {result['paper_id']}")
print(f"mode: {result['mode']}")
print(f"markdown_path: {result['markdown_path']}")
print(f"markdown 前 300 字:\n{result['markdown'][:300]}")