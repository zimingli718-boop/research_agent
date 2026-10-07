import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.chunker import Chunker
from services.bm25_retriever import BM25Retriever


class HybridRetriever:
    """混合检索：Dense (BGE-M3) + Sparse (BM25) + RRF 融合 + FlashRank 重排"""

    def __init__(self):
        print("[HybridRetriever] 初始化...")
        self.chunker = Chunker()
        self.bm25 = BM25Retriever()
        self._ranker = None

    @property
    def ranker(self):
        if self._ranker is None:
            from flashrank import Ranker
            print("[HybridRetriever] 加载 FlashRank 重排器...")
            self._ranker = Ranker()
        return self._ranker

    def search(self, query: str, top_k: int = 5, paper_ids: list = None, use_rerank: bool = True) -> list:
        dense_hits = self.chunker.search(query, top_k=top_k * 2, paper_ids=paper_ids)
        sparse_hits = self.bm25.search(query, top_k=top_k * 2)
        fused = self._rrf_fusion(dense_hits, sparse_hits)
        if use_rerank and fused:
            fused = self._rerank(query, fused, top_k)
        else:
            fused = fused[:top_k]
        return fused

    def _rrf_fusion(self, dense_hits: list, sparse_hits: list, k: int = 60) -> list:
        scores = {}
        docs = {}
        for rank, hit in enumerate(dense_hits):
            key = hit["content"][:100]
            scores[key] = scores.get(key, 0) + 1 / (k + rank + 1)
            docs[key] = hit
        for rank, hit in enumerate(sparse_hits):
            key = hit["content"][:100]
            scores[key] = scores.get(key, 0) + 1 / (k + rank + 1)
            if key not in docs:
                docs[key] = hit
        sorted_keys = sorted(scores.keys(), key=lambda x: scores[x], reverse=True)
        return [docs[key] for key in sorted_keys]

    def _rerank(self, query: str, hits: list, top_k: int) -> list:
        from flashrank import RerankRequest
        passages = [
            {"id": i, "text": hit["content"], "meta": hit.get("metadata", {})}
            for i, hit in enumerate(hits)
        ]
        rerank_request = RerankRequest(query=query, passages=passages)
        results = self.ranker.rerank(rerank_request)
        reranked = []
        for r in results[:top_k]:
            original = hits[r["id"]]
            original["rerank_score"] = r["score"]
            reranked.append(original)
        return reranked