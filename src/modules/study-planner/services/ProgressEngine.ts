/**
 * ProgressEngine - 进度引擎
 * 
 * Linus的原则：
 * 1. 简单可靠比复杂智能更重要
 * 2. 进度条要平滑，不要跳跃
 * 3. 资源管理要干净，不要泄漏
 * 4. 错误处理要优雅，不要崩溃
 */

// 进度步骤状态
export type StepStatus = 'pending' | 'in_progress' | 'completed' | 'error';

// 进度步骤定义
export interface ProgressStep {
  id: string;
  title: string;
  status: StepStatus;
  startTime?: number;
  endTime?: number;
  duration?: number;
  message?: string;
}

// 进度状态
export interface ProgressState {
  percentage: number;
  currentStep: number;
  stepTitle: string;
  estimatedTime: string;
  isActive: boolean;
  steps: ProgressStep[];
}

// 进度配置
export interface ProgressConfig {
  totalDuration: number; // 240-360秒
  steps: ProgressStep[];
  easingFunction: 'linear' | 'easeInOut' | 'cubic';
  updateInterval: number; // 100ms
}

// 事件回调类型
export type ProgressCallback = (state: ProgressState) => void;
export type CompleteCallback = () => void;
export type ErrorCallback = (error: Error) => void;

/**
 * 进度引擎
 * 
 * 职责：
 * 1. 提供240-360秒的伪进度条
 * 2. 管理6个分析步骤的状态
 * 3. 提供平滑的进度更新
 * 4. 支持取消和错误处理
 */
export class ProgressEngine {
  private timer: NodeJS.Timeout | null = null;
  private startTime: number = 0;
  private isRunning: boolean = false;
  private isCompleted: boolean = false;
  private isStopped: boolean = false;
  private currentStepIndex: number = 0;
  private lastEmitTs: number = 0; // 上次回调时间戳，用于节流
  
  // 配置参数
  private readonly totalDuration: number = 600000; // 10分钟 (600秒)
  private updateInterval: number = 100; // 100ms - 允许运行时调整
  private readonly easingType: 'linear' | 'quad' | 'cubic' = 'cubic'; // 缓动类型
  private readonly steps: ProgressStep[] = [
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
      message: '正在生成完整分析报告...'
    }
  ];

  // 事件回调
  private onProgressUpdate: ProgressCallback | null = null;
  private onComplete: CompleteCallback | null = null;
  private onError: ErrorCallback | null = null;
  private lastError: Error | null = null;

  /**
   * 启动进度引擎
   * Linus: "启动要简单，但要有完整的错误处理"
   */
  start(): void {
    if (this.isRunning) {
      console.warn('ProgressEngine已经在运行中');
      return;
    }

    try {
      this.isRunning = true;
      this.isCompleted = false;
      this.isStopped = false;
      this.startTime = Date.now();
      this.currentStepIndex = 0;
      
      // 初始化所有步骤为pending
      this.steps.forEach(step => {
        step.status = 'pending';
        step.startTime = undefined;
        step.endTime = undefined;
        step.duration = undefined;
      });

      // 启动第一个步骤
      this.steps[0].status = 'in_progress';
      this.steps[0].startTime = Date.now();

      // 启动定时器
      this.timer = setInterval(() => {
        this.updateProgress();
      }, this.updateInterval);

      console.log('ProgressEngine启动成功');
    } catch (error) {
      this.isRunning = false;
      console.error('ProgressEngine启动失败:', error);
      this.lastError = error as Error;
      this.onError?.(this.lastError);
    }
  }

  /**
   * 停止进度引擎
   * Linus: "停止要干净，不要留下垃圾"
   */
  stop(): void {
    if (!this.isRunning) {
      return;
    }

    try {
      this.isRunning = false;
      this.isStopped = true;
      
      // 清理定时器
      this.clearTimer();
      
      // 标记当前步骤为错误
      if (this.currentStepIndex < this.steps.length) {
        this.steps[this.currentStepIndex].status = 'error';
        this.steps[this.currentStepIndex].endTime = Date.now();
        this.steps[this.currentStepIndex].duration = 
          this.steps[this.currentStepIndex].endTime! - this.steps[this.currentStepIndex].startTime!;
        this.steps[this.currentStepIndex].message = `${this.steps[this.currentStepIndex].title}已中断`;
      }

      console.log('ProgressEngine已停止');
    } catch (error) {
      console.error('ProgressEngine停止时出错:', error);
      this.lastError = error as Error;
      this.onError?.(this.lastError);
    }
  }

  /**
   * 完成进度
   * Linus: "完成要完整，不要半途而废"
   */
  complete(): void {
    if (!this.isRunning) {
      return;
    }

    try {
      this.isRunning = false;
      this.isCompleted = true;
      
      // 清理定时器
      this.clearTimer();

      // 完成所有步骤
      this.steps.forEach((step, index) => {
        if (step.status === 'pending' || step.status === 'in_progress') {
          step.status = 'completed';
          step.startTime = this.startTime + (index * this.totalDuration / this.steps.length);
          step.endTime = step.startTime + (this.totalDuration / this.steps.length);
          step.duration = step.endTime - step.startTime;
          step.message = `${step.title}已完成`;
        }
      });

      // 发送完成回调
      this.onComplete?.();
      
      console.log('ProgressEngine完成');
    } catch (error) {
      console.error('ProgressEngine完成时出错:', error);
      this.lastError = error as Error;
      this.onError?.(this.lastError);
    }
  }

  /**
   * 获取当前状态
   * Linus: "状态查询要快，不要阻塞"
   */
  getCurrentState(): ProgressState {
    if (this.startTime === 0) {
      return {
        percentage: 0,
        currentStep: 0,
        stepTitle: this.steps[0]?.title || '查找相似案例',
        estimatedTime: '预计需要5分钟',
        isActive: false,
        steps: [...this.steps] // 返回副本，避免外部修改
      };
    }
    
    if (this.isCompleted) {
      return {
        percentage: 100,
        currentStep: this.steps.length - 1,
        stepTitle: '分析完成',
        estimatedTime: '即将完成',
        isActive: false,
        steps: [...this.steps] // 返回副本，避免外部修改
      };
    }
    
    const elapsed = Date.now() - this.startTime;
    const percentage = Math.min((elapsed / this.totalDuration) * 100, 100);
    
    return {
      percentage: Math.round(percentage * 100) / 100, // 保留两位小数
      currentStep: this.currentStepIndex,
      stepTitle: this.steps[this.currentStepIndex]?.title || '分析完成',
      estimatedTime: this.calculateEstimatedTime(percentage),
      isActive: this.isRunning,
      steps: [...this.steps] // 返回副本，避免外部修改
    };
  }

  /**
   * 设置进度更新回调
   */
  setProgressCallback(callback: ProgressCallback): void {
    this.onProgressUpdate = callback;
  }

  /**
   * 设置完成回调
   */
  setCompleteCallback(callback: CompleteCallback): void {
    this.onComplete = callback;
  }

  /**
   * 设置错误回调
   */
  setErrorCallback(callback: ErrorCallback): void {
    this.onError = callback;
  }

  /**
   * 设置缓动类型
   * Linus: "配置要灵活，但要有默认值"
   */
  setEasingType(type: 'linear' | 'quad' | 'cubic'): void {
    if (!this.isRunning) {
      (this as any).easingType = type;
    }
  }

  /**
   * 设置更新间隔（毫秒），仅在未运行时可调整
   */
  setUpdateInterval(ms: number): void {
    if (!this.isRunning && Number.isFinite(ms) && ms >= 16) {
      this.updateInterval = Math.floor(ms);
    }
  }

  /**
   * 获取当前步骤信息
   * Linus: "信息要完整，不要遗漏"
   */
  getCurrentStepInfo(): ProgressStep | null {
    if (this.currentStepIndex < this.steps.length) {
      return { ...this.steps[this.currentStepIndex] };
    }
    return null;
  }

  /**
   * 获取所有步骤信息
   * Linus: "数据要完整，不要截断"
   */
  getAllStepsInfo(): ProgressStep[] {
    return this.steps.map(step => ({ ...step }));
  }

  /**
   * 获取步骤完成统计
   * Linus: "统计要准确，不要估算"
   */
  getStepStatistics(): {
    total: number;
    completed: number;
    inProgress: number;
    pending: number;
    error: number;
  } {
    const stats = {
      total: this.steps.length,
      completed: 0,
      inProgress: 0,
      pending: 0,
      error: 0
    };

    this.steps.forEach(step => {
      switch (step.status) {
        case 'completed':
          stats.completed++;
          break;
        case 'in_progress':
          stats.inProgress++;
          break;
        case 'pending':
          stats.pending++;
          break;
        case 'error':
          stats.error++;
          break;
      }
    });

    return stats;
  }

  /**
   * 更新进度
   * Linus: "更新要平滑，不要跳跃"
   */
  private updateProgress(): void {
    if (!this.isRunning) {
      return;
    }

    try {
      // 节流：若距离上次回调不足更新间隔，则跳过本次计算
      const nowTs = Date.now();
      if (nowTs - this.lastEmitTs < this.updateInterval) {
        return;
      }

      const elapsed = Date.now() - this.startTime;
      const rawPercentage = (elapsed / this.totalDuration) * 100;
      
      // 确保百分比在有效范围内
      const clampedPercentage = Math.max(0, Math.min(100, rawPercentage));
      
      // 使用配置的缓动函数使进度更自然
      const easedPercentage = this.applyEasing(clampedPercentage / 100) * 100;
      
      // 更新当前步骤
      this.updateCurrentStep(easedPercentage);
      
      // 发送进度更新
      this.onProgressUpdate?.(this.getCurrentState());
      this.lastEmitTs = nowTs;
      
      // 检查是否完成
      if (easedPercentage >= 100) {
        this.complete();
      }
    } catch (error) {
      console.error('进度更新出错:', error);
      this.lastError = error as Error;
      this.onError?.(this.lastError);
    }
  }

  /**
   * 更新当前步骤
   * Linus: "步骤切换要清晰，不要模糊"
   */
  private updateCurrentStep(percentage: number): void {
    const stepDuration = 100 / this.steps.length;
    const newStepIndex = Math.floor(percentage / stepDuration);
    
    if (newStepIndex !== this.currentStepIndex && newStepIndex < this.steps.length) {
      // 完成当前步骤
      if (this.currentStepIndex < this.steps.length) {
        this.steps[this.currentStepIndex].status = 'completed';
        this.steps[this.currentStepIndex].endTime = Date.now();
        this.steps[this.currentStepIndex].duration = 
          this.steps[this.currentStepIndex].endTime! - this.steps[this.currentStepIndex].startTime!;
        
        // 更新步骤完成消息
        this.steps[this.currentStepIndex].message = `${this.steps[this.currentStepIndex].title}已完成`;
      }
      
      // 开始新步骤
      this.currentStepIndex = newStepIndex;
      if (this.currentStepIndex < this.steps.length) {
        this.steps[this.currentStepIndex].status = 'in_progress';
        this.steps[this.currentStepIndex].startTime = Date.now();
        
        // 更新步骤开始消息
        this.steps[this.currentStepIndex].message = this.getStepMessage(this.currentStepIndex);
      }
    }
  }

  /**
   * 缓动函数 - 使进度更自然
   * Linus: "数学要简单，不要复杂"
   */
  private easeInOutCubic(t: number): number {
    // 确保输入在有效范围内
    const clampedT = Math.max(0, Math.min(1, t));
    
    // 三次方缓动函数：开始和结束慢，中间快
    return clampedT < 0.5 
      ? 4 * clampedT * clampedT * clampedT 
      : 1 - Math.pow(-2 * clampedT + 2, 3) / 2;
  }

  /**
   * 线性缓动函数 - 匀速进度
   */
  private easeLinear(t: number): number {
    return Math.max(0, Math.min(1, t));
  }

  /**
   * 二次方缓动函数 - 更平滑的过渡
   */
  private easeInOutQuad(t: number): number {
    const clampedT = Math.max(0, Math.min(1, t));
    return clampedT < 0.5 
      ? 2 * clampedT * clampedT 
      : 1 - Math.pow(-2 * clampedT + 2, 2) / 2;
  }

  /**
   * 应用缓动函数
   * Linus: "选择要简单，不要复杂"
   */
  private applyEasing(t: number): number {
    switch (this.easingType) {
      case 'linear':
        return this.easeLinear(t);
      case 'quad':
        return this.easeInOutQuad(t);
      case 'cubic':
      default:
        return this.easeInOutCubic(t);
    }
  }

  /**
   * 获取步骤消息
   * Linus: "消息要动态，不要静态"
   */
  private getStepMessage(stepIndex: number): string {
    const stepMessages = [
      '正在分析历史申请案例，查找相似背景...',
      '正在评估申请竞争力，分析优势劣势...',
      '正在匹配适合的院校，筛选最佳选择...',
      '正在制定个性化申请策略...',
      '正在优化申请材料建议，提升竞争力...',
      '正在生成完整分析报告，整理所有建议...'
    ];
    
    return stepMessages[stepIndex] || '正在处理...';
  }

  /**
   * 计算预计剩余时间
   * Linus: "时间估算要准确，不要忽悠用户"
   */
  private calculateEstimatedTime(percentage: number): string {
    if (percentage >= 100) {
      return '即将完成';
    }
    
    if (!this.isRunning) {
      return '即将完成';
    }
    
    const elapsed = Date.now() - this.startTime;
    const remaining = (this.totalDuration - elapsed) / 1000; // 转换为秒
    
    if (remaining < 60) {
      return `${Math.ceil(remaining)}秒`;
    } else if (remaining < 3600) {
      const minutes = Math.ceil(remaining / 60);
      return `${minutes}分钟`;
    } else {
      const hours = Math.ceil(remaining / 3600);
      return `${hours}小时`;
    }
  }

  /**
   * 计算当前步骤剩余时间
   * Linus: "步骤时间要精确，不要模糊"
   */
  private calculateStepRemainingTime(percentage: number): number {
    const stepDuration = this.totalDuration / this.steps.length;
    const currentStepProgress = (percentage % (100 / this.steps.length)) / (100 / this.steps.length);
    const stepElapsed = currentStepProgress * stepDuration;
    const stepRemaining = stepDuration - stepElapsed;
    
    return stepRemaining / 1000; // 转换为秒
  }

  /**
   * 重置进度引擎
   * Linus: "重置要彻底，不要留尾巴"
   */
  reset(): void {
    // 先停止当前运行
    this.stop();
    
    // 重置所有状态
    this.currentStepIndex = 0;
    this.startTime = 0;
    this.isRunning = false;
    this.isCompleted = false;
    this.isStopped = false;
    
    // 重置所有步骤
    this.steps.forEach(step => {
      step.status = 'pending';
      step.startTime = undefined;
      step.endTime = undefined;
      step.duration = undefined;
      step.message = this.getStepMessage(this.steps.indexOf(step));
    });
    
    // 清理定时器
    this.clearTimer();
    
    console.log('ProgressEngine已重置');
  }

  /**
   * 清理定时器
   * Linus: "清理要彻底，不要遗漏"
   */
  private clearTimer(): void {
    if (this.timer) {
      clearInterval(this.timer);
      this.timer = null;
    }
  }

  /**
   * 暂停进度引擎
   * Linus: "暂停要可恢复，不要丢失状态"
   */
  pause(): void {
    if (!this.isRunning) {
      return;
    }

    try {
      this.isRunning = false;
      this.clearTimer();
      
      console.log('ProgressEngine已暂停');
    } catch (error) {
      console.error('ProgressEngine暂停时出错:', error);
      this.lastError = error as Error;
      this.onError?.(this.lastError);
    }
  }

  /**
   * 恢复进度引擎
   * Linus: "恢复要准确，不要跳跃"
   */
  resume(): void {
    if (this.isRunning || this.isCompleted || this.isStopped) {
      return;
    }

    try {
      this.isRunning = true;
      
      // 重新启动定时器
      this.timer = setInterval(() => {
        this.updateProgress();
      }, this.updateInterval);

      console.log('ProgressEngine已恢复');
    } catch (error) {
      console.error('ProgressEngine恢复时出错:', error);
      this.lastError = error as Error;
      this.onError?.(this.lastError);
    }
  }

  /**
   * 检查是否正在运行
   * Linus: "状态检查要快，不要阻塞"
   */
  isActive(): boolean {
    return this.isRunning;
  }

  /**
   * 检查是否已完成
   * Linus: "完成检查要准确，不要模糊"
   */
  isFinished(): boolean {
    return this.isCompleted;
  }

  /**
   * 获取运行时间
   * Linus: "时间计算要精确，不要估算"
   */
  getElapsedTime(): number {
    if (this.startTime === 0) {
      return 0;
    }
    return Date.now() - this.startTime;
  }

  /**
   * 销毁进度引擎
   * Linus: "销毁要干净，不要内存泄漏"
   */
  destroy(): void {
    this.stop();
    this.onProgressUpdate = null;
    this.onComplete = null;
    this.onError = null;
  }

  /**
   * 获取最近一次错误（若存在）
   */
  getLastError(): Error | null {
    return this.lastError;
  }
}

// 导出单例实例
export const progressEngine = new ProgressEngine();
export default progressEngine;
