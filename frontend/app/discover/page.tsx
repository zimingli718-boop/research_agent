'use client';

import { useState, useEffect, useRef } from 'react';

interface Recommendation {
  arxiv_id: string;
  title: string;
  authors: string[];
  abstract: string;
  published: string;
  pdf_url: string;
  abs_url: string;
  relevance_score: number;
  has_code: boolean;
  max_stars: number;
  reasons: string[];
  like_count: number;
  dislike_count: number;
}

export default function DiscoverPage() {
  const [query, setQuery] = useState('');
  const [recommendations, setRecommendations] = useState<Recommendation[]>([]);
  const [loading, setLoading] = useState(false);
  const [feedback, setFeedback] = useState<Record<string, string>>({});
  
  // 历史记录相关状态
  const [history, setHistory] = useState<string[]>([]);
  const [showHistory, setShowHistory] = useState(false);
  const historyRef = useRef<HTMLDivElement>(null);

  // 初始化加载历史记录
  useEffect(() => {
    const savedHistory = localStorage.getItem('search_history');
    if (savedHistory) {
      try { setHistory(JSON.parse(savedHistory)); } catch (e) {}
    }
  }, []);

  // 点击外部关闭下拉框
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (historyRef.current && !historyRef.current.contains(event.target as Node)) {
        setShowHistory(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  // 保存历史记录并搜索
  async function fetchRecommendations(searchQuery: string = query) {
    if (!searchQuery.trim()) return;
    
    setQuery(searchQuery);
    setLoading(true);
    setShowHistory(false);

    // 更新历史记录（去重，放到最前面，最多保留 8 条）
    const newHistory = [searchQuery, ...history.filter(h => h !== searchQuery)].slice(0, 8);
    setHistory(newHistory);
    localStorage.setItem('search_history', JSON.stringify(newHistory));

    try {
      const res = await fetch('http://localhost:8000/api/recommend', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: searchQuery, top_k: 5 }),
      });
      const data = await res.json();
      setRecommendations(data.recommendations || []);
    } catch (e) {
      console.error('推荐请求失败:', e);
    } finally {
      setLoading(false);
    }
  }

  // 清除历史记录
  function clearHistory() {
    setHistory([]);
    localStorage.removeItem('search_history');
    setShowHistory(false);
  }

  async function sendFeedback(arxivId: string, action: 'like' | 'dislike') {
    try {
      const res = await fetch('http://localhost:8000/api/recommend/feedback', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ arxiv_id: arxivId, action, user_id: 'demo_user' }),
      });
      const data = await res.json();
      setRecommendations((prev) =>
        prev.map((r) =>
          r.arxiv_id === arxivId
            ? { ...r, like_count: data.counts.like, dislike_count: data.counts.dislike }
            : r
        )
      );

      setFeedback((prev) => {
        const newFeedback = { ...prev };
        if (data.current_action === null) {
          delete newFeedback[arxivId];
        } else {
          newFeedback[arxivId] = data.current_action;
        }
        return newFeedback;
      });
    } catch (e) {
      console.error('反馈失败:', e);
    }
  }

  return (
    <div className="p-8 max-w-5xl mx-auto">
      <div className="mb-8">
        <h1 className="text-3xl font-extrabold text-slate-900 tracking-tight">论文发现</h1>
        <p className="text-sm text-slate-500 mt-2">基于你的兴趣向量，从 arXiv 实时追踪并推荐高质量学术文献</p>
      </div>

      <div className="mb-8 relative" ref={historyRef}>
        <div className="flex gap-3">
          <div className="relative flex-1">
            <span className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400">🔍</span>
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onFocus={() => setShowHistory(true)}
              onKeyDown={(e) => e.key === 'Enter' && fetchRecommendations()}
              placeholder="输入关键词，比如 transformer、diffusion..."
              className="w-full pl-11 pr-4 py-3 bg-white border border-slate-200 rounded-xl text-sm shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 transition-shadow"
            />
            
            {/* 历史记录下拉框 */}
            {showHistory && history.length > 0 && (
              <div className="absolute top-full left-0 w-full mt-2 bg-white border border-slate-200 rounded-xl shadow-lg z-20 overflow-hidden">
                <div className="flex justify-between items-center px-4 py-2 bg-slate-50 border-b border-slate-100">
                  <span className="text-xs font-semibold text-slate-500">最近的搜索</span>
                  <button onClick={clearHistory} className="text-xs text-red-500 hover:text-red-700">清除历史</button>
                </div>
                <ul className="max-h-64 overflow-y-auto">
                  {history.map((h, i) => (
                    <li 
                      key={i} 
                      onClick={() => fetchRecommendations(h)}
                      className="px-4 py-2.5 text-sm text-slate-700 hover:bg-blue-50 cursor-pointer flex items-center gap-2 transition-colors"
                    >
                      <span className="text-slate-400">🕒</span> {h}
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
          
          <button
            onClick={() => fetchRecommendations()}
            disabled={loading}
            className="px-8 py-3 bg-blue-600 text-white font-medium rounded-xl hover:bg-blue-700 shadow-sm hover:shadow transition-all disabled:bg-slate-300 flex items-center gap-2"
          >
            {loading ? '搜索中...' : '智能推荐'}
          </button>
        </div>
      </div>

      {loading && (
        <div className="flex flex-col items-center justify-center py-20 text-slate-400">
          <div className="w-8 h-8 border-4 border-blue-200 border-t-blue-600 rounded-full animate-spin mb-4"></div>
          <p>正在计算兴趣向量并检索 arXiv...</p>
        </div>
      )}

      {!loading && recommendations.length === 0 && (
        <div className="text-slate-400 text-sm p-16 text-center border-2 border-dashed border-slate-200 rounded-2xl bg-slate-50/50">
          <div className="text-4xl mb-4">🔭</div>
          <p>输入研究关键词，探索最前沿的学术成果</p>
        </div>
      )}

      <div className="space-y-5">
        {recommendations.map((paper, idx) => (
          <div
            key={paper.arxiv_id}
            className="bg-white rounded-2xl border border-slate-200 p-6 hover:shadow-lg hover:border-blue-200 transition-all group"
          >
            <div className="flex items-start justify-between gap-4 mb-3">
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-2 flex-wrap">
                  <span className="text-xs font-bold text-blue-600 bg-blue-50 px-2 py-0.5 rounded">#{idx + 1}</span>
                  <span className="text-xs px-2 py-0.5 bg-green-50 text-green-700 rounded border border-green-200">
                    相关性 {paper.relevance_score.toFixed(2)}
                  </span>
                  {paper.has_code && (
                    <span className="text-xs px-2 py-0.5 bg-yellow-50 text-yellow-700 rounded border border-yellow-200 flex items-center gap-1">
                      ⭐ {paper.max_stars} Stars
                    </span>
                  )}
                  <span className="text-xs text-slate-400 ml-auto">{paper.published.slice(0, 10)}</span>
                </div>
                <h2 className="text-lg font-bold text-slate-800 leading-snug group-hover:text-blue-600 transition-colors">
                  {paper.title}
                </h2>
              </div>
            </div>

            <div className="text-xs text-slate-500 mb-3 flex items-center gap-1">
              <span className="font-medium text-slate-700">Authors:</span> 
              {paper.authors.join(', ')}
              {paper.authors.length >= 5 ? ' 等' : ''}
            </div>

            <div className="text-sm text-slate-600 mb-4 leading-relaxed bg-slate-50/50 p-3 rounded-lg border border-slate-100">
              {paper.abstract}...
            </div>

            <div className="flex flex-wrap gap-2 mb-4">
              {paper.reasons.map((reason, i) => {
                const isQuality = reason.includes('含金量') || reason.includes('潜力');
                return (
                  <span
                    key={i}
                    className={`text-xs px-2.5 py-1 rounded-md flex items-center gap-1 ${
                      isQuality
                        ? 'bg-amber-50 text-amber-700 border border-amber-200 font-medium'
                        : 'bg-blue-50 text-blue-700 border border-blue-100'
                    }`}
                  >
                    💡 {reason}
                  </span>
                );
              })}
            </div>

            <div className="flex items-center gap-4 pt-4 border-t border-slate-100">
              <a href={paper.abs_url} target="_blank" rel="noopener noreferrer" className="text-xs text-slate-500 hover:text-blue-600 flex items-center gap-1 transition-colors">
                🔗 arXiv 摘要
              </a>
              <a href={paper.pdf_url} target="_blank" rel="noopener noreferrer" className="text-xs text-slate-500 hover:text-red-500 flex items-center gap-1 transition-colors">
                📄 PDF 原文
              </a>

              <div className="ml-auto flex items-center gap-2 bg-slate-50 p-1 rounded-lg border border-slate-200">
                <button
                  onClick={() => sendFeedback(paper.arxiv_id, 'like')}
                  className={`px-3 py-1 text-xs rounded transition-colors ${
                    feedback[paper.arxiv_id] === 'like'
                      ? 'bg-green-500 text-white shadow-sm'
                      : 'hover:bg-green-100 text-slate-600'
                  }`}
                >
                  👍 {paper.like_count}
                </button>
                <button
                  onClick={() => sendFeedback(paper.arxiv_id, 'dislike')}
                  className={`px-3 py-1 text-xs rounded transition-colors ${
                    feedback[paper.arxiv_id] === 'dislike'
                      ? 'bg-red-500 text-white shadow-sm'
                      : 'hover:bg-red-100 text-slate-600'
                  }`}
                >
                  👎 {paper.dislike_count}
                </button>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}