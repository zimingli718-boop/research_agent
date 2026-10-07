import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.pdf_parser import PDFParser
from services.structure_extractor import StructureExtractor
from services.deduplicator import Deduplicator

# 解析 v7 和 v1（模拟"库中已有 v7"）
parser = PDFParser(output_dir="E:/research_agent/data/parsed")
extractor = StructureExtractor()

print("=== 解析 v7 ===")
v7 = parser.parse_flash("E:/research_agent/data/1706.03762v7.pdf")
v7_struct = extractor.extract(v7["markdown"])

print("\n=== 解析 v1 ===")
v1 = parser.parse_flash("E:/research_agent/data/1706.03762v1.pdf")
v1_struct = extractor.extract(v1["markdown"])

# 模拟库中已有 v7
existing_papers = [{
    "id": v7["paper_id"],
    "title": "Attention Is All You Need (v7)",
    "abstract": v7_struct["abstract"],
}]

# 检测 v1 是否与 v7 重复
dedup = Deduplicator()
result = dedup.check_duplicate(v1_struct["abstract"], existing_papers)

print("\n=== 去重检测结果 ===")
print(f"是否重复: {result['is_duplicate']}")
print(f"相似度: {result['similarity']:.4f}")
if result["is_duplicate"]:
    print(f"匹配论文: {result['matched_paper']['title']}")
    print(f"建议操作: {result['suggested_action']}")