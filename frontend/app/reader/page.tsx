'use client';

import { useState, useEffect } from 'react';
import dynamic from 'next/dynamic';

const PDFViewer = dynamic(() => import('./PDFViewer'), {
  ssr: false,
  loading: () => <div className="p-8 text-slate-500">加载阅读器...</div>,
});

interface Paper {
  id: string;
  title: string;
  authors: string;
}

export default function ReaderPage() {
  const [papers, setPapers] = useState<Paper[]>([]);
  const [selectedId, setSelectedId] = useState<string>('');

  // 获取论文列表
  useEffect(() => {
    fetch('http://localhost:8000/api/papers')
      .then((r) => r.json())
      .then((data) => {
        const list = data.papers || [];
        setPapers(list);
        // 默认选中第一篇
        if (list.length > 0) {
          setSelectedId(list[0].id);
        }
      })
      .catch((e) => console.error('获取论文列表失败:', e));
  }, []);

  return (
    <div className="p-6 h-[calc(100vh-2rem)] flex flex-col">
      {/* 顶部工具栏 */}
      <div className="flex items-center justify-between mb-6 shrink-0">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">阅读翻译</h1>
          <p className="text-sm text-slate-500 mt-1">支持原生渲染、公式提取与中英对照</p>
        </div>
        
        {/* 核心：文献选择框 */}
        <div className="flex items-center gap-3 bg-white border border-slate-200 rounded-lg px-4 py-2 shadow-sm">
          <span className="text-sm font-medium text-slate-700 whitespace-nowrap">📚 当前阅读：</span>
          <select
            value={selectedId}
            onChange={(e) => setSelectedId(e.target.value)}
            className="w-[400px] text-sm text-slate-800 bg-transparent focus:outline-none cursor-pointer truncate"
          >
            {papers.map((p) => (
              <option key={p.id} value={p.id}>
                {p.title || '未命名论文'}
              </option>
            ))}
            {papers.length === 0 && <option value="">暂无论文</option>}
          </select>
        </div>
      </div>

      {/* 核心阅读区 */}
      <div className="flex-1 min-h-0 bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
        {selectedId ? (
          <PDFViewer 
            key={selectedId} // 加上 key 确保切换论文时组件完全重新渲染
            pdfUrl={`http://localhost:8000/api/papers/${selectedId}/pdf`} 
            paperId={selectedId} 
          />
        ) : (
          <div className="h-full flex flex-col items-center justify-center text-slate-400">
            <div className="text-4xl mb-4">📄</div>
            <p>暂无论文，请先去"论文管理"页面上传</p>
          </div>
        )}
      </div>
    </div>
  );
}