import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.graph_builder import GraphBuilder

builder = GraphBuilder()
G = builder.build_from_database()

metrics = builder.compute_metrics(G)

print(f"\n=== 图论指标 ===")
print(f"{'论文':<50} {'PageRank':>10} {'Betweenness':>12} {'入度':>6} {'出度':>6}")

for n in G.nodes():
    title = G.nodes[n].get("title", "Untitled")[:48]
    pr = metrics["pagerank"].get(n, 0)
    bc = metrics["betweenness"].get(n, 0)
    ind = metrics["in_degree"].get(n, 0)
    outd = metrics["out_degree"].get(n, 0)
    print(f"{title:<50} {pr:>10.4f} {bc:>12.4f} {ind:>6} {outd:>6}")

# 识别"基石论文"（PageRank 最高）
if metrics["pagerank"]:
    cornerstone_id = max(metrics["pagerank"], key=metrics["pagerank"].get)
    print(f"\n🏆 基石论文（PageRank 最高）: {G.nodes[cornerstone_id]['title']}")

# 识别"桥梁论文"（Betweenness 最高）
if metrics["betweenness"]:
    max_bc = max(metrics["betweenness"].values())
    if max_bc > 0:
        bridge_id = max(metrics["betweenness"], key=metrics["betweenness"].get)
        print(f"🌉 桥梁论文（Betweenness 最高）: {G.nodes[bridge_id]['title']}")
    else:
        print(f"🌉 没有明显的桥梁论文（图结构简单）")