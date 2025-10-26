'use client';

import React, { useCallback, useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { essayAPI } from '@/lib/api';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

interface GradingResult {
  id: number;
  essay_id: number;
  overall_score: number;
  tr_score: number;
  cc_score: number;
  lr_score: number;
  gra_score: number;
  tr_analysis: any;
  cc_analysis: any;
  lr_analysis: any;
  gra_analysis: any;
  overall_comment: string;
  improvement_suggestions: string[];
  status?: string;
  created_at: string;
}

interface Essay {
  id: number;
  title: string;
  content: string;
  task_type: string;
  essay_type?: string;
  word_count: number;
  status?: string;
  grading_status?: string;
  created_at: string;
  grading_result?: GradingResult;
}

const ESSAY_TYPE_LABELS = {
  agree_disagree: '观点型 (Opinion/Argument)',
  positive_negative: '好坏型 (Positive/Negative)',
  discuss_both: '讨论型 (Discussion)',
  advantages_disadvantages: '比较型 (Comparison)',
  problem_solution: '报告型 (Report)',
  two_part_question: '混搭型 (Mixed)',
};

interface EssayDetailClientProps {
  essayId?: string;
}

const EssayDetailClient: React.FC<EssayDetailClientProps> = ({ essayId }) => {
  const router = useRouter();
  const [essay, setEssay] = useState<Essay | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [gradingProgress, setGradingProgress] = useState(0);
  const [gradingStage, setGradingStage] = useState('准备中...');

  useEffect(() => {
    const fetchEssay = async () => {
      if (!essayId) {
        setError('无效的作文编号');
        setLoading(false);
        return;
      }

      try {
        const response = await essayAPI.getEssay(Number(essayId));
        const essayData = response as unknown as Essay;
        setEssay(essayData);

        if ((essayData.status ?? essayData.grading_status) === 'processing' || (essayData.status ?? essayData.grading_status) === 'pending') {
          startGradingProgress();
        }
      } catch (err: any) {
        setError(err.response?.data?.detail || '获取作文详情失败');
      } finally {
        setLoading(false);
      }
    };

    fetchEssay();
  }, [essayId]);

  const startGradingProgress = useCallback(() => {
    if (!essayId) {
      return;
    }

    const stages = [
      { progress: 10, stage: '正在分析题目...' },
      { progress: 25, stage: '正在检查作文结构...' },
      { progress: 40, stage: '正在评估任务回应度...' },
      { progress: 55, stage: '正在分析连贯性和衔接...' },
      { progress: 70, stage: '正在评估词汇资源...' },
      { progress: 85, stage: '正在检查语法准确性...' },
      { progress: 95, stage: '正在生成评语和建议...' },
      { progress: 100, stage: '评分完成！' }
    ];

    let currentStageIndex = 0;

    const updateProgress = () => {
      if (currentStageIndex < stages.length) {
        const currentStage = stages[currentStageIndex];
        setGradingProgress(currentStage.progress);
        setGradingStage(currentStage.stage);
        currentStageIndex++;
      }
    };

    const checkGradingStatus = async () => {
      try {
        const response = await essayAPI.getEssay(Number(essayId));
        const pollStatus = (response as any).status ?? response.grading_status;
        if (pollStatus === 'completed') {
          clearInterval(progressInterval);
          clearInterval(statusCheckInterval);
          setGradingProgress(100);
          setGradingStage('评分完成！');
          setTimeout(() => {
            window.location.reload();
          }, 1000);
        } else if (pollStatus === 'failed') {
          clearInterval(progressInterval);
          clearInterval(statusCheckInterval);
          setGradingStage('评分失败，请重试');
          setError('评分过程中出现错误');
        }
      } catch (err) {
        console.error('检查评分状态失败:', err);
      }
    };

    const intervalDuration = (3 * 60 * 1000) / stages.length;
    const progressInterval: NodeJS.Timeout = setInterval(updateProgress, intervalDuration);
    const statusCheckInterval: NodeJS.Timeout = setInterval(checkGradingStatus, 10000);

    updateProgress();
    checkGradingStatus();

    return () => {
      clearInterval(progressInterval);
      clearInterval(statusCheckInterval);
    };
  }, [essayId]);

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">加载中...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="text-red-600 text-xl mb-4">❌</div>
          <p className="text-gray-600 mb-4">{error}</p>
          <button
            onClick={() => router.push('/ielts/dashboard')}
            className="bg-indigo-600 text-white px-4 py-2 rounded-md hover:bg-indigo-700"
          >
            返回仪表板
          </button>
        </div>
      </div>
    );
  }

  if (!essay) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <p className="text-gray-600 mb-4">作文不存在</p>
          <button
            onClick={() => router.push('/ielts/dashboard')}
            className="bg-indigo-600 text-white px-4 py-2 rounded-md hover:bg-indigo-700"
          >
            返回仪表板
          </button>
        </div>
      </div>
    );
  }

  const getScoreColor = (score: number) => {
    if (score >= 7) return 'text-green-600';
    if (score >= 6) return 'text-yellow-600';
    return 'text-red-600';
  };

  const renderScoreTag = (label: string, score: number) => (
    <div className="flex flex-col items-center p-4 bg-white rounded-lg shadow-md">
      <span className="text-gray-600 text-sm mb-1">{label}</span>
      <span className={`text-2xl font-semibold ${getScoreColor(score)}`}>{score.toFixed(1)}</span>
    </div>
  );

  const renderImprovementSection = () => {
    const suggestions = essay.grading_result?.improvement_suggestions;
    const items =
      Array.isArray(suggestions) && suggestions.length > 0
        ? suggestions
        : [
            '建议关注雅思写作官方评分标准，明确各评分项要求',
            '建议多练习高分范文，积累地道表达和句型',
            '建议进行针对性语法、词汇改进，例如使用量化词汇替换笼统描述',
          ];

    return (
      <ul className="space-y-3 text-gray-600">
        {items.map((tip) => (
          <li key={tip} className="p-3 bg-indigo-50 rounded-lg">
            {tip}
          </li>
        ))}
      </ul>
    );
  };

  return (
    <div className="min-h-screen bg-gray-50 py-10">
      <div className="max-w-6xl mx-auto px-4">
        <div className="flex justify-between items-center mb-6">
          <div>
            <h1 className="text-2xl font-semibold text-gray-900">{essay.title}</h1>
            <p className="text-gray-500 mt-2">
              <span className="inline-flex items-center px-3 py-1 rounded-full bg-indigo-50 text-indigo-600 text-sm mr-2">
                {ESSAY_TYPE_LABELS[essay.essay_type as keyof typeof ESSAY_TYPE_LABELS] || '其他类型'}
              </span>
              <span className="text-sm text-gray-400">{new Date(essay.created_at).toLocaleString()}</span>
            </p>
          </div>
          <button
            onClick={() => router.push('/ielts/dashboard')}
            className="bg-indigo-600 text-white px-4 py-2 rounded-md hover:bg-indigo-700"
          >
            返回仪表板
          </button>
        </div>

        {(essay.status ?? essay.grading_status) === 'processing' && (
          <div className="mb-6 bg-white rounded-xl shadow-md p-6 border border-indigo-100">
            <h2 className="text-lg font-medium text-gray-800 mb-4">评分状态</h2>
            <div className="relative w-full h-4 bg-gray-100 rounded-full overflow-hidden mb-2">
              <div
                className="absolute left-0 top-0 h-full bg-gradient-to-r from-indigo-500 to-purple-500 transition-all duration-500"
                style={{ width: `${gradingProgress}%` }}
              />
            </div>
            <div className="text-sm text-gray-600">{gradingStage}</div>
          </div>
        )}

        {essay.grading_result && (
          <div className="mb-6 grid grid-cols-1 md:grid-cols-5 gap-4">
            <div className="md:col-span-2 bg-white rounded-xl shadow-md p-6 border border-indigo-100">
              <h2 className="text-lg font-medium text-gray-800 mb-4">总评成绩</h2>
              <div className="flex items-center justify-center">
                <div className="text-5xl font-bold text-indigo-600">
                  {essay.grading_result.overall_score.toFixed(1)}
                </div>
              </div>
              <p className="text-center text-gray-500 mt-3">AI评分，仅供参考</p>
            </div>
            <div className="md:col-span-3 grid grid-cols-2 sm:grid-cols-4 gap-4">
              {renderScoreTag('任务回应 (TR)', essay.grading_result.tr_score)}
              {renderScoreTag('连贯衔接 (CC)', essay.grading_result.cc_score)}
              {renderScoreTag('词汇资源 (LR)', essay.grading_result.lr_score)}
              {renderScoreTag('语法准确性 (GRA)', essay.grading_result.gra_score)}
            </div>
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="bg-white rounded-xl shadow-md p-6 border border-gray-100">
            <h2 className="text-lg font-medium text-gray-800 mb-4">作文原文</h2>
            <div className="prose prose-indigo max-w-none">
              <ReactMarkdown remarkPlugins={[remarkGfm]}>
                {essay.content || '暂无作文内容'}
              </ReactMarkdown>
            </div>
          </div>

          <div className="space-y-6">
            <div className="bg-white rounded-xl shadow-md p-6 border border-gray-100">
              <h2 className="text-lg font-medium text-gray-800 mb-4">总体分析</h2>
              <p className="text-gray-600 leading-relaxed">
                {essay.grading_result?.overall_comment || '系统正在生成详细分析，请稍后查看。'}
              </p>
            </div>

            <div className="bg-white rounded-xl shadow-md p-6 border border-gray-100">
              <h2 className="text-lg font-medium text-gray-800 mb-4">提升建议</h2>
              {renderImprovementSection()}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default EssayDetailClient;
