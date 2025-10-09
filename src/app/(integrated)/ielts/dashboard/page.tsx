'use client';

import { useCallback, useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { useAuthStore, useEssayStore } from '@/lib/store';
import { essayAPI } from '@/lib/api';
import { format } from 'date-fns';

// 题型映射
const ESSAY_TYPE_LABELS = {
  agree_disagree: '观点型',
  positive_negative: '好坏型',
  discuss_both: '讨论型',
  advantages_disadvantages: '比较型',
  problem_solution: '报告型',
  two_part_question: '混搭型',
};

export default function DashboardPage() {
  const router = useRouter();
  const { user, isAuthenticated } = useAuthStore();
  const { essays, setEssays } = useEssayStore();
  const [isLoadingEssays, setIsLoadingEssays] = useState(true);

  const loadEssays = useCallback(async () => {
    try {
      setIsLoadingEssays(true);
      const userEssays = await essayAPI.getUserEssays();
      setEssays(userEssays);
    } catch (error: unknown) {
      const status = (error as { response?: { status?: number } })?.response?.status;
      if (status !== 401 && status !== 403) {
        console.error('Failed to load essays:', error);
      }
    } finally {
      setIsLoadingEssays(false);
    }
  }, [setEssays]);

  useEffect(() => {
    if (!isAuthenticated) {
      router.push('/auth?mode=login&redirect=/ielts/dashboard');
      return;
    }

    loadEssays();
  }, [isAuthenticated, loadEssays, router]);

  const getStatusBadge = (status: string, isGraded: boolean) => {
    if (isGraded) {
      return (
        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
          已完成
        </span>
      );
    }

    switch (status) {
      case 'pending':
        return (
          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800">
            等待中
          </span>
        );
      case 'processing':
        return (
          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
            评分中
          </span>
        );
      case 'failed':
        return (
          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800">
            失败
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-800">
            未知
          </span>
        );
    }
  };

  if (!isAuthenticated || !user) {
    return null;
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* 导航栏 */}
      <nav className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            <div className="flex items-center">
              <h1 className="text-xl font-semibold text-gray-900">
                雅思作文批改系统
              </h1>
            </div>
            <div className="flex items-center space-x-4">
              <span className="text-sm text-gray-700">欢迎，{user.username}</span>
              <Link
                href="/ielts/submit"
                className="bg-indigo-600 hover:bg-indigo-700 text-white px-4 py-2 rounded-md text-sm font-medium"
              >
                提交作文
              </Link>
            </div>
          </div>
        </div>
      </nav>

      <div className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
        {/* 作文列表 */}
        <div className="bg-white shadow overflow-hidden sm:rounded-md">
          <div className="px-4 py-5 sm:px-6">
            <h3 className="text-lg leading-6 font-medium text-gray-900">
              我的作文
            </h3>
            <p className="mt-1 max-w-2xl text-sm text-gray-500">
              查看您提交的作文和评分结果
            </p>
          </div>
          
          {isLoadingEssays ? (
            <div className="px-4 py-5 sm:p-6">
              <div className="text-center">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600 mx-auto"></div>
                <p className="mt-2 text-sm text-gray-500">加载中...</p>
              </div>
            </div>
          ) : essays.length === 0 ? (
            <div className="px-4 py-5 sm:p-6">
              <div className="text-center">
                <p className="text-sm text-gray-500 mb-4">您还没有提交任何作文</p>
                <Link
                  href="/ielts/submit"
                  className="bg-indigo-600 hover:bg-indigo-700 text-white px-4 py-2 rounded-md text-sm font-medium"
                >
                  提交第一篇作文
                </Link>
              </div>
            </div>
          ) : (
            <ul className="divide-y divide-gray-200">
              {essays.map((essay) => (
                <li key={essay.id}>
                  <div className="px-4 py-4 sm:px-6 hover:bg-gray-50">
                    <div className="flex items-center justify-between">
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium text-indigo-600 truncate">
                          {essay.title}
                        </p>
                        <div className="flex items-center space-x-2 text-sm text-gray-500">
                          <span>{essay.task_type.toUpperCase()}</span>
                          {essay.task_type === 'task2' && essay.essay_type && (
                            <>
                              <span>•</span>
                              <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-indigo-100 text-indigo-700">
                                {ESSAY_TYPE_LABELS[essay.essay_type as keyof typeof ESSAY_TYPE_LABELS] || essay.essay_type}
                              </span>
                            </>
                          )}
                          <span>•</span>
                          <span>{essay.word_count} 词</span>
                          <span>•</span>
                          <span>{format(new Date(essay.created_at), 'yyyy-MM-dd HH:mm')}</span>
                        </div>
                      </div>
                      <div className="flex items-center space-x-4">
                        {getStatusBadge(essay.grading_status, essay.is_graded)}
                        <div className="flex space-x-2">
                          <Link
                            href={`/ielts/essay/${essay.id}`}
                            className="text-indigo-600 hover:text-indigo-900 text-sm font-medium"
                          >
                            查看
                          </Link>
                          {essay.is_graded && (
                            <Link
                              href={`/ielts/result/${essay.id}`}
                              className="text-green-600 hover:text-green-900 text-sm font-medium"
                            >
                              评分结果
                            </Link>
                          )}
                        </div>
                      </div>
                    </div>
                  </div>
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>
    </div>
  );
}
