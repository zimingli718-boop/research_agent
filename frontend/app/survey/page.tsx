'use client';

import { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

export default function SurveyPage() {
  const [activeTab, setActiveTab] = useState<'survey' | 'future'>('survey');
  const [surveyResult, setSurveyResult] = useState<any>(null);
  const [futureResult, setFutureResult] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  async function generateSurvey() {
    setLoading(true);
    setSurveyResult(null);
    try {
      const res = await fetch('http://localhost:8000/api/survey/generate', { method: 'POST' });
      const data = await res.json();
      setSurveyResult(data);
    } catch (e) {
      console.error(e);
      alert('生成失败，请检查后端');
    } finally {
      setLoading(false);
    }
  }

  async function generateFuture() {
    setLoading(true);
    setFutureResult(null);
    try {
      const res = await fetch('http://localhost:8000/api/future-work/analyze', { method: 'POST' });
      const data = await res.json();
      setFutureResult(data);
    } catch (e) {
      console.error(e);
      alert('分析失败，请检查后端');
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="p-8 max-w-7xl mx-auto h-[calc(100vh-2rem)] flex flex-col">
      {/* 页头 */}
      <div className="mb-6 shrink-0">
        <h1 className="text-2xl font-bold text-slate-900">学术综述与前沿探索</h1>
        <p className="text-sm text-slate-500 mt-1">
          基于领域文献图谱的宏观脉络梳理与微观痛点挖掘
        </p>
      </div>

      {/* 标签页切换 */}
      <div className="flex gap-4 mb-6 border-b border-slate-200 shrink-0">
        <button
          onClick={() => setActiveTab('survey')}
          className={`pb-3 text-sm font-medium border-b-2 transition-colors ${
            activeTab === 'survey'
              ? 'border-blue-600 text-blue-600'
              : 'border-transparent text-slate-500 hover:text-slate-800'
          }`}
        >
          📚 自动综述生成
        </button>
        <button
          onClick={() => setActiveTab('future')}
          className={`pb-3 text-sm font-medium border-b-2 transition-colors ${
            activeTab === 'future'
              ? 'border-green-600 text-green-600'
              : 'border-transparent text-slate-500 hover:text-slate-800'
          }`}
        >
          🚀 Future Work 前沿挖掘
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-6 flex-1 min-h-0">
        {/* 左侧控制区 */}
        <div className="md:col-span-1 space-y-4">
          <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm">
            <h3 className="text-sm font-semibold text-slate-800 mb-2">
              {activeTab === 'survey' ? '生成领域综述' : '挖掘探索方向'}
            </h3>
            <p className="text-xs text-slate-500 mb-4 leading-relaxed">
              {activeTab === 'survey'
                ? '结合本地文献库与 PageRank 图谱结构，自动生成带引用的领域综述。'
                : '提取多篇论文的 Future Work，结合时间线去重，排除已被解决的旧 idea。'}
            </p>
            <button
              onClick={activeTab === 'survey' ? generateSurvey : generateFuture}
              disabled={loading}
              className={`w-full py-2 text-sm text-white rounded-lg transition-colors disabled:bg-slate-300 ${
                activeTab === 'survey'
                  ? 'bg-blue-600 hover:bg-blue-700'
                  : 'bg-green-600 hover:bg-green-700'
              }`}
            >
              {loading ? '深度分析中...' : activeTab === 'survey' ? '一键生成' : '开始挖掘'}
            </button>
          </div>

          <div className="bg-slate-50 rounded-xl border border-slate-200 p-5">
            <h4 className="text-xs font-semibold text-slate-700 mb-2">💡 提示</h4>
            <p className="text-xs text-slate-500 leading-relaxed">
              本功能依赖 DeepSeek 大模型。生成过程约需 10-30 秒，请耐心等待。
            </p>
          </div>
        </div>

        {/* 右侧内容展示区（独立滚动） */}
        <div className="md:col-span-3 flex flex-col min-h-0">
          <div className="bg-white rounded-xl border border-slate-200 p-8 shadow-sm flex-1 overflow-y-auto">
            {/* 综述展示 */}
            {activeTab === 'survey' && (
              <>
                {!surveyResult && !loading && (
                  <div className="h-full flex flex-col items-center justify-center text-slate-400 mt-32">
                    <div className="text-4xl mb-4">📝</div>
                    <p className="text-sm">点击左侧按钮，生成基于本地库的学术综述</p>
                  </div>
                )}
                {loading && activeTab === 'survey' && (
                  <div className="text-center text-blue-600 mt-32 animate-pulse">
                    正在阅读文献摘要并撰写综述...
                  </div>
                )}
                {surveyResult && (
                  <div>
                    {/* 启用 prose 渲染，大幅优化排版 */}
                    <div className="prose prose-slate prose-sm md:prose-base max-w-none prose-headings:font-semibold prose-a:text-blue-600 leading-8">
                      <ReactMarkdown remarkPlugins={[remarkGfm]}>
                        {surveyResult.survey}
                      </ReactMarkdown>
                    </div>

                    <div className="mt-8 pt-6 border-t border-slate-100">
                      <h3 className="text-xs font-semibold text-slate-500 mb-3 uppercase tracking-wider">
                        引用来源 ({surveyResult.papers?.length || 0})
                      </h3>
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                        {surveyResult.papers?.map((p: any) => (
                          <div key={p.index} className="flex items-start gap-2 text-xs text-slate-600 bg-slate-50 p-3 rounded-lg border border-slate-100">
                            <span className="font-mono bg-blue-100 text-blue-700 px-2 py-0.5 rounded shrink-0 font-medium">
                              [{p.index}]
                            </span>
                            <span className="truncate leading-relaxed">{p.title} ({p.year})</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                )}
              </>
            )}

            {/* Future Work 展示 */}
            {activeTab === 'future' && (
              <>
                {!futureResult && !loading && (
                  <div className="h-full flex flex-col items-center justify-center text-slate-400 mt-32">
                    <div className="text-4xl mb-4">🔭</div>
                    <p className="text-sm">点击左侧按钮，挖掘真正有价值的未解之谜</p>
                  </div>
                )}
                {loading && activeTab === 'future' && (
                  <div className="text-center text-green-600 mt-32 animate-pulse">
                    正在对比文献痛点与时序，排除失效方向...
                  </div>
                )}
                {futureResult && (
                  <div>
                    {/* 启用 prose 渲染，彻底解决表格和标题挤在一起的问题 */}
                    <div className="prose prose-slate prose-sm md:prose-base max-w-none prose-headings:font-semibold prose-table:text-sm prose-td:border prose-td:border-slate-200 prose-td:p-2 prose-th:bg-slate-50 prose-th:p-2 leading-8">
                      <ReactMarkdown remarkPlugins={[remarkGfm]}>
                        {futureResult.analysis}
                      </ReactMarkdown>
                    </div>

                    <div className="mt-8 pt-6 border-t border-slate-100">
                      <h3 className="text-xs font-semibold text-slate-500 mb-3 uppercase tracking-wider">
                        分析来源文献 ({futureResult.papers?.length || 0})
                      </h3>
                      <div className="flex flex-wrap gap-2">
                        {futureResult.papers?.map((p: any, i: number) => (
                          <div key={i} className="text-xs text-slate-600 bg-slate-50 px-3 py-1.5 rounded-full border border-slate-200">
                            {p.title} ({p.year})
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                )}
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}