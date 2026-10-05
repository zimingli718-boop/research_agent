import os
import pickle
import jieba
from rank_bm25 import BM25Okapi
from pathlib import Path


class BM25Retriever:
    """BM25 稀疏检索（关键词匹配）"""

    def __init__(self, index_path: str = "E:/research_agent/data/bm25_index.pkl"):
        self.index_path = index_path
        self.corpus = []       # chunk 文本列表
        self.metadata = []     # 对应的 metadata
        self.bm25 = None

        # 尝试加载已有索引
        if os.path.exists(index_path):
            self._load()

    def _tokenize(self, text: str) -> list:
        """英文按空格 + 中文按 jieba 分词"""
        # 简单方案：英文小写后按空格分，中文用 jieba
        tokens = []
        for token in text.lower().split():
            # 对含中文的部分用 jieba 再分
            if any('\u4e00' <= c <= '\u9fff' for c in token):
                tokens.extend(jieba.lcut(token))
            else:
                tokens.append(token)
        return tokens

    def build_index(self, chunks: list, metadatas: list = None):
        """构建 BM25 索引"""
        if not chunks:
            print("[BM25] 没有 chunk，跳过")
            return

        self.corpus = chunks
        self.metadata = metadatas or [{} for _ in chunks]

        tokenized = [self._tokenize(c) for c in chunks]
        self.bm25 = BM25Okapi(tokenized)

        # 保存到磁盘
        Path(self.index_path).parent.mkdir(parents=True, exist_ok=True)
        with open(self.index_path, "wb") as f:
            pickle.dump({
                "corpus": self.corpus,
                "metadata": self.metadata,
            }, f)

        print(f"[BM25] 索引构建完成，共 {len(chunks)} 个文档")

    def _load(self):
        """从磁盘加载索引"""
        with open(self.index_path, "rb") as f:
            data = pickle.load(f)
        self.corpus = data["corpus"]
        self.metadata = data["metadata"]
        tokenized = [self._tokenize(c) for c in self.corpus]
        self.bm25 = BM25Okapi(tokenized)
        print(f"[BM25] 已加载索引，共 {len(self.corpus)} 个文档")

    def search(self, query: str, top_k: int = 5) -> list:
        """BM25 检索"""
        if not self.bm25:
            return []

        tokenized_query = self._tokenize(query)
        scores = self.bm25.get_scores(tokenized_query)

        top_indices = sorted(
            range(len(scores)), key=lambda i: scores[i], reverse=True
        )[:top_k]

        results = []
        for i in top_indices:
            if scores[i] > 0:
                results.append({
                    "content": self.corpus[i],
                    "metadata": self.metadata[i],
                    "score": float(scores[i]),
                })
        return results