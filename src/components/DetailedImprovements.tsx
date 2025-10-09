'use client';

import React, { useState, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { improvementAPI } from '@/lib/api';

const SERVICE_WECHAT_ID = 'Godeternitys';

interface DetailedImprovementsProps {
  essayContent: string;
  essayTitle: string;
  dimensionScores: Record<string, number>;
  overallScore: number;
  targetScore?: number;
}

interface ImprovementSection {
  id: string;
  title: string;
  content: string;
  isLoading: boolean;
  isExpanded: boolean;
  error?: string;
  progress?: number;
  tokensUsed?: number;
  customContentType?: 'serviceContact';
}

const ANALYSIS_TYPES = [
  { key: 'comprehensive', title: '📋 综合详细改进建议', description: '基于所有数据资源的深度分析' },
  { key: 'sentence', title: '📝 逐句详细分析', description: '对每个句子进行深度分析和改进' },
  { key: 'error', title: '🔍 全面错误分析', description: '识别和修正所有类型的错误' },
  { key: 'comparison', title: '📊 范文对比分析', description: '与高分范文的详细对比学习' },
  { key: 'learning', title: '🎯 个性化学习计划', description: '基于具体问题的学习规划' }
];

export default function DetailedImprovements({
  essayContent,
  essayTitle,
  dimensionScores,
  overallScore,
  targetScore = 7.0
}: DetailedImprovementsProps) {
  const [sections, setSections] = useState<ImprovementSection[]>([]);
  const [isInitializing, setIsInitializing] = useState(true);
  const [currentLoadingIndex, setCurrentLoadingIndex] = useState(-1);

  // 初始化所有分析类型的section
  useEffect(() => {
    const initialSections: ImprovementSection[] = ANALYSIS_TYPES.map(type => ({
      id: type.key,
      title: type.title,
      content: '',
      isLoading: false,
      isExpanded: false
    }));
    setSections(initialSections);
    setIsInitializing(false);
  }, []);

  // 处理AI返回的数据，提取和格式化内容
  const processAIResponse = (data: any): { content: string; tokensUsed?: number } => {
    let content = '';
    let tokensUsed = 0;

    // 如果直接返回文本（单个分析类型）
    if (typeof data.text === 'string') {
      content = data.text;
      tokensUsed = data.tokens_used || 0;
    }
    // 如果是分步骤生成的完整结果
    else if (data.data && data.data.analysis_results) {
      const results = data.data.analysis_results;

      // 按顺序处理各种分析结果
      const analysisOrder = ['comprehensive', 'sentence', 'error', 'comparison', 'learning'];

      for (const analysisType of analysisOrder) {
        const result = results[analysisType];
        if (result && result.success && result.text) {
          const titles = {
            comprehensive: '## 📋 综合详细改进建议',
            sentence: '## 📝 逐句详细分析',
            error: '## 🔍 全面错误分析',
            comparison: '## 📊 范文对比分析',
            learning: '## 🎯 个性化学习计划'
          };

          content += `${titles[analysisType as keyof typeof titles]}\n\n`;
          content += result.text + '\n\n';
          tokensUsed += result.tokens_used || 0;
        }
      }

      // 添加生成摘要
      if (data.data.generation_summary) {
        const summary = data.data.generation_summary;
        content += `## 📊 生成摘要\n\n`;
        content += `- 总步骤数: ${summary.total_steps}\n`;
        content += `- 成功步骤: ${summary.completed_steps}\n`;
        content += `- 失败步骤: ${summary.failed_steps}\n`;
        content += `- 成功率: ${(summary.success_rate * 100).toFixed(1)}%\n`;
        content += `- 总Token使用: ${summary.total_tokens_used}\n\n`;
      }
    }
    // 如果是完整的改进建议包（旧格式兼容）
    else if (data.comprehensive_improvements || data.sentence_level_analysis || data.error_analysis) {
      if (data.comprehensive_improvements?.text) {
        content += '## 📋 综合详细改进建议\n\n' + data.comprehensive_improvements.text + '\n\n';
      }
      if (data.sentence_level_analysis?.text) {
        content += '## 📝 逐句详细分析\n\n' + data.sentence_level_analysis.text + '\n\n';
      }
      if (data.error_analysis?.text) {
        content += '## 🔍 全面错误分析\n\n' + data.error_analysis.text + '\n\n';
      }
      if (data.sample_comparison?.text) {
        content += '## 📊 范文对比分析\n\n' + data.sample_comparison.text + '\n\n';
      }
      if (data.learning_plan?.text) {
        content += '## 🎯 个性化学习计划\n\n' + data.learning_plan.text + '\n\n';
      }
    }

    // 如果没有找到合适的内容，返回JSON格式
    if (!content) {
      content = JSON.stringify(data, null, 2);
    }

    return { content, tokensUsed };
  };

  // 生成特定类型的改进建议
  const generateImprovement = async (analysisType: string, sectionIndex: number) => {
    if (analysisType === 'comparison') {
      // 范文对比分析暂时显示客服信息
      setSections(prev => prev.map((section, index) =>
        index === sectionIndex
          ? {
              ...section,
              isLoading: false,
              error: undefined,
              isExpanded: true,
              customContentType: 'serviceContact',
              content: '',
              tokensUsed: undefined,
              progress: 100
            }
          : section
      ));
      setCurrentLoadingIndex(-1);
      return;
    }

    // 更新loading状态
    setSections(prev => prev.map((section, index) =>
      index === sectionIndex
        ? { ...section, isLoading: true, error: undefined, customContentType: undefined }
        : section
    ));
    setCurrentLoadingIndex(sectionIndex);

    try {
      const response = await improvementAPI.generateDetailedImprovements({
        essay_content: essayContent,
        essay_title: essayTitle,
        dimension_scores: dimensionScores,
        overall_score: overallScore,
        target_score: targetScore,
        analysis_type: analysisType
      });

      if (response.success && response.data) {
        const { content, tokensUsed } = processAIResponse(response.data);

        setSections(prev => prev.map((section, index) =>
          index === sectionIndex
            ? {
                ...section,
                content,
                isLoading: false,
                isExpanded: true,
                tokensUsed,
                progress: 100,
                customContentType: undefined
              }
            : section
        ));
      } else {
        throw new Error(response.error || '生成改进建议失败');
      }
    } catch (error) {
      console.error('Error generating improvement:', error);
      setSections(prev => prev.map((section, index) =>
        index === sectionIndex
          ? {
              ...section,
              isLoading: false,
              error: error instanceof Error ? error.message : '生成改进建议时发生错误，请稍后重试',
              customContentType: undefined
            }
          : section
      ));
    } finally {
      setCurrentLoadingIndex(-1);
    }
  };

  // 切换展开/折叠状态
  const toggleSection = (index: number) => {
    setSections(prev => prev.map((section, i) => 
      i === index 
        ? { ...section, isExpanded: !section.isExpanded }
        : section
    ));
  };

  // 复制内容到剪贴板
  const copyToClipboard = async (content: string) => {
    try {
      await navigator.clipboard.writeText(content);
      // 显示成功提示
      const button = document.activeElement as HTMLButtonElement;
      if (button) {
        const originalText = button.innerHTML;
        button.innerHTML = '✅ 已复制';
        button.disabled = true;
        setTimeout(() => {
          button.innerHTML = originalText;
          button.disabled = false;
        }, 2000);
      }
    } catch (error) {
      console.error('Failed to copy:', error);
      // 显示错误提示
      const button = document.activeElement as HTMLButtonElement;
      if (button) {
        const originalText = button.innerHTML;
        button.innerHTML = '❌ 复制失败';
        setTimeout(() => {
          button.innerHTML = originalText;
        }, 2000);
      }
    }
  };

  // 打印特定section的内容
  const printSection = (content: string, title: string) => {
    const printWindow = window.open('', '_blank');
    if (printWindow) {
      printWindow.document.write(`
        <html>
          <head>
            <title>${title} - 改进建议</title>
            <style>
              body { font-family: Arial, sans-serif; line-height: 1.6; margin: 20px; }
              h1, h2, h3 { color: #333; }
              .header { border-bottom: 2px solid #4F46E5; padding-bottom: 10px; margin-bottom: 20px; }
              .content { white-space: pre-wrap; }
              @media print { body { margin: 0; } }
            </style>
          </head>
          <body>
            <div class="header">
              <h1>${title}</h1>
              <p>生成时间: ${new Date().toLocaleString('zh-CN')}</p>
            </div>
            <div class="content">${content}</div>
          </body>
        </html>
      `);
      printWindow.document.close();
      printWindow.print();
    }
  };

  // 展开所有已生成的section
  const expandAll = () => {
    setSections(prev => prev.map(section =>
      (section.content || section.customContentType) ? { ...section, isExpanded: true } : section
    ));
  };

  // 折叠所有section
  const collapseAll = () => {
    setSections(prev => prev.map(section => ({ ...section, isExpanded: false })));
  };

  // 生成所有类型的改进建议
  const generateAllImprovements = async () => {
    for (let i = 0; i < sections.length; i++) {
      if (!sections[i].content && !sections[i].customContentType && !sections[i].isLoading) {
        await generateImprovement(sections[i].id, i);
        // 添加延迟避免同时发送太多请求
        await new Promise(resolve => setTimeout(resolve, 1000));
      }
    }
  };

  if (isInitializing) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <div className="animate-pulse">
          <div className="h-6 bg-gray-200 rounded w-1/3 mb-4"></div>
          <div className="space-y-3">
            <div className="h-4 bg-gray-200 rounded"></div>
            <div className="h-4 bg-gray-200 rounded w-5/6"></div>
            <div className="h-4 bg-gray-200 rounded w-4/6"></div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <div className="mb-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-xl font-bold text-gray-900">🎯 详细改进建议</h3>
          <div className="flex space-x-2">
            <button
              onClick={generateAllImprovements}
              className="px-3 py-1 bg-indigo-600 text-white rounded text-sm hover:bg-indigo-700 transition-colors"
              disabled={currentLoadingIndex >= 0}
            >
              🚀 生成全部
            </button>
            <button
              onClick={expandAll}
              className="px-3 py-1 bg-green-600 text-white rounded text-sm hover:bg-green-700 transition-colors"
            >
              📖 展开全部
            </button>
            <button
              onClick={collapseAll}
              className="px-3 py-1 bg-gray-600 text-white rounded text-sm hover:bg-gray-700 transition-colors"
            >
              📚 折叠全部
            </button>
          </div>
        </div>
        <p className="text-gray-600 text-sm">
          点击下方按钮生成不同类型的详细改进建议。AI会像雅思老师一样，给出非常细致的建议，
          针对文章的每一个可以改进的单词、句子、段落结构、逻辑结构、语法、任务回应给出改进后的结果。
        </p>
      </div>

      <div className="space-y-4">
        {sections.map((section, index) => (
          <div key={section.id} className="border border-gray-200 rounded-lg">
            {/* Section Header */}
            <div className="p-4 bg-gray-50 border-b border-gray-200">
              <div className="flex items-center justify-between">
                <div className="flex-1">
                  <h4 className="font-semibold text-gray-900">{section.title}</h4>
                  <p className="text-sm text-gray-600 mt-1">
                    {ANALYSIS_TYPES.find(t => t.key === section.id)?.description}
                  </p>
                  {section.customContentType === 'serviceContact' && (
                    <p className="text-xs text-indigo-600 mt-1">
                      📌 添加客服即可领取对比范文与额外次数
                    </p>
                  )}
                  {section.tokensUsed && (
                    <p className="text-xs text-green-600 mt-1">
                      ✅ 已生成 ({section.tokensUsed} tokens)
                    </p>
                  )}
                </div>
                <div className="flex items-center space-x-2">
                  {section.content && (
                    <>
                      <button
                        onClick={() => copyToClipboard(section.content)}
                        className="p-2 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded transition-colors"
                        title="复制内容"
                      >
                        📋
                      </button>
                      <button
                        onClick={() => printSection(section.content, section.title)}
                        className="p-2 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded transition-colors"
                        title="打印内容"
                      >
                        🖨️
                      </button>
                    </>
                  )}
                  {(section.content || section.customContentType) && (
                    <button
                      onClick={() => toggleSection(index)}
                      className="p-2 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded transition-colors"
                      title={section.isExpanded ? "折叠" : "展开"}
                    >
                      {section.isExpanded ? '🔼' : '🔽'}
                    </button>
                  )}
                  {!section.content && !section.customContentType && !section.isLoading && (
                    <button
                      onClick={() => generateImprovement(section.id, index)}
                      className="px-4 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700 transition-colors disabled:opacity-50"
                      disabled={currentLoadingIndex >= 0}
                    >
                      生成建议
                    </button>
                  )}
                </div>
              </div>
            </div>

            {/* Section Content */}
            {section.isLoading && (
              <div className="p-6">
                <div className="flex items-center justify-center space-x-3 mb-4">
                  <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-indigo-600"></div>
                  <span className="text-gray-600">AI正在生成详细的改进建议，请稍候...</span>
                </div>

                {/* 进度指示器 */}
                <div className="w-full bg-gray-200 rounded-full h-2 mb-4">
                  <div
                    className="bg-indigo-600 h-2 rounded-full transition-all duration-500"
                    style={{width: `${section.progress || 30}%`}}
                  ></div>
                </div>

                <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                  <div className="flex items-start space-x-3">
                    <span className="text-blue-600 text-xl">🤖</span>
                    <div>
                      <p className="text-blue-800 text-sm font-medium mb-2">
                        AI正在深度分析您的作文...
                      </p>
                      <ul className="text-blue-700 text-xs space-y-1">
                        <li>• 分析文章结构和逻辑</li>
                        <li>• 检测语法和词汇问题</li>
                        <li>• 生成具体改进建议</li>
                        <li>• 提供修改示例</li>
                      </ul>
                      <div className="flex justify-between items-center mt-2">
                        <p className="text-blue-600 text-xs">
                          预计需要30-60秒
                        </p>
                        {section.tokensUsed && (
                          <span className="text-blue-500 text-xs">
                            已使用 {section.tokensUsed} tokens
                          </span>
                        )}
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {section.error && (
              <div className="p-6">
                <div className="bg-red-50 border border-red-200 rounded-lg p-4">
                  <div className="flex items-start space-x-3">
                    <span className="text-red-600 text-xl">⚠️</span>
                    <div className="flex-1">
                      <h5 className="text-red-800 font-medium mb-1">生成失败</h5>
                      <p className="text-red-700 text-sm mb-3">{section.error}</p>
                      <div className="flex space-x-2">
                        <button
                          onClick={() => generateImprovement(section.id, index)}
                          className="px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 transition-colors text-sm"
                        >
                          🔄 重试
                        </button>
                        <button
                          onClick={() => setSections(prev => prev.map((s, i) =>
                            i === index ? { ...s, error: undefined } : s
                          ))}
                          className="px-4 py-2 bg-gray-300 text-gray-700 rounded-md hover:bg-gray-400 transition-colors text-sm"
                        >
                          关闭
                        </button>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {section.customContentType === 'serviceContact' && section.isExpanded && (
              <div className="p-6">
                <div className="flex flex-col items-center space-y-4 text-center">
                  <img
                    src="/data/service.JPG"
                    alt="客服二维码"
                    className="w-full max-w-xs rounded-lg shadow-md"
                  />
                  <p className="text-gray-700 text-sm md:text-base">
                    添加客服，免费获取范文、保分资料和10 次免费使用次数
                  </p>
                  <div className="flex flex-col items-center space-y-2">
                    <span className="text-gray-600 text-sm">
                      微信号：{SERVICE_WECHAT_ID}
                    </span>
                    <button
                      onClick={() => copyToClipboard(SERVICE_WECHAT_ID)}
                      className="px-4 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700 transition-colors"
                    >
                      复制客服微信号
                    </button>
                  </div>
                </div>
              </div>
            )}

            {section.content && section.isExpanded && (
              <div className="p-6">
                <div className="prose max-w-none">
                  <ReactMarkdown remarkPlugins={[remarkGfm]}>
                    {section.content}
                  </ReactMarkdown>
                </div>
              </div>
            )}
          </div>
        ))}
      </div>

      {/* 使用说明 */}
      <div className="mt-6 bg-yellow-50 border border-yellow-200 rounded-lg p-4">
        <h5 className="font-semibold text-yellow-800 mb-2">📚 使用说明</h5>
        <ul className="text-yellow-700 text-sm space-y-1">
          <li>• <strong>综合详细改进建议</strong>：最全面的分析，推荐首先生成</li>
          <li>• <strong>逐句详细分析</strong>：对每个句子进行深度分析和多个改进版本</li>
          <li>• <strong>全面错误分析</strong>：识别语法、词汇、结构等所有错误类型</li>
          <li>• <strong>范文对比分析</strong>：与高分范文对比，学习优秀特征</li>
          <li>• <strong>个性化学习计划</strong>：基于您的具体问题制定8周学习计划</li>
        </ul>
      </div>
    </div>
  );
}
