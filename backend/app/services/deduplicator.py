import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
from sentence_transformers import SentenceTransformer


class Deduplicator:

    def __init__(self, model_path: str = "E:/research_agent/models/bge-m3"):
        print("[Deduplicator] 正在加载 BGE-M3 模型...")
        self.model = SentenceTransformer(model_path)
        print("[Deduplicator] 模型加载完成")

    def compute_similarity(self, text1: str, text2: str) -> float:
        """计算两段文本的余弦相似度"""
        if not text1 or not text2:
            return 0.0

        embeddings = self.model.encode([text1, text2])
        vec1, vec2 = embeddings[0], embeddings[1]

        # 余弦相似度
        cos_sim = np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))
        return float(cos_sim)

    def check_duplicate(self, new_abstract: str, existing_papers: list, threshold: float = 0.92) -> dict:
        """
        检查新论文是否与已有论文重复
        existing_papers: [{"id": ..., "title": ..., "abstract": ...}, ...]
        返回: {"is_duplicate": bool, "similarity": float, "matched_paper": dict or None}
        """
        if not new_abstract or not existing_papers:
            return {"is_duplicate": False, "similarity": 0.0, "matched_paper": None}

        new_emb = self.model.encode([new_abstract])[0]
        existing_abstracts = [p.get("abstract", "") for p in existing_papers]
        existing_embs = self.model.encode(existing_abstracts)

        # 批量计算余弦相似度
        similarities = np.dot(existing_embs, new_emb) / (
            np.linalg.norm(existing_embs, axis=1) * np.linalg.norm(new_emb)
        )

        max_idx = int(np.argmax(similarities))
        max_sim = float(similarities[max_idx])

        if max_sim >= threshold:
            return {
                "is_duplicate": True,
                "similarity": max_sim,
                "matched_paper": existing_papers[max_idx],
                "suggested_action": "keep_existing",
            }
        return {
            "is_duplicate": False,
            "similarity": max_sim,
            "matched_paper": None,
        }