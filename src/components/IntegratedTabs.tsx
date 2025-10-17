'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';

const tabs = [
  {
    href: '/ielts',
    title: '雅思作文批改',
    description: '完整的 AI 雅思评分与反馈工作流',
  },
  {
    href: '/study-planner',
    title: '留学规划助手',
    description: '背景分析、院校推荐与职业测评工具',
  },
  {
    href: '/documents',
    title: '文书生成',
    description: '头脑风暴 / CV / PS',
  },
  {
    href: '/profile',
    title: '个人中心',
    description: '账户信息、分析次数与雅思设置',
  },
];

const hiddenTabHrefs = new Set<string>(['/documents']);
const visibleTabs = tabs.filter((tab) => !hiddenTabHrefs.has(tab.href));

const isActive = (pathname: string, href: string) => {
  if (href === '/') {
    return pathname === '/';
  }
  return pathname === href || pathname.startsWith(`${href}/`);
};

export default function IntegratedTabs() {
  const pathname = usePathname();

  return (
    <header className="bg-white/80 backdrop-blur shadow-sm">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <nav className="flex items-center justify-between py-4">
          <div className="flex items-center space-x-2">
            <span className="text-xl font-semibold text-indigo-600">箴言留学</span>
            <span className="hidden sm:inline text-sm text-gray-400">不靠营销、不靠制造焦虑，单纯靠实力</span>
          </div>
          <div className="flex flex-wrap gap-2 sm:gap-4">
            {visibleTabs.map((tab) => {
              const active = isActive(pathname, tab.href);
              return (
                <Link
                  key={tab.href}
                  href={tab.href}
                  className={`group relative rounded-xl px-4 py-2 transition-all ${
                    active
                      ? 'bg-indigo-600 text-white shadow-lg shadow-indigo-500/30'
                      : 'bg-slate-100 text-slate-600 hover:bg-indigo-50 hover:text-indigo-600'
                  }`}
                >
                  <div className="text-sm font-medium">
                    {tab.title}
                  </div>
                  <div
                    className={`text-[11px] mt-0.5 ${
                      active ? 'text-indigo-100' : 'text-slate-400 group-hover:text-indigo-400'
                    }`}
                  >
                    {tab.description}
                  </div>
                </Link>
              );
            })}
          </div>
        </nav>
      </div>
    </header>
  );
}
