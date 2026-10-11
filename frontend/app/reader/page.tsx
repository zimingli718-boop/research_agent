'use client';

import dynamic from 'next/dynamic';

const PDFViewer = dynamic(() => import('./PDFViewer'), {
  ssr: false,
  loading: () => <div className="p-8 text-slate-500">加载阅读器...</div>,
});

export default function ReaderPage() {
  const paperId = '6c6b5d88-a5c9-4a78-bb5d-f29415a2684e';
  const pdfUrl = `http://localhost:8000/api/papers/${paperId}/pdf`;

  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold text-slate-900 mb-6">阅读翻译</h1>
      <PDFViewer pdfUrl={pdfUrl} paperId={paperId} />
    </div>
  );
}