import os
import uuid
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from dotenv import load_dotenv
from mineru import MinerU
import pymupdf

load_dotenv()

MAX_PAGES_PER_REQUEST = 20   # MinerU flash 单段页数上限
MAX_CONCURRENT = 5           # 并发数（太高会被 MinerU 限流）


class PDFParser:

    def __init__(self, output_dir: str = "./data/parsed"):
        self.client = MinerU(os.getenv("MINERU_TOKEN"))
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def _has_text_layer(self, pdf_path: str, sample_pages: int = 3) -> bool:
        try:
            doc = pymupdf.open(pdf_path)
            total_chars = 0
            pages_to_check = min(sample_pages, doc.page_count)
            for i in range(pages_to_check):
                page = doc[i]
                text = page.get_text().strip()
                total_chars += len(text)
            doc.close()
            return (total_chars / max(pages_to_check, 1)) > 50
        except Exception as e:
            print(f"[PDFParser] 文本层检测失败: {e}")
            return True

    def _split_pdf(self, pdf_path: str, max_pages: int) -> list:
        """把大 PDF 拆成多个小 PDF"""
        doc = pymupdf.open(pdf_path)
        total_pages = doc.page_count
        segments = []

        for start in range(0, total_pages, max_pages):
            end = min(start + max_pages, total_pages)
            new_doc = pymupdf.open()
            new_doc.insert_pdf(doc, from_page=start, to_page=end - 1)

            seg_path = f"{pdf_path}.seg_{start}_{end}.pdf"
            new_doc.save(seg_path)
            new_doc.close()
            segments.append({"path": seg_path, "start": start, "end": end})

        doc.close()
        return segments

    def _save_result(self, markdown: str, pdf_path: str, mode: str, page_count=None) -> dict:
        if not markdown:
            raise ValueError(f"{mode} 模式返回空 markdown")

        paper_id = str(uuid.uuid4())
        paper_dir = self.output_dir / paper_id
        paper_dir.mkdir(parents=True, exist_ok=True)

        md_path = paper_dir / "content.md"
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(markdown)

        return {
            "paper_id": paper_id,
            "markdown": markdown,
            "markdown_path": str(md_path),
            "pdf_path": pdf_path,
            "page_count": page_count,
            "mode": mode,
        }

    def _parse_one_segment(self, seg: dict, mode: str) -> tuple:
        """解析单段，返回 (seg, markdown, error)"""
        try:
            if mode == "flash":
                result = self.client.flash_extract(seg["path"])
            else:
                result = self.client.extract(seg["path"])

            markdown = getattr(result, "markdown", None)
            return (seg, markdown, None)
        except Exception as e:
            return (seg, None, str(e))
        finally:
            if os.path.exists(seg["path"]):
                os.remove(seg["path"])

    def _parse_segmented_concurrent(self, pdf_path: str, mode: str, total_pages: int) -> dict:
        """并发分段解析大文档"""
        segments = self._split_pdf(pdf_path, MAX_PAGES_PER_REQUEST)
        print(f"[PDFParser] 拆分为 {len(segments)} 段，并发 {MAX_CONCURRENT} 个线程处理...")

        results = {}  # start_page -> markdown

        with ThreadPoolExecutor(max_workers=MAX_CONCURRENT) as executor:
            futures = {
                executor.submit(self._parse_one_segment, seg, mode): seg
                for seg in segments
            }

            completed = 0
            for future in as_completed(futures):
                seg, markdown, error = future.result()
                completed += 1
                if markdown:
                    results[seg["start"]] = markdown
                    print(f"[PDFParser] 完成 {completed}/{len(segments)}: 第 {seg['start']+1}-{seg['end']} 页（{len(markdown)} 字符）")
                else:
                    print(f"[PDFParser] 失败 {completed}/{len(segments)}: 第 {seg['start']+1}-{seg['end']} 页（{error}）")

        # 按页码顺序拼接
        all_markdown = []
        for start_page in sorted(results.keys()):
            all_markdown.append(f"\n\n<!-- ===== 第 {start_page+1} 页起 ===== -->\n\n")
            all_markdown.append(results[start_page])

        full_markdown = "".join(all_markdown)

        if not full_markdown.strip():
            raise ValueError("所有段解析都失败")

        return self._save_result(full_markdown, pdf_path, mode, total_pages)

    def parse_flash(self, pdf_path: str) -> dict:
        pdf_path = str(Path(pdf_path).resolve())
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"PDF 文件不存在: {pdf_path}")

        doc = pymupdf.open(pdf_path)
        total_pages = doc.page_count
        doc.close()

        if total_pages <= MAX_PAGES_PER_REQUEST:
            print(f"[PDFParser] flash 模式解析: {pdf_path}（{total_pages} 页）")
            result = self.client.flash_extract(pdf_path)
            markdown = getattr(result, "markdown", None)
            try:
                return self._save_result(markdown, pdf_path, "flash", total_pages)
            except ValueError as e:
                print(f"[PDFParser] flash 失败: {e}，降级到精准模式")
                return self.parse_precise(pdf_path)

        return self._parse_segmented_concurrent(pdf_path, "flash", total_pages)

    def parse_precise(self, pdf_path: str) -> dict:
        pdf_path = str(Path(pdf_path).resolve())
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"PDF 文件不存在: {pdf_path}")

        doc = pymupdf.open(pdf_path)
        total_pages = doc.page_count
        doc.close()

        if total_pages <= MAX_PAGES_PER_REQUEST:
            print(f"[PDFParser] 精准模式解析: {pdf_path}（{total_pages} 页）")
            result = self.client.extract(pdf_path)
            markdown = getattr(result, "markdown", None)
            return self._save_result(markdown, pdf_path, "precise", total_pages)

        return self._parse_segmented_concurrent(pdf_path, "precise", total_pages)

    def parse_auto(self, pdf_path: str) -> dict:
        pdf_path = str(Path(pdf_path).resolve())
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"PDF 文件不存在: {pdf_path}")

        if self._has_text_layer(pdf_path):
            print(f"[PDFParser] 检测到文本层，使用 flash 模式")
            return self.parse_flash(pdf_path)
        else:
            print(f"[PDFParser] 检测为扫描件，使用精准模式（OCR）")
            return self.parse_precise(pdf_path)