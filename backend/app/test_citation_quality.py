import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.citation_quality import CitationQualityScorer

scorer = CitationQualityScorer()

# 测试 1：不同章节的引用
print("\n=== 测试 1：位置权重 ===")
tests = [
    ("Introduction", "Our model significantly outperforms the state-of-the-art approaches described in previous work, achieving a new best result."),
    ("Related Work", "Some methods use attention [1]."),
    ("Conclusion", "In this work, we proposed X [2]."),
]

for section, context in tests:
    result = scorer.score_citation(context, section)
    print(f"\n[{section}]")
    print(f"  上下文: {context[:60]}...")
    print(f"  总分: {result['score']} ({result['level']})")
    print(f"  位置分: {result['position_score']}, 长度分: {result['length_score']}, 评价词分: {result['keyword_score']}")

# 测试 2：含评价词 vs 中性
print("\n=== 测试 2：评价词影响 ===")
tests2 = [
    "This pioneering work is fundamental to our approach and significantly improves performance.",
    "See also [3] for details.",
]

for ctx in tests2:
    result = scorer.score_citation(ctx, "Method")
    print(f"\n上下文: {ctx[:60]}")
    print(f"  总分: {result['score']} ({result['level']})")