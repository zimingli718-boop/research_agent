import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import time
import json
import requests
import urllib.parse
import xml.etree.ElementTree as ET
from pathlib import Path


class ArxivClient:
    """arXiv 论文检索客户端（遵守 3 秒/请求 限流）"""

    BASE_URL = "http://export.arxiv.org/api/query"
    CACHE_DIR = Path("E:/research_agent/data/arxiv_cache")
    DOWNLOAD_DIR = Path("E:/research_agent/data/downloads")

    def __init__(self):
        self.CACHE_DIR.mkdir(parents=True, exist_ok=True)
        self.DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)
        self._last_request_time = 0

    def _rate_limit(self):
        """确保每次请求间隔 >= 3 秒"""
        elapsed = time.time() - self._last_request_time
        if elapsed < 3:
            time.sleep(3 - elapsed)
        self._last_request_time = time.time()

    def _cache_path(self, key: str) -> Path:
        """缓存文件路径"""
        safe_key = "".join(c if c.isalnum() else "_" for c in key)[:100]
        return self.CACHE_DIR / f"{safe_key}.json"

    def _load_cache(self, key: str) -> dict:
        """读缓存"""
        path = self._cache_path(key)
        if path.exists():
            try:
                with open(path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return None
        return None

    def _save_cache(self, key: str, data: dict):
        """写缓存"""
        path = self._cache_path(key)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def search(self, query: str, max_results: int = 10, use_cache: bool = True) -> list:
        """按关键词搜索 arXiv 论文"""
        cache_key = f"search_{query}_{max_results}"
        if use_cache:
            cached = self._load_cache(cache_key)
            if cached:
                print(f"[Arxiv] 命中缓存: {query}")
                return cached.get("results", [])

        self._rate_limit()

        params = {
            "search_query": f"all:{query}",
            "start": 0,
            "max_results": max_results,
            "sortBy": "submittedDate",
            "sortOrder": "descending",
        }
        url = f"{self.BASE_URL}?{urllib.parse.urlencode(params)}"

        print(f"[Arxiv] 请求: {query}")
        try:
            resp = requests.get(url, timeout=30)
            resp.raise_for_status()
            xml_data = resp.text
        except Exception as e:
            print(f"[Arxiv] 请求失败: {e}")
            return []

        results = self._parse_atom(xml_data)
        self._save_cache(cache_key, {"query": query, "results": results})
        return results

    def search_by_title(self, title: str, use_cache: bool = True) -> dict:
        """按标题精确搜索，返回第一条结果"""
        cache_key = f"title_{title}"
        if use_cache:
            cached = self._load_cache(cache_key)
            if cached:
                print(f"[Arxiv] 命中缓存: {title}")
                return cached.get("result")

        self._rate_limit()

        params = {
            "search_query": f'ti:"{title}"',
            "start": 0,
            "max_results": 1,
        }
        url = f"{self.BASE_URL}?{urllib.parse.urlencode(params)}"

        print(f"[Arxiv] 请求标题: {title}")
        try:
            resp = requests.get(url, timeout=30)
            resp.raise_for_status()
            xml_data = resp.text
        except Exception as e:
            print(f"[Arxiv] 请求失败: {e}")
            return None

        results = self._parse_atom(xml_data)
        result = results[0] if results else None
        self._save_cache(cache_key, {"title": title, "result": result})
        return result

    def download_pdf(self, arxiv_id: str) -> str:
        """下载 arXiv PDF 到本地，返回本地路径"""
        base_id = arxiv_id.split("v")[0]
        pdf_url = f"https://arxiv.org/pdf/{base_id}.pdf"
        local_file = self.DOWNLOAD_DIR / f"{base_id}.pdf"

        if local_file.exists() and local_file.stat().st_size > 10000:
            print(f"[Arxiv] 已存在: {local_file}")
            return str(local_file)

        print(f"[Arxiv] 下载 PDF: {pdf_url}")
        try:
            resp = requests.get(pdf_url, timeout=60, stream=True)
            resp.raise_for_status()
            with open(local_file, "wb") as f:
                for chunk in resp.iter_content(chunk_size=8192):
                    f.write(chunk)
            print(f"[Arxiv] 已保存: {local_file}（{local_file.stat().st_size // 1024} KB）")
            return str(local_file)
        except Exception as e:
            print(f"[Arxiv] 下载失败: {e}")
            return ""

    def search_and_download(self, title: str) -> dict:
        """给定标题，搜索并下载"""
        result = self.search_by_title(title)
        if not result:
            print(f"[Arxiv] 未找到: {title}")
            return None

        pdf_path = self.download_pdf(result["id"])
        return {
            **result,
            "local_pdf": pdf_path,
        }

    def _parse_atom(self, xml_data: str) -> list:
        """解析 arXiv Atom XML"""
        ns = {
            "atom": "http://www.w3.org/2005/Atom",
            "arxiv": "http://arxiv.org/schemas/atom",
        }
        root = ET.fromstring(xml_data)
        results = []

        for entry in root.findall("atom:entry", ns):
            id_url = entry.find("atom:id", ns).text
            arxiv_id = id_url.split("/abs/")[-1]

            title = entry.find("atom:title", ns).text.strip().replace("\n", " ")
            abstract = entry.find("atom:summary", ns).text.strip().replace("\n", " ")

            authors = [
                a.find("atom:name", ns).text
                for a in entry.findall("atom:author", ns)
            ]

            published = entry.find("atom:published", ns).text

            pdf_url = ""
            for link in entry.findall("atom:link", ns):
                if link.get("title") == "pdf":
                    pdf_url = link.get("href")
                    break
            if not pdf_url:
                pdf_url = f"https://arxiv.org/pdf/{arxiv_id}.pdf"

            categories = [c.get("term") for c in entry.findall("atom:category", ns)]

            results.append({
                "id": arxiv_id,
                "title": title,
                "authors": authors,
                "abstract": abstract,
                "published": published,
                "pdf_url": pdf_url,
                "categories": categories,
                "abs_url": f"https://arxiv.org/abs/{arxiv_id}",
            })

        return results