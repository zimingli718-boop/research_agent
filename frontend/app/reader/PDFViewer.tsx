'use client';

import { useState, useEffect, useRef } from 'react';
import { Document, Page, pdfjs } from 'react-pdf';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import 'react-pdf/dist/Page/AnnotationLayer.css';
import 'react-pdf/dist/Page/TextLayer.css';

pdfjs.GlobalWorkerOptions.workerSrc = `https://unpkg.com/pdfjs-dist@${pdfjs.version}/build/pdf.worker.min.mjs`;

interface Heading { level: number; title: string; page: number | null; y: number | null; }
interface Reference { num: number; text: string; ref_page: number; in_text_pages: number[]; in_text_first_page: number | null; }
interface PDFViewerProps { pdfUrl: string; paperId: string; }

export default function PDFViewer({ pdfUrl, paperId }: PDFViewerProps) {
  const [numPages, setNumPages] = useState<number>(0);
  const [pageNumber, setPageNumber] = useState<number>(1);
  const [headings, setHeadings] = useState<Heading[]>([]);
  const [references, setReferences] = useState<Reference[]>([]);
  const [activeHeading, setActiveHeading] = useState<number>(-1);
  const [activeRef, setActiveRef] = useState<number>(-1);
  const [showRefs, setShowRefs] = useState<boolean>(false);

  const [translation, setTranslation] = useState<string>('');
  const [translating, setTranslating] = useState<boolean>(false);
  const [showTranslation, setShowTranslation] = useState<boolean>(false);
  const [selectedText, setSelectedText] = useState<string>('');
  const [selectionTranslation, setSelectionTranslation] = useState<string>('');

  const [headingLoading, setHeadingLoading] = useState(false);
  const [refLoading, setRefLoading] = useState(false);

  const pdfScrollRef = useRef<HTMLDivElement>(null);
  const translationScrollRef = useRef<HTMLDivElement>(null);
  const syncingRef = useRef<boolean>(false);

  useEffect(() => {
    setHeadingLoading(true);
    fetch(`http://localhost:8000/api/papers/${paperId}/structure`)
      .then((r) => r.json()).then((data) => setHeadings(data.headings || []))
      .catch(() => setHeadings([])).finally(() => setHeadingLoading(false));
  }, [paperId]);

  useEffect(() => {
    setRefLoading(true);
    fetch(`http://localhost:8000/api/papers/${paperId}/references`)
      .then((r) => r.json()).then((data) => setReferences(data.references || []))
      .catch(() => setReferences([])).finally(() => setRefLoading(false));
  }, [paperId]);

  function onDocumentLoadSuccess({ numPages }: { numPages: number }) { setNumPages(numPages); }

  function handlePdfScroll(e: React.UIEvent<HTMLDivElement>) {
    if (syncingRef.current) return; syncingRef.current = true;
    const pdfEl = e.currentTarget, transEl = translationScrollRef.current;
    if (transEl) {
      const ratio = pdfEl.scrollTop / (pdfEl.scrollHeight - pdfEl.clientHeight || 1);
      transEl.scrollTop = ratio * (transEl.scrollHeight - transEl.clientHeight);
    }
    setTimeout(() => { syncingRef.current = false; }, 50);
  }

  function handleTranslationScroll(e: React.UIEvent<HTMLDivElement>) {
    if (syncingRef.current) return; syncingRef.current = true;
    const transEl = e.currentTarget, pdfEl = pdfScrollRef.current;
    if (pdfEl) {
      const ratio = transEl.scrollTop / (transEl.scrollHeight - transEl.clientHeight || 1);
      pdfEl.scrollTop = ratio * (pdfEl.scrollHeight - pdfEl.clientHeight);
    }
    setTimeout(() => { syncingRef.current = false; }, 50);
  }

  function handleMouseUp() {
    const selection = window.getSelection();
    const text = selection?.toString().trim() || '';
    if (text && text.length > 2 && text.length < 2000) setSelectedText(text);
  }

  async function translateSelection() {
    if (!selectedText) return;
    setTranslating(true);
    try {
      const res = await fetch('http://localhost:8000/api/translate', {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text: selectedText, target_lang: 'zh' }),
      });
      const data = await res.json();
      setSelectionTranslation(data.translated || '翻译失败');
    } catch (e) { setSelectionTranslation('翻译请求失败'); } finally { setTranslating(false); }
  }

  async function translateCurrentPage() {
    setTranslating(true); setShowTranslation(true); setTranslation('');
    try {
      const pageRes = await fetch(`http://localhost:8000/api/papers/${paperId}/page/${pageNumber}`);
      const pageData = await pageRes.json();
      const pageText = pageData.text || '';
      if (!pageText.trim()) { setTranslation('当前页无文本内容'); return; }

      const res = await fetch('http://localhost:8000/api/translate', {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text: pageText, target_lang: 'zh' }),
      });
      const data = await res.json();
      setTranslation(data.translated || '翻译失败');
    } catch (e) { setTranslation('翻译请求失败'); } finally { setTranslating(false); }
  }

  function onRenderTextLayerSuccess() {
    setTimeout(() => {
      const textLayer = document.querySelector('.react-pdf__Page__textContent');
      if (!textLayer) return;
      textLayer.querySelectorAll('span').forEach((span) => {
        const match = (span.textContent || '').match(/^\[(\d+)(?:,\s*\d+)*\]$/);
        if (match) {
          const el = span as HTMLElement;
          el.style.cursor = 'pointer'; el.style.color = '#2563eb'; el.style.textDecoration = 'underline';
          el.onclick = (e) => {
            e.stopPropagation();
            const ref = references.find((r) => r.num === parseInt(match[1]));
            if (ref) {
              setPageNumber(ref.ref_page); setActiveRef(ref.num); setShowRefs(true);
              setTimeout(() => document.getElementById(`ref-${ref.num}`)?.scrollIntoView({ behavior: 'smooth' }), 300);
            }
          };
        }
      });
    }, 100);
  }

  // 核心：强制所有面板并排显示，绝不因换行或数据为空导致变形
  return (
    <div className="flex gap-4 w-full h-[calc(100vh-140px)] items-stretch">
      
      {/* 1. 左侧目录 */}
      <aside className="w-48 flex-shrink-0 bg-slate-50 rounded-lg border border-slate-200 p-3 overflow-y-auto hidden md:block">
        <h2 className="text-sm font-semibold text-slate-700 mb-3">目录</h2>
        {headingLoading ? <div className="text-xs text-slate-400">解析中...</div> : (
          <nav className="space-y-1">
            {headings.map((h, idx) => (
              <div key={idx} onClick={() => { if (h.page) { setPageNumber(h.page); setActiveHeading(idx); } }}
                className={`text-xs cursor-pointer truncate rounded px-2 py-1 transition ${activeHeading === idx ? 'bg-blue-100 text-blue-700 font-medium' : 'text-slate-600 hover:bg-slate-200'}`}
                style={{ paddingLeft: `${(h.level - 1) * 12 + 8}px` }}>{h.title}</div>
            ))}
          </nav>
        )}
      </aside>

      {/* 2. 中间 PDF 区域 */}
      <div className="flex-1 flex flex-col min-w-0 bg-white rounded-lg border border-slate-200 overflow-hidden">
        <div className="flex items-center gap-3 p-3 border-b border-slate-100 bg-slate-50 shrink-0">
          <button onClick={() => setPageNumber((p) => Math.max(1, p - 1))} disabled={pageNumber <= 1} className="px-3 py-1.5 text-xs bg-white border rounded shadow-sm hover:bg-slate-50">上一页</button>
          <span className="text-xs text-slate-600 font-mono">第 {pageNumber} 页 / {numPages} 页</span>
          <button onClick={() => setPageNumber((p) => Math.min(numPages, p + 1))} disabled={pageNumber >= numPages} className="px-3 py-1.5 text-xs bg-white border rounded shadow-sm hover:bg-slate-50">下一页</button>
          <button onClick={translateCurrentPage} disabled={translating} className="px-3 py-1.5 text-xs bg-green-600 text-white rounded shadow-sm hover:bg-green-700">翻译本页</button>
          <button onClick={() => setShowRefs(!showRefs)} className="ml-auto px-3 py-1.5 text-xs bg-blue-600 text-white rounded shadow-sm hover:bg-blue-700">参考文献</button>
        </div>
        
        {/* 内部双栏容器 */}
        <div className="flex flex-1 overflow-hidden">
          <div ref={pdfScrollRef} onScroll={handlePdfScroll} className={`overflow-auto p-4 flex justify-center ${showTranslation ? 'w-1/2 border-r border-slate-100' : 'w-full'}`} onMouseUp={handleMouseUp}>
            <Document file={pdfUrl} onLoadSuccess={onDocumentLoadSuccess}>
              <Page pageNumber={pageNumber} width={showTranslation ? 450 : 800} renderTextLayer={true} renderAnnotationLayer={true} onRenderTextLayerSuccess={onRenderTextLayerSuccess} />
            </Document>
          </div>

          {/* 翻译面板（强制携带 prose 渲染） */}
          {showTranslation && (
            <div ref={translationScrollRef} onScroll={handleTranslationScroll} className="w-1/2 bg-amber-50 overflow-auto p-6">
              <h2 className="text-sm font-bold text-amber-800 mb-4 pb-2 border-b border-amber-200">中文翻译（第 {pageNumber} 页）</h2>
              {translating ? <div className="text-sm text-slate-500 animate-pulse">正在翻译...</div> : (
                <div className="prose prose-sm prose-slate max-w-none text-slate-800 leading-loose">
                  <ReactMarkdown remarkPlugins={[remarkGfm]}>{translation}</ReactMarkdown>
                </div>
              )}
            </div>
          )}
        </div>
      </div>

      {/* 3. 右侧参考文献面板 */}
      {showRefs && (
        <aside className="w-72 flex-shrink-0 bg-slate-50 rounded-lg border border-slate-200 p-3 overflow-y-auto hidden xl:block">
          <h2 className="text-sm font-semibold text-slate-700 mb-3">参考文献（{references.length}）</h2>
          {refLoading ? <div className="text-xs text-slate-400">解析中...</div> : (
            <div className="space-y-2">
              {references.map((ref) => (
                <div key={ref.num} id={`ref-${ref.num}`} className={`text-xs p-2 rounded border transition ${activeRef === ref.num ? 'bg-blue-100 border-blue-300' : 'bg-white border-slate-200'}`}>
                  <span className="font-semibold cursor-pointer text-blue-600" onClick={() => setPageNumber(ref.ref_page)}>[{ref.num}]</span>
                  <p className="mt-1 text-slate-600 line-clamp-3">{ref.text}</p>
                </div>
              ))}
            </div>
          )}
        </aside>
      )}

      {/* 划词翻译弹窗 */}
      {selectedText && (
        <div className="fixed bottom-8 left-1/2 -translate-x-1/2 bg-white border border-blue-200 shadow-2xl rounded-xl p-4 w-[600px] z-50">
          <div className="flex justify-between items-center mb-2">
            <span className="text-xs font-bold text-blue-800">划词翻译</span>
            <div className="space-x-2">
              <button onClick={translateSelection} className="px-3 py-1 bg-blue-600 text-white rounded text-xs">翻译</button>
              <button onClick={() => { setSelectedText(''); setSelectionTranslation(''); }} className="px-3 py-1 bg-slate-200 rounded text-xs">关闭</button>
            </div>
          </div>
          <div className="text-xs text-slate-500 mb-2 truncate">{selectedText}</div>
          {selectionTranslation && <div className="text-sm text-slate-800 bg-blue-50 p-2 rounded">{selectionTranslation}</div>}
        </div>
      )}
    </div>
  );
}