import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import APIRouter, HTTPException

from services.graph_builder import GraphBuilder

router = APIRouter()
builder = GraphBuilder()


@router.get("/graph")
async def get_graph():
    """构建论文引用图谱"""
    try:
        G = builder.build_from_database()
        data = builder.to_json(G)
        metrics = builder.compute_metrics(G)

        # 把 PageRank 和 Betweenness 加到节点上
        for node in data["nodes"]:
            nid = node["id"]
            node["pagerank"] = round(metrics["pagerank"].get(nid, 0), 4)
            node["betweenness"] = round(metrics["betweenness"].get(nid, 0), 4)
            node["in_degree"] = metrics["in_degree"].get(nid, 0)
            node["out_degree"] = metrics["out_degree"].get(nid, 0)

        # 识别基石和桥梁
        if metrics["pagerank"]:
            cornerstone_id = max(metrics["pagerank"], key=metrics["pagerank"].get)
            data["cornerstone"] = {
                "id": cornerstone_id,
                "title": G.nodes[cornerstone_id].get("title", ""),
                "pagerank": metrics["pagerank"][cornerstone_id],
            }

        if metrics["betweenness"]:
            max_bc = max(metrics["betweenness"].values())
            if max_bc > 0:
                bridge_id = max(metrics["betweenness"], key=metrics["betweenness"].get)
                data["bridge"] = {
                    "id": bridge_id,
                    "title": G.nodes[bridge_id].get("title", ""),
                    "betweenness": max_bc,
                }
            else:
                data["bridge"] = None

        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"图谱构建失败: {str(e)}")