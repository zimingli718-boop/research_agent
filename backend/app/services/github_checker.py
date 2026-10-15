import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import re
import json
import requests
from pathlib import Path


class GitHubChecker:
    """检测论文中的 GitHub 代码仓库"""

    CACHE_DIR = Path("E:/research_agent/data/github_cache")
    API_BASE = "https://api.github.com/repos"

    def __init__(self, token: str = None):
        self.CACHE_DIR.mkdir(parents=True, exist_ok=True)
        self.token = token or os.getenv("GITHUB_TOKEN")
        self.headers = {"Accept": "application/vnd.github+json"}
        if self.token:
            self.headers["Authorization"] = f"Bearer {self.token}"

    def _cache_path(self, repo: str) -> Path:
        safe = repo.replace("/", "_")
        return self.CACHE_DIR / f"{safe}.json"

    def _load_cache(self, repo: str) -> dict:
        path = self._cache_path(repo)
        if path.exists():
            try:
                with open(path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return None
        return None

    def _save_cache(self, repo: str, data: dict):
        with open(self._cache_path(repo), "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def extract_github_links(self, text: str) -> list:
        """从文本里提取 GitHub 链接"""
        if not text:
            return []
        pattern = r'github\.com/([A-Za-z0-9_.-]+)/([A-Za-z0-9_.-]+)'
        matches = re.findall(pattern, text)
        repos = []
        for user, repo in matches:
            # 去掉尾部标点（句号、逗号、分号等）
            repo = repo.rstrip(".,;:!?)。，；：！？")
            if repo.endswith(".git"):
                repo = repo[:-4]
            repo = repo.rstrip("/")
            user = user.strip()
            if not user or not repo:
                continue
            full_name = f"{user}/{repo}"
            if full_name not in repos:
                repos.append(full_name)
        return repos
    def check_repo(self, repo_full_name: str) -> dict:
        """检查 GitHub 仓库的活跃度"""
        # 读缓存（缓存 24 小时）
        cached = self._load_cache(repo_full_name)
        if cached:
            print(f"[GitHub] 命中缓存: {repo_full_name}")
            return cached

        print(f"[GitHub] 请求: {repo_full_name}")
        try:
            resp = requests.get(
                f"{self.API_BASE}/{repo_full_name}",
                headers=self.headers,
                timeout=15,
            )
            if resp.status_code == 404:
                result = {"exists": False, "repo": repo_full_name}
            elif resp.status_code == 403:
                result = {"exists": True, "repo": repo_full_name, "error": "API 限流"}
            elif resp.status_code == 200:
                data = resp.json()
                result = {
                    "exists": True,
                    "repo": repo_full_name,
                    "stars": data.get("stargazers_count", 0),
                    "forks": data.get("forks_count", 0),
                    "last_push": data.get("pushed_at", ""),
                    "description": data.get("description", ""),
                    "language": data.get("language", ""),
                    "html_url": data.get("html_url", ""),
                }
            else:
                result = {"exists": False, "repo": repo_full_name, "error": f"HTTP {resp.status_code}"}

            self._save_cache(repo_full_name, result)
            return result

        except Exception as e:
            print(f"[GitHub] 请求失败: {e}")
            return {"exists": False, "repo": repo_full_name, "error": str(e)}

    def analyze_paper(self, text: str) -> dict:
        """分析论文里的所有 GitHub 链接"""
        repos = self.extract_github_links(text)
        results = []
        for repo in repos:
            results.append(self.check_repo(repo))

        # 综合判断：是否有高星仓库
        has_popular_repo = any(r.get("stars", 0) >= 50 for r in results if r.get("exists"))
        max_stars = max((r.get("stars", 0) for r in results if r.get("exists")), default=0)

        return {
            "has_code": len(results) > 0 and any(r.get("exists") for r in results),
            "repos": results,
            "max_stars": max_stars,
            "has_popular_repo": has_popular_repo,
        }