'use client';

import { useState, useEffect, useRef } from 'react';

interface GraphNode {
  id: string;
  label: string;
  year: number | null;
  authors: string;
  pagerank: number;
  betweenness: number;
  in_degree: number;
  out_degree: number;
}

interface GraphEdge {
  source: string;
  target: string;
  weight: number;
}

interface Cornerstone {
  id: string;
  title: string;
  pagerank: number;
}

export default function GraphPage() {
  const [loading, setLoading] = useState(true);
  const [nodes, setNodes] = useState<GraphNode[]>([]);
  const [edges, setEdges] = useState<GraphEdge[]>([]);
  const [cornerstone, setCornerstone] = useState<Cornerstone | null>(null);
  const [selectedNode, setSelectedNode] = useState<GraphNode | null>(null);
  
  const containerRef = useRef<HTMLDivElement>(null);
  const cyRef = useRef<any>(null);

  // 1. 获取图谱数据
  useEffect(() => {
    fetch('http://localhost:8000/api/graph')
      .then((r) => r.json())
      .then((data) => {
        setNodes(data.nodes || []);
        setEdges(data.edges || []);
        setCornerstone(data.cornerstone);
        setLoading(false);
      })
      .catch((e) => {
        console.error('图谱加载失败:', e);
        setLoading(false);
      });
  }, []);

  // 2. 初始化 Cytoscape
  useEffect(() => {
    if (loading || nodes.length === 0) return;

    let cancelled = false;
    let cyInstance: any = null;

    async function initGraph() {
      const cytoscape = (await import('cytoscape')).default;
      
      // 等待 React 渲染出容器，并防止 Strict Mode 下的卸载冲突
      if (cancelled || !containerRef.current) return;

      const elements = [
        ...nodes.map((n) => ({
          data: {
            id: n.id,
            label: n.label,
            pagerank: n.pagerank,
            in_degree: n.in_degree,
            out_degree: n.out_degree,
            isCornerstone: cornerstone?.id === n.id ? 1 : 0,
            size: 40 + n.pagerank * 200,
            shortLabel: n.label.split(':')[0].slice(0, 30),
          },
        })),
        ...edges.map((e) => ({
          data: {
            id: `${e.source}-${e.target}`,
            source: e.source,
            target: e.target,
            weight: e.weight,
          },
        })),
      ];

      try {
        cyInstance = cytoscape({
          container: containerRef.current,
          elements,
          style: [
            {
              selector: 'node',
              style: {
                'background-color': '#3b82f6',
                'background-opacity': 0.9,
                'label': 'data(shortLabel)',
                'width': 'data(size)',
                'height': 'data(size)',
                'font-size': 11,
                'font-weight': 500,
                'text-valign': 'bottom',
                'text-margin-y': 8,
                'text-wrap': 'wrap',
                'text-max-width': '140px',
                'color': '#0f172a',
                'border-width': 3,
                'border-color': '#ffffff',
                'border-opacity': 0.8,
              } as any,
            },
            {
              selector: 'node[isCornerstone = 1]',
              style: {
                'background-color': '#ef4444',
                'border-color': '#fecaca',
                'border-width': 5,
              } as any,
            },
            {
              selector: 'edge',
              style: {
                'width': 2.5,
                'line-color': '#94a3b8',
                'target-arrow-color': '#94a3b8',
                'target-arrow-shape': 'triangle',
                'curve-style': 'bezier',
                'arrow-scale': 1.5,
              } as any,
            },
            {
              selector: 'node:selected',
              style: {
                'border-color': '#10b981',
                'border-width': 5,
              } as any,
            },
          ],
          layout: {
            name: 'cose',
            animate: false, // 关掉动画，防止初始化时容器尺寸计算错误
            nodeRepulsion: () => 8000,
            idealEdgeLength: () => 200,
            gravity: 0.2,
            numIter: 1000,
          } as any,
          wheelSensitivity: 0.2,
          backgroundColor: '#f8fafc',
        } as any);

        cyInstance.on('tap', 'node', (evt: any) => {
          const nodeId = evt.target.id();
          const node = nodes.find((n) => n.id === nodeId);
          if (node) setSelectedNode(node);
        });

        cyInstance.on('tap', (evt: any) => {
          if (evt.target === cyInstance) setSelectedNode(null);
        });

        cyRef.current = cyInstance;
      } catch (err) {
        console.error('Cytoscape 渲染失败:', err);
      }
    }

    // 延迟 100ms 确保 DOM 节点高度已被撑开
    const timer = setTimeout(initGraph, 100);

    return () => {
      cancelled = true;
      clearTimeout(timer);
      if (cyInstance) {
        cyInstance.destroy();
      }
      cyRef.current = null;
    };
  }, [loading, nodes, edges, cornerstone]);

  const sortedNodes = [...nodes].sort((a, b) => b.pagerank - a.pagerank);

  return (
    <div className="p-8 max-w-6xl mx-auto">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-slate-900">引用图谱</h1>
        <p className="text-sm text-slate-500 mt-1">
          基于论文间的 References 解析构建的有向引用关系图
        </p>
      </div>

      {loading && <div className="text-slate-500 p-8 text-center">加载中...</div>}

      {cornerstone && (
        <div className="mb-4 p-4 bg-gradient-to-r from-red-50 to-amber-50 border border-red-200 rounded-lg flex items-center gap-3">
          <div className="text-2xl">🏆</div>
          <div>
            <div className="text-sm font-semibold text-red-800">基石论文</div>
            <div className="text-xs text-red-700">
              {cornerstone.title}（PageRank {cornerstone.pagerank.toFixed(4)}）
            </div>
          </div>
        </div>
      )}

      <div className="grid grid-cols-3 gap-4">
        {/* 图谱区 */}
        <div className="col-span-2 bg-white rounded-xl border border-slate-200 overflow-hidden shadow-sm">
          <div
            ref={containerRef}
            style={{
              width: '100%',
              height: '620px',
              backgroundImage: 'radial-gradient(circle, #e2e8f0 1px, transparent 1px)',
              backgroundSize: '20px 20px',
            }}
          />
        </div>

        {/* 右侧：详情 + 图例 */}
        <div className="space-y-4">
          {/* 图例 */}
          <div className="bg-white rounded-xl border border-slate-200 p-4 shadow-sm">
            <h2 className="text-sm font-semibold text-slate-700 mb-3">图例</h2>
            <div className="space-y-2 text-xs text-slate-600">
              <div className="flex items-center gap-2">
                <span className="w-4 h-4 rounded-full bg-red-500 inline-block" />
                基石论文（PageRank 最高）
              </div>
              <div className="flex items-center gap-2">
                <span className="w-4 h-4 rounded-full bg-blue-500 inline-block" />
                普通论文
              </div>
              <div className="flex items-center gap-2">
                <span className="w-4 h-0.5 bg-slate-400 inline-block" />
                <span className="text-slate-400">→</span>
                引用关系（指向被引论文）
              </div>
              <div className="text-slate-400 pt-2 border-t border-slate-100">
                节点大小 = PageRank 值
              </div>
            </div>
          </div>

          {/* 节点详情 */}
          <div className="bg-white rounded-xl border border-slate-200 p-4 shadow-sm">
            <h2 className="text-sm font-semibold text-slate-700 mb-3">
              {selectedNode ? '节点详情' : '点击节点查看详情'}
            </h2>

            {selectedNode ? (
              <div className="space-y-2 text-sm">
                <div className="font-medium text-slate-800 text-xs leading-relaxed">
                  {selectedNode.label}
                </div>
                <div className="flex justify-between text-xs">
                  <span className="text-slate-500">PageRank</span>
                  <span className="font-mono text-blue-600">{selectedNode.pagerank.toFixed(4)}</span>
                </div>
                <div className="flex justify-between text-xs">
                  <span className="text-slate-500">被引次数</span>
                  <span className="font-mono">{selectedNode.in_degree}</span>
                </div>
                <div className="flex justify-between text-xs">
                  <span className="text-slate-500">引用他人</span>
                  <span className="font-mono">{selectedNode.out_degree}</span>
                </div>
              </div>
            ) : (
              <div className="text-xs text-slate-400">点击图谱中的节点，查看论文详情</div>
            )}
          </div>

          {/* 排行榜 */}
          <div className="bg-white rounded-xl border border-slate-200 p-4 shadow-sm">
            <h2 className="text-sm font-semibold text-slate-700 mb-3">论文排序（PageRank）</h2>
            <div className="space-y-2">
              {sortedNodes.map((n, idx) => (
                <div
                  key={n.id}
                  onClick={() => {
                    setSelectedNode(n);
                    if (cyRef.current) {
                      cyRef.current.getElementById(n.id).select();
                    }
                  }}
                  className={`flex items-center gap-2 p-2 rounded cursor-pointer hover:bg-slate-50 transition ${
                    cornerstone?.id === n.id ? 'bg-red-50' : ''
                  }`}
                >
                  <span className={`text-xs font-mono w-6 ${cornerstone?.id === n.id ? 'text-red-600' : 'text-slate-400'}`}>
                    #{idx + 1}
                  </span>
                  <span className="text-xs text-slate-700 flex-1 truncate">
                    {n.label.split(':')[0]}
                  </span>
                  <span className="text-xs font-mono text-blue-600">
                    {n.pagerank.toFixed(3)}
                  </span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}