'use client';

import Link from 'next/link';

export default function Home() {
  const features = [
    {
      title: '论文管理',
      desc: '上传、解析、语义去重',
      href: '/papers',
      icon: '📚',
      color: 'bg-blue-50 text-blue-600',
    },
    {
      title: '智能问答',
      desc: 'RAG 检索 + 溯源锚点',
      href: '/chat',
      icon: '💬',
      color: 'bg-green-50 text-green-600',
    },
    {
      title: '阅读翻译',
      desc: '版式感知 + 中英对比',
      href: '/reader',
      icon: '🌐',
      color: 'bg-amber-50 text-amber-600',
    },
    {
      title: '论文发现',
      desc: 'arXiv 追踪 + 个性化推荐',
      href: '/discover',
      icon: '🔍',
      color: 'bg-purple-50 text-purple-600',
    },
    {
      title: '引用图谱',
      desc: 'PageRank 基石节点挖掘',
      href: '/graph',
      icon: '🕸️',
      color: 'bg-red-50 text-red-600',
    },
    {
      title: '综述与前沿',
      desc: '自动综述 + Future Work',
      href: '/survey',
      icon: '📝',
      color: 'bg-indigo-50 text-indigo-600',
    },
    {
      title: '写作 Copilot',
      desc: '框架生成 + CSV 可视化',
      href: '/writer',
      icon: '✍️',
      color: 'bg-teal-50 text-teal-600',
    }
  ];

  return (
    <div className="p-10 max-w-6xl mx-auto">
      {/* 头部 Hero 区 */}
      <div className="mb-12 text-center animate-fade-in">
        <h1 className="text-4xl font-extrabold text-slate-900 tracking-tight mb-4">
          科研助手 <span className="text-blue-600">Agent</span>
        </h1>
        <p className="text-lg text-slate-500 max-w-2xl mx-auto">
          全栈式科研助手系统 — 从文献导入到写作辅助的全流程闭环，基于大模型与图论驱动的学术探索平台。
        </p>
      </div>

      {/* 卡片网格 */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {features.map((feature) => (
          <Link href={feature.href} key={feature.title}>
            <div className="group h-full bg-white rounded-2xl border border-slate-200 p-6 cursor-pointer hover:border-blue-400 hover:shadow-xl hover:-translate-y-1 transition-all duration-300">
              <div className="flex items-center gap-4 mb-4">
                <div className={`w-12 h-12 rounded-xl flex items-center justify-center text-2xl ${feature.color}`}>
                  {feature.icon}
                </div>
                <h2 className="text-xl font-bold text-slate-800 group-hover:text-blue-600 transition-colors">
                  {feature.title}
                </h2>
              </div>
              <p className="text-sm text-slate-500 leading-relaxed">
                {feature.desc}
              </p>
            </div>
          </Link>
        ))}
      </div>

      {/* 底部统计信息 */}
      <div className="mt-16 pt-8 border-t border-slate-200 flex justify-center gap-12 text-slate-400 text-sm">
        <div className="text-center">
          <div className="text-2xl font-bold text-slate-800 mb-1">6+</div>
          <div>核心模块</div>
        </div>
        <div className="text-center">
          <div className="text-2xl font-bold text-slate-800 mb-1">RAG</div>
          <div>抗幻觉检索</div>
        </div>
        <div className="text-center">
          <div className="text-2xl font-bold text-slate-800 mb-1">AI4S</div>
          <div>全流程赋能</div>
        </div>
      </div>
    </div>
  );
}