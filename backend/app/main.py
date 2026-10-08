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
app.include_router(upload.router, prefix="/api")
app.include_router(qa.router, prefix="/api")


@app.get("/health")
async def health():
    return {"status": "ok", "message": "Research Agent backend is running"}