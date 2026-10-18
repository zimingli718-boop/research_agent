import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import re
import json
import networkx as nx

from models.database import SessionLocal, Paper


class GraphBuilder:
    """引用图谱构建：解析论文间的引用关系，构建有向图"""

    def build_from_database(self) -> nx.DiGraph:
        """从数据库所有论文构建引用图谱"""
        db = SessionLocal()
        try:
            papers = db.query(Paper).all()
        finally:
            db.close()

        print(f"[Graph] 从数据库加载 {len(papers)} 篇论文")

        paper_meta = {}
        title_to_id = {}

        for p in papers:
            year = None
            if p.created_at:
                year = p.created_at.year
            paper_meta[p.id] = {
                "id": p.id,
                "title": p.title or "Untitled",
                "year": year,
                "authors": p.authors or "",
            }
            if p.title:
                norm = self._normalize_title(p.title)
                title_to_id[norm] = p.id

        G = nx.DiGraph()

        for pid, meta in paper_meta.items():
            G.add_node(pid, **meta)

        db = SessionLocal()
        try:
            for p in papers:
                if not p.markdown_path or not os.path.exists(p.markdown_path):
                    continue

                with open(p.markdown_path, "r", encoding="utf-8") as f:
                    markdown = f.read()

                refs = self._extract_references(markdown)
                print(f"[Graph] {p.title[:40]} 提取到 {len(refs)} 条 References")

                for ref_text in refs:
                    for norm_title, target_id in title_to_id.items():
                        if target_id == p.id:
                            continue
                        if self._title_matches(ref_text, norm_title):
                            G.add_edge(p.id, target_id, weight=1)
                            print(f"[Graph] 边: {p.title[:30]} → {paper_meta[target_id]['title'][:30]}")
        finally:
            db.close()

        print(f"[Graph] 完成：{G.number_of_nodes()} 个节点，{G.number_of_edges()} 条边")
        return G

    def _extract_references(self, markdown: str) -> list:
        """从 Markdown 提取 References 文本列表（支持 [N] 格式和纯文本段落格式）"""
        # 找 References 标题（支持 # References / ## References / References）
        ref_match = re.search(
            r'^#*\s*References\s*$',
            markdown, re.MULTILINE | re.IGNORECASE
        )
        if not ref_match:
            return []

        ref_section = markdown[ref_match.end():]
        # 截断到下一个一级标题
        next_heading = re.search(r'^#\s+', ref_section, re.MULTILINE)
        if next_heading:
            ref_section = ref_section[:next_heading.start()]

        # 方式 1：`[N]` 格式
        pattern = re.compile(r'^\[(\d+)\]\s+(.+?)(?=^\[\d+\]|\Z)', re.MULTILINE | re.DOTALL)
        refs = []
        for match in pattern.finditer(ref_section):
            text = match.group(2).strip().replace("\n", " ")
            text = re.sub(r'\s+', ' ', text)
            refs.append(text)

        if refs:
            return refs

        # 方式 2：纯文本段落格式（每条用空行分隔）
        paragraphs = re.split(r'\n\s*\n', ref_section)
        for p in paragraphs:
            text = p.strip().replace("\n", " ")
            text = re.sub(r'\s+', ' ', text)
            # 过滤太短的行（可能是标题残留）
            if len(text) > 20:
                refs.append(text)

        return refs

    def _normalize_title(self, title: str) -> str:
        """规范化标题：小写、去标点、去多余空格"""
        t = title.lower()
        t = re.sub(r'[^\w\s]', ' ', t)
        t = re.sub(r'\s+', ' ', t).strip()
        return t

    def _title_matches(self, ref_text: str, norm_title: str) -> bool:
        """判断 References 条目是否引用了某标题（匹配更宽松）"""
        norm_ref = self._normalize_title(ref_text)

        title_words = norm_title.split()
        # 短标题（<5 词）：完全包含即可
        if len(title_words) < 5:
            return norm_title in norm_ref

        # 长标题：用前 4 个词匹配
        key_phrase = " ".join(title_words[:4])
        if key_phrase in norm_ref:
            return True

        # 兜底：用前 3 个词
        key_phrase_short = " ".join(title_words[:3])
        return key_phrase_short in norm_ref

    def compute_metrics(self, G: nx.DiGraph) -> dict:
        """计算 PageRank 和 Betweenness Centrality"""
        if G.number_of_nodes() == 0:
            return {}

        # PageRank（有向图）
        try:
            pagerank = nx.pagerank(G, alpha=0.85)
        except Exception:
            pagerank = {n: 0.0 for n in G.nodes()}

        # Betweenness Centrality（有向图）
        try:
            betweenness = nx.betweenness_centrality(G)
        except Exception:
            betweenness = {n: 0.0 for n in G.nodes()}

        # 度中心性（入度 + 出度）
        in_degree = dict(G.in_degree())
        out_degree = dict(G.out_degree())

        return {
            "pagerank": pagerank,
            "betweenness": betweenness,
            "in_degree": in_degree,
            "out_degree": out_degree,
        }
    
    def to_json(self, G: nx.DiGraph) -> dict:
        """转为前端可用的 JSON 格式"""
        nodes = []
        for n, data in G.nodes(data=True):
            nodes.append({
                "id": n,
                "label": data.get("title", "Untitled"),
                "year": data.get("year"),
                "authors": data.get("authors", ""),
            })

        edges = []
        for u, v, data in G.edges(data=True):
            edges.append({
                "source": u,
                "target": v,
                "weight": data.get("weight", 1),
            })

        return {"nodes": nodes, "edges": edges}