/**
 * ErrorHandler - 前端错误处理服务（任务 6.1）
 *
 * 目标：
 * - 错误分类与标准化
 * - 错误消息本地化
 * - 基础的恢复策略建议（不做副作用，仅返回建议）
 *
 * Linus 原则：
 * - 简单优先：清晰的分类与最小可用接口
 * - 不破坏用户：默认给安全、可恢复的建议
 * - 实用主义：不做过度抽象，后续按需扩展
 */

export type SupportedLocale = 'zh' | 'en';

export type DataErrorCode =
  | 'CACHE_MISS'
  | 'FILE_NOT_FOUND'
  | 'PARSE_ERROR'
  | 'NETWORK_ERROR'
  | 'VALIDATION_ERROR';

export type ProgressErrorCode =
  | 'TIMEOUT'
  | 'INTERRUPTED'
  | 'API_ERROR'
  | 'STATE_INCONSISTENCY';

export type ErrorCode = DataErrorCode | ProgressErrorCode | 'UNKNOWN';

export interface ErrorContext {
  component: string; // 发生错误的组件或模块名
  action: string; // 执行动作，如: loadData/startAnalysis
  userData?: unknown; // 可选的用户输入数据，用于记录与诊断
}

export interface ErrorInfo {
  code: ErrorCode;
  message: string; // 标准化技术消息（英文/内部）
  details?: unknown; // 原始错误或上下文
  timestamp: number;
  retryable: boolean;
  userAction?: string; // 简短的用户可执行建议（英文）
  context?: ErrorContext;
}

export type RecoveryAction =
  | 'retry' // 重试当前动作
  | 'reload' // 刷新/重新加载数据
  | 'resetProgress' // 重置进度
  | 'returnToForm' // 返回表单页
  | 'none'; // 无需动作

export interface LocalizedMessage {
  title: string;
  description: string;
  suggestion?: string;
}

const defaultLocale: SupportedLocale =
  typeof navigator !== 'undefined' && navigator.language?.toLowerCase().startsWith('en')
    ? 'en'
    : 'zh';

const LOCALIZED_MESSAGES: Record<ErrorCode, Record<SupportedLocale, LocalizedMessage>> = {
  CACHE_MISS: {
    zh: {
      title: '缓存已过期或不存在',
      description: '未找到可用的本地缓存数据，需要重新加载。',
      suggestion: '点击重试以重新加载数据。'
    },
    en: {
      title: 'Cache missing or expired',
      description: 'No valid cached data found. A reload is required.',
      suggestion: 'Press retry to reload data.'
    }
  },
  FILE_NOT_FOUND: {
    zh: {
      title: '数据文件未找到',
      description: '静态数据文件缺失或路径错误。',
      suggestion: '请刷新页面或稍后再试。'
    },
    en: {
      title: 'Data file not found',
      description: 'The static data file is missing or the path is incorrect.',
      suggestion: 'Please reload the page or try again later.'
    }
  },
  PARSE_ERROR: {
    zh: {
      title: '数据解析失败',
      description: '读取到的静态数据格式不正确。',
      suggestion: '请刷新页面，若问题持续请联系支持。'
    },
    en: {
      title: 'Data parse error',
      description: 'The static data has an invalid format.',
      suggestion: 'Reload the page. If the issue persists, contact support.'
    }
  },
  NETWORK_ERROR: {
    zh: {
      title: '网络连接异常',
      description: '当前网络不可用或连接不稳定。',
      suggestion: '请检查网络后重试。'
    },
    en: {
      title: 'Network error',
      description: 'The network is unavailable or unstable.',
      suggestion: 'Check your connection and retry.'
    }
  },
  VALIDATION_ERROR: {
    zh: {
      title: '表单校验失败',
      description: '部分输入数据不符合要求，请检查标红字段。',
      suggestion: '根据提示修正后再次提交。'
    },
    en: {
      title: 'Validation failed',
      description: 'Some inputs are invalid. Please check highlighted fields.',
      suggestion: 'Fix the issues and submit again.'
    }
  },
  TIMEOUT: {
    zh: {
      title: '分析超时',
      description: '分析进度超出预期时间。',
      suggestion: '可尝试重试，或稍后再试。'
    },
    en: {
      title: 'Analysis timeout',
      description: 'The analysis exceeded the expected time.',
      suggestion: 'Retry now or try again later.'
    }
  },
  INTERRUPTED: {
    zh: {
      title: '分析已中断',
      description: '进度被手动取消或发生异常中断。',
      suggestion: '可重新开始分析。'
    },
    en: {
      title: 'Analysis interrupted',
      description: 'The progress was cancelled or interrupted.',
      suggestion: 'You can start the analysis again.'
    }
  },
  API_ERROR: {
    zh: {
      title: '服务端错误',
      description: '调用分析服务失败或返回无效结果。',
      suggestion: '请重试，若问题持续请联系支持。'
    },
    en: {
      title: 'API error',
      description: 'The analysis service failed or returned an invalid response.',
      suggestion: 'Retry. If it persists, contact support.'
    }
  },
  STATE_INCONSISTENCY: {
    zh: {
      title: '状态不一致',
      description: '检测到前端状态机异常。',
      suggestion: '返回表单重新开始，以恢复正常流程。'
    },
    en: {
      title: 'State inconsistency',
      description: 'An inconsistency was detected in the frontend state.',
      suggestion: 'Return to the form and restart the flow.'
    }
  },
  UNKNOWN: {
    zh: {
      title: '未知错误',
      description: '发生未预期的异常。',
      suggestion: '刷新页面或稍后再试。'
    },
    en: {
      title: 'Unknown error',
      description: 'An unexpected error occurred.',
      suggestion: 'Reload the page or try again later.'
    }
  }
};

function toError(input: unknown): Error {
  if (input instanceof Error) return input;
  if (typeof input === 'string') return new Error(input);
  try {
    return new Error(JSON.stringify(input));
  } catch {
    return new Error('Unknown error');
  }
}

function pickLocale(locale?: SupportedLocale): SupportedLocale {
  return locale ?? defaultLocale;
}

function inferCodeFromError(error: Error): ErrorCode {
  const message = (error?.message || '').toLowerCase();
  const name = (error?.name || '').toLowerCase();

  if (message.includes('network') || name.includes('network')) return 'NETWORK_ERROR';
  if (message.includes('timeout')) return 'TIMEOUT';
  if (message.includes('not found') || message.includes('enoent')) return 'FILE_NOT_FOUND';
  if (message.includes('parse') || message.includes('json')) return 'PARSE_ERROR';
  if (message.includes('validation')) return 'VALIDATION_ERROR';
  if (message.includes('interrupted') || message.includes('cancel')) return 'INTERRUPTED';
  if (message.includes('api')) return 'API_ERROR';
  if (message.includes('state inconsistency') || message.includes('inconsist')) return 'STATE_INCONSISTENCY';
  return 'UNKNOWN';
}

function isRetryable(code: ErrorCode): boolean {
  switch (code) {
    case 'CACHE_MISS':
    case 'FILE_NOT_FOUND':
    case 'NETWORK_ERROR':
    case 'TIMEOUT':
    case 'API_ERROR':
      return true;
    case 'PARSE_ERROR':
    case 'VALIDATION_ERROR':
    case 'INTERRUPTED':
    case 'STATE_INCONSISTENCY':
    case 'UNKNOWN':
    default:
      return false;
  }
}

function suggestRecoveryAction(code: ErrorCode): RecoveryAction {
  switch (code) {
    case 'CACHE_MISS':
    case 'FILE_NOT_FOUND':
      return 'reload';
    case 'NETWORK_ERROR':
    case 'API_ERROR':
      return 'retry';
    case 'TIMEOUT':
      return 'retry';
    case 'INTERRUPTED':
      return 'resetProgress';
    case 'STATE_INCONSISTENCY':
      return 'returnToForm';
    case 'PARSE_ERROR':
    case 'VALIDATION_ERROR':
    case 'UNKNOWN':
    default:
      return 'none';
  }
}

export class ErrorHandler {
  classify(error: unknown, context?: ErrorContext): ErrorInfo {
    const err = toError(error);
    const code = inferCodeFromError(err);
    const info: ErrorInfo = {
      code,
      message: err.message || 'Unknown error',
      details: err,
      timestamp: Date.now(),
      retryable: isRetryable(code),
      userAction: this.getDefaultUserAction(code),
      context
    };
    return info;
  }

  localize(info: ErrorInfo, locale?: SupportedLocale): LocalizedMessage {
    const loc = pickLocale(locale);
    const messages = LOCALIZED_MESSAGES[info.code] ?? LOCALIZED_MESSAGES.UNKNOWN;
    return messages[loc];
  }

  getRecoveryAction(info: ErrorInfo): RecoveryAction {
    return suggestRecoveryAction(info.code);
  }

  buildUserFacingError(
    error: unknown,
    context?: ErrorContext,
    locale?: SupportedLocale
  ): { info: ErrorInfo; userMessage: LocalizedMessage; action: RecoveryAction } {
    const info = this.classify(error, context);
    const userMessage = this.localize(info, locale);
    const action = this.getRecoveryAction(info);
    return { info, userMessage, action };
  }

  private getDefaultUserAction(code: ErrorCode): string | undefined {
    switch (code) {
      case 'NETWORK_ERROR':
        return 'retry';
      case 'API_ERROR':
        return 'retry';
      case 'CACHE_MISS':
      case 'FILE_NOT_FOUND':
        return 'reload';
      case 'INTERRUPTED':
        return 'resetProgress';
      case 'STATE_INCONSISTENCY':
        return 'returnToForm';
      default:
        return undefined;
    }
  }
}

export const errorHandler = new ErrorHandler();
export default errorHandler;


