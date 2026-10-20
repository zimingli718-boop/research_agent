import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import APIRouter, HTTPException

from services.future_work_analyzer import FutureWorkAnalyzer

router = APIRouter()
analyzer = FutureWorkAnalyzer()


@router.post("/future-work/analyze")
async def analyze_future_work():
    """Future Work 去重与时效性分析"""
    try:
        result = analyzer.analyze()
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"分析失败: {str(e)}")