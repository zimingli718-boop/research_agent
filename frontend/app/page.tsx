export default function Home() {
  return (
    <div className="p-8">
      <h1 className="text-3xl font-bold text-slate-900">科研助手 Agent</h1>
      <p className="text-slate-600 mt-2">
        全栈式科研助手系统 — 从文献导入到写作辅助的全流程闭环
      </p>

      <div className="grid grid-cols-3 gap-4 mt-8">
        {[
          { title: "论文管理", desc: "上传、解析、语义去重" },
          { title: "智能问答", desc: "RAG 检索 + 溯源锚点" },
          { title: "阅读翻译", desc: "版式感知 + 中英对比" },
          { title: "引用图谱", desc: "基石节点挖掘" },
          { title: "学术综述", desc: "Future Work 提炼" },
          { title: "写作 Copilot", desc: "框架生成 + 数据可视化" },
        ].map((card) => (
          <div
            key={card.title}
            className="p-4 bg-white rounded-lg border border-slate-200 hover:shadow-md transition"
          >
            <h2 className="font-semibold text-slate-800">{card.title}</h2>
            <p className="text-sm text-slate-500 mt-1">{card.desc}</p>
          </div>
        ))}
      </div>
    </div>
  );
}