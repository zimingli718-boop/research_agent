import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.github_checker import GitHubChecker

checker = GitHubChecker()

# 测试 1：提取 GitHub 链接
print("\n=== 测试 1：提取 GitHub 链接 ===")
text = """
Code will be released at https://github.com/google-research/bert.
We also provide the implementation at https://github.com/huggingface/transformers.
See https://github.com/facebookresearch/fairseq for details.
"""
repos = checker.extract_github_links(text)
print(f"提取到 {len(repos)} 个仓库:")
for r in repos:
    print(f"  - {r}")

# 测试 2：检查仓库活跃度
print("\n=== 测试 2：检查仓库活跃度 ===")
for repo in repos[:2]:
    result = checker.check_repo(repo)
    print(f"\n[{repo}]")
    if result.get("exists"):
        print(f"  ⭐ Stars: {result.get('stars', 0)}")
        print(f"  🍴 Forks: {result.get('forks', 0)}")
        print(f"  最后 push: {result.get('last_push', '')[:10]}")
        print(f"  语言: {result.get('language', '')}")
    else:
        print(f"  仓库不存在或出错: {result.get('error', '')}")

# 测试 3：综合分析
print("\n=== 测试 3：综合分析 ===")
analysis = checker.analyze_paper(text)
print(f"  有代码: {analysis['has_code']}")
print(f"  最高 star: {analysis['max_stars']}")
print(f"  有高星仓库: {analysis['has_popular_repo']}")