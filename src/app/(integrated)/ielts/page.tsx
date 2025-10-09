'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { useAuthStore } from '@/lib/store';

export default function Home() {
  const router = useRouter();
  const { isAuthenticated } = useAuthStore();

  useEffect(() => {
    if (isAuthenticated) {
      router.push('/ielts/dashboard');
    }
  }, [isAuthenticated, router]);

  return (
    <div className="min-h-screen bg-gradient-to-br from-indigo-50 to-white">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* 导航栏 */}
        <nav className="flex justify-between items-center py-6">
          <div className="text-2xl font-bold text-indigo-600">
            雅思作文批改系统
          </div>
          <div className="space-x-4">
            <Link
              href="/auth?mode=login&redirect=/ielts/dashboard"
              className="text-gray-600 hover:text-gray-900 px-3 py-2 rounded-md text-sm font-medium"
            >
              登录
            </Link>
            <Link
              href="/auth?mode=register&redirect=/ielts/dashboard"
              className="bg-indigo-600 hover:bg-indigo-700 text-white px-4 py-2 rounded-md text-sm font-medium"
            >
              注册
            </Link>
          </div>
        </nav>

        {/* 主要内容 */}
        <div className="py-20">
          <div className="text-center">
            <h1 className="text-4xl tracking-tight font-extrabold text-gray-900 sm:text-5xl md:text-6xl">
              <span className="block">AI驱动的</span>
              <span className="block text-indigo-600">雅思作文批改</span>
            </h1>
            <p className="mt-3 max-w-md mx-auto text-base text-gray-500 sm:text-lg md:mt-5 md:text-xl md:max-w-3xl">
              利用先进的大模型技术，采用工作流方式为您的雅思作文提供专业的评分与建议。
              基于官方评分标准，给出详细的四维度分析和具体的改进建议。
            </p>
            <div className="mt-5 max-w-md mx-auto sm:flex sm:justify-center md:mt-8">
              <div className="rounded-md shadow">
                <Link
                  href="/auth?mode=register&redirect=/ielts/dashboard"
                  className="w-full flex items-center justify-center px-8 py-3 border border-transparent text-base font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 md:py-4 md:text-lg md:px-10"
                >
                  开始使用
                </Link>
              </div>
              <div className="mt-3 rounded-md shadow sm:mt-0 sm:ml-3">
                <Link
                  href="/auth?mode=login&redirect=/ielts/dashboard"
                  className="w-full flex items-center justify-center px-8 py-3 border border-transparent text-base font-medium rounded-md text-indigo-600 bg-white hover:bg-gray-50 md:py-4 md:text-lg md:px-10"
                >
                  立即登录
                </Link>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
