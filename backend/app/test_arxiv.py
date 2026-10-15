import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.arxiv_client import ArxivClient

client = ArxivClient()

# 测试 1：关键词搜索
print("\n=== 测试 1：搜索 'transformer attention' ===")
results = client.search("transformer attention", max_results=3)
for r in results:
    print(f"\n[{r['id']}]")
    print(f"  标题: {r['title']}")
    print(f"  作者: {', '.join(r['authors'][:3])}")
    print(f"  发布: {r['published'][:10]}")
    print(f"  PDF: {r['pdf_url']}")

# 测试 2：按标题搜索
print("\n=== 测试 2：按标题搜 'Attention Is All You Need' ===")
result = client.search_by_title("Attention Is All You Need")
if result:
    print(f"  找到: {result['id']} - {result['title']}")
    print(f"  作者: {', '.join(result['authors'])}")
else:
    print("  未找到")