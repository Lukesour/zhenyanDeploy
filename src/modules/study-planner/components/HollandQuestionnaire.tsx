'use client';

import React, { useState } from 'react';
import { 
  Card, 
  Typography, 
  Radio, 
  Button, 
  Progress, 
  Space, 
  Divider,
  Alert,
  Row,
  Col
} from 'antd';
import { CheckCircleOutlined } from '@ant-design/icons';

const { Title, Text, Paragraph } = Typography;

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

// 答案接口
interface Answer {
  question_id: number;
  score: number;
}

interface HollandQuestionnaireProps {
  data: HollandData;
  onSubmit: (answers: Answer[]) => void;
  isSubmitting: boolean;
}

const HollandQuestionnaire: React.FC<HollandQuestionnaireProps> = ({
  data,
  onSubmit,
  isSubmitting
}) => {
  const [answers, setAnswers] = useState<Record<number, number>>({});
  
  // 获取所有问题
  const allQuestions = data.sections.flatMap(section => section.questions);
  const totalQuestions = allQuestions.length;
  const answeredQuestions = Object.keys(answers).length;
  const progress = (answeredQuestions / totalQuestions) * 100;
  
  // 处理答案变化
  const handleAnswerChange = (questionId: number, score: number) => {
    setAnswers(prev => ({
      ...prev,
      [questionId]: score
    }));
  };

  // 检查是否所有问题都已回答
  const isComplete = answeredQuestions === totalQuestions;

  // 提交问卷
  const handleSubmit = () => {
    if (!isComplete) return;
    
    const answerList: Answer[] = Object.entries(answers).map(([questionId, score]) => ({
      question_id: parseInt(questionId),
      score
    }));
    
    onSubmit(answerList);
  };

  return (
    <div className="holland-assessment">
      {/* 标题和说明 */}
      <Card style={{ marginBottom: '24px' }}>
        <Title level={2} className="holland-title">
          {data.title}
        </Title>
        <Paragraph style={{ fontSize: '16px', textAlign: 'center', marginBottom: '24px' }}>
          {data.description}
        </Paragraph>
        
        {/* 指导语 */}
        <div className="holland-instructions">
          <Alert
            message="评估指导"
            description={
              <div>
                <Paragraph style={{ marginBottom: '8px' }}>
                  {data.instructions.intro}
                </Paragraph>
                <Paragraph style={{ marginBottom: '16px' }}>
                  {data.instructions.scoring_guide}
                </Paragraph>

                {/* 评分标准 */}
                <div>
                  <Text strong>评分标准：</Text>
                  <Row gutter={[8, 8]} style={{ marginTop: '8px' }}>
                    {data.instructions.scale.map(item => (
                      <Col key={item.score} span={4}>
                        <div className="holland-scale-item">
                          <div className="holland-scale-score">{item.score}分</div>
                          <div>{item.label}</div>
                        </div>
                      </Col>
                    ))}
                  </Row>
                </div>
              </div>
            }
            type="info"
            showIcon
            style={{ marginBottom: '24px' }}
          />
        </div>
        
        {/* 进度条 */}
        <div className="holland-progress">
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
            <Text>完成进度</Text>
            <Text>{answeredQuestions}/{totalQuestions}</Text>
          </div>
          <Progress
            percent={progress}
            status={isComplete ? 'success' : 'active'}
            strokeColor={isComplete ? '#52c41a' : '#1890ff'}
          />
        </div>
      </Card>

      {/* 问卷部分 */}
      {data.sections.map((section, sectionIndex) => (
        <Card 
          key={sectionIndex}
          title={section.title}
          style={{ marginBottom: '24px' }}
        >
          <Paragraph style={{ marginBottom: '24px', color: '#666' }}>
            {section.description}
          </Paragraph>
          
          <Space direction="vertical" size="large" style={{ width: '100%' }}>
            {section.questions.map((question, questionIndex) => (
              <div
                key={question.id}
                className={`holland-question ${answers[question.id] ? 'holland-question-answered' : ''}`}
              >
                <div className="holland-question-text">
                  {question.id}. {question.text}
                  {answers[question.id] && (
                    <CheckCircleOutlined
                      style={{ color: '#52c41a', marginLeft: '8px' }}
                    />
                  )}
                </div>
                
                <Radio.Group
                  value={answers[question.id]}
                  onChange={(e) => handleAnswerChange(question.id, e.target.value)}
                  style={{ width: '100%' }}
                >
                  <Row gutter={[16, 8]}>
                    {data.instructions.scale.map(scaleItem => (
                      <Col key={scaleItem.score} xs={24} sm={12} md={8} lg={4}>
                        <Radio
                          value={scaleItem.score}
                          className={`holland-option ${answers[question.id] === scaleItem.score ? 'holland-option-selected' : ''}`}
                        >
                          <div className="holland-option-content">
                            <div className="holland-option-score">
                              {scaleItem.score}分
                            </div>
                            <div className="holland-option-label">
                              {scaleItem.label}
                            </div>
                          </div>
                        </Radio>
                      </Col>
                    ))}
                  </Row>
                </Radio.Group>
                
                {questionIndex < section.questions.length - 1 && (
                  <Divider style={{ margin: '16px 0' }} />
                )}
              </div>
            ))}
          </Space>
        </Card>
      ))}

      {/* 提交按钮 */}
      <Card style={{ textAlign: 'center' }}>
        <Button
          type="primary"
          size="large"
          onClick={handleSubmit}
          disabled={!isComplete}
          loading={isSubmitting}
          className="holland-submit-button"
        >
          {isSubmitting ? '正在分析...' : '完成评估并查看结果'}
        </Button>
        
        {!isComplete && (
          <div style={{ marginTop: '16px' }}>
            <Text type="secondary">
              请完成所有 {totalQuestions} 道题目后提交
            </Text>
          </div>
        )}
      </Card>
    </div>
  );
};

export default HollandQuestionnaire;
