import type { Metadata } from "next";
import Link from "next/link";
import "./globals.css";

export const metadata: Metadata = {
  title: "科研助手 Agent",
  description: "全栈式科研助手系统",
};

const navItems = [
  { href: "/", label: "首页" },
  { href: "/papers", label: "论文管理" },
  { href: "/chat", label: "智能问答" },
  { href: "/reader", label: "阅读翻译" },
  { href: "/graph", label: "引用图谱" },
  { href: "/writer", label: "写作 Copilot" },
];

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="zh-CN">
      <body className="flex h-screen bg-gray-50">
        {/* 左侧导航栏 */}
        <aside className="w-56 bg-slate-900 text-white flex flex-col">
          <div className="p-4 border-b border-slate-700">
            <h1 className="text-lg font-bold">科研助手</h1>
            <p className="text-xs text-slate-400 mt-1">Research Agent</p>
          </div>
          <nav className="flex-1 p-2">
            {navItems.map((item) => (
              <Link
                key={item.href}
                href={item.href}
                className="block px-3 py-2 rounded text-sm text-slate-300 hover:bg-slate-700 hover:text-white transition"
              >
                {item.label}
              </Link>
            ))}
          </nav>
          <div className="p-4 text-xs text-slate-500 border-t border-slate-700">
            v0.1.0
          </div>
        </aside>

        {/* 主内容区 */}
        <main className="flex-1 overflow-auto">{children}</main>
      </body>
    </html>
  );
}