import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import APIRouter, File, UploadFile, HTTPException
from pydantic import BaseModel

from services.writer_agent import WriterAgent
from services.data_visualizer import DataVisualizer

router = APIRouter()
writer = WriterAgent()
visualizer = DataVisualizer()


class OutlineRequest(BaseModel):
    idea: str

class DiagramRequest(BaseModel):
    description: str
    diagram_type: str = "mermaid"

class TranslateAcademicRequest(BaseModel):
    text: str
    target_lang: str = "en"


@router.post("/writer/outline")
async def generate_outline(req: OutlineRequest):
    try:
        return writer.generate_outline(req.idea)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/writer/diagram")
async def generate_diagram(req: DiagramRequest):
    try:
        code = writer.generate_diagram(req.description, req.diagram_type)
        return {"code": code, "type": req.diagram_type}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/writer/translate")
async def translate_academic(req: TranslateAcademicRequest):
    try:
        result = writer.translate_academic(req.text, req.target_lang)
        return {"translated": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/writer/csv")
async def process_csv(file: UploadFile = File(...)):
    try:
        contents = await file.read()
        return visualizer.process_csv(contents)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))