import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from apscheduler.schedulers.background import BackgroundScheduler

app = FastAPI(title="Research Agent API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

from app.api import upload
from app.api import qa
from app.api import translate
from app.api import recommendation_api
from app.api import graph_api
from app.api import survey_api
from app.api import future_api
from app.api import writer_api

app.include_router(upload.router, prefix="/api")
app.include_router(qa.router, prefix="/api")
app.include_router(translate.router, prefix="/api")
app.include_router(recommendation_api.router, prefix="/api")
app.include_router(graph_api.router, prefix="/api")
app.include_router(survey_api.router, prefix="/api")
app.include_router(future_api.router, prefix="/api")
app.include_router(writer_api.router, prefix="/api")

@app.get("/health")
async def health():
    return {"status": "ok", "message": "Research Agent backend is running"}


# ================= 核心新增：后台定时追踪 arXiv =================
scheduler = BackgroundScheduler()

def scheduled_arxiv_fetch():
    print("[Scheduler] 正在执行定时的 arXiv 追踪任务...")
    try:
        from app.services.arxiv_client import ArxivClient
        client = ArxivClient()
        # 定期抓取最新 transformer 相关论文
        results = client.search("transformer", max_results=3, use_cache=False)
        print(f"[Scheduler] 成功追踪到 {len(results)} 篇最新论文")
    except Exception as e:
        print(f"[Scheduler] arXiv 追踪失败: {e}")

@app.on_event("startup")
def startup_event():
    # 启动时先跑一次，之后每 24 小时跑一次
    scheduler.add_job(scheduled_arxiv_fetch, 'interval', hours=24)
    scheduler.start()
    print("[Scheduler] 后台 arXiv 定时追踪任务已启动")
# ================================================================