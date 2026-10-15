'use client';

import { useState, useEffect, useRef } from 'react';
import { Document, Page, pdfjs } from 'react-pdf';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import 'react-pdf/dist/Page/AnnotationLayer.css';
import 'react-pdf/dist/Page/TextLayer.css';

pdfjs.GlobalWorkerOptions.workerSrc = `https://unpkg.com/pdfjs-dist@${pdfjs.version}/build/pdf.worker.min.mjs`;

interface Heading {
  level: number;
  title: string;
  page: number | null;
  y: number | null;
}

interface Reference {
  num: number;
  text: string;
  ref_page: number;
  in_text_pages: number[];
  in_text_first_page: number | null;
}

interface PDFViewerProps {
  pdfUrl: string;
  paperId: string;
}

export default function PDFViewer({ pdfUrl, paperId }: PDFViewerProps) {
  const [numPages, setNumPages] = useState<number>(0);
  const [pageNumber, setPageNumber] = useState<number>(1);
  const [headings, setHeadings] = useState<Heading[]>([]);
  const [references, setReferences] = useState<Reference[]>([]);
  const [refSectionPage, setRefSectionPage] = useState<number>(0);
  const [activeHeading, setActiveHeading] = useState<number>(-1);
  const [activeRef, setActiveRef] = useState<number>(-1);
  const [showRefs, setShowRefs] = useState<boolean>(false);

  const [translation, setTranslation] = useState<string>('');
  const [translating, setTranslating] = useState<boolean>(false);
  const [showTranslation, setShowTranslation] = useState<boolean>(false);
  const [selectedText, setSelectedText] = useState<string>('');
  const [selectionTranslation, setSelectionTranslation] = useState<string>('');

  const pdfScrollRef = useRef<HTMLDivElement>(null);
  const translationScrollRef = useRef<HTMLDivElement>(null);
  const syncingRef = useRef<boolean>(false);

  useEffect(() => {
    fetch(`http://localhost:8000/api/papers/${paperId}/structure`)
      .then((r) => r.json())
      .then((data) => setHeadings(data.headings || []))
      .catch((e) => console.error('标题树加载失败:', e));
  }, [paperId]);

  useEffect(() => {
    fetch(`http://localhost:8000/api/papers/${paperId}/references`)
      .then((r) => r.json())
      .then((data) => {
        setReferences(data.references || []);
        setRefSectionPage(data.ref_section_page || 0);
      })
      .catch((e) => console.error('References 加载失败:', e));
  }, [paperId]);

  function onDocumentLoadSuccess({ numPages }: { numPages: number }) {
    setNumPages(numPages);
  }

  function onItemClick({ pageNumber: targetPage }: { pageNumber: number }) {
    setPageNumber(targetPage);
  }

  function handlePdfScroll(e: React.UIEvent<HTMLDivElement>) {
    if (syncingRef.current) return;
    syncingRef.current = true;

    const pdfEl = e.currentTarget;
    const transEl = translationScrollRef.current;
    if (transEl) {
      const ratio = pdfEl.scrollTop / (pdfEl.scrollHeight - pdfEl.clientHeight || 1);
      transEl.scrollTop = ratio * (transEl.scrollHeight - transEl.clientHeight);
    }

    setTimeout(() => { syncingRef.current = false; }, 50);
  }

  function handleTranslationScroll(e: React.UIEvent<HTMLDivElement>) {
    if (syncingRef.current) return;
    syncingRef.current = true;

    const transEl = e.currentTarget;
    const pdfEl = pdfScrollRef.current;
    if (pdfEl) {
      const ratio = transEl.scrollTop / (transEl.scrollHeight - transEl.clientHeight || 1);
      pdfEl.scrollTop = ratio * (pdfEl.scrollHeight - pdfEl.clientHeight);
    }

    setTimeout(() => { syncingRef.current = false; }, 50);
  }

  function handleMouseUp() {
    const selection = window.getSelection();
    const text = selection?.toString().trim() || '';
    if (text && text.length > 2 && text.length < 2000) {
      setSelectedText(text);
    }
  }

  async function translateSelection() {
    if (!selectedText) return;
    setTranslating(true);
    try {
      const res = await fetch('http://localhost:8000/api/translate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text: selectedText, target_lang: 'zh' }),
      });
      const data = await res.json();
      setSelectionTranslation(data.translated || data.detail || '翻译失败');
    } catch (e) {
      setSelectionTranslation('翻译请求失败');
    } finally {
      setTranslating(false);
    }
  }

  async function translateCurrentPage() {
    setTranslating(true);
    setShowTranslation(true);
    setTranslation('');
    try {
      const pageRes = await fetch(
        `http://localhost:8000/api/papers/${paperId}/page/${pageNumber}`
      );
      const pageData = await pageRes.json();
      const pageText = pageData.text || '';

      if (!pageText.trim()) {
        setTranslation('当前页无文本内容');
        return;
      }

      const res = await fetch('http://localhost:8000/api/translate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text: pageText, target_lang: 'zh' }),
      });
      const data = await res.json();
      setTranslation(data.translated || data.detail || '翻译失败');
    } catch (e) {
      setTranslation('翻译请求失败: ' + String(e));
    } finally {
      setTranslating(false);
    }
  }

  function onRenderTextLayerSuccess() {
    setTimeout(() => {
      const textLayer = document.querySelector('.react-pdf__Page__textContent');
      if (!textLayer) return;

      const spans = textLayer.querySelectorAll('span');
      spans.forEach((span) => {
        const text = span.textContent || '';
        const match = text.match(/^\[(\d+)(?:,\s*\d+)*\]$/);
        if (match) {
          const refNum = parseInt(match[1]);
          const el = span as HTMLElement;
          el.style.cursor = 'pointer';
          el.style.color = '#2563eb';
          el.style.textDecoration = 'underline';
          el.onclick = (e) => {
            e.stopPropagation();
            const ref = references.find((r) => r.num === refNum);
            if (ref) {
              setPageNumber(ref.ref_page);
              setActiveRef(ref.num);
              setShowRefs(true);
              setTimeout(() => {
                const refEl = document.getElementById(`ref-${refNum}`);
                if (refEl) refEl.scrollIntoView({ behavior: 'smooth', block: 'center' });
              }, 300);
            }
          };
        }
      });
    }, 100);
  }

  function handleHeadingClick(h: Heading, idx: number) {
    if (h.page) {
      setPageNumber(h.page);
      setActiveHeading(idx);
    }
  }

  function jumpToRefPage(ref: Reference, page: number) {
    setPageNumber(page);
    setActiveRef(ref.num);
  }

  return (
    <div className="flex gap-3 items-start">
      <aside className="w-48 flex-shrink-0 bg-slate-50 rounded-lg border border-slate-200 p-3 max-h-[800px] overflow-auto sticky top-4">
        <h2 className="text-sm font-semibold text-slate-700 mb-3">目录</h2>
        <nav className="space-y-1">
          {headings.map((h, idx) => (
            <div
              key={idx}
              onClick={() => handleHeadingClick(h, idx)}
              className={`text-xs cursor-pointer truncate rounded px-2 py-1 transition ${
                activeHeading === idx
                  ? 'bg-blue-100 text-blue-700 font-medium'
                  : 'text-slate-600 hover:bg-slate-200 hover:text-blue-600'
              }`}
              style={{ paddingLeft: `${(h.level - 1) * 12 + 8}px` }}
              title={h.page ? `${h.title}（第 ${h.page} 页）` : h.title}
            >
              {h.title}
            </div>
          ))}
        </nav>
      </aside>

      <div className="flex-1 min-w-0">
        <div className="mb-4 flex flex-wrap items-center gap-3">
          <button
            onClick={() => setPageNumber((p) => Math.max(1, p - 1))}
            disabled={pageNumber <= 1}
            className="px-3 py-1.5 text-sm bg-slate-200 rounded hover:bg-slate-300 disabled:opacity-50"
          >
            上一页
          </button>
          <span className="text-sm text-slate-600">
            第 {pageNumber} 页 / 共 {numPages} 页
          </span>
          <button
            onClick={() => setPageNumber((p) => Math.min(numPages, p + 1))}
            disabled={pageNumber >= numPages}
            className="px-3 py-1.5 text-sm bg-slate-200 rounded hover:bg-slate-300 disabled:opacity-50"
          >
            下一页
          </button>

          <button
            onClick={translateCurrentPage}
            disabled={translating}
            className="px-3 py-1.5 text-sm bg-green-600 text-white rounded hover:bg-green-700 disabled:bg-slate-300"
          >
            {translating ? '翻译中...' : showTranslation ? '刷新翻译' : '翻译本页'}
          </button>

          <button
            onClick={() => setShowRefs(!showRefs)}
            className="ml-auto px-3 py-1.5 text-sm bg-blue-600 text-white rounded hover:bg-blue-700"
          >
            {showRefs ? '隐藏参考文献' : '显示参考文献'}
          </button>
        </div>

        <div className={`grid ${showTranslation ? 'grid-cols-2' : 'grid-cols-1'} gap-4`}>
          <div
            ref={pdfScrollRef}
            onScroll={handlePdfScroll}
            className="bg-white rounded-lg border border-slate-200 p-4 flex justify-center overflow-auto max-h-[900px]"
            onMouseUp={handleMouseUp}
          >
            <Document
              file={pdfUrl}
              onLoadSuccess={onDocumentLoadSuccess}
              onLoadError={(err) => console.error('PDF 加载失败:', err)}
              onItemClick={onItemClick}
              loading={<div className="p-8 text-slate-500">PDF 加载中...</div>}
              error={<div className="p-8 text-red-500">PDF 加载失败</div>}
            >
              <Page
                pageNumber={pageNumber}
                width={showTranslation ? 500 : 680}
                renderTextLayer={true}
                renderAnnotationLayer={true}
                onRenderTextLayerSuccess={onRenderTextLayerSuccess}
              />
            </Document>
          </div>

          {showTranslation && (
            <div
              ref={translationScrollRef}
              onScroll={handleTranslationScroll}
              className="bg-amber-50 rounded-lg border border-amber-200 p-4 overflow-auto max-h-[900px]"
            >
              <h2 className="text-sm font-semibold text-amber-800 mb-3">
                中文翻译（第 {pageNumber} 页）
              </h2>
              {translating && <div className="text-sm text-slate-500">翻译中...</div>}
              {!translating && translation && (
                <div className="text-sm text-slate-800 leading-relaxed whitespace-pre-wrap">
                  {translation}
                </div>
              )}
              {!translating && !translation && (
                <div className="text-sm text-slate-400">点击"翻译本页"按钮生成译文</div>
              )}
            </div>
          )}
        </div>

        {selectedText && (
          <div className="mt-4 bg-blue-50 border border-blue-200 rounded-lg p-4">
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs font-semibold text-blue-800">划词翻译</span>
              <div className="flex gap-2">
                <button
                  onClick={translateSelection}
                  disabled={translating}
                  className="px-2 py-1 text-xs bg-blue-600 text-white rounded hover:bg-blue-700"
                >
                  翻译
                </button>
                <button
                  onClick={() => {
                    setSelectedText('');
                    setSelectionTranslation('');
                  }}
                  className="px-2 py-1 text-xs bg-slate-200 rounded hover:bg-slate-300"
                >
                  关闭
                </button>
              </div>
            </div>
            <div className="text-xs text-slate-700 mb-2">
              <span className="text-slate-500">原文：</span>
              {selectedText.slice(0, 200)}
              {selectedText.length > 200 ? '...' : ''}
            </div>
            {selectionTranslation && (
              <div className="text-xs text-slate-800 bg-white rounded p-2">
                <span className="text-slate-500">译文：</span>
                {selectionTranslation}
              </div>
            )}
          </div>
        )}
      </div>

      {showRefs && (
        <aside className="w-72 flex-shrink-0 bg-slate-50 rounded-lg border border-slate-200 p-3 max-h-[800px] overflow-auto sticky top-4">
          <h2 className="text-sm font-semibold text-slate-700 mb-3">
            参考文献（{references.length}）
          </h2>
          {activeRef > 0 && (
            <div className="text-xs text-blue-600 bg-blue-50 rounded px-2 py-1 mb-2">
              已定位到 [{activeRef}]
            </div>
          )}
          <div className="space-y-2">
            {references.map((ref) => (
              <div
                key={ref.num}
                id={`ref-${ref.num}`}
                className={`text-xs rounded p-2 transition ${
                  activeRef === ref.num
                    ? 'bg-blue-100 text-blue-700 border border-blue-300'
                    : 'bg-white text-slate-600 border border-slate-200'
                }`}
              >
                <div className="flex items-center justify-between mb-1">
                  <span
                    className="font-semibold cursor-pointer hover:text-blue-600"
                    onClick={() => {
                      if (ref.in_text_first_page) {
                        jumpToRefPage(ref, ref.in_text_first_page);
                      } else {
                        jumpToRefPage(ref, ref.ref_page);
                      }
                    }}
                  >
                    [{ref.num}]
                  </span>
                  {ref.in_text_pages.length > 0 && (
                    <span className="text-[10px] text-slate-400">
                      {ref.in_text_pages.length} 处引用
                    </span>
                  )}
                </div>

                <div className="mb-2 leading-snug">
                  {ref.text.slice(0, 120)}
                  {ref.text.length > 120 ? '...' : ''}
                </div>

                {ref.in_text_pages.length > 0 ? (
                  <div className="flex flex-wrap gap-1">
                    {ref.in_text_pages.map((p) => (
                      <button
                        key={p}
                        onClick={() => jumpToRefPage(ref, p)}
                        className="px-2 py-0.5 bg-slate-100 hover:bg-blue-100 text-slate-600 hover:text-blue-700 rounded text-[10px]"
                      >
                        第 {p} 页
                      </button>
                    ))}
                  </div>
                ) : (
                  <div className="text-[10px] text-slate-400 italic">
                    正文未找到引用位置
                  </div>
                )}
              </div>
            ))}
          </div>
        </aside>
      )}
    </div>
  );
}