'use client';

import React, { useState, useEffect } from 'react';
import { Card, Typography, Spin, Button, App } from 'antd';
import { ReloadOutlined } from '@ant-design/icons';
import HollandQuestionnaire from './HollandQuestionnaire';
import HollandResults from './HollandResults';
import { hollandService } from '../services/hollandService';
import './HollandAssessment.css';

const { Title, Text } = Typography;

// 霍兰德数据接口
interface HollandData {
  title: string;
  description: string;
  instructions: {
    intro: string;
    scoring_guide: string;
    scale: Array<{
      score: number;
      label: string;
    }>;
  };
  sections: Array<{
    title: string;
    description: string;
    questions: Array<{
      id: number;
      text: string;
      type: string;
    }>;
  }>;
}

// 评估结果接口
interface HollandResult {
  holland_code: string;
  type_scores: Array<{
    type_code: string;
    type_name: string;
    score: number;
    percentage: number;
  }>;
  top_three_types: Array<{
    type_code: string;
    name: string;
    nickname: string;
    characteristics: string;
    typical_careers: string[];
  }>;
  assessment_date: string;
}

// 答案接口
interface Answer {
  question_id: number;
  score: number;
}

type AssessmentState = 'loading' | 'questionnaire' | 'submitting' | 'results' | 'error';

const HollandAssessment: React.FC = () => {
  const { message } = App.useApp();
  const [state, setState] = useState<AssessmentState>('loading');
  const [hollandData, setHollandData] = useState<HollandData | null>(null);
  const [result, setResult] = useState<HollandResult | null>(null);
  const [error, setError] = useState<string>('');

  // 加载霍兰德数据
  const loadHollandData = async () => {
    try {
      setState('loading');
      setError('');
      const data = await hollandService.getHollandData();
      setHollandData(data);
      setState('questionnaire');
    } catch (err) {
      console.error('Failed to load Holland data:', err);
      setError('加载问卷数据失败，请稍后重试');
      setState('error');
    }
  };

  // 初始化加载数据
  useEffect(() => {
    loadHollandData();
  }, []);

  // 处理问卷提交
  const handleQuestionnaireSubmit = async (submittedAnswers: Answer[]) => {
    try {
      setState('submitting');

      const assessmentResult = await hollandService.submitAssessment(submittedAnswers);
      setResult(assessmentResult);
      setState('results');

      message.success('评估完成！');
    } catch (err) {
      console.error('Assessment submission failed:', err);
      setError('评估提交失败，请稍后重试');
      setState('error');
      message.error('评估提交失败');
    }
  };

  // 重新开始评估
  const handleRestart = () => {
    setResult(null);
    setError('');
    setState('questionnaire');
  };

  // 重试加载数据
  const handleRetry = () => {
    loadHollandData();
  };

  // 渲染加载状态
  if (state === 'loading') {
    return (
      <div className="holland-assessment" style={{ textAlign: 'center' }}>
        <Spin size="large" />
        <div style={{ marginTop: '16px' }}>
          <Text>正在加载问卷数据...</Text>
        </div>
      </div>
    );
  }

  // 渲染错误状态
  if (state === 'error') {
    return (
      <div className="holland-assessment" style={{ textAlign: 'center' }}>
        <Card>
          <Title level={4} type="danger">加载失败</Title>
          <Text>{error}</Text>
          <div style={{ marginTop: '16px' }}>
            <Button
              type="primary"
              icon={<ReloadOutlined />}
              onClick={handleRetry}
              className="holland-submit-button"
            >
              重试
            </Button>
          </div>
        </Card>
      </div>
    );
  }

  // 渲染结果页面
  if (state === 'results' && result) {
    return (
      <HollandResults 
        result={result}
        onRestart={handleRestart}
      />
    );
  }

  // 渲染问卷页面
  if (hollandData) {
    return (
      <HollandQuestionnaire
        data={hollandData}
        onSubmit={handleQuestionnaireSubmit}
        isSubmitting={state === 'submitting'}
      />
    );
  }

  return null;
};

export default HollandAssessment;
