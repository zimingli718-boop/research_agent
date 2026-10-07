import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import shutil
import uuid
from fastapi import APIRouter, UploadFile, File, HTTPException

from services.pdf_parser import PDFParser
from services.structure_extractor import StructureExtractor
from services.chunker import Chunker
from services.bm25_retriever import BM25Retriever
from services.deduplicator import Deduplicator
from models.database import SessionLocal, Paper, Chunk

router = APIRouter()

# 全局实例（避免每次请求都重新加载模型）
parser = PDFParser(output_dir="E:/research_agent/data/parsed")
extractor = StructureExtractor()
chunker = Chunker()
bm25 = BM25Retriever()
deduplicator = Deduplicator()

UPLOAD_DIR = "E:/research_agent/data/uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


def assign_section_path(chunks, headings, paper_id):
    """为每个 chunk 推断所属的 section_path"""
    metadatas = []
    for i, chunk in enumerate(chunks):
        section_path = ""
        for h in headings:
            if h["title"] in chunk[:200]:
                section_path = h["title"]
                break
        if not section_path and metadatas:
            section_path = metadatas[-1]["section_path"]
        metadatas.append({
            "paper_id": paper_id,
            "chunk_index": i,
            "section_path": section_path,
        })
    return metadatas


@router.post("/upload")
async def upload_pdf(file: UploadFile = File(...)):
    """上传 PDF → 解析 → 分块 → 向量化 → 入库"""
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="只支持 PDF 文件")

    # 1. 保存上传文件
    file_path = os.path.join(UPLOAD_DIR, f"{uuid.uuid4().hex}_{file.filename}")
    with open(file_path, "wb") as f:
        shutil.copyfileobj(file.file, f)
    print(f"[Upload] 文件已保存: {file_path}")

    # 2. 解析 PDF
    try:
        parse_result = parser.parse_flash(file_path)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PDF 解析失败: {str(e)}")

    # 3. 结构化抽取
    structure = extractor.extract(parse_result["markdown"])

    # 3.5 语义去重检测
    db_check = SessionLocal()
    try:
        existing_papers = [
            {"id": p.id, "title": p.title, "abstract": p.abstract}
            for p in db_check.query(Paper).all()
            if p.abstract
        ]
    finally:
        db_check.close()

    dup_result = deduplicator.check_duplicate(structure["abstract"], existing_papers)

    if dup_result["is_duplicate"]:
        return {
            "status": "duplicate_detected",
            "similarity": round(dup_result["similarity"], 4),
            "matched_paper_id": dup_result["matched_paper"]["id"],
            "matched_paper_title": dup_result["matched_paper"]["title"],
            "message": f"库中已有高度相似的论文（相似度 {dup_result['similarity']:.2%}），建议保留已有版本",
            "suggested_action": "keep_existing",
            "new_paper_id": parse_result["paper_id"],
        }

    # 4. 分块 + 向量化（带 section_path 推断）
    chunks = chunker.chunk_text(parse_result["markdown"])
    metadatas = assign_section_path(chunks, structure["headings"], parse_result["paper_id"])
    chunk_ids = chunker.add_chunks(parse_result["paper_id"], chunks, metadatas)

    # 5. 更新 BM25 索引（增量追加）
    all_data = chunker.collection.get()
    bm25.build_index(all_data["documents"], all_data["metadatas"])

    # 6. 写入 SQLite
    db = SessionLocal()
    try:
        paper = Paper(
            id=parse_result["paper_id"],
            title=structure["headings"][0]["title"] if structure["headings"] else file.filename,
            authors=" | ".join(structure["authors"][:10]),
            abstract=structure["abstract"][:2000],
            file_path=file_path,
            markdown_path=parse_result["markdown_path"],
            page_count=parse_result.get("page_count"),
            parse_mode=parse_result.get("mode"),
        )
        db.add(paper)

        for i, (cid, content) in enumerate(zip(chunk_ids, chunks)):
            db.add(Chunk(
                id=cid,
                paper_id=parse_result["paper_id"],
                content=content,
                chunk_index=i,
            ))
        db.commit()
        paper_title = paper.title
    finally:
        db.close()

    return {
        "status": "success",
        "paper_id": parse_result["paper_id"],
        "title": paper_title,
        "authors_count": len(structure["authors"]),
        "headings_count": len(structure["headings"]),
        "chunks_count": len(chunks),
        "abstract_preview": structure["abstract"][:200],
    }


@router.get("/papers")
async def list_papers():
    """列出所有已上传的论文"""
    db = SessionLocal()
    try:
        papers = db.query(Paper).order_by(Paper.created_at.desc()).all()
        return {
            "total": len(papers),
            "papers": [
                {
                    "id": p.id,
                    "title": p.title,
                    "authors": p.authors,
                    "page_count": p.page_count,
                    "created_at": p.created_at.isoformat() if p.created_at else None,
                }
                for p in papers
            ],
        }
    finally:
        db.close()