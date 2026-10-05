import os
import uuid
from pathlib import Path
from sentence_transformers import SentenceTransformer
import chromadb
from dotenv import load_dotenv

load_dotenv()


class Chunker:

    def __init__(self, persist_dir: str = None):
        # 加载 BGE-M3 模型（首次运行会下载约 2GB 模型文件）
        print("[Chunker] 正在加载 BGE-M3 模型...")
        self.model = SentenceTransformer("E:/research_agent/models/bge-m3")
        print("[Chunker] BGE-M3 加载完成")

        # 初始化 ChromaDB
        persist_dir = persist_dir or os.getenv(
            "CHROMA_PERSIST_DIR", "E:/research_agent/data/chroma"
        )
        Path(persist_dir).mkdir(parents=True, exist_ok=True)
        self.client = chromadb.PersistentClient(path=persist_dir)
        self.collection = self.client.get_or_create_collection(
            name="paper_chunks",
            metadata={"hnsw:space": "cosine"},
        )
        print(f"[Chunker] ChromaDB 就绪，持久化目录: {persist_dir}")

    def chunk_text(self, text: str, chunk_size: int = 512, overlap: int = 64) -> list:
        """按字符数分块（带重叠），返回 chunk 列表"""
        if not text:
            return []

        chunks = []
        start = 0
        while start < len(text):
            end = start + chunk_size
            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)
            start = end - overlap  # 重叠部分

        return chunks

    def add_chunks(self, paper_id: str, chunks: list, metadatas: list = None) -> list:
        """将分块向量化并存入 ChromaDB，返回 chunk ID 列表"""
        if not chunks:
            return []

        # 批量生成 embedding
        print(f"[Chunker] 正在向量化 {len(chunks)} 个 chunk...")
        embeddings = self.model.encode(chunks, show_progress_bar=False).tolist()

        # 生成唯一 ID
        ids = [f"{paper_id}_{i}_{uuid.uuid4().hex[:8]}" for i in range(len(chunks))]

        # 默认 metadata
        if metadatas is None:
            metadatas = [{"paper_id": paper_id, "chunk_index": i} for i in range(len(chunks))]
        else:
            for i, m in enumerate(metadatas):
                m.setdefault("paper_id", paper_id)
                m.setdefault("chunk_index", i)

        # 写入 ChromaDB
        self.collection.add(
            ids=ids,
            embeddings=embeddings,
            documents=chunks,
            metadatas=metadatas,
        )
        print(f"[Chunker] 已写入 {len(ids)} 个 chunk 到 ChromaDB")

        return ids

    def search(self, query: str, top_k: int = 5, paper_ids: list = None) -> list:
        """向量检索"""
        query_emb = self.model.encode([query]).tolist()

        where = {"paper_id": {"$in": paper_ids}} if paper_ids else None

        results = self.collection.query(
            query_embeddings=query_emb,
            n_results=top_k,
            where=where,
        )

        hits = []
        if results and results["ids"] and results["ids"][0]:
            for i in range(len(results["ids"][0])):
                hits.append({
                    "id": results["ids"][0][i],
                    "content": results["documents"][0][i],
                    "metadata": results["metadatas"][0][i],
                    "distance": results["distances"][0][i],
                })
        return hits