import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from services.translator import Translator

router = APIRouter()
translator = Translator()


class TranslateRequest(BaseModel):
    text: str
    target_lang: str = "zh"


@router.post("/translate")
async def translate(req: TranslateRequest):
    """翻译接口（支持划词翻译和整篇翻译）"""
    if not req.text.strip():
        raise HTTPException(status_code=400, detail="文本不能为空")
    if len(req.text) > 20000:
        raise HTTPException(status_code=400, detail="文本过长，请分段翻译")

    try:
        result = translator.translate(req.text, req.target_lang)
        return {
            "status": "success",
            "original": req.text,
            "translated": result,
            "target_lang": req.target_lang,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"翻译失败: {str(e)}")