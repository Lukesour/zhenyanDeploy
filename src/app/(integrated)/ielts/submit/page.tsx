'use client';

import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import { useForm } from 'react-hook-form';
import Link from 'next/link';
import { useAuthStore, useEssayStore } from '@/lib/store';
import { essayAPI } from '@/lib/api';
import SeparateImageUpload from '@/components/SeparateImageUpload';
import authService from '@/modules/study-planner/services/authService';

interface EssayForm {
  task_type: string;
  essay_type?: string;
  title: string;
  content: string;
}

const ESSAY_TYPES = {
  agree_disagree: {
    label: '观点型 (Opinion/Argument)',
    description: '需要明确表达个人观点，支持或反对某个观点',
    examples: ['To what extent do you agree or disagree?', 'Do you agree or disagree?']
  },
  positive_negative: {
    label: '好坏型 (Positive/Negative)',
    description: '评判某个现象或发展的好坏，需要明确立场',
    examples: ['Is this a positive or negative development?', 'Do you think this is positive or negative?']
  },
  discuss_both: {
    label: '讨论型 (Discussion)',
    description: '客观讨论两个预设观点，然后给出个人看法',
    examples: ['Discuss both views and give your opinion', 'Discuss both sides and give your view']
  },
  advantages_disadvantages: {
    label: '比较型 (Comparison)',
    description: '比较利弊并判断哪方面更重要，需要明确表态',
    examples: ['Do the advantages outweigh the disadvantages?', 'Do the benefits outweigh the problems?']
  },
  problem_solution: {
    label: '报告型 (Report)',
    description: '客观分析原因和提出解决方案，不需要个人观点',
    examples: ['Why has this happened? What can be done?', 'What are the causes and solutions?']
  },
  two_part_question: {
    label: '混搭型 (Mixed)',
    description: '结合报告型和观点型要求，既要分析又要评判',
    examples: ['Why has this happened? Is it positive or negative?', 'What causes this? Do you agree?']
  },
};

export default function SubmitPage() {
  const router = useRouter();
  const { isAuthenticated } = useAuthStore();
  const { addEssay } = useEssayStore();
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [wordCount, setWordCount] = useState(0);

  const {
    register,
    handleSubmit,
    watch,
    setValue,
    formState: { errors },
  } = useForm<EssayForm>();

  const taskType = watch('task_type');
  const content = watch('content') || '';

  // 实时计算字数
  React.useEffect(() => {
    const words = content.trim().split(/\s+/).filter(word => word.length > 0);
    setWordCount(words.length);
  }, [content]);

  const onSubmit = async (data: EssayForm) => {
    if (!isAuthenticated) {
      router.push('/auth?mode=login&redirect=/ielts/submit');
      return;
    }

    setIsLoading(true);
    setError('');

    try {
      const response = await essayAPI.submitEssay(data);
      addEssay(response.essay);
      authService.updateUserInfo({
        remaining_analyses: response.remaining_analyses,
        total_analyses_used: response.total_analyses_used,
      });
      router.push(`/ielts/essay/${response.essay.id}`);
    } catch (err: any) {
      setError(err.response?.data?.detail || '提交失败，请重试');
    } finally {
      setIsLoading(false);
    }
  };

  const minWords = taskType === 'task1' ? 150 : 250;
  const isWordCountValid = wordCount >= minWords;

  return (
    <div className="min-h-screen bg-gray-50">
      {/* 导航栏 */}
      <nav className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            <div className="flex items-center">
              <Link href="/ielts/dashboard" className="text-xl font-semibold text-gray-900">
                雅思作文批改系统
              </Link>
            </div>
            <div className="flex items-center">
              <Link
                href="/ielts/dashboard"
                className="text-gray-500 hover:text-gray-700 px-3 py-2 rounded-md text-sm font-medium"
              >
                返回首页
              </Link>
            </div>
          </div>
        </div>
      </nav>

      <div className="max-w-4xl mx-auto py-6 sm:px-6 lg:px-8">
        <div className="bg-white shadow rounded-lg">
          <div className="px-4 py-5 sm:p-6">
            <h3 className="text-lg leading-6 font-medium text-gray-900 mb-6">
              提交作文
            </h3>

            {error && (
              <div className="bg-red-50 border border-red-200 text-red-600 px-4 py-3 rounded mb-6">
                {error}
              </div>
            )}

            <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
              {/* 任务类型选择 */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  任务类型 *
                </label>
                <div className="grid grid-cols-2 gap-4">
                  <label className="relative">
                    <input
                      {...register('task_type', { required: '请选择任务类型' })}
                      type="radio"
                      value="task1"
                      className="sr-only"
                    />
                    <div className="border-2 border-gray-300 rounded-lg p-4 cursor-pointer hover:border-indigo-500 peer-checked:border-indigo-600 peer-checked:bg-indigo-50">
                      <h4 className="font-medium text-gray-900">Task 1</h4>
                      <p className="text-sm text-gray-500">图表描述、流程图等</p>
                      <p className="text-xs text-gray-400 mt-1">最少 150 词</p>
                    </div>
                  </label>
                  <label className="relative">
                    <input
                      {...register('task_type', { required: '请选择任务类型' })}
                      type="radio"
                      value="task2"
                      className="sr-only"
                    />
                    <div className="border-2 border-gray-300 rounded-lg p-4 cursor-pointer hover:border-indigo-500 peer-checked:border-indigo-600 peer-checked:bg-indigo-50">
                      <h4 className="font-medium text-gray-900">Task 2</h4>
                      <p className="text-sm text-gray-500">议论文写作</p>
                      <p className="text-xs text-gray-400 mt-1">最少 250 词</p>
                    </div>
                  </label>
                </div>
                {errors.task_type && (
                  <p className="mt-1 text-sm text-red-600">{errors.task_type.message}</p>
                )}
              </div>

              {/* Task 2 题型选择 */}
              {taskType === 'task2' && (
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-3">
                    题型分类
                  </label>
                  <div className="space-y-3">
                    <div className="grid grid-cols-1 gap-3">
                      {Object.entries(ESSAY_TYPES).map(([value, typeInfo]) => (
                        <label key={value} className="relative">
                          <input
                            {...register('essay_type')}
                            type="radio"
                            value={value}
                            className="sr-only peer"
                          />
                          <div className="border-2 border-gray-200 rounded-lg p-4 cursor-pointer hover:border-indigo-300 peer-checked:border-indigo-500 peer-checked:bg-indigo-50 transition-all">
                            <div className="flex items-start justify-between">
                              <div className="flex-1">
                                <h4 className="font-medium text-gray-900 mb-1">
                                  {typeInfo.label}
                                </h4>
                                <p className="text-sm text-gray-600 mb-2">
                                  {typeInfo.description}
                                </p>
                                <div className="text-xs text-gray-500">
                                  <span className="font-medium">常见指令：</span>
                                  <div className="mt-1">
                                    {typeInfo.examples.map((example, index) => (
                                      <div key={index} className="italic">
                                        &ldquo;{example}&rdquo;
                                      </div>
                                    ))}
                                  </div>
                                </div>
                              </div>
                              <div className="ml-3 flex-shrink-0">
                                <div className="w-4 h-4 border-2 border-gray-300 rounded-full peer-checked:border-indigo-500 peer-checked:bg-indigo-500 transition-all"></div>
                              </div>
                            </div>
                          </div>
                        </label>
                      ))}
                    </div>
                    <div className="text-xs text-gray-500 bg-blue-50 p-3 rounded-lg">
                      💡 <strong>提示：</strong>选择正确的题型有助于AI更准确地评分和提供针对性建议。如果不确定，可以留空让AI自动识别。
                    </div>
                  </div>
                </div>
              )}

              {/* 图片上传 */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  图片上传（可选）
                </label>

                {/* Task1 图表分析 */}
                {taskType === 'task1' && (
                  <div className="mb-6">
                    <h4 className="text-sm font-medium text-gray-700 mb-2">📊 图表分析</h4>
                    <p className="text-sm text-gray-500 mb-3">
                      上传Task1图表图片，AI将智能分析图表内容并提供写作建议
                    </p>
                    <SeparateImageUpload
                      mode="chart"
                      onChartAnalyzed={(analysis) => {
                        // 可以在这里处理图表分析结果，比如显示分析结果或提供写作建议
                        console.log('图表分析结果:', analysis);
                      }}
                      className="mb-4"
                    />
                  </div>
                )}

                {/* 分开的题目和内容上传 */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
                  <div>
                    <h4 className="text-sm font-medium text-gray-700 mb-2">📝 题目识别</h4>
                    <p className="text-sm text-gray-500 mb-3">
                      单独上传题目图片，自动识别题目文字
                    </p>
                    <SeparateImageUpload
                      mode="title"
                      onTitleExtracted={(title) => {
                        setValue('title', title);
                      }}
                    />
                  </div>

                  <div>
                    <h4 className="text-sm font-medium text-gray-700 mb-2">✍️ 作文识别</h4>
                    <p className="text-sm text-gray-500 mb-3">
                      单独上传作文内容图片，自动识别作文文字
                    </p>
                    <SeparateImageUpload
                      mode="content"
                      onContentExtracted={(content) => {
                        setValue('content', content);
                      }}
                    />
                  </div>
                </div>
              </div>

              {/* 作文题目 */}
              <div>
                <label htmlFor="title" className="block text-sm font-medium text-gray-700 mb-2">
                  作文题目 *
                </label>
                <textarea
                  {...register('title', {
                    required: '请输入作文题目',
                    minLength: {
                      value: 10,
                      message: '题目至少10个字符',
                    },
                  })}
                  rows={3}
                  className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
                  placeholder="请输入完整的作文题目..."
                />
                {errors.title && (
                  <p className="mt-1 text-sm text-red-600">{errors.title.message}</p>
                )}
              </div>

              {/* 作文内容 */}
              <div>
                <div className="flex justify-between items-center mb-2">
                  <label htmlFor="content" className="block text-sm font-medium text-gray-700">
                    作文内容 *
                  </label>
                  <div className="text-sm">
                    <span className={`${isWordCountValid ? 'text-green-600' : 'text-red-600'}`}>
                      {wordCount}
                    </span>
                    <span className="text-gray-500"> / {minWords} 词</span>
                  </div>
                </div>
                <textarea
                  {...register('content', {
                    required: '请输入作文内容',
                    minLength: {
                      value: 100,
                      message: '作文内容至少100个字符',
                    },
                  })}
                  rows={20}
                  className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
                  placeholder="请在此输入您的作文内容..."
                />
                {errors.content && (
                  <p className="mt-1 text-sm text-red-600">{errors.content.message}</p>
                )}
                {!isWordCountValid && wordCount > 0 && (
                  <p className="mt-1 text-sm text-red-600">
                    字数不足，{taskType === 'task1' ? 'Task 1' : 'Task 2'} 至少需要 {minWords} 词
                  </p>
                )}
              </div>

              {/* 提交按钮 */}
              <div className="flex justify-end space-x-4">
                <Link
                  href="/ielts/dashboard"
                  className="px-4 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 hover:bg-gray-50"
                >
                  取消
                </Link>
                <button
                  type="submit"
                  disabled={isLoading || !isWordCountValid}
                  className="px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {isLoading ? '提交中...' : '提交作文'}
                </button>
              </div>
            </form>
          </div>
        </div>
      </div>
    </div>
  );
}
