import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import re
import shutil
import uuid
# 加在 import 之后
_STRUCTURE_CACHE = {}
_REFERENCE_CACHE = {}
from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import FileResponse

from services.pdf_parser import PDFParser
from services.structure_extractor import StructureExtractor
from services.chunker import Chunker
from services.bm25_retriever import BM25Retriever
from services.deduplicator import Deduplicator
from services.pdf_locator import PDFLocator
from models.database import SessionLocal, Paper, Chunk

router = APIRouter()

parser = PDFParser(output_dir="E:/research_agent/data/parsed")
extractor = StructureExtractor()
chunker = Chunker()
bm25 = BM25Retriever()
deduplicator = Deduplicator()

UPLOAD_DIR = "E:/research_agent/data/uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


def assign_section_path(chunks, headings, paper_id):
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
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="只支持 PDF 文件")

    file_path = os.path.join(UPLOAD_DIR, f"{uuid.uuid4().hex}_{file.filename}")
    with open(file_path, "wb") as f:
        shutil.copyfileobj(file.file, f)
    print(f"[Upload] 文件已保存: {file_path}")

    try:
        parse_result = parser.parse_auto(file_path)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PDF 解析失败: {str(e)}")

    structure = extractor.extract(parse_result["markdown"])

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

    chunks = chunker.chunk_text(parse_result["markdown"])
    metadatas = assign_section_path(chunks, structure["headings"], parse_result["paper_id"])
    chunk_ids = chunker.add_chunks(parse_result["paper_id"], chunks, metadatas)

    all_data = chunker.collection.get()
    bm25.build_index(all_data["documents"], all_data["metadatas"])

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


@router.get("/papers/{paper_id}/pdf")
async def get_paper_pdf(paper_id: str):
    db = SessionLocal()
    try:
        paper = db.query(Paper).filter(Paper.id == paper_id).first()
        if not paper:
            raise HTTPException(status_code=404, detail="论文不存在")
        if not os.path.exists(paper.file_path):
            raise HTTPException(status_code=404, detail="PDF 文件不存在")
        return FileResponse(
            paper.file_path,
            media_type="application/pdf",
            headers={"Content-Disposition": "inline"},
        )
    finally:
        db.close()


@router.get("/papers/{paper_id}/structure")
async def get_paper_structure(paper_id: str):
    """获取论文的标题树结构（带缓存）"""
    # 1. 先查缓存
    if paper_id in _STRUCTURE_CACHE:
        return _STRUCTURE_CACHE[paper_id]

    db = SessionLocal()
    try:
        paper = db.query(Paper).filter(Paper.id == paper_id).first()
        if not paper:
            raise HTTPException(status_code=404, detail="论文不存在")
        if not os.path.exists(paper.markdown_path):
            raise HTTPException(status_code=404, detail="Markdown 文件不存在")

        with open(paper.markdown_path, "r", encoding="utf-8") as f:
            markdown = f.read()

        extractor = StructureExtractor()
        structure = extractor.extract(markdown)

        locator = PDFLocator(paper.file_path)
        located_headings = locator.locate_headings(structure["headings"])

        result = {
            "paper_id": paper_id,
            "title": paper.title,
            "total_pages": locator.doc.page_count,
            "headings": located_headings,
        }
        
        # 2. 写入缓存
        _STRUCTURE_CACHE[paper_id] = result
        return result
    finally:
        db.close()


@router.get("/papers/{paper_id}/references")
async def get_paper_references(paper_id: str):
    """提取论文的 References 列表"""
    db = SessionLocal()
    try:
        paper = db.query(Paper).filter(Paper.id == paper_id).first()
        if not paper:
            raise HTTPException(status_code=404, detail="论文不存在")

        if not os.path.exists(paper.markdown_path):
            raise HTTPException(status_code=404, detail="Markdown 文件不存在")

        with open(paper.markdown_path, "r", encoding="utf-8") as f:
            markdown = f.read()

        # 兼容各种标题格式
        ref_match = re.search(r'^#*\s*References\s*$', markdown, re.MULTILINE | re.IGNORECASE)
        refs = []
        if ref_match:
            ref_section = markdown[ref_match.end():]
            next_heading = re.search(r'^#\s+', ref_section, re.MULTILINE)
            if next_heading:
                ref_section = ref_section[:next_heading.start()]

            # 方式 1：[N] 格式
            pattern = re.compile(r'^\[(\d+)\]\s+(.+?)(?=^\[\d+\]|\Z)', re.MULTILINE | re.DOTALL)
            for match in pattern.finditer(ref_section):
                ref_num = int(match.group(1))
                ref_text = match.group(2).strip().replace("\n", " ")
                ref_text = re.sub(r'\s+', ' ', ref_text)[:300]
                refs.append({"num": ref_num, "text": ref_text})
            
            # 方式 2：纯文本段落格式（如果 [N] 没提取到）
            if not refs:
                paragraphs = re.split(r'\n\s*\n', ref_section)
                for i, p in enumerate(paragraphs, start=1):
                    text = p.strip().replace("\n", " ")
                    text = re.sub(r'\s+', ' ', text)
                    if len(text) > 20:
                        refs.append({"num": i, "text": text[:300]})

        # 用 PyMuPDF 定位
        locator = PDFLocator(paper.file_path)
        ref_section_loc = locator.locate_ref_section()
        ref_page = ref_section_loc["page"] if ref_section_loc else None

        exclude_pages = []
        if ref_page:
            exclude_pages = list(range(ref_page, locator.doc.page_count + 1))

        max_num = max([r["num"] for r in refs], default=0) + 5
        citations = locator.locate_citations(max_ref_num=max_num, exclude_pages=exclude_pages)

        for ref in refs:
            num_str = str(ref["num"])
            locs = citations.get(num_str, [])
            in_text_pages = sorted(set(l["page"] for l in locs))

            ref["ref_page"] = ref_page
            ref["in_text_pages"] = in_text_pages
            ref["in_text_first_page"] = in_text_pages[0] if in_text_pages else None

        return {
            "paper_id": paper_id,
            "references": refs,
            "ref_section_page": ref_page,
        }
    finally:
        db.close()

@router.get("/papers/{paper_id}/page/{page_num}")
async def get_paper_page_text(paper_id: str, page_num: int):
    """获取论文指定页的文本（PyMuPDF 精确提取该页文字）"""
    db = SessionLocal()
    try:
        paper = db.query(Paper).filter(Paper.id == paper_id).first()
        if not paper:
            raise HTTPException(status_code=404, detail="论文不存在")

        if not os.path.exists(paper.file_path):
            raise HTTPException(status_code=404, detail="PDF 文件不存在")

        import pymupdf
        doc = pymupdf.open(paper.file_path)
        if page_num < 1 or page_num > doc.page_count:
            doc.close()
            raise HTTPException(status_code=400, detail="页码超出范围")

        page = doc[page_num - 1]
        page_text = page.get_text()
        doc.close()

        page_text = re.sub(r'\n{3,}', '\n\n', page_text).strip()

        return {
            "paper_id": paper_id,
            "page_num": page_num,
            "text": page_text[:5000],
            "format": "plain",
        }
    finally:
        db.close()