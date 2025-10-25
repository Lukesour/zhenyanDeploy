'use client';

import React, { useCallback, useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { essayAPI } from '@/lib/api';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import DetailedImprovements from '@/components/DetailedImprovements';
import MockDetailedImprovements from '@/components/MockDetailedImprovements';

export const runtime = 'edge';

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

// 题型映射
const ESSAY_TYPE_LABELS = {
  agree_disagree: '观点型 (Opinion/Argument)',
  positive_negative: '好坏型 (Positive/Negative)',
  discuss_both: '讨论型 (Discussion)',
  advantages_disadvantages: '比较型 (Comparison)',
  problem_solution: '报告型 (Report)',
  two_part_question: '混搭型 (Mixed)',
};

export default function EssayDetailPage() {
  const params = useParams();
  const router = useRouter();
  const [essay, setEssay] = useState<Essay | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [gradingProgress, setGradingProgress] = useState(0);
  const [gradingStage, setGradingStage] = useState('准备中...');

  useEffect(() => {
    const fetchEssay = async () => {
      try {
        const response = await essayAPI.getEssay(Number(params.id));
        const essayData = response as unknown as Essay;
        setEssay(essayData);

        // 如果作文正在评分中，启动进度条
        if ((essayData.status ?? essayData.grading_status) === 'processing' || (essayData.status ?? essayData.grading_status) === 'pending') {
          startGradingProgress();
        }
      } catch (err: any) {
        setError(err.response?.data?.detail || '获取作文详情失败');
      } finally {
        setLoading(false);
      }
    };

    if (params.id) {
      fetchEssay();
    }
  }, [params.id]);

  const startGradingProgress = useCallback(() => {
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

    // 进度条更新逻辑
    const updateProgress = () => {
      if (currentStageIndex < stages.length) {
        const currentStage = stages[currentStageIndex];
        setGradingProgress(currentStage.progress);
        setGradingStage(currentStage.stage);
        currentStageIndex++;
      }
    };

    // 检查评分状态
    const checkGradingStatus = async () => {
      try {
        const response = await essayAPI.getEssay(Number(params.id));
        const pollStatus = (response as any).status ?? response.grading_status;
        if (pollStatus === 'completed') {
          // 评分完成，清除所有定时器
          clearInterval(progressInterval);
          clearInterval(statusCheckInterval);

          // 设置为100%完成状态
          setGradingProgress(100);
          setGradingStage('评分完成！');

          // 1秒后刷新页面显示结果
          setTimeout(() => {
            window.location.reload();
          }, 1000);
        } else if (pollStatus === 'failed') {
          // 评分失败
          clearInterval(progressInterval);
          clearInterval(statusCheckInterval);
          setGradingStage('评分失败，请重试');
          setError('评分过程中出现错误');
        }
      } catch (err) {
        console.error('检查评分状态失败:', err);
      }
    };

    // 启动进度条更新（每22.5秒更新一次，总共3分钟）
    const intervalDuration = (3 * 60 * 1000) / stages.length;
    const progressInterval: NodeJS.Timeout = setInterval(updateProgress, intervalDuration);

    // 启动状态检查（每10秒检查一次）
    const statusCheckInterval: NodeJS.Timeout = setInterval(checkGradingStatus, 10000);

    // 立即执行一次进度更新和状态检查
    updateProgress();
    checkGradingStatus();

    return () => {
      clearInterval(progressInterval);
      clearInterval(statusCheckInterval);
    };
  }, [params.id]);

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

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'completed':
        return <span className="bg-green-100 text-green-800 px-2 py-1 rounded-full text-sm">已完成</span>;
      case 'processing':
        return <span className="bg-yellow-100 text-yellow-800 px-2 py-1 rounded-full text-sm">评分中</span>;
      case 'failed':
        return <span className="bg-red-100 text-red-800 px-2 py-1 rounded-full text-sm">评分失败</span>;
      default:
        return <span className="bg-gray-100 text-gray-800 px-2 py-1 rounded-full text-sm">待评分</span>;
    }
  };

  const parseOverallComment = (comment: string) => {
    try {
      // 尝试解析JSON格式的评语
      if (comment.includes('```json')) {
        const jsonMatch = comment.match(/```json\s*(\{[\s\S]*?\})\s*```/);
        if (jsonMatch) {
          const parsed = JSON.parse(jsonMatch[1]);
          return parsed;
        }
      }
      return { overall_comment: comment };
    } catch (_error) {
      return { overall_comment: comment };
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* 头部 */}
        <div className="mb-8">
          <button
            onClick={() => router.push('/ielts/dashboard')}
            className="text-indigo-600 hover:text-indigo-800 mb-4 flex items-center"
          >
            ← 返回仪表板
          </button>
          <div className="flex justify-between items-start">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">{essay.title}</h1>
              <div className="mt-2 space-y-2">
                <div className="flex items-center space-x-4 text-sm text-gray-500">
                  <span>任务类型: {essay.task_type === 'task1' ? 'Task 1' : 'Task 2'}</span>
                  <span>字数: {essay.word_count}</span>
                  <span>提交时间: {new Date(essay.created_at).toLocaleString('zh-CN')}</span>
                </div>
                {essay.task_type === 'task2' && essay.essay_type && (
                  <div className="flex items-center space-x-2">
                    <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-indigo-100 text-indigo-800">
                      {ESSAY_TYPE_LABELS[essay.essay_type as keyof typeof ESSAY_TYPE_LABELS] || essay.essay_type}
                    </span>
                    <span className="text-xs text-gray-400">题型分类</span>
                  </div>
                )}
              </div>
            </div>
            {getStatusBadge(essay.status ?? essay.grading_status ?? "pending")}
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* 作文内容 */}
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">作文内容</h2>
            <div className="prose max-w-none">
              <div className="whitespace-pre-wrap text-gray-700 leading-relaxed">
                {essay.content}
              </div>
            </div>
          </div>

          {/* 评分结果 */}
          <div className="space-y-6">
            {essay.grading_result ? (
              <>
                {/* 总分 */}
                <div className="bg-white rounded-lg shadow p-6">
                  <h2 className="text-xl font-semibold text-gray-900 mb-4">评分结果</h2>
                  <div className="text-center">
                    <div className={`text-4xl font-bold ${getScoreColor(essay.grading_result.overall_score)}`}>
                      {essay.grading_result.overall_score}
                    </div>
                    <p className="text-gray-600 mt-2">总分</p>
                  </div>
                </div>

                {/* 四个维度分数 */}
                <div className="bg-white rounded-lg shadow p-6">
                  <h3 className="text-lg font-semibold text-gray-900 mb-4">各维度分数</h3>
                  <div className="grid grid-cols-2 gap-4">
                    <div className="text-center p-4 bg-gray-50 rounded-lg">
                      <div className={`text-2xl font-bold ${getScoreColor(essay.grading_result.tr_score)}`}>
                        {essay.grading_result.tr_score}
                      </div>
                      <p className="text-sm text-gray-600 mt-1">TR/TA</p>
                      <p className="text-xs text-gray-500">任务回应</p>
                    </div>
                    <div className="text-center p-4 bg-gray-50 rounded-lg">
                      <div className={`text-2xl font-bold ${getScoreColor(essay.grading_result.cc_score)}`}>
                        {essay.grading_result.cc_score}
                      </div>
                      <p className="text-sm text-gray-600 mt-1">CC</p>
                      <p className="text-xs text-gray-500">连贯衔接</p>
                    </div>
                    <div className="text-center p-4 bg-gray-50 rounded-lg">
                      <div className={`text-2xl font-bold ${getScoreColor(essay.grading_result.lr_score)}`}>
                        {essay.grading_result.lr_score}
                      </div>
                      <p className="text-sm text-gray-600 mt-1">LR</p>
                      <p className="text-xs text-gray-500">词汇资源</p>
                    </div>
                    <div className="text-center p-4 bg-gray-50 rounded-lg">
                      <div className={`text-2xl font-bold ${getScoreColor(essay.grading_result.gra_score)}`}>
                        {essay.grading_result.gra_score}
                      </div>
                      <p className="text-sm text-gray-600 mt-1">GRA</p>
                      <p className="text-xs text-gray-500">语法准确</p>
                    </div>
                  </div>
                </div>

                {/* 题型分析 */}
                {essay.grading_result.tr_analysis && (
                  <div className="bg-white rounded-lg shadow p-6">
                    <h3 className="text-lg font-semibold text-gray-900 mb-4">📝 题型分析</h3>
                    {(() => {
                      try {
                        const trAnalysis = typeof essay.grading_result.tr_analysis === 'string'
                          ? JSON.parse(essay.grading_result.tr_analysis)
                          : essay.grading_result.tr_analysis;

                        return (
                          <div className="space-y-4">
                            {trAnalysis.question_type && (
                              <div className="bg-blue-50 p-4 rounded-lg">
                                <h4 className="font-semibold text-blue-800 mb-2">识别题型</h4>
                                <div className="flex items-center space-x-2">
                                  <span className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-blue-100 text-blue-800">
                                    {trAnalysis.question_type}
                                  </span>
                                  {trAnalysis.confidence && (
                                    <span className="text-sm text-blue-600">
                                      置信度: {(trAnalysis.confidence * 100).toFixed(0)}%
                                    </span>
                                  )}
                                </div>
                              </div>
                            )}

                            {trAnalysis.topic && (
                              <div className="bg-green-50 p-4 rounded-lg">
                                <h4 className="font-semibold text-green-800 mb-2">主题识别</h4>
                                <p className="text-green-700">{trAnalysis.topic}</p>
                              </div>
                            )}

                            {trAnalysis.required_elements && (
                              <div className="bg-yellow-50 p-4 rounded-lg">
                                <h4 className="font-semibold text-yellow-800 mb-2">必需要素检查</h4>
                                <div className="space-y-2">
                                  {Object.entries(trAnalysis.required_elements).map(([element, status]) => (
                                    <div key={element} className="flex items-center space-x-2">
                                      <span className={`w-2 h-2 rounded-full ${status ? 'bg-green-500' : 'bg-red-500'}`}></span>
                                      <span className="text-sm text-yellow-700">
                                        {element}: {status ? '✓ 已包含' : '✗ 缺失'}
                                      </span>
                                    </div>
                                  ))}
                                </div>
                              </div>
                            )}

                            {trAnalysis.argument_depth !== undefined && (
                              <div className="bg-purple-50 p-4 rounded-lg">
                                <h4 className="font-semibold text-purple-800 mb-2">论证深度</h4>
                                <div className="flex items-center space-x-2">
                                  <div className="flex-1 bg-gray-200 rounded-full h-2">
                                    <div
                                      className="bg-purple-600 h-2 rounded-full"
                                      style={{ width: `${trAnalysis.argument_depth * 100}%` }}
                                    ></div>
                                  </div>
                                  <span className="text-sm text-purple-700">
                                    {(trAnalysis.argument_depth * 100).toFixed(0)}%
                                  </span>
                                </div>
                              </div>
                            )}
                          </div>
                        );
                      } catch (_error) {
                        return (
                          <div className="text-gray-600">
                            题型分析数据解析中...
                          </div>
                        );
                      }
                    })()}
                  </div>
                )}

                {/* 总体评语 */}
                <div className="bg-white rounded-lg shadow p-6">
                  {(() => {
                    const comment = essay.grading_result.overall_comment;

                    // 检查是否是格式化后的Markdown内容（包含##标题）
                    if (comment.includes('## 📋') || comment.includes('##')) {
                      return (
                        <div className="prose prose-sm max-w-none">
                          <ReactMarkdown
                            remarkPlugins={[remarkGfm]}
                            components={{
                              h2: ({children}) => (
                                <h2 className="text-lg font-semibold text-gray-900 mb-3 mt-6 first:mt-0 flex items-center">
                                  {children}
                                </h2>
                              ),
                              h3: ({children}) => (
                                <h3 className="text-base font-semibold text-gray-800 mb-2 mt-4 flex items-center">
                                  {children}
                                </h3>
                              ),
                              p: ({children}) => (
                                <p className="text-gray-700 leading-relaxed mb-3">
                                  {children}
                                </p>
                              ),
                              ul: ({children}) => (
                                <ul className="list-disc list-inside space-y-1 text-gray-600 mb-3 ml-4">
                                  {children}
                                </ul>
                              ),
                              ol: ({children}) => (
                                <ol className="list-decimal list-inside space-y-1 text-gray-600 mb-3 ml-4">
                                  {children}
                                </ol>
                              ),
                              li: ({children}) => (
                                <li className="text-gray-600">
                                  {children}
                                </li>
                              ),
                            }}
                          >
                            {comment}
                          </ReactMarkdown>
                        </div>
                      );
                    } else {
                      // 兼容旧格式：尝试解析JSON格式的评语
                      const parsedComment = parseOverallComment(comment);
                      return (
                        <div className="space-y-4">
                          <h3 className="text-lg font-semibold text-gray-900 mb-4">📋 总体评语</h3>
                          <div className="text-gray-700 leading-relaxed">
                            {parsedComment.overall_comment}
                          </div>

                          {parsedComment.key_strengths && (
                            <div>
                              <h4 className="font-semibold text-green-700 mb-2">主要优点:</h4>
                              <ul className="list-disc list-inside space-y-1 text-sm text-gray-600">
                                {parsedComment.key_strengths.map((strength: string, index: number) => (
                                  <li key={index}>{strength}</li>
                                ))}
                              </ul>
                            </div>
                          )}

                          {parsedComment.key_weaknesses && (
                            <div>
                              <h4 className="font-semibold text-red-700 mb-2">主要不足:</h4>
                              <ul className="list-disc list-inside space-y-1 text-sm text-gray-600">
                                {parsedComment.key_weaknesses.map((weakness: string, index: number) => (
                                  <li key={index}>{weakness}</li>
                                ))}
                              </ul>
                            </div>
                          )}

                          {parsedComment.priority_improvements && (
                            <div>
                              <h4 className="font-semibold text-blue-700 mb-2">优先改进建议:</h4>
                              <ul className="list-disc list-inside space-y-1 text-sm text-gray-600">
                                {parsedComment.priority_improvements.map((improvement: string, index: number) => (
                                  <li key={index}>{improvement}</li>
                                ))}
                              </ul>
                            </div>
                          )}
                        </div>
                      );
                    }
                  })()}
                </div>

                {/* 简单改进建议 */}
                {essay.grading_result.improvement_suggestions && essay.grading_result.improvement_suggestions.length > 0 && (
                  <div className="bg-white rounded-lg shadow p-6">
                    <h3 className="text-lg font-semibold text-gray-900 mb-4">📝 基础改进建议</h3>
                    <ul className="space-y-2">
                      {essay.grading_result.improvement_suggestions.map((suggestion, index) => (
                        <li key={index} className="flex items-start">
                          <span className="text-indigo-600 mr-2">•</span>
                          <span className="text-gray-700">{suggestion}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                {/* 详细改进建议 - 实际版本（分步骤生成，解决token限制） */}
                <DetailedImprovements
                  essayContent={essay.content}
                  essayTitle={essay.title}
                  dimensionScores={{
                    TR: essay.grading_result.tr_analysis?.score || 0,
                    CC: essay.grading_result.cc_analysis?.score || 0,
                    LR: essay.grading_result.lr_analysis?.score || 0,
                    GRA: essay.grading_result.gra_analysis?.score || 0
                  }}
                  overallScore={essay.grading_result.overall_score || 0}
                  targetScore={7.0}
                />

                {/* 详细改进建议 - 演示版本（备用）
                <MockDetailedImprovements
                  essayContent={essay.content}
                  essayTitle={essay.title}
                  dimensionScores={{
                    TR: essay.grading_result.tr_analysis?.score || 0,
                    CC: essay.grading_result.cc_analysis?.score || 0,
                    LR: essay.grading_result.lr_analysis?.score || 0,
                    GRA: essay.grading_result.gra_analysis?.score || 0
                  }}
                  overallScore={essay.grading_result.overall_score || 0}
                />
                */}
              </>
            ) : (
              <div className="bg-white rounded-lg shadow p-6">
                <div className="text-center">
                  <div className="text-indigo-600 text-4xl mb-4">🤖</div>
                  <h3 className="text-lg font-semibold text-gray-900 mb-2">AI正在评分中</h3>
                  <p className="text-gray-600 mb-6">
                    {gradingStage}
                  </p>

                  {/* 进度条 */}
                  <div className="w-full bg-gray-200 rounded-full h-3 mb-4">
                    <div
                      className="bg-gradient-to-r from-indigo-500 to-purple-600 h-3 rounded-full transition-all duration-1000 ease-out"
                      style={{ width: `${gradingProgress}%` }}
                    ></div>
                  </div>

                  <div className="flex justify-between text-sm text-gray-500 mb-6">
                    <span>0%</span>
                    <span className="font-medium text-indigo-600">{gradingProgress}%</span>
                    <span>100%</span>
                  </div>

                  <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-4">
                    <div className="flex items-center">
                      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600 mr-2"></div>
                      <span className="text-blue-800 text-sm font-medium">预计还需 {Math.ceil((100 - gradingProgress) * 1.8)} 秒</span>
                    </div>
                  </div>

                  <p className="text-xs text-gray-500">
                    AI正在从四个维度全面分析您的作文，请耐心等待...
                  </p>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
