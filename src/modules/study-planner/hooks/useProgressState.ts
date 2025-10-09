'use client';

import { useState, useCallback, useRef, useEffect } from 'react';
import { ProgressEngine, ProgressState, ProgressStep, StepStatus } from '../services/ProgressEngine';

// 进度状态接口
export interface ProgressStateData {
  // 基础状态
  isActive: boolean;
  isCompleted: boolean;
  isStopped: boolean;
  hasError: boolean;
  
  // 进度数据
  percentage: number;
  currentStep: number;
  stepTitle: string;
  estimatedTime: string;
  
  // 步骤数据
  steps: ProgressStep[];
  
  // 错误信息
  errorMessage?: string;
  errorDetails?: any;
  
  // 时间信息
  startTime?: number;
  elapsedTime: number;
  totalDuration: number;
}

// 进度操作接口
export interface ProgressActions {
  // 控制操作
  start: () => void;
  stop: () => void;
  pause: () => void;
  resume: () => void;
  reset: () => void;
  
  // 状态查询
  isRunning: () => boolean;
  isFinished: () => boolean;
  isPaused: () => boolean;
  
  // 数据获取
  getCurrentState: () => ProgressStateData;
  getStepInfo: (stepIndex: number) => ProgressStep | undefined;
  getAllStepsInfo: () => ProgressStep[];
  getStepStatistics: () => {
    total: number;
    completed: number;
    inProgress: number;
    pending: number;
    error: number;
  };
  
  // 错误处理
  setError: (error: Error | string) => void;
  clearError: () => void;
  
  // 配置操作
  updateStepMessage: (stepIndex: number, message: string) => void;
  updateStepStatus: (stepIndex: number, status: StepStatus) => void;
}

// 初始进度状态
const INITIAL_STATE: ProgressStateData = {
  isActive: false,
  isCompleted: false,
  isStopped: false,
  hasError: false,
  percentage: 0,
  currentStep: 0,
  stepTitle: '',
  estimatedTime: '',
  steps: [
    {
      id: 'step1',
      title: '查找相似案例',
      status: 'pending',
      message: '正在分析历史申请案例...'
    },
    {
      id: 'step2', 
      title: '分析竞争力',
      status: 'pending',
      message: '正在评估申请竞争力...'
    },
    {
      id: 'step3',
      title: '匹配目标院校',
      status: 'pending', 
      message: '正在匹配适合的院校...'
    },
    {
      id: 'step4',
      title: '生成申请策略',
      status: 'pending',
      message: '正在制定申请策略...'
    },
    {
      id: 'step5',
      title: '优化申请材料',
      status: 'pending',
      message: '正在优化申请材料建议...'
    },
    {
      id: 'step6',
      title: '生成分析报告',
      status: 'pending',
      message: '正在生成最终分析报告...'
    }
  ],
  elapsedTime: 0,
  totalDuration: 600000 // 10分钟
};

/**
 * 进度状态管理Hook
 * 基于Linus原则：精确控制，实时更新，资源管理
 */
export const useProgressState = (): [ProgressStateData, ProgressActions] => {
  const [state, setState] = useState<ProgressStateData>(INITIAL_STATE);
  const progressEngineRef = useRef<ProgressEngine | null>(null);
  const updateTimerRef = useRef<NodeJS.Timeout | null>(null);

  // 初始化ProgressEngine
  useEffect(() => {
    if (!progressEngineRef.current) {
      progressEngineRef.current = new ProgressEngine();
      
      // 设置事件回调
      progressEngineRef.current.setProgressCallback((progressState: ProgressState) => {
        setState(prev => ({
          ...prev,
          percentage: progressState.percentage,
          currentStep: progressState.currentStep,
          stepTitle: progressState.stepTitle,
          estimatedTime: progressState.estimatedTime,
          steps: progressState.steps,
          isActive: progressState.isActive
        }));
      });

      progressEngineRef.current.setCompleteCallback(() => {
        setState(prev => ({
          ...prev,
          isActive: false,
          isCompleted: true,
          percentage: 100,
          estimatedTime: '即将完成'
        }));
      });

      progressEngineRef.current.setErrorCallback((error: Error) => {
        setState(prev => ({
          ...prev,
          isActive: false,
          hasError: true,
          errorMessage: error.message,
          errorDetails: error
        }));
      });
    }

    // 清理函数
    return () => {
      if (progressEngineRef.current) {
        progressEngineRef.current.destroy();
        progressEngineRef.current = null;
      }
      if (updateTimerRef.current) {
        clearInterval(updateTimerRef.current);
        updateTimerRef.current = null;
      }
    };
  }, []);

  // 开始进度
  const start = useCallback(() => {
    if (progressEngineRef.current && !state.isActive && !state.isCompleted) {
      setState(prev => ({
        ...prev,
        isActive: true,
        isStopped: false,
        hasError: false,
        errorMessage: undefined,
        errorDetails: undefined,
        startTime: Date.now(),
        elapsedTime: 0
      }));

      progressEngineRef.current.start();

      // 启动时间更新定时器
      updateTimerRef.current = setInterval(() => {
        setState(prev => ({
          ...prev,
          elapsedTime: prev.startTime ? Date.now() - prev.startTime : 0
        }));
      }, 100);
    }
  }, [state.isActive, state.isCompleted]);

  // 停止进度
  const stop = useCallback(() => {
    if (progressEngineRef.current) {
      progressEngineRef.current.stop();
      setState(prev => ({
        ...prev,
        isActive: false,
        isStopped: true
      }));

      if (updateTimerRef.current) {
        clearInterval(updateTimerRef.current);
        updateTimerRef.current = null;
      }
    }
  }, []);

  // 暂停进度
  const pause = useCallback(() => {
    if (progressEngineRef.current && state.isActive) {
      progressEngineRef.current.pause();
      setState(prev => ({
        ...prev,
        isActive: false
      }));

      if (updateTimerRef.current) {
        clearInterval(updateTimerRef.current);
        updateTimerRef.current = null;
      }
    }
  }, [state.isActive]);

  // 恢复进度
  const resume = useCallback(() => {
    if (progressEngineRef.current && !state.isActive && !state.isStopped) {
      progressEngineRef.current.resume();
      setState(prev => ({
        ...prev,
        isActive: true
      }));

      // 重新启动时间更新定时器
      updateTimerRef.current = setInterval(() => {
        setState(prev => ({
          ...prev,
          elapsedTime: prev.startTime ? Date.now() - prev.startTime : 0
        }));
      }, 100);
    }
  }, [state.isActive, state.isStopped]);

  // 重置进度
  const reset = useCallback(() => {
    if (progressEngineRef.current) {
      progressEngineRef.current.reset();
      setState(INITIAL_STATE);

      if (updateTimerRef.current) {
        clearInterval(updateTimerRef.current);
        updateTimerRef.current = null;
      }
    }
  }, []);

  // 状态查询方法
  const isRunning = useCallback(() => {
    return state.isActive && !state.isCompleted && !state.hasError;
  }, [state.isActive, state.isCompleted, state.hasError]);

  const isFinished = useCallback(() => {
    return state.isCompleted || state.hasError || state.isStopped;
  }, [state.isCompleted, state.hasError, state.isStopped]);

  const isPaused = useCallback(() => {
    // 仅在曾经启动过(startTime存在)且当前非活动、未完成、未停止、无错误时判定为“暂停”
    return (
      !!state.startTime &&
      !state.isActive &&
      !state.isCompleted &&
      !state.isStopped &&
      !state.hasError
    );
  }, [state.startTime, state.isActive, state.isCompleted, state.isStopped, state.hasError]);

  // 数据获取方法
  const getCurrentState = useCallback(() => {
    return state;
  }, [state]);

  const getStepInfo = useCallback((stepIndex: number) => {
    return state.steps[stepIndex];
  }, [state.steps]);

  const getAllStepsInfo = useCallback(() => {
    return state.steps;
  }, [state.steps]);

  const getStepStatistics = useCallback(() => {
    const stats = {
      total: state.steps.length,
      completed: 0,
      inProgress: 0,
      pending: 0,
      error: 0
    };

    state.steps.forEach(step => {
      switch (step.status) {
        case 'completed':
          stats.completed++;
          break;
        case 'in_progress':
          stats.inProgress++;
          break;
        case 'error':
          stats.error++;
          break;
        default:
          stats.pending++;
      }
    });

    return stats;
  }, [state.steps]);

  // 错误处理方法
  const setError = useCallback((error: Error | string) => {
    const errorMessage = typeof error === 'string' ? error : error.message;
    const errorDetails = typeof error === 'string' ? new Error(error) : error;

    setState(prev => ({
      ...prev,
      isActive: false,
      hasError: true,
      errorMessage,
      errorDetails
    }));

    if (updateTimerRef.current) {
      clearInterval(updateTimerRef.current);
      updateTimerRef.current = null;
    }
  }, []);

  const clearError = useCallback(() => {
    setState(prev => ({
      ...prev,
      hasError: false,
      errorMessage: undefined,
      errorDetails: undefined
    }));
  }, []);

  // 配置操作方法
  const updateStepMessage = useCallback((stepIndex: number, message: string) => {
    if (stepIndex >= 0 && stepIndex < state.steps.length) {
      setState(prev => ({
        ...prev,
        steps: prev.steps.map((step, index) => 
          index === stepIndex ? { ...step, message } : step
        )
      }));
    }
  }, [state.steps.length]);

  const updateStepStatus = useCallback((stepIndex: number, status: StepStatus) => {
    if (stepIndex >= 0 && stepIndex < state.steps.length) {
      setState(prev => ({
        ...prev,
        steps: prev.steps.map((step, index) => 
          index === stepIndex ? { ...step, status } : step
        )
      }));
    }
  }, [state.steps.length]);

  // Actions对象
  const actions: ProgressActions = {
    start,
    stop,
    pause,
    resume,
    reset,
    isRunning,
    isFinished,
    isPaused,
    getCurrentState,
    getStepInfo,
    getAllStepsInfo,
    getStepStatistics,
    setError,
    clearError,
    updateStepMessage,
    updateStepStatus
  };

  return [state, actions];
};

export default useProgressState;
