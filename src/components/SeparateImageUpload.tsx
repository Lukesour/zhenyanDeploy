'use client';

import React, { useState, useRef } from 'react';
import { PhotoIcon, XMarkIcon, DocumentTextIcon, ChartBarIcon } from '@heroicons/react/24/outline';

interface SeparateImageUploadProps {
  onTitleExtracted?: (title: string) => void;
  onContentExtracted?: (content: string) => void;
  onChartAnalyzed?: (analysis: ChartAnalysis) => void;
  mode: 'title' | 'content' | 'chart';
  className?: string;
}

interface ChartAnalysis {
  chart_type: string;
  description: string;
  key_features: string[];
  data_points: string[];
  trends: string[];
  writing_suggestions: {
    introduction: string;
    overview: string;
    body_paragraphs: string[];
    key_vocabulary: string[];
  };
}

export default function SeparateImageUpload({ 
  onTitleExtracted, 
  onContentExtracted, 
  onChartAnalyzed,
  mode, 
  className = '' 
}: SeparateImageUploadProps) {
  const [isUploading, setIsUploading] = useState(false);
  const [dragActive, setDragActive] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [error, setError] = useState<string>('');
  const fileInputRef = useRef<HTMLInputElement>(null);

  const getModeConfig = () => {
    switch (mode) {
      case 'title':
        return {
          title: '上传题目图片',
          description: '拖拽或点击上传题目图片，自动识别题目文字',
          icon: DocumentTextIcon,
          endpoint: '/api/v1/upload/ocr/extract-title',
          acceptText: '支持 JPG, PNG, BMP, TIFF, WebP 格式'
        };
      case 'content':
        return {
          title: '上传作文图片',
          description: '拖拽或点击上传作文内容图片，自动识别作文文字',
          icon: DocumentTextIcon,
          endpoint: '/api/v1/upload/ocr/extract-content',
          acceptText: '支持 JPG, PNG, BMP, TIFF, WebP 格式'
        };
      case 'chart':
        return {
          title: '上传图表图片',
          description: '拖拽或点击上传Task1图表，AI智能分析图表内容',
          icon: ChartBarIcon,
          endpoint: '/api/v1/upload/chart/analyze',
          acceptText: '支持柱状图、折线图、饼图、表格、流程图等'
        };
      default:
        return {
          title: '上传图片',
          description: '拖拽或点击上传图片',
          icon: PhotoIcon,
          endpoint: '/api/v1/upload/ocr/extract-text',
          acceptText: '支持图片格式'
        };
    }
  };

  const config = getModeConfig();
  const IconComponent = config.icon;

  const handleFiles = async (files: FileList) => {
    if (files.length === 0) return;
    
    const file = files[0];
    
    // 验证文件类型
    const allowedTypes = ['image/jpeg', 'image/jpg', 'image/png', 'image/bmp', 'image/tiff', 'image/webp'];
    if (!allowedTypes.includes(file.type)) {
      setError('请上传图片文件 (JPG, PNG, BMP, TIFF, WebP)');
      return;
    }
    
    // 验证文件大小 (10MB)
    if (file.size > 10 * 1024 * 1024) {
      setError('文件大小不能超过 10MB');
      return;
    }
    
    setIsUploading(true);
    setError('');
    setResult(null);
    
    try {
      const formData = new FormData();
      formData.append('file', file);
      
      const token = localStorage.getItem('access_token');
      
      const response = await fetch(`http://localhost:8000${config.endpoint}`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
        },
        body: formData,
      });
      
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || '上传失败');
      }
      
      const responseData = await response.json();
      
      if (responseData.success) {
        const extractedData = responseData.data;
        setResult(extractedData);
        
        // 根据模式调用相应的回调
        if (mode === 'title' && onTitleExtracted) {
          onTitleExtracted(extractedData.title);
        } else if (mode === 'content' && onContentExtracted) {
          onContentExtracted(extractedData.content);
        } else if (mode === 'chart' && onChartAnalyzed) {
          onChartAnalyzed(extractedData);
        }
      } else {
        throw new Error(responseData.message || '处理失败');
      }
      
    } catch (err) {
      console.error('Upload error:', err);
      setError(err instanceof Error ? err.message : '上传失败，请重试');
    } finally {
      setIsUploading(false);
    }
  };

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFiles(e.dataTransfer.files);
    }
  };

  const handleClick = () => {
    fileInputRef.current?.click();
  };

  const clearResult = () => {
    setResult(null);
    setError('');
  };

  return (
    <div className={`w-full ${className}`}>
      <div
        className={`relative border-2 border-dashed rounded-lg p-6 text-center hover:bg-gray-50 transition-colors cursor-pointer ${
          dragActive ? 'border-blue-400 bg-blue-50' : 'border-gray-300'
        } ${isUploading ? 'opacity-50 cursor-not-allowed' : ''}`}
        onDragEnter={handleDrag}
        onDragLeave={handleDrag}
        onDragOver={handleDrag}
        onDrop={handleDrop}
        onClick={!isUploading ? handleClick : undefined}
      >
        <input
          ref={fileInputRef}
          type="file"
          className="hidden"
          accept="image/*"
          onChange={(e) => e.target.files && handleFiles(e.target.files)}
          disabled={isUploading}
        />
        
        <div className="space-y-4">
          <IconComponent className="mx-auto h-12 w-12 text-gray-400" />
          <div>
            <h3 className="text-lg font-medium text-gray-900">{config.title}</h3>
            <p className="text-sm text-gray-500 mt-1">{config.description}</p>
            <p className="text-xs text-gray-400 mt-2">{config.acceptText}</p>
          </div>
          
          {isUploading && (
            <div className="flex items-center justify-center space-x-2">
              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600"></div>
              <span className="text-sm text-blue-600">
                {mode === 'chart' ? '正在分析图表...' : '正在识别文字...'}
              </span>
            </div>
          )}
        </div>
      </div>

      {error && (
        <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-md">
          <div className="flex">
            <XMarkIcon className="h-5 w-5 text-red-400" />
            <div className="ml-3">
              <p className="text-sm text-red-800">{error}</p>
            </div>
          </div>
        </div>
      )}

      {result && (
        <div className="mt-4 p-4 bg-green-50 border border-green-200 rounded-md">
          <div className="flex justify-between items-start">
            <div className="flex-1">
              <h4 className="text-sm font-medium text-green-800 mb-2">
                {mode === 'chart' ? '图表分析结果' : '识别结果'}
              </h4>
              
              {mode === 'title' && (
                <div>
                  <p className="text-sm text-green-700 mb-1">识别的题目：</p>
                  <p className="text-sm text-gray-800 bg-white p-2 rounded border">
                    {result.title}
                  </p>
                  <p className="text-xs text-green-600 mt-1">
                    置信度: {result.confidence}% | 字数: {result.word_count}
                  </p>
                </div>
              )}
              
              {mode === 'content' && (
                <div>
                  <p className="text-sm text-green-700 mb-1">识别的内容：</p>
                  <div className="text-sm text-gray-800 bg-white p-2 rounded border max-h-32 overflow-y-auto">
                    {result.content.split('\n').map((line: string, index: number) => (
                      <p key={index} className="mb-1">{line}</p>
                    ))}
                  </div>
                  <p className="text-xs text-green-600 mt-1">
                    置信度: {result.confidence}% | 字数: {result.word_count}
                  </p>
                </div>
              )}
              
              {mode === 'chart' && (
                <div className="space-y-2">
                  <div>
                    <span className="text-sm font-medium text-green-700">图表类型：</span>
                    <span className="text-sm text-gray-800">{result.chart_type}</span>
                  </div>
                  <div>
                    <span className="text-sm font-medium text-green-700">描述：</span>
                    <p className="text-sm text-gray-800">{result.description}</p>
                  </div>
                  <div>
                    <span className="text-sm font-medium text-green-700">关键特征：</span>
                    <ul className="text-sm text-gray-800 list-disc list-inside">
                      {result.key_features?.map((feature: string, index: number) => (
                        <li key={index}>{feature}</li>
                      ))}
                    </ul>
                  </div>
                </div>
              )}
            </div>
            
            <button
              onClick={clearResult}
              className="ml-2 text-green-400 hover:text-green-600"
            >
              <XMarkIcon className="h-5 w-5" />
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
