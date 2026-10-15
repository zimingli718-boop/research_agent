import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
from sentence_transformers import SentenceTransformer

from models.database import SessionLocal, Paper


class Recommender:
    """个性化推荐：基于用户本地文献库的 embedding 兴趣向量"""

    def __init__(self, model_path: str = "E:/research_agent/models/bge-m3"):
        print("[Recommender] 加载 BGE-M3 模型...")
        self.model = SentenceTransformer(model_path)
        print("[Recommender] 模型加载完成")

    def _get_user_interest_vector(self) -> np.ndarray:
        """从用户本地库的论文摘要计算兴趣向量（均值）"""
        db = SessionLocal()
        try:
            papers = db.query(Paper).filter(Paper.abstract != None).all()
            abstracts = [p.abstract for p in papers if p.abstract and len(p.abstract) > 50]
        finally:
            db.close()

        if not abstracts:
            return None

        print(f"[Recommender] 从 {len(abstracts)} 篇本地论文计算兴趣向量")
        embeddings = self.model.encode(abstracts, show_progress_bar=False)
        interest_vector = np.mean(embeddings, axis=0)
        return interest_vector

    def rank_papers(self, candidate_papers: list, top_k: int = 10) -> list:
        """
        对候选论文按相关性排序
        candidate_papers: [{"id": ..., "title": ..., "abstract": ...}, ...]
        返回: 排序后的列表，每项加 "relevance_score" 字段
        """
        if not candidate_papers:
            return []

        interest_vector = self._get_user_interest_vector()
        if interest_vector is None:
            print("[Recommender] 本地库为空，返回原始顺序")
            return [{"relevance_score": 0.5, **p} for p in candidate_papers[:top_k]]

        # 计算候选论文的 embedding
        abstracts = [p.get("abstract", "") for p in candidate_papers]
        embeddings = self.model.encode(abstracts, show_progress_bar=False)

        # 计算余弦相似度
        interest_norm = np.linalg.norm(interest_vector)
        scores = []
        for emb in embeddings:
            emb_norm = np.linalg.norm(emb)
            if emb_norm == 0 or interest_norm == 0:
                sim = 0.0
            else:
                sim = float(np.dot(emb, interest_vector) / (emb_norm * interest_norm))
            scores.append(sim)

        # 排序
        ranked = []
        for p, s in zip(candidate_papers, scores):
            ranked.append({"relevance_score": round(s, 4), **p})

        ranked.sort(key=lambda x: x["relevance_score"], reverse=True)
        return ranked[:top_k]