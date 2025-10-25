'use client';

import React, { useMemo, useEffect, useCallback, useState } from 'react';
import { Progress, Card, List, Typography, Space, Button, Alert } from 'antd';
import { CheckCircleOutlined, LoadingOutlined, ClockCircleOutlined, PlayCircleOutlined, CloseCircleOutlined, InfoCircleOutlined } from '@ant-design/icons';
import useProgressState from '../hooks/useProgressState';
import errorHandler from '../services/ErrorHandler';
import { apiService, AnalysisTask, UserBackground, AnalysisReport } from '../services/api';

const { Title, Text } = Typography;

interface ProgressDisplayProps {
  onComplete?: (result: AnalysisReport) => void;
  onError?: (error: string) => void;
  isActive?: boolean; // 控制进度是否激活
  onStart?: () => void; // 开始进度的回调
  onCancel?: () => void; // 取消分析回调
  onRetry?: () => void; // 重试回调
  userBackground?: UserBackground; // 用户背景数据
}

type StepStatus = 'pending' | 'in_progress' | 'completed' | 'error';

const ProgressDisplay: React.FC<ProgressDisplayProps> = ({ 
  onComplete, 
  onError, 
  isActive = false, 
  onStart,
  onCancel,
  onRetry,
  userBackground
}) => {
  const [progressState, actions] = useProgressState();
  const [currentTask, setCurrentTask] = useState<AnalysisTask | null>(null);
  const [isPolling, setIsPolling] = useState(false);
  const [pollingError, setPollingError] = useState<string | null>(null);

  const handleStart = useCallback(async () => {
    console.log('ProgressDisplay handleStart called with userBackground:', userBackground);
    if (!userBackground) {
      console.error('用户背景数据缺失');
      onError?.('用户背景数据缺失');
      return;
    }

    try {
      actions.start();
      onStart?.();
      
      // 启动异步分析任务
      const task = await apiService.startAnalysis(userBackground);
      setCurrentTask(task);
      setPollingError(null);
      
      // 开始轮询任务状态
      setIsPolling(true);
      
      // 轮询直到任务完成
      const result = await apiService.pollAnalysisUntilComplete(
        task.task_id,
        (updatedTask) => {
          setCurrentTask(updatedTask);
          // 更新本地进度状态 - 使用现有的进度更新机制
          if (updatedTask.progress) {
            // 这里我们直接更新状态，因为ProgressEngine有自己的进度管理
            // 如果需要，可以通过actions.updateStepStatus来更新步骤状态
          }
        },
        5000, // 5秒轮询一次
        600000 // 最大轮询10分钟
      );
      
      // 任务完成
      setIsPolling(false);
      actions.reset(); // 重置进度状态
      onComplete?.(result);
      
    } catch (error) {
      console.error('启动分析任务失败:', error);
      setIsPolling(false);
      setPollingError(error instanceof Error ? error.message : '启动分析任务失败');
      actions.setError(error instanceof Error ? error.message : '启动分析任务失败');
      onError?.(error instanceof Error ? error.message : '启动分析任务失败');
    }
  }, [actions, onStart, onComplete, onError, userBackground]);

  const handleCancel = useCallback(async () => {
    if (currentTask && currentTask.task_id) {
      try {
        await apiService.cancelAnalysis(currentTask.task_id);
        setCurrentTask(null);
        setIsPolling(false);
      } catch (error) {
        console.error('取消分析任务失败:', error);
      }
    }
    
    actions.stop();
    onCancel?.();
  }, [actions, onCancel, currentTask]);

  const handleRetry = useCallback(() => {
    actions.clearError();
    actions.reset();
    setCurrentTask(null);
    setIsPolling(false);
    setPollingError(null);
    actions.start();
    onRetry?.();
  }, [actions, onRetry]);

  // 外部 isActive 控制开始/停止
  useEffect(() => {
    if (isActive && !progressState.isActive && !progressState.isCompleted && !isPolling) {
      handleStart();
    } else if (!isActive && (progressState.isActive || isPolling)) {
      handleCancel();
    }
  }, [isActive, progressState.isActive, progressState.isCompleted, isPolling, handleStart, handleCancel]);

  // 完成/错误回调
  useEffect(() => {
    if (progressState.isCompleted) {
      // 完成回调已在轮询完成时处理
    }
  }, [progressState.isCompleted]);

  useEffect(() => {
    if (progressState.hasError && progressState.errorMessage) {
      const { userMessage } = errorHandler.buildUserFacingError(progressState.errorMessage, {
        component: 'ProgressDisplay',
        action: 'progress'
      });
      onError?.(userMessage.title);
    }
  }, [progressState.hasError, progressState.errorMessage, onError]);

  const currentMessage = useMemo(() => {
    if (currentTask) {
      return currentTask.message || '正在分析...';
    }
    const step = progressState.steps[progressState.currentStep];
    return progressState.stepTitle || step?.message || '正在分析...';
  }, [currentTask, progressState.stepTitle, progressState.steps, progressState.currentStep]);

  const getStepIcon = (step: { status: StepStatus }) => {
    switch (step.status) {
      case 'completed':
        return <CheckCircleOutlined style={{ color: '#52c41a' }} />;
      case 'in_progress':
        return <LoadingOutlined style={{ color: '#1890ff' }} />;
      case 'error':
        return <CloseCircleOutlined style={{ color: '#ff4d4f' }} />;
      default:
        return <ClockCircleOutlined style={{ color: '#d9d9d9' }} />;
    }
  };

  const getStepDescription = (step: { message?: string; title: string }) => {
    return step.message || step.title;
  };



  return (
    <div style={{ maxWidth: 600, margin: '0 auto', padding: '20px' }}>
      <Card>
        <Space direction="vertical" size="large" style={{ width: '100%' }}>
          <div style={{ textAlign: 'center' }}>
            <Title level={3}>AI 分析进行中</Title>
            <Text type="secondary">
              {currentTask?.estimated_time || progressState.estimatedTime || '预计需要 5-10 分钟'}
            </Text>
            {/* <div>
              <Text type="secondary">因服务器原因，无法正常加载进度条，但已经开始分析</Text>
            </div> */}
            <div>
              <Text type="secondary">可以不用停留在此页面，但请不要关闭！</Text>
            </div>
            <div>
              <Text type="secondary">只需耐心等待5～10 分钟，会将分析结果自动上传</Text>
            </div>
          </div>



          {!progressState.isActive && !isActive && !progressState.isCompleted && !progressState.hasError && !progressState.isStopped && !isPolling && (
            <div style={{ textAlign: 'center' }}>
              <Button 
                type="primary" 
                size="large" 
                icon={<PlayCircleOutlined />}
                onClick={handleStart}
                disabled={progressState.isActive || isPolling}
              >
                开始分析
              </Button>
            </div>
          )}

          <div>
            <Progress
              percent={currentTask?.progress || progressState.percentage}
              status={progressState.hasError ? 'exception' : (progressState.isCompleted || (currentTask?.progress || progressState.percentage) >= 100 ? 'success' : 'active')}
              strokeColor={{
                '0%': '#108ee9',
                '100%': '#87d068',
              }}
              size={10}
              showInfo
              format={(percent) => `${Math.round(percent ?? 0)}%`}
              style={{ marginBottom: 16 }}
            />
            
            <div style={{ textAlign: 'center', marginBottom: 20 }}>
              <Text strong style={{ fontSize: 16 }}>
                {currentMessage}
              </Text>
            </div>
          </div>

          <Card size="small" title="分析步骤" style={{ backgroundColor: '#fafafa' }}>
            <List
              size="small"
              dataSource={progressState.steps}
              renderItem={(step) => (
                <List.Item>
                  <Space>
                    {getStepIcon(step)}
                    <div>
                      <Text strong={step.status === 'in_progress'}>
                        {step.title}
                      </Text>
                      {step.status !== 'pending' && (
                        <div>
                          <Text type="secondary" style={{ fontSize: 12 }}>
                            {getStepDescription(step)}
                          </Text>
                        </div>
                      )}
                    </div>
                  </Space>
                </List.Item>
              )}
            />
          </Card>

          {/* 错误提示 */}
          {pollingError && (
            <Alert
              message="分析任务出错"
              description={pollingError}
              type="error"
              showIcon
              style={{ marginBottom: 16 }}
            />
          )}

          {/* 控制区域：取消 / 重试 / 状态提示 */}
          <div style={{ textAlign: 'center' }}>
            {(progressState.isActive || isPolling) && (
              <Space>
                <Button danger onClick={handleCancel}>取消分析</Button>
              </Space>
            )}

            {!progressState.isActive && !isPolling && (progressState.hasError || progressState.isStopped) && !progressState.isCompleted && (
              <Space direction="vertical">
                {progressState.hasError && (
                  <Text type="danger">{progressState.errorMessage || '分析出错，请重试'}</Text>
                )}
                {progressState.isStopped && !progressState.hasError && (
                  <Text type="secondary">已取消分析</Text>
                )}
                <Button type="primary" onClick={handleRetry}>重新开始</Button>
              </Space>
            )}

            {progressState.isCompleted && (
              <Text type="success">分析完成</Text>
            )}
          </div>

          <div style={{ textAlign: 'center' }}>
            <Text type="secondary" style={{ fontSize: 12 }}>
              {currentTask?.estimated_time || progressState.estimatedTime || '预计需要 5-10 分钟'}
            </Text>
          </div>
        </Space>
      </Card>
    </div>
  );
};

export default ProgressDisplay;
