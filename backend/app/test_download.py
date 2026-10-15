import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.arxiv_client import ArxivClient

client = ArxivClient()

# 测试 1：按标题下载
print("\n=== 测试 1：按标题下载 ===")
result = client.search_and_download("BERT: Pre-training of Deep Bidirectional Transformers")
if result:
    print(f"  标题: {result['title']}")
    print(f"  arXiv ID: {result['id']}")
    print(f"  本地 PDF: {result['local_pdf']}")

# 测试 2：批量下载
print("\n=== 测试 2：批量下载 ===")
titles = [
    "Attention Is All You Need",
    "Deep Residual Learning for Image Recognition",
]
for t in titles:
    print(f"\n--- {t} ---")
    r = client.search_and_download(t)
    if r:
        print(f"  ✅ {r['id']} - {r['local_pdf']}")
    else:
        print(f"  ❌ 未找到")