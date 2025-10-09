/**
 * PerformanceMonitor - 性能监控工具类
 * 
 * 功能：
 * 1. 监控虚拟滚动组件性能
 * 2. 收集性能指标
 * 3. 检测性能回归
 * 4. 生成性能报告
 */

export interface PerformanceMetric {
  name: string;
  value: number;
  timestamp: number;
  category: 'render' | 'search' | 'scroll' | 'memory' | 'interaction';
  metadata?: Record<string, any>;
}

export interface PerformanceReport {
  summary: {
    totalMetrics: number;
    averageRenderTime: number;
    averageSearchTime: number;
    averageScrollTime: number;
    memoryUsage: number;
    performanceScore: number;
  };
  metrics: PerformanceMetric[];
  recommendations: string[];
  timestamp: number;
}

export interface PerformanceThresholds {
  render: {
    small: number;    // 小数据集渲染阈值 (ms)
    medium: number;   // 中等数据集渲染阈值 (ms)
    large: number;    // 大数据集渲染阈值 (ms)
  };
  search: {
    input: number;    // 搜索输入响应阈值 (ms)
    filter: number;   // 搜索过滤阈值 (ms)
    debounce: number; // 防抖延迟阈值 (ms)
  };
  scroll: {
    single: number;   // 单次滚动阈值 (ms)
    continuous: number; // 连续滚动阈值 (ms)
  };
  memory: {
    initial: number;  // 初始内存阈值 (bytes)
    peak: number;     // 峰值内存阈值 (bytes)
    growth: number;   // 内存增长阈值 (bytes)
  };
}

// 默认性能阈值
const DEFAULT_THRESHOLDS: PerformanceThresholds = {
  render: {
    small: 50,
    medium: 100,
    large: 200
  },
  search: {
    input: 30,
    filter: 50,
    debounce: 150
  },
  scroll: {
    single: 20,
    continuous: 100
  },
  memory: {
    initial: 5 * 1024 * 1024,  // 5MB
    peak: 10 * 1024 * 1024,    // 10MB
    growth: 2 * 1024 * 1024    // 2MB
  }
};

export class PerformanceMonitor {
  private metrics: PerformanceMetric[] = [];
  private timers: Map<string, number> = new Map();
  private thresholds: PerformanceThresholds;
  private isEnabled: boolean = true;

  constructor(customThresholds?: Partial<PerformanceThresholds>) {
    this.thresholds = { ...DEFAULT_THRESHOLDS, ...customThresholds };
  }

  /**
   * 启用或禁用性能监控
   */
  enable(enabled: boolean = true): void {
    this.isEnabled = enabled;
  }

  /**
   * 开始计时
   */
  startTimer(name: string): void {
    if (!this.isEnabled) return;
    this.timers.set(name, performance.now());
  }

  /**
   * 结束计时并记录指标
   */
  endTimer(name: string, category: PerformanceMetric['category'], metadata?: Record<string, any>): number {
    if (!this.isEnabled) return 0;

    const startTime = this.timers.get(name);
    if (!startTime) {
      console.warn(`Timer '${name}' was not started`);
      return 0;
    }

    const duration = performance.now() - startTime;
    this.recordMetric(name, duration, category, metadata);
    this.timers.delete(name);

    return duration;
  }

  /**
   * 记录性能指标
   */
  recordMetric(name: string, value: number, category: PerformanceMetric['category'], metadata?: Record<string, any>): void {
    if (!this.isEnabled) return;

    const metric: PerformanceMetric = {
      name,
      value,
      timestamp: Date.now(),
      category,
      metadata
    };

    this.metrics.push(metric);

    // 检查是否超过阈值
    this.checkThreshold(metric);
  }

  /**
   * 记录内存使用情况
   */
  recordMemoryUsage(usage: number, type: 'initial' | 'peak' | 'current'): void {
    if (!this.isEnabled) return;

    this.recordMetric(
      `memory_${type}`,
      usage,
      'memory',
      { type, usageInMB: usage / 1024 / 1024 }
    );
  }

  /**
   * 检查性能阈值
   */
  private checkThreshold(metric: PerformanceMetric): void {
    const threshold = this.getThresholdForMetric(metric);
    if (threshold && metric.value > threshold) {
      console.warn(`性能警告: ${metric.name} (${metric.value.toFixed(2)}ms) 超过阈值 (${threshold}ms)`);
    }
  }

  /**
   * 获取指标的阈值
   */
  private getThresholdForMetric(metric: PerformanceMetric): number | null {
    const { name, category } = metric;

    switch (category) {
      case 'render':
        if (name.includes('small')) return this.thresholds.render.small;
        if (name.includes('medium')) return this.thresholds.render.medium;
        if (name.includes('large')) return this.thresholds.render.large;
        break;
      case 'search':
        if (name.includes('input')) return this.thresholds.search.input;
        if (name.includes('filter')) return this.thresholds.search.filter;
        if (name.includes('debounce')) return this.thresholds.search.debounce;
        break;
      case 'scroll':
        if (name.includes('single')) return this.thresholds.scroll.single;
        if (name.includes('continuous')) return this.thresholds.scroll.continuous;
        break;
      case 'memory':
        if (name.includes('initial')) return this.thresholds.memory.initial;
        if (name.includes('peak')) return this.thresholds.memory.peak;
        if (name.includes('growth')) return this.thresholds.memory.growth;
        break;
    }

    return null;
  }

  /**
   * 获取性能指标统计
   */
  getMetricsByCategory(category: PerformanceMetric['category']): PerformanceMetric[] {
    return this.metrics.filter(metric => metric.category === category);
  }

  /**
   * 获取平均性能指标
   */
  getAverageMetric(name: string): number {
    const metrics = this.metrics.filter(metric => metric.name === name);
    if (metrics.length === 0) return 0;

    const sum = metrics.reduce((total, metric) => total + metric.value, 0);
    return sum / metrics.length;
  }

  /**
   * 获取最佳性能指标
   */
  getBestMetric(name: string): PerformanceMetric | null {
    const metrics = this.metrics.filter(metric => metric.name === name);
    if (metrics.length === 0) return null;

    return metrics.reduce((best, current) => 
      current.value < best.value ? current : best
    );
  }

  /**
   * 获取最差性能指标
   */
  getWorstMetric(name: string): PerformanceMetric | null {
    const metrics = this.metrics.filter(metric => metric.name === name);
    if (metrics.length === 0) return null;

    return metrics.reduce((worst, current) => 
      current.value > worst.value ? current : worst
    );
  }

  /**
   * 检测性能回归
   */
  detectRegression(baselineMetrics: Record<string, number>, tolerance: number = 0.2): string[] {
    const regressions: string[] = [];

    for (const [name, baselineValue] of Object.entries(baselineMetrics)) {
      const currentAverage = this.getAverageMetric(name);
      const threshold = baselineValue * (1 + tolerance);

      if (currentAverage > threshold) {
        regressions.push(`${name}: 当前平均 ${currentAverage.toFixed(2)}ms, 基准 ${baselineValue}ms (允许 ${(tolerance * 100).toFixed(0)}% 下降)`);
      }
    }

    return regressions;
  }

  /**
   * 生成性能报告
   */
  generateReport(): PerformanceReport {
    const renderMetrics = this.getMetricsByCategory('render');
    const searchMetrics = this.getMetricsByCategory('search');
    const scrollMetrics = this.getMetricsByCategory('scroll');
    const memoryMetrics = this.getMetricsByCategory('memory');

    const averageRenderTime = renderMetrics.length > 0 
      ? renderMetrics.reduce((sum, m) => sum + m.value, 0) / renderMetrics.length 
      : 0;

    const averageSearchTime = searchMetrics.length > 0 
      ? searchMetrics.reduce((sum, m) => sum + m.value, 0) / searchMetrics.length 
      : 0;

    const averageScrollTime = scrollMetrics.length > 0 
      ? scrollMetrics.reduce((sum, m) => sum + m.value, 0) / scrollMetrics.length 
      : 0;

    const memoryUsage = memoryMetrics.length > 0 
      ? memoryMetrics[memoryMetrics.length - 1]?.value || 0 
      : 0;

    // 计算性能得分 (0-100)
    const performanceScore = this.calculatePerformanceScore();

    // 生成建议
    const recommendations = this.generateRecommendations();

    return {
      summary: {
        totalMetrics: this.metrics.length,
        averageRenderTime,
        averageSearchTime,
        averageScrollTime,
        memoryUsage,
        performanceScore
      },
      metrics: [...this.metrics],
      recommendations,
      timestamp: Date.now()
    };
  }

  /**
   * 计算性能得分
   */
  private calculatePerformanceScore(): number {
    if (this.metrics.length === 0) return 100;

    let totalScore = 0;
    let totalWeight = 0;

    // 渲染性能权重 40%
    const renderScore = this.calculateCategoryScore('render');
    totalScore += renderScore * 0.4;
    totalWeight += 0.4;

    // 搜索性能权重 30%
    const searchScore = this.calculateCategoryScore('search');
    totalScore += searchScore * 0.3;
    totalWeight += 0.3;

    // 滚动性能权重 20%
    const scrollScore = this.calculateCategoryScore('scroll');
    totalScore += scrollScore * 0.2;
    totalWeight += 0.2;

    // 内存使用权重 10%
    const memoryScore = this.calculateCategoryScore('memory');
    totalScore += memoryScore * 0.1;
    totalWeight += 0.1;

    return totalWeight > 0 ? Math.round(totalScore / totalWeight) : 100;
  }

  /**
   * 计算分类性能得分
   */
  private calculateCategoryScore(category: PerformanceMetric['category']): number {
    const metrics = this.getMetricsByCategory(category);
    if (metrics.length === 0) return 100;

    let totalScore = 0;
    let totalWeight = 0;

    for (const metric of metrics) {
      const threshold = this.getThresholdForMetric(metric);
      if (!threshold) continue;

      const ratio = metric.value / threshold;
      const score = ratio <= 1 ? 100 : Math.max(0, 100 - (ratio - 1) * 50);
      
      totalScore += score;
      totalWeight += 1;
    }

    return totalWeight > 0 ? totalScore / totalWeight : 100;
  }

  /**
   * 生成性能建议
   */
  private generateRecommendations(): string[] {
    const recommendations: string[] = [];

    // 检查渲染性能
    const renderMetrics = this.getMetricsByCategory('render');
    const avgRenderTime = renderMetrics.length > 0 
      ? renderMetrics.reduce((sum, m) => sum + m.value, 0) / renderMetrics.length 
      : 0;

    if (avgRenderTime > this.thresholds.render.medium) {
      recommendations.push('渲染性能较慢，建议检查组件优化和数据结构');
    }

    // 检查搜索性能
    const searchMetrics = this.getMetricsByCategory('search');
    const avgSearchTime = searchMetrics.length > 0 
      ? searchMetrics.reduce((sum, m) => sum + m.value, 0) / searchMetrics.length 
      : 0;

    if (avgSearchTime > this.thresholds.search.filter) {
      recommendations.push('搜索性能较慢，建议优化搜索算法或增加防抖');
    }

    // 检查内存使用
    const memoryMetrics = this.getMetricsByCategory('memory');
    if (memoryMetrics.length > 0) {
      const latestMemory = memoryMetrics[memoryMetrics.length - 1];
      if (latestMemory.value > this.thresholds.memory.peak) {
        recommendations.push('内存使用过高，建议检查内存泄漏和优化数据结构');
      }
    }

    // 检查滚动性能
    const scrollMetrics = this.getMetricsByCategory('scroll');
    const avgScrollTime = scrollMetrics.length > 0 
      ? scrollMetrics.reduce((sum, m) => sum + m.value, 0) / scrollMetrics.length 
      : 0;

    if (avgScrollTime > this.thresholds.scroll.continuous) {
      recommendations.push('滚动性能较慢，建议优化虚拟滚动配置');
    }

    if (recommendations.length === 0) {
      recommendations.push('性能表现良好，继续保持当前优化水平');
    }

    return recommendations;
  }

  /**
   * 清除所有指标
   */
  clear(): void {
    this.metrics = [];
    this.timers.clear();
  }

  /**
   * 导出性能数据
   */
  exportData(): string {
    return JSON.stringify({
      metrics: this.metrics,
      thresholds: this.thresholds,
      timestamp: Date.now()
    }, null, 2);
  }

  /**
   * 导入性能数据
   */
  importData(data: string): void {
    try {
      const parsed = JSON.parse(data);
      if (parsed.metrics) {
        this.metrics = parsed.metrics;
      }
      if (parsed.thresholds) {
        this.thresholds = { ...this.thresholds, ...parsed.thresholds };
      }
    } catch (error) {
      console.error('导入性能数据失败:', error);
    }
  }
}

// 全局性能监控实例
export const performanceMonitor = new PerformanceMonitor();

// 导出便捷方法
export const startTimer = (name: string) => performanceMonitor.startTimer(name);
export const endTimer = (name: string, category: PerformanceMetric['category'], metadata?: Record<string, any>) => 
  performanceMonitor.endTimer(name, category, metadata);
export const recordMetric = (name: string, value: number, category: PerformanceMetric['category'], metadata?: Record<string, any>) => 
  performanceMonitor.recordMetric(name, value, category, metadata);
export const generateReport = () => performanceMonitor.generateReport();
export const clearMetrics = () => performanceMonitor.clear();

