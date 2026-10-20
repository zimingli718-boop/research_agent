from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

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