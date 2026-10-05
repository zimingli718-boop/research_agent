import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.chunker import Chunker
from services.bm25_retriever import BM25Retriever

# 从 ChromaDB 取出所有 chunk
chunker = Chunker()
all_data = chunker.collection.get()
chunks = all_data["documents"]
metadatas = all_data["metadatas"]

print(f"\n从 ChromaDB 读到 {len(chunks)} 个 chunk")

# 构建 BM25 索引
bm25 = BM25Retriever()
bm25.build_index(chunks, metadatas)

# 检索测试
print("\n=== BM25 检索：attention mechanism ===")
results = bm25.search("attention mechanism", top_k=3)
for i, r in enumerate(results):
    print(f"\n[结果 {i+1}] 得分: {r['score']:.4f}")
    print(f"内容: {r['content'][:200]}...")