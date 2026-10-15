import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.arxiv_client import ArxivClient
from services.recommender import Recommender

# 从 arXiv 搜索候选论文
client = ArxivClient()
print("=== 从 arXiv 搜索 'transformer' 论文 ===")
candidates = client.search("transformer", max_results=5)
print(f"找到 {len(candidates)} 篇候选")

# 计算相关性排序
recommender = Recommender()
ranked = recommender.rank_papers(candidates, top_k=5)

print("\n=== 推荐排序（相关性） ===")
for i, p in enumerate(ranked):
    print(f"\n[{i+1}] 相关性: {p['relevance_score']}")
    print(f"  标题: {p['title']}")
    print(f"  arXiv: {p['id']}")