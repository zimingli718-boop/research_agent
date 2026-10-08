'use client';

import { useState, useRef, useEffect } from 'react';

interface Source {
  index: number;
  paper_id: string;
  chunk_index: number;
  section_path: string;
  content_preview: string;
}

interface Guardrails {
  total_sentences: number;
  unsupported_sentences: string[];
  faithfulness_score: number;
  citations_used: number[];
}

export default function ChatPage() {
  const [query, setQuery] = useState('');
  const [answer, setAnswer] = useState('');
  const [sources, setSources] = useState<Source[]>([]);
  const [guardrails, setGuardrails] = useState<Guardrails | null>(null);
  const [loading, setLoading] = useState(false);
  const [status, setStatus] = useState('');
  const answerRef = useRef<HTMLDivElement>(null);

  const handleAsk = async () => {
    if (!query.trim() || loading) return;

    setLoading(true);
    setAnswer('');
    setSources([]);
    setGuardrails(null);
    setStatus('正在检索...');

    try {
      const response = await fetch('http://localhost:8000/api/qa/stream', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query, top_k: 5 }),
      });

      const reader = response.body?.getReader();
      const decoder = new TextDecoder();

      if (!reader) throw new Error('无法读取响应流');

      let buffer = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n\n');
        buffer = lines.pop() || '';

        for (const line of lines) {
          if (!line.startsWith('data: ')) continue;
          try {
            const data = JSON.parse(line.slice(6));
            if (data.type === 'status') {
              setStatus(data.message);
            } else if (data.type === 'token') {
              setStatus('');
              setAnswer((prev) => prev + data.content);
            } else if (data.type === 'sources') {
              setSources(data.sources);
            } else if (data.type === 'guardrails') {
              setGuardrails(data.guardrails);
            } else if (data.type === 'done') {
              setLoading(false);
            } else if (data.type === 'error') {
              setAnswer('出错: ' + data.message);
              setLoading(false);
            }
          } catch (e) {
            console.error('解析失败', e);
          }
        }
      }
    } catch (e) {
      setAnswer('请求失败: ' + String(e));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    answerRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [answer]);

  return (
    <div className="p-8 max-w-4xl mx-auto">
      <h1 className="text-2xl font-bold text-slate-900 mb-6">智能问答</h1>

      <div className="flex gap-2 mb-6">
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && handleAsk()}
          placeholder="问点什么，比如：Transformer 用了多少块 GPU？"
          className="flex-1 px-4 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
        <button
          onClick={handleAsk}
          disabled={loading}
          className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-slate-300"
        >
          {loading ? '思考中...' : '提问'}
        </button>
      </div>

      {status && (
        <div className="text-sm text-slate-500 mb-4">⏳ {status}</div>
      )}

      {answer && (
        <div className="bg-white rounded-lg border border-slate-200 p-6 mb-4">
          <h2 className="text-sm font-semibold text-slate-500 mb-3">回答</h2>
          <div className="text-slate-800 whitespace-pre-wrap leading-relaxed">
            {answer}
          </div>
          <div ref={answerRef} />
        </div>
      )}

      {sources.length > 0 && (
        <div className="bg-slate-50 rounded-lg border border-slate-200 p-6">
          <h2 className="text-sm font-semibold text-slate-500 mb-3">
            引用来源（{sources.length} 个）
          </h2>
          <div className="space-y-2">
            {sources.map((s) => (
              <div
                key={s.index}
                className="text-sm bg-white rounded p-3 border border-slate-200"
              >
                <div className="flex items-center gap-2 mb-1">
                  <span className="px-2 py-0.5 bg-blue-100 text-blue-700 rounded text-xs font-medium">
                    来源{s.index}
                  </span>
                  <span className="text-slate-500 text-xs">
                    {s.section_path || '未知章节'}
                  </span>
                </div>
                <div className="text-slate-600 text-xs">
                  {s.content_preview}...
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {guardrails && (
        <div className="bg-green-50 rounded-lg border border-green-200 p-4 mt-4">
          <h2 className="text-sm font-semibold text-green-700 mb-2">
            Guardrails 幻觉防护
          </h2>
          <div className="text-sm text-slate-700 space-y-1">
            <div>
              忠实度分数：
              <span className="font-mono font-semibold text-green-700">
                {guardrails.faithfulness_score}
              </span>
            </div>
            <div>句子总数：{guardrails.total_sentences}</div>
            <div>无引用句子数：{guardrails.unsupported_sentences?.length || 0}</div>
            {guardrails.citations_used?.length > 0 && (
              <div>使用的来源编号：{[...guardrails.citations_used].join(', ')}</div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}