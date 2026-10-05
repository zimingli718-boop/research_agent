import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.pdf_parser import PDFParser
from services.structure_extractor import StructureExtractor
from services.chunker import Chunker

# 解析 PDF
parser = PDFParser(output_dir=r"E:\research_agent\data\parsed")
result = parser.parse_flash(r"E:\research_agent\data\1706.03762v7.pdf")

# 分块
chunker = Chunker()
chunks = chunker.chunk_text(result["markdown"])
print(f"\n=== 分块完成，共 {len(chunks)} 个 chunk ===")

# 向量化并写入 ChromaDB
chunk_ids = chunker.add_chunks(result["paper_id"], chunks)

# 检索测试
print("\n=== 检索测试：What is the attention mechanism? ===")
hits = chunker.search("What is the attention mechanism?", top_k=3)
for i, hit in enumerate(hits):
    print(f"\n[结果 {i+1}] 距离: {hit['distance']:.4f}")
    print(f"内容: {hit['content'][:200]}...")