'use client';

import { useState, useRef, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

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
}

interface Message {
  role: 'user' | 'assistant';
  content: string;
  sources?: Source[];
  guardrails?: Guardrails;
}

export default function ChatPage() {
  const [query, setQuery] = useState('');
  const [messages, setMessages] = useState<Message[]>([]);
  const [loading, setLoading] = useState(false);
  const [status, setStatus] = useState('');
  const [expandedSources, setExpandedSources] = useState<Record<string, boolean>>({});
  
  const chatEndRef = useRef<HTMLDivElement>(null);

  // 1. 组件挂载时，从 localStorage 恢复聊天记录
  useEffect(() => {
    const saved = localStorage.getItem('chat_history');
    if (saved) {
      try {
        setMessages(JSON.parse(saved));
      } catch (e) {}
    }
  }, []);

  // 2. 消息更新时，自动存入 localStorage
  useEffect(() => {
    if (messages.length > 0) {
      localStorage.setItem('chat_history', JSON.stringify(messages));
    }
  }, [messages]);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const toggleExpand = (msgIndex: number, srcIndex: number) => {
    const key = `${msgIndex}-${srcIndex}`;
    setExpandedSources(prev => ({ ...prev, [key]: !prev[key] }));
  };

  const handleAsk = async () => {
    if (!query.trim() || loading) return;

    const currentQuery = query;
    setQuery('');
    setLoading(true);
    setStatus('正在检索知识库...');

    const newMessages = [...messages, { role: 'user', content: currentQuery } as Message];
    setMessages(newMessages);
    setMessages(prev => [...prev, { role: 'assistant', content: '', sources: [], guardrails: undefined }]);

    try {
      const response = await fetch('http://localhost:8000/api/qa/stream', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: currentQuery, top_k: 5 }),
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
              setMessages(prev => {
                const newMsgs = [...prev];
                const lastMsg = newMsgs[newMsgs.length - 1];
                if (lastMsg && lastMsg.role === 'assistant') lastMsg.content += data.content;
                return newMsgs;
              });
            } else if (data.type === 'sources') {
              setMessages(prev => {
                const newMsgs = [...prev];
                const lastMsg = newMsgs[newMsgs.length - 1];
                if (lastMsg && lastMsg.role === 'assistant') lastMsg.sources = data.sources;
                return newMsgs;
              });
            } else if (data.type === 'guardrails') {
              setMessages(prev => {
                const newMsgs = [...prev];
                const lastMsg = newMsgs[newMsgs.length - 1];
                if (lastMsg && lastMsg.role === 'assistant') lastMsg.guardrails = data.guardrails;
                return newMsgs;
              });
            } else if (data.type === 'done') {
              setLoading(false);
            } else if (data.type === 'error') {
              setMessages(prev => {
                const newMsgs = [...prev];
                const lastMsg = newMsgs[newMsgs.length - 1];
                if (lastMsg) lastMsg.content = '出错: ' + data.message;
                return newMsgs;
              });
              setLoading(false);
            }
          } catch (e) {}
        }
      }
    } catch (e) {
      setMessages(prev => {
        const newMsgs = [...prev];
        const lastMsg = newMsgs[newMsgs.length - 1];
        if (lastMsg) lastMsg.content = '请求失败: ' + String(e);
        return newMsgs;
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-[calc(100vh-2rem)] max-w-6xl mx-auto p-4">
      <div className="mb-4 shrink-0 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">智能问答</h1>
          <p className="text-sm text-slate-500 mt-1">基于混合检索与双重溯源，杜绝大模型幻觉</p>
        </div>
        {/* 清空按钮 */}
        {messages.length > 0 && (
          <button
            onClick={() => {
              if(confirm('确定要清空所有对话记录吗？')) {
                setMessages([]);
                localStorage.removeItem('chat_history');
              }
            }}
            className="text-xs px-3 py-1.5 text-red-600 bg-red-50 rounded-lg hover:bg-red-100 transition-colors"
          >
            🗑️ 清空对话
          </button>
        )}
      </div>

      <div className="flex-1 bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden flex flex-col">
        <div className="flex-1 overflow-y-auto p-6 space-y-6 bg-slate-50/50">
          {messages.length === 0 ? (
            <div className="h-full flex flex-col items-center justify-center text-slate-400">
              <div className="text-6xl mb-4">💬</div>
              <p className="text-lg">有什么我可以帮你的吗？</p>
              <p className="text-sm mt-2">试试问：“Transformer 的 beta1 和 beta2 是多少？”</p>
            </div>
          ) : (
            messages.map((msg, msgIdx) => (
              <div key={msgIdx} className="space-y-4">
                {msg.role === 'user' && (
                  <div className="flex justify-end">
                    <div className="bg-blue-600 text-white px-5 py-3 rounded-2xl rounded-tr-sm max-w-[80%] shadow-sm">
                      {msg.content}
                    </div>
                  </div>
                )}

                {msg.role === 'assistant' && (
                  <div className="flex justify-start">
                    <div className="bg-white border border-slate-200 px-6 py-4 rounded-2xl rounded-tl-sm max-w-[85%] shadow-sm w-full">
                      <div className="flex items-center gap-2 mb-3">
                        <div className="w-8 h-8 rounded-full bg-blue-100 flex items-center justify-center text-lg">🤖</div>
                        <span className="text-sm font-semibold text-slate-700">Research Agent</span>
                      </div>
                      
                      {msgIdx === messages.length - 1 && status && (
                        <div className="text-xs text-blue-500 animate-pulse mb-2">⏳ {status}</div>
                      )}
                      
                      <div className="prose prose-sm md:prose-base prose-slate max-w-none text-slate-800 leading-relaxed">
                        <ReactMarkdown remarkPlugins={[remarkGfm]}>{msg.content}</ReactMarkdown>
                        {msgIdx === messages.length - 1 && loading && <span className="inline-block w-2 h-4 bg-blue-500 animate-pulse ml-1 align-middle" />}
                      </div>

                      {msg.guardrails && (
                        <div className="mt-4 pt-4 border-t border-slate-100 flex items-center gap-4 text-xs">
                          <span className="text-green-600 font-medium bg-green-50 px-2 py-1 rounded flex items-center gap-1">
                            🛡️ 忠实度 {(msg.guardrails.faithfulness_score * 100).toFixed(0)}%
                          </span>
                          <span className="text-slate-500">共 {msg.guardrails.total_sentences} 句话，{msg.guardrails.unsupported_sentences.length} 句未溯源</span>
                        </div>
                      )}

                      {msg.sources && msg.sources.length > 0 && 
                       !msg.content.includes('不足') && 
                       !msg.content.includes('无法回答') && 
                       !msg.content.includes('没有找到') && (
                        <div className="mt-6">
                          <div className="text-xs font-semibold text-slate-500 mb-3">📎 引用溯源（{msg.sources.length} 个片段）</div>
                          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            {msg.sources.map((s) => {
                              const isExpanded = expandedSources[`${msgIdx}-${s.index}`];
                              return (
                                <div key={s.index} className="bg-slate-50 border border-slate-200 p-4 rounded-xl">
                                  <div className="flex items-center gap-2 mb-2">
                                    <span className="text-[10px] font-bold text-blue-600 bg-blue-100 px-2 py-0.5 rounded">[来源{s.index}]</span>
                                    <span className="text-[10px] text-slate-500 truncate">{s.section_path || '未知章节'}</span>
                                  </div>
                                  <div className={`text-xs text-slate-600 leading-relaxed ${isExpanded ? '' : 'line-clamp-3'}`}>
                                    {s.content_preview}
                                  </div>
                                  <button
                                    onClick={() => toggleExpand(msgIdx, s.index)}
                                    className="text-[10px] text-blue-500 hover:text-blue-700 mt-2 font-medium"
                                  >
                                    {isExpanded ? '收起片段' : '展开完整片段'}
                                  </button>
                                </div>
                              );
                            })}
                          </div>
                        </div>
                      )}
                    </div>
                  </div>
                )}
              </div>
            ))
          )}
          <div ref={chatEndRef} />
        </div>

        <div className="p-4 bg-white border-t border-slate-200 shrink-0">
          <div className="relative">
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleAsk()}
              placeholder="输入你的问题，按 Enter 发送..."
              className="w-full pl-5 pr-14 py-4 bg-slate-50 border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:bg-white transition-all shadow-inner"
            />
            <button
              onClick={handleAsk}
              disabled={loading || !query.trim()}
              className="absolute right-2 top-1/2 -translate-y-1/2 p-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-slate-300 transition-colors"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8"></path></svg>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}