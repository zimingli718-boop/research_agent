'use client';

import { useState } from 'react';

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
  const [query, setQuery] = useState('transformer');
  const [recommendations, setRecommendations] = useState<Recommendation[]>([]);
  const [loading, setLoading] = useState(false);
  const [feedback, setFeedback] = useState<Record<string, string>>({});

  async function fetchRecommendations() {
    setLoading(true);
    try {
      const res = await fetch('http://localhost:8000/api/recommend', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query, top_k: 5 }),
      });
      const data = await res.json();
      setRecommendations(data.recommendations || []);
    } catch (e) {
      console.error('推荐请求失败:', e);
    } finally {
      setLoading(false);
    }
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
      <h1 className="text-2xl font-bold text-slate-900 mb-6">论文发现</h1>

      <div className="flex gap-2 mb-6">
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && fetchRecommendations()}
          placeholder="输入关键词，比如 transformer、diffusion..."
          className="flex-1 px-4 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
        <button
          onClick={fetchRecommendations}
          disabled={loading}
          className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-slate-300"
        >
          {loading ? '搜索中...' : '推荐'}
        </button>
      </div>

      {loading && <div className="text-slate-500 text-sm">正在搜索 arXiv 并计算相关性...</div>}

      {!loading && recommendations.length === 0 && (
        <div className="text-slate-400 text-sm p-8 text-center border border-dashed border-slate-300 rounded-lg">
          输入关键词，点击"推荐"，获取基于你研究兴趣的论文
        </div>
      )}

      <div className="space-y-4">
        {recommendations.map((paper, idx) => (
          <div
            key={paper.arxiv_id}
            className="bg-white rounded-lg border border-slate-200 p-5 hover:shadow-md transition"
          >
            <div className="flex items-start justify-between gap-4 mb-2">
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-1">
                  <span className="text-xs font-semibold text-slate-400">#{idx + 1}</span>
                  <span className="text-xs px-2 py-0.5 bg-green-100 text-green-700 rounded">
                    相关性 {paper.relevance_score.toFixed(2)}
                  </span>
                  {paper.has_code && (
                    <span className="text-xs px-2 py-0.5 bg-yellow-100 text-yellow-700 rounded">
                      ⭐ {paper.max_stars}
                    </span>
                  )}
                </div>
                <h2 className="text-base font-semibold text-slate-900 leading-tight">
                  {paper.title}
                </h2>
              </div>
            </div>

            <div className="text-xs text-slate-500 mb-3">
              {paper.authors.join(', ')}
              {paper.authors.length >= 5 ? ' 等' : ''} · {paper.published.slice(0, 10)}
            </div>

            <div className="text-sm text-slate-600 mb-3 leading-relaxed">
              {paper.abstract}...
            </div>

            <div className="flex flex-wrap gap-2 mb-3">
              {paper.reasons.map((reason, i) => (
                <span
                  key={i}
                  className="text-xs px-2 py-1 bg-blue-50 text-blue-700 rounded"
                >
                  💡 {reason}
                </span>
              ))}
            </div>

            <div className="flex items-center gap-3 pt-3 border-t border-slate-100">
              <a
                href={paper.abs_url}
                target="_blank"
                rel="noopener noreferrer"
                className="text-xs text-blue-600 hover:underline"
              >
                arXiv
              </a>
              <a
                href={paper.pdf_url}
                target="_blank"
                rel="noopener noreferrer"
                className="text-xs text-blue-600 hover:underline"
              >
                PDF
              </a>

              <div className="ml-auto flex items-center gap-2">
                <button
                  onClick={() => sendFeedback(paper.arxiv_id, 'like')}
                  className={`text-xs px-3 py-1 rounded border transition ${
                    feedback[paper.arxiv_id] === 'like'
                      ? 'bg-green-100 border-green-300 text-green-700'
                      : 'bg-white border-slate-200 text-slate-600 hover:bg-green-50'
                  }`}
                >
                  👍 {paper.like_count}
                </button>
                <button
                  onClick={() => sendFeedback(paper.arxiv_id, 'dislike')}
                  className={`text-xs px-3 py-1 rounded border transition ${
                    feedback[paper.arxiv_id] === 'dislike'
                      ? 'bg-red-100 border-red-300 text-red-700'
                      : 'bg-white border-slate-200 text-slate-600 hover:bg-red-50'
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