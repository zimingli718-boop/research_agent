import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.graph_builder import GraphBuilder

builder = GraphBuilder()
G = builder.build_from_database()

print(f"\n=== 图统计 ===")
print(f"节点数: {G.number_of_nodes()}")
print(f"边数: {G.number_of_edges()}")
print(f"密度: {G.number_of_edges() / max(G.number_of_nodes() * (G.number_of_nodes() - 1), 1):.4f}")

print(f"\n=== 所有节点 ===")
for n, d in G.nodes(data=True):
    print(f"  [{n[:8]}] {d.get('title', 'Untitled')[:60]}")

print(f"\n=== 所有边 ===")
for u, v in G.edges():
    print(f"  {G.nodes[u]['title'][:40]} → {G.nodes[v]['title'][:40]}")