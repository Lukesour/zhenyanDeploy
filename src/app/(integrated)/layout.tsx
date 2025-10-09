import type { ReactNode } from 'react';
import IntegratedTabs from '@/components/IntegratedTabs';

export default function IntegratedLayout({ children }: { children: ReactNode }) {
  return (
    <div className="min-h-screen bg-slate-50 text-slate-900 flex flex-col">
      <IntegratedTabs />
      <main className="flex-1">{children}</main>
    </div>
  );
}
