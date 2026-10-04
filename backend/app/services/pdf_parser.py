import os
import uuid
from pathlib import Path
from dotenv import load_dotenv
from mineru import MinerU

load_dotenv()


class PDFParser:

    def __init__(self, output_dir: str = "./data/parsed"):
        self.client = MinerU()
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def parse_flash(self, pdf_path: str) -> dict:
        """使用 flash 模式解析（免 Token，速度快）"""
        pdf_path = str(Path(pdf_path).resolve())
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"PDF 文件不存在: {pdf_path}")

        print(f"[PDFParser] flash 模式解析: {pdf_path}")
        result = self.client.flash_extract(pdf_path)

        paper_id = str(uuid.uuid4())
        paper_dir = self.output_dir / paper_id
        paper_dir.mkdir(parents=True, exist_ok=True)

        md_path = paper_dir / "content.md"
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(result.markdown)

        return {
            "paper_id": paper_id,
            "markdown": result.markdown,
            "markdown_path": str(md_path),
            "pdf_path": pdf_path,
            "page_count": getattr(result, "page_count", None),
            "mode": "flash",
        }

    def parse_precise(self, pdf_path: str) -> dict:
        """使用精准模式解析（需要 Token，支持公式、表格、扫描件）"""
        pdf_path = str(Path(pdf_path).resolve())
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"PDF 文件不存在: {pdf_path}")

        print(f"[PDFParser] 精准模式解析: {pdf_path}")
        result = self.client.extract(pdf_path)

        paper_id = str(uuid.uuid4())
        paper_dir = self.output_dir / paper_id
        paper_dir.mkdir(parents=True, exist_ok=True)

        md_path = paper_dir / "content.md"
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(result.markdown)

        return {
            "paper_id": paper_id,
            "markdown": result.markdown,
            "markdown_path": str(md_path),
            "pdf_path": pdf_path,
            "page_count": getattr(result, "page_count", None),
            "mode": "precise",
        }