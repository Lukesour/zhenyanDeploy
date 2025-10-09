'use client';

import React from 'react';
import { Alert } from 'antd';
import errorHandler from '../services/ErrorHandler';
import ErrorRecovery from './ErrorRecovery';

interface ErrorBoundaryProps {
  locale?: 'zh' | 'en';
  onRetry?: () => void;
  onReload?: () => void;
  onResetProgress?: () => void;
  onReturnToForm?: () => void;
  children?: React.ReactNode;
}

interface ErrorBoundaryState {
  error: Error | null;
}

class ErrorBoundary extends React.Component<ErrorBoundaryProps, ErrorBoundaryState> {
  constructor(props: ErrorBoundaryProps) {
    super(props);
    this.state = { error: null };
  }

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { error };
  }

  componentDidCatch(error: Error) {
    // 可扩展：在此处上报日志
    // console.error('ErrorBoundary caught:', error);
  }

  render(): React.ReactNode {
    const { error } = this.state;
    if (!error) return this.props.children;

    const { info, userMessage, action } = errorHandler.buildUserFacingError(error, {
      component: 'ErrorBoundary',
      action: 'render'
    }, this.props.locale);

    return (
      <div style={{ maxWidth: 600, margin: '0 auto', padding: '20px' }}>
        <Alert
          message={userMessage.title}
          description={userMessage.description}
          type="error"
          showIcon
          style={{ marginBottom: 16 }}
        />

        <ErrorRecovery
          action={action}
          onRetry={this.props.onRetry}
          onReload={this.props.onReload}
          onResetProgress={this.props.onResetProgress}
          onReturnToForm={this.props.onReturnToForm}
        />
        {/* 技术细节可选显示：info.message */}
      </div>
    );
  }
}

export default ErrorBoundary;


