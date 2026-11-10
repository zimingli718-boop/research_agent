import os
import sys
import pytest

# 把 app 路径加入环境变量
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.deduplicator import Deduplicator
from services.pdf_locator import PDFLocator
from services.citation_quality import CitationQualityScorer
from agents.guardrails import Guardrails

def test_semantic_deduplication():
    """测试 1：语义去重计算"""
    dedup = Deduplicator()
    text1 = "This is a paper about Transformer architecture."
    text2 = "This is a paper about Transformer architecture."
    # 完全相同的两句话，相似度必须大于 0.99
    sim = dedup.compute_similarity(text1, text2)
    assert sim > 0.99

def test_pdf_location():
    """测试 2：PDF 文本精确定位"""
    pdf_path = "E:/research_agent/data/1706.03762v7.pdf"
    if not os.path.exists(pdf_path):
        pytest.skip("缺少测试用 PDF 文件")
        
    locator = PDFLocator(pdf_path)
    # 搜索 Transformer 标题，应该能在第 1 页找到
    loc = locator.locate_first("Attention Is All You Need")
    assert loc is not None
    assert loc["page"] == 1

def test_citation_quality():
    """测试 3：引用含金量评分"""
    scorer = CitationQualityScorer()
    context = "This is a pioneering work, it significantly improves the state-of-the-art."
    result = scorer.score_citation(context, "Introduction")
    # 包含多个评价词且在 Introduction，含金量必须很高（level 为 high）
    assert result["level"] == "high"

def test_guardrails_anti_hallucination():
    """测试 4：Guardrails 幻觉检测"""
    guard = Guardrails()
    # 故意写一句超过 15 个字、且没有 [来源N] 的废话
    answer = "Transformer 使用了 8 块 GPU [来源1]。这是一段完全没有引用来源支持的瞎编乱造的废话句子。"
    # 模拟只有 1 个来源
    sources = [{"index": 1}]
    result = guard.verify(answer, sources)
    
    # 应该能检测出 1 句未溯源的话
    assert result["total_sentences"] == 2
    assert len(result["unsupported_sentences"]) == 1