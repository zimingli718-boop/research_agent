import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from services.arxiv_client import ArxivClient
from services.recommender import Recommender
from services.github_checker import GitHubChecker
from services.citation_quality import CitationQualityScorer

router = APIRouter()

arxiv = ArxivClient()
recommender = Recommender()
github = GitHubChecker()
citation_scorer = CitationQualityScorer()

# 内存存储用户反馈
FEEDBACK_STORE = {}


class RecommendRequest(BaseModel):
    query: str = "transformer"
    top_k: int = 5


class FeedbackRequest(BaseModel):
    arxiv_id: str
    action: str  # "like" or "dislike"
    user_id: str = "anonymous"


@router.post("/recommend")
async def recommend(req: RecommendRequest):
    """推荐论文：搜索 + 相关性排序 + GitHub 检测 + 引用含金量 + 推荐理由"""
    candidates = arxiv.search(req.query, max_results=15)
    if not candidates:
        return {"total": 0, "recommendations": []}

    ranked = recommender.rank_papers(candidates, top_k=req.top_k)

    recommendations = []
    for paper in ranked:
        full_text = paper.get("abstract", "") + " " + paper.get("title", "")
        github_info = github.analyze_paper(full_text)

        reasons = []
        rel = paper["relevance_score"]
        if rel > 0.6:
            reasons.append(f"与你的研究兴趣高度相关（相关性 {rel:.2f}）")
        elif rel > 0.5:
            reasons.append(f"与你的研究兴趣相关（相关性 {rel:.2f}）")

        if github_info["has_code"]:
            max_stars = github_info["max_stars"]
            if max_stars >= 1000:
                reasons.append(f"附带高星开源代码（⭐ {max_stars}）")
            elif max_stars >= 50:
                reasons.append(f"附带开源代码（⭐ {max_stars}）")
            else:
                reasons.append("附带开源代码")

        # 核心新增：计算引用含金量
        # 用摘要作为上下文，模拟 Introduction 场景，计算评价词密度与长度评分
        quality_result = citation_scorer.score_citation(full_text, "Introduction")
        
        # 严格判定：只有在相关性和评分都很高的情况下才展示“极高”
        if quality_result["score"] > 0.8:
            reasons.append("引用含金量极高（核心基石文献）")
        elif quality_result["score"] > 0.6:
            reasons.append("引用含金量较高（重要参考文献）")
        # 分数太低就不展示了，保持界面干净

        if not reasons:
            reasons.append("arXiv 最新论文")

        feedback_data = FEEDBACK_STORE.get(paper["id"], {"like": 0, "dislike": 0})

        recommendations.append({
            "arxiv_id": paper["id"],
            "title": paper["title"],
            "authors": paper["authors"][:5],
            "abstract": paper["abstract"][:300],
            "published": paper["published"],
            "pdf_url": paper["pdf_url"],
            "abs_url": paper["abs_url"],
            "relevance_score": paper["relevance_score"],
            "has_code": github_info["has_code"],
            "max_stars": github_info["max_stars"],
            "reasons": reasons,
            "like_count": feedback_data.get("like", 0),
            "dislike_count": feedback_data.get("dislike", 0),
        })

    return {"total": len(recommendations), "recommendations": recommendations}


@router.post("/recommend/feedback")
async def feedback(req: FeedbackRequest):
    """用户点赞/踩（支持取消和切换）"""
    if req.action not in ("like", "dislike"):
        raise HTTPException(status_code=400, detail="action 必须是 like 或 dislike")

    if req.arxiv_id not in FEEDBACK_STORE:
        FEEDBACK_STORE[req.arxiv_id] = {"like": 0, "dislike": 0, "users": {}}

    store = FEEDBACK_STORE[req.arxiv_id]
    user_id = req.user_id or "anonymous"
    prev_action = store["users"].get(user_id)

    if prev_action == req.action:
        # 相同操作 → 取消
        store[req.action] = max(0, store[req.action] - 1)
        del store["users"][user_id]
        current_action = None
    else:
        # 不同操作 → 切换
        if prev_action:
            store[prev_action] = max(0, store[prev_action] - 1)
        store[req.action] += 1
        store["users"][user_id] = req.action
        current_action = req.action

    return {
        "status": "ok",
        "arxiv_id": req.arxiv_id,
        "current_action": current_action,
        "counts": {
            "like": store["like"],
            "dislike": store["dislike"],
        },
    }