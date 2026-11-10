'use client';

import { useState, useEffect, useRef } from 'react';

interface Paper {
  id: string;
  title: string;
  authors: string;
  page_count: number | null;
  created_at: string;
}

export default function PapersPage() {
  const [papers, setPapers] = useState<Paper[]>([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [duplicateInfo, setDuplicateInfo] = useState<any>(null);
  const currentFileRef = useRef<File | null>(null);

  async function fetchPapers() {
    try {
      const res = await fetch('http://localhost:8000/api/papers');
      const data = await res.json();
      setPapers(data.papers || []);
    } catch (e) {
      console.error('获取论文列表失败:', e);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    fetchPapers();
  }, []);

  // 处理上传
  async function handleUpload(e: React.ChangeEvent<HTMLInputElement>, force: boolean = false) {
    let file = e.target.files?.[0];
    
    if (force && currentFileRef.current) {
      file = currentFileRef.current;
    } else if (file) {
      currentFileRef.current = file;
    }

    if (!file) return;

    setUploading(true);
    if (!force) setDuplicateInfo(null);

    const formData = new FormData();
    formData.append('file', file);
    if (force) {
      formData.append('force_upload', 'true');
    }

    try {
      const res = await fetch('http://localhost:8000/api/upload', {
        method: 'POST',
        body: formData,
      });
      const data = await res.json();

      if (data.status === 'duplicate_detected') {
        setDuplicateInfo(data);
      } else if (data.status === 'success') {
        alert(`上传成功：${data.title}\n分块数量：${data.chunks_count}`);
        currentFileRef.current = null;
        fetchPapers();
      } else {
        alert('上传失败：' + (data.detail || '未知错误'));
      }
    } catch (e) {
      console.error(e);
      alert('请求失败，请检查后端是否启动');
    } finally {
      setUploading(false);
      if (e.target && e.target.value) {
        e.target.value = ''; 
      }
    }
  }

  // 处理删除
  async function handleDelete(paperId: string, title: string) {
    if (!confirm(`确定要彻底删除《${title}》吗？该操作不可恢复，并且会同时删除其向量索引。`)) return;

    try {
      const res = await fetch(`http://localhost:8000/api/papers/${paperId}`, {
        method: 'DELETE',
      });
      const data = await res.json();
      
      if (res.ok) {
        alert('删除成功');
        fetchPapers();
      } else {
        alert('删除失败：' + (data.detail || '未知错误'));
      }
    } catch (e) {
      console.error(e);
      alert('网络请求失败');
    }
  }

  return (
    <div className="p-8 max-w-5xl mx-auto">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-slate-900">论文管理</h1>
        <p className="text-sm text-slate-500 mt-1">
          支持单篇/批量 PDF 上传，系统会自动进行结构化解析与语义级去重
        </p>
      </div>

      {/* 上传区 */}
      <div className="mb-8">
        <label className={`flex flex-col items-center justify-center w-full h-40 border-2 border-dashed rounded-xl cursor-pointer transition-colors ${
          uploading ? 'border-blue-400 bg-blue-50' : 'border-slate-300 bg-slate-50 hover:bg-slate-100'
        }`}>
          <div className="flex flex-col items-center justify-center pt-5 pb-6">
            <div className="text-3xl mb-2">{uploading ? '⏳' : '📄'}</div>
            <p className="mb-2 text-sm text-slate-700 font-medium">
              {uploading ? '正在解析 PDF 并计算语义相似度...' : '点击此处上传 PDF 论文'}
            </p>
            <p className="text-xs text-slate-500">支持标准版、扫描版、长篇书籍</p>
          </div>
          <input
            type="file"
            accept=".pdf"
            className="hidden"
            onChange={(e) => handleUpload(e, false)}
            disabled={uploading}
          />
        </label>
      </div>

      {/* 去重预警弹窗 */}
      {duplicateInfo && (
        <div className="mb-8 bg-amber-50 border border-amber-300 rounded-xl p-5 shadow-sm animate-fade-in">
          <div className="flex items-start gap-3">
            <div className="text-2xl">⚠️</div>
            <div className="flex-1">
              <h3 className="text-amber-800 font-bold mb-1">检测到高度相似的论文</h3>
              <p className="text-sm text-amber-700 mb-4">
                系统基于摘要语义计算，发现该论文与库中已有的《{duplicateInfo.matched_paper_title}》相似度高达 {(duplicateInfo.similarity * 100).toFixed(2)}%。
              </p>
                {duplicateInfo.diff_summary && (
                <div className="bg-white/60 p-3 rounded-lg border border-amber-200 mb-4 text-xs text-slate-700 leading-relaxed">
                  <span className="font-semibold text-amber-800">📝 版本差异对比：</span>
                  {duplicateInfo.diff_summary}
                </div>
              )}
              <div className="flex gap-3">
                <button
                  onClick={() => {
                    setDuplicateInfo(null);
                    currentFileRef.current = null;
                  }}
                  className="px-4 py-1.5 text-xs bg-slate-200 text-slate-700 rounded hover:bg-slate-300 transition"
                >
                  取消（保留旧版）
                </button>
                <button
                  onClick={() => {
                    const fakeEvent = { target: { value: '', files: null } } as any;
                    handleUpload(fakeEvent, true);
                    setDuplicateInfo(null);
                  }}
                  className="px-4 py-1.5 text-xs bg-red-600 text-white rounded hover:bg-red-700 transition"
                >
                  仍要保存为新版本（强制入库）
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* 论文列表 */}
      <div>
        <h2 className="text-sm font-semibold text-slate-700 mb-3 flex items-center justify-between">
          <span>知识库（{papers.length} 篇）</span>
          <button onClick={fetchPapers} className="text-xs text-blue-600 hover:underline">刷新</button>
        </h2>

        {loading ? (
          <div className="text-sm text-slate-500 text-center py-8">加载中...</div>
        ) : papers.length === 0 ? (
          <div className="text-sm text-slate-400 text-center py-12 border rounded-xl bg-white">
            知识库为空，请上传第一篇论文
          </div>
        ) : (
          <div className="space-y-3">
            {papers.map((p) => (
              <div key={p.id} className="bg-white border border-slate-200 rounded-xl p-4 hover:shadow-sm transition flex justify-between items-start">
                <div className="flex-1 min-w-0 pr-4">
                  <div className="font-semibold text-slate-800 text-sm mb-1">{p.title}</div>
                  <div className="text-xs text-slate-500 mb-2 truncate">
                    {p.authors?.slice(0, 100) || '未知作者'}
                  </div>
                  <div className="flex items-center gap-4 text-[11px] text-slate-400">
                    <span className="font-mono bg-slate-100 px-2 py-0.5 rounded">{p.id.slice(0, 8)}</span>
                    {p.page_count && <span>{p.page_count} 页</span>}
                    <span>上传于 {new Date(p.created_at).toLocaleString()}</span>
                  </div>
                </div>
                
                {/* 删除按钮 */}
                <button
                  onClick={() => handleDelete(p.id, p.title)}
                  className="px-3 py-1.5 text-xs text-red-600 bg-red-50 hover:bg-red-100 rounded-lg transition shrink-0 flex items-center gap-1"
                >
                  🗑️ 删除
                </button>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}