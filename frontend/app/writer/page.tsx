'use client';

import { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

export default function WriterPage() {
  const [activeTab, setActiveTab] = useState<'outline' | 'diagram' | 'csv' | 'translate'>('outline');
  const [loading, setLoading] = useState(false);

  // 1. 框架
  const [idea, setIdea] = useState('');
  const [outlineResult, setOutlineResult] = useState<any>(null);

  // 2. 拓扑图
  const [diagramDesc, setDiagramDesc] = useState('');
  const [diagramType, setDiagramType] = useState('mermaid');
  const [diagramResult, setDiagramResult] = useState<any>(null);

  // 3. CSV
  const [csvResult, setCsvResult] = useState<any>(null);
  const [csvFile, setCsvFile] = useState<File | null>(null);

  // 4. 翻译
  const [transText, setTransText] = useState('');
  const [transLang, setTransLang] = useState('en');
  const [transResult, setTransResult] = useState('');

  async function handleGenerateOutline() {
    if (!idea.trim()) return alert('请输入 idea');
    setLoading(true);
    try {
      const res = await fetch('http://localhost:8000/api/writer/outline', {
        method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ idea }),
      });
      setOutlineResult(await res.json());
    } catch (e) { console.error(e); } finally { setLoading(false); }
  }

  async function handleGenerateDiagram() {
    if (!diagramDesc.trim()) return alert('请输入描述');
    setLoading(true);
    try {
      const res = await fetch('http://localhost:8000/api/writer/diagram', {
        method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ description: diagramDesc, diagram_type: diagramType }),
      });
      setDiagramResult(await res.json());
    } catch (e) { console.error(e); } finally { setLoading(false); }
  }

  async function handleUploadCsv(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;
    setCsvFile(file); setLoading(true);
    const formData = new FormData(); formData.append('file', file);
    try {
      const res = await fetch('http://localhost:8000/api/writer/csv', { method: 'POST', body: formData });
      setCsvResult(await res.json());
    } catch (e) { console.error(e); } finally { setLoading(false); }
  }

  async function handleTranslate() {
    if (!transText.trim()) return alert('请输入文本');
    setLoading(true);
    try {
      const res = await fetch('http://localhost:8000/api/writer/translate', {
        method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ text: transText, target_lang: transLang }),
      });
      const data = await res.json(); setTransResult(data.translated);
    } catch (e) { console.error(e); } finally { setLoading(false); }
  }

  return (
    <div className="p-8 max-w-6xl mx-auto h-[calc(100vh-2rem)] flex flex-col">
      <div className="mb-6 shrink-0">
        <h1 className="text-2xl font-bold text-slate-900">学术写作辅助 Copilot</h1>
        <p className="text-sm text-slate-500 mt-1">无幻觉框架 · 拓扑图生成 · 数据可视化 · 学术翻译</p>
      </div>

      <div className="flex gap-4 mb-6 border-b border-slate-200 shrink-0 overflow-x-auto">
        <button onClick={() => setActiveTab('outline')} className={`pb-3 text-sm font-medium border-b-2 whitespace-nowrap ${activeTab === 'outline' ? 'border-blue-600 text-blue-600' : 'border-transparent text-slate-500'}`}>📝 论文框架</button>
        <button onClick={() => setActiveTab('diagram')} className={`pb-3 text-sm font-medium border-b-2 whitespace-nowrap ${activeTab === 'diagram' ? 'border-blue-600 text-blue-600' : 'border-transparent text-slate-500'}`}>📊 拓扑图脚本</button>
        <button onClick={() => setActiveTab('csv')} className={`pb-3 text-sm font-medium border-b-2 whitespace-nowrap ${activeTab === 'csv' ? 'border-blue-600 text-blue-600' : 'border-transparent text-slate-500'}`}>📈 CSV 可视化</button>
        <button onClick={() => setActiveTab('translate')} className={`pb-3 text-sm font-medium border-b-2 whitespace-nowrap ${activeTab === 'translate' ? 'border-blue-600 text-blue-600' : 'border-transparent text-slate-500'}`}>🌐 学术翻译</button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 flex-1 min-h-0">
        <div className="md:col-span-1 space-y-4 overflow-y-auto pr-2">
          {activeTab === 'outline' && (
            <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm">
              <h3 className="text-sm font-semibold text-slate-800 mb-2">输入 Idea</h3>
              <textarea value={idea} onChange={(e) => setIdea(e.target.value)} placeholder="基于图神经网络的推荐系统..." className="w-full h-32 p-3 text-sm border rounded-lg resize-none mb-4" />
              <button onClick={handleGenerateOutline} disabled={loading} className="w-full py-2 bg-blue-600 text-white rounded-lg text-sm hover:bg-blue-700 disabled:bg-slate-300">生成框架</button>
            </div>
          )}
          {activeTab === 'diagram' && (
            <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm">
              <h3 className="text-sm font-semibold text-slate-800 mb-2">架构描述</h3>
              <textarea value={diagramDesc} onChange={(e) => setDiagramDesc(e.target.value)} placeholder="输入层 -> 双分支注意力 -> 拼接 -> 输出" className="w-full h-32 p-3 text-sm border rounded-lg resize-none mb-4" />
              <select value={diagramType} onChange={(e) => setDiagramType(e.target.value)} className="w-full mb-4 p-2 text-sm border rounded-lg">
                <option value="mermaid">Mermaid</option><option value="graphviz">Graphviz</option><option value="tikz">TikZ</option>
              </select>
              <button onClick={handleGenerateDiagram} disabled={loading} className="w-full py-2 bg-blue-600 text-white rounded-lg text-sm hover:bg-blue-700 disabled:bg-slate-300">生成代码</button>
            </div>
          )}
          {activeTab === 'csv' && (
            <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm">
              <h3 className="text-sm font-semibold text-slate-800 mb-2">上传 CSV</h3>
              <input type="file" accept=".csv" onChange={handleUploadCsv} className="block w-full text-sm file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:bg-blue-50 file:text-blue-700 mb-4" />
              {csvFile && <div className="text-xs text-slate-600">已选: {csvFile.name}</div>}
            </div>
          )}
          {activeTab === 'translate' && (
            <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm">
              <h3 className="text-sm font-semibold text-slate-800 mb-2">翻译文本</h3>
              <textarea value={transText} onChange={(e) => setTransText(e.target.value)} placeholder="粘贴学术文本..." className="w-full h-32 p-3 text-sm border rounded-lg resize-none mb-4" />
              <select value={transLang} onChange={(e) => setTransLang(e.target.value)} className="w-full mb-4 p-2 text-sm border rounded-lg">
                <option value="en">中文 → 英文</option><option value="zh">英文 → 中文</option>
              </select>
              <button onClick={handleTranslate} disabled={loading} className="w-full py-2 bg-blue-600 text-white rounded-lg text-sm hover:bg-blue-700 disabled:bg-slate-300">翻译</button>
            </div>
          )}
        </div>

        <div className="md:col-span-2 flex flex-col min-h-0">
          <div className="bg-white rounded-xl border border-slate-200 p-8 shadow-sm flex-1 overflow-y-auto">
            {loading && <div className="text-center mt-32 text-blue-600 animate-pulse">处理中...</div>}
            
            {activeTab === 'outline' && !loading && outlineResult && (
              <div>
                <div className="prose prose-slate prose-sm max-w-none"><ReactMarkdown remarkPlugins={[remarkGfm]}>{outlineResult.outline}</ReactMarkdown></div>
                <div className="mt-8 pt-4 border-t border-slate-100">
                  <h4 className="text-xs font-semibold text-slate-500 mb-2">本地真实文献</h4>
                  <ul className="text-xs text-slate-600 list-disc pl-4">{outlineResult.available_refs?.map((r: string, i: number) => <li key={i}>{r}</li>)}</ul>
                </div>
              </div>
            )}

            {activeTab === 'diagram' && !loading && diagramResult && (
              <div>
                <div className="flex justify-between items-center mb-2"><h3 className="text-sm font-semibold">生成代码</h3><button onClick={() => navigator.clipboard.writeText(diagramResult.code)} className="text-xs text-blue-600">复制</button></div>
                <pre className="bg-slate-900 text-slate-200 p-4 rounded-lg text-sm overflow-x-auto"><code>{diagramResult.code}</code></pre>
              </div>
            )}

            {activeTab === 'csv' && !loading && csvResult && (
              <div>
                <img 
                  src={`data:image/png;base64,${csvResult.image_base64}`} 
                  alt="图表" 
                  className="w-full max-w-2xl mx-auto border rounded-lg shadow-sm mb-8 bg-white" 
                />
                
                <div className="bg-amber-50 p-6 rounded-xl border border-amber-200">
                  <h3 className="text-base font-semibold text-amber-900 mb-4 flex items-center gap-2">
                    <span>📝</span> 自动提炼的学术 Caption
                  </h3>
                  <div className="prose prose-slate prose-sm md:prose-base max-w-none text-amber-900 leading-relaxed">
                    <ReactMarkdown remarkPlugins={[remarkGfm]}>
                      {csvResult.caption}
                    </ReactMarkdown>
                  </div>
                </div>
              </div>
            )}

            {activeTab === 'translate' && !loading && transResult && (
              <div>
                <h3 className="text-sm font-semibold mb-2">翻译结果</h3>
                <div className="text-sm whitespace-pre-wrap bg-slate-50 p-4 rounded-lg border">{transResult}</div>
              </div>
            )}

            {!loading && !outlineResult && !diagramResult && !csvResult && !transResult && (
              <div className="h-full flex flex-col items-center justify-center text-slate-400 mt-32"><div className="text-4xl mb-4">✍️</div><p className="text-sm">在左侧操作，结果展示在此处</p></div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}