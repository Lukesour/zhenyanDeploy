'use client';

import React from 'react';
import { Button, Space } from 'antd';
import type { RecoveryAction } from '../services/ErrorHandler';

interface ErrorRecoveryProps {
  action: RecoveryAction;
  onRetry?: () => void;
  onReload?: () => void;
  onResetProgress?: () => void;
  onReturnToForm?: () => void;
}

const ErrorRecovery: React.FC<ErrorRecoveryProps> = ({
  action,
  onRetry,
  onReload,
  onResetProgress,
  onReturnToForm
}) => {
  const buttons: React.ReactNode[] = [];

  // 推荐动作优先显示
  switch (action) {
    case 'retry':
      if (onRetry) buttons.push(<Button key="retry" type="primary" onClick={onRetry}>重试</Button>);
      break;
    case 'reload':
      if (onReload) buttons.push(<Button key="reload" type="primary" onClick={onReload}>刷新页面</Button>);
      break;
    case 'resetProgress':
      if (onResetProgress) buttons.push(<Button key="reset" type="primary" onClick={onResetProgress}>重新开始</Button>);
      break;
    case 'returnToForm':
      if (onReturnToForm) buttons.push(<Button key="back" type="primary" onClick={onReturnToForm}>返回表单</Button>);
      break;
    default:
      break;
  }

  // 提供可选的次级动作
  if (!buttons.length) {
    if (onRetry) buttons.push(<Button key="retry" onClick={onRetry}>重试</Button>);
    if (onReturnToForm) buttons.push(<Button key="back" onClick={onReturnToForm}>返回表单</Button>);
    if (onReload) buttons.push(<Button key="reload" onClick={onReload}>刷新页面</Button>);
    if (!buttons.length) {
      buttons.push(
        <Button
          key="default-reload"
          onClick={() => {
            if (typeof window !== 'undefined' && typeof window.location?.reload === 'function') {
              window.location.reload();
            }
          }}
        >
          刷新页面
        </Button>
      );
    }
  }

  return (
    <Space>
      {buttons}
    </Space>
  );
};

export default ErrorRecovery;


