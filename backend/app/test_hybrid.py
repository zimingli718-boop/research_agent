import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.hybrid_retriever import HybridRetriever

retriever = HybridRetriever()

query = "What is the attention mechanism?"
print(f"\n=== 混合检索：{query} ===")

results = retriever.search(query, top_k=3, use_rerank=True)

for i, r in enumerate(results):
    print(f"\n[结果 {i+1}]")
    if "rerank_score" in r:
        print(f"重排得分: {r['rerank_score']:.4f}")
    if "distance" in r:
        print(f"向量距离: {r['distance']:.4f}")
    if "score" in r:
        print(f"BM25 得分: {r['score']:.4f}")
    print(f"内容: {r['content'][:200]}...")