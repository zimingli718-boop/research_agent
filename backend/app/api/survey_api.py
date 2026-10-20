import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import APIRouter, HTTPException

from services.survey_generator import SurveyGenerator
from services.graph_builder import GraphBuilder

router = APIRouter()

survey_gen = SurveyGenerator()
graph_builder = GraphBuilder()


@router.post("/survey/generate")
async def generate_survey():
    """自动生成领域综述"""
    try:
        # 先获取图谱数据
        G = graph_builder.build_from_database()
        graph_data = graph_builder.to_json(G)
        metrics = graph_builder.compute_metrics(G)

        # 把 pagerank 加到节点
        for node in graph_data["nodes"]:
            node["pagerank"] = round(metrics["pagerank"].get(node["id"], 0), 4)

        # 生成综述
        result = survey_gen.generate_survey(graph_data)

        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])

        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"综述生成失败: {str(e)}")