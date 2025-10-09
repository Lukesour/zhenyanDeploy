'use client';

import React, { useState } from 'react';
import { Card, Input, Button, Space, Typography, Alert, Tag, Row, Col, Divider } from 'antd';
import { MailOutlined, CheckCircleOutlined, CloseCircleOutlined, WarningOutlined } from '@ant-design/icons';

const { Title, Text, Paragraph } = Typography;

interface VerificationResult {
  valid: boolean;
  result: string;
  score: number;
  regexp: boolean;
  gibberish: boolean;
  disposable: boolean;
  webmail: boolean;
  mx_records: boolean;
  smtp_server: boolean;
  smtp_check: boolean;
  accept_all: boolean;
  block: boolean;
  message: string;
}

const EmailVerificationDemo: React.FC = () => {
  const [email, setEmail] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [result, setResult] = useState<VerificationResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleVerify = async () => {
    if (!email) {
      setError('请输入邮箱地址');
      return;
    }

    setIsLoading(true);
    setError(null);
    setResult(null);

    try {
      // 这里应该调用后端API，但由于演示目的，我们模拟一些结果
      const mockResults: { [key: string]: VerificationResult } = {
        'test@example.com': {
          valid: false,
          result: 'risky',
          score: 0,
          regexp: true,
          gibberish: false,
          disposable: true,
          webmail: false,
          mx_records: false,
          smtp_server: false,
          smtp_check: false,
          accept_all: false,
          block: false,
          message: '邮箱地址存在风险 (可信度: 0%)'
        },
        'admin@yahoo.com': {
          valid: false,
          result: 'risky',
          score: 93,
          regexp: true,
          gibberish: false,
          disposable: false,
          webmail: true,
          mx_records: true,
          smtp_server: true,
          smtp_check: true,
          accept_all: false,
          block: false,
          message: '邮箱地址存在风险 (可信度: 93%)'
        },
        'fake@10minutemail.com': {
          valid: false,
          result: 'risky',
          score: 0,
          regexp: true,
          gibberish: false,
          disposable: true,
          webmail: false,
          mx_records: true,
          smtp_server: true,
          smtp_check: false,
          accept_all: false,
          block: false,
          message: '邮箱地址存在风险 (可信度: 0%)'
        }
      };

      // 模拟API延迟
      await new Promise(resolve => setTimeout(resolve, 1500));

      const mockResult = mockResults[email.toLowerCase()] || {
        valid: true,
        result: 'deliverable',
        score: 85,
        regexp: true,
        gibberish: false,
        disposable: false,
        webmail: true,
        mx_records: true,
        smtp_server: true,
        smtp_check: true,
        accept_all: false,
        block: false,
        message: '邮箱地址有效且可接收邮件'
      };

      setResult(mockResult);
    } catch (err) {
      setError('验证失败，请稍后重试');
    } finally {
      setIsLoading(false);
    }
  };

  const getResultColor = (result: string) => {
    switch (result) {
      case 'deliverable':
        return 'success';
      case 'undeliverable':
        return 'error';
      case 'risky':
        return 'warning';
      default:
        return 'default';
    }
  };

  const getResultIcon = (result: string) => {
    switch (result) {
      case 'deliverable':
        return <CheckCircleOutlined style={{ color: '#52c41a' }} />;
      case 'undeliverable':
        return <CloseCircleOutlined style={{ color: '#ff4d4f' }} />;
      case 'risky':
        return <WarningOutlined style={{ color: '#faad14' }} />;
      default:
        return null;
    }
  };

  const getScoreColor = (score: number) => {
    if (score >= 80) return '#52c41a';
    if (score >= 50) return '#faad14';
    return '#ff4d4f';
  };

  return (
    <div style={{ padding: '24px', maxWidth: '800px', margin: '0 auto' }}>
      <Card>
        <Title level={2}>🔍 Hunter.io 邮箱验证演示</Title>
        <Paragraph>
          本演示展示了集成的Hunter.io邮箱验证服务功能。该服务可以验证邮箱地址的有效性，
          检测临时邮箱和垃圾邮箱，为用户注册提供安全保障。
        </Paragraph>

        <Space direction="vertical" style={{ width: '100%' }}>
          <div>
            <Text strong>输入邮箱地址进行验证：</Text>
            <Space.Compact style={{ width: '100%', marginTop: '8px' }}>
              <Input
                prefix={<MailOutlined />}
                placeholder="请输入邮箱地址"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                onPressEnter={handleVerify}
                size="large"
              />
              <Button
                type="primary"
                onClick={handleVerify}
                loading={isLoading}
                size="large"
              >
                验证
              </Button>
            </Space.Compact>
          </div>

          <div>
            <Text type="secondary">
              试试这些示例邮箱：test@example.com, admin@yahoo.com, fake@10minutemail.com
            </Text>
          </div>

          {error && (
            <Alert
              message="验证失败"
              description={error}
              type="error"
              showIcon
            />
          )}

          {result && (
            <Card title="验证结果" style={{ marginTop: '16px' }}>
              <Row gutter={16}>
                <Col span={12}>
                  <Space direction="vertical" style={{ width: '100%' }}>
                    <div>
                      <Text strong>验证状态：</Text>
                      <div style={{ marginTop: '4px' }}>
                        {getResultIcon(result.result)}
                        <Tag color={getResultColor(result.result)} style={{ marginLeft: '8px' }}>
                          {result.result.toUpperCase()}
                        </Tag>
                      </div>
                    </div>

                    <div>
                      <Text strong>质量分数：</Text>
                      <div style={{ marginTop: '4px' }}>
                        <span style={{ 
                          fontSize: '24px', 
                          fontWeight: 'bold',
                          color: getScoreColor(result.score)
                        }}>
                          {result.score}
                        </span>
                        <span style={{ marginLeft: '4px', color: '#666' }}>/100</span>
                      </div>
                    </div>

                    <div>
                      <Text strong>验证消息：</Text>
                      <div style={{ marginTop: '4px' }}>
                        <Text type="secondary">{result.message}</Text>
                      </div>
                    </div>
                  </Space>
                </Col>

                <Col span={12}>
                  <Space direction="vertical" style={{ width: '100%' }}>
                    <div>
                      <Text strong>邮箱特征：</Text>
                      <div style={{ marginTop: '8px' }}>
                        <Space wrap>
                          {result.disposable && <Tag color="red">临时邮箱</Tag>}
                          {result.webmail && <Tag color="blue">网页邮箱</Tag>}
                          {result.gibberish && <Tag color="orange">无意义字符</Tag>}
                          {result.block && <Tag color="red">被阻止</Tag>}
                          {result.mx_records && <Tag color="green">有MX记录</Tag>}
                          {result.smtp_server && <Tag color="green">有SMTP服务器</Tag>}
                          {result.accept_all && <Tag color="yellow">接受所有邮件</Tag>}
                        </Space>
                      </div>
                    </div>

                    <div>
                      <Text strong>技术检查：</Text>
                      <div style={{ marginTop: '8px' }}>
                        <Space direction="vertical" size="small">
                          <div>
                            <Text>正则表达式：</Text>
                            <Tag color={result.regexp ? 'success' : 'error'}>
                              {result.regexp ? '通过' : '失败'}
                            </Tag>
                          </div>
                          <div>
                            <Text>SMTP检查：</Text>
                            <Tag color={result.smtp_check ? 'success' : 'error'}>
                              {result.smtp_check ? '通过' : '失败'}
                            </Tag>
                          </div>
                        </Space>
                      </div>
                    </div>
                  </Space>
                </Col>
              </Row>

              <Divider />

              <Alert
                message="安全提示"
                description={
                  result.disposable || result.score < 30
                    ? "此邮箱存在风险，建议用户使用其他邮箱地址注册。"
                    : result.score < 70
                    ? "此邮箱质量一般，可以注册但建议提醒用户确认邮箱地址。"
                    : "此邮箱质量良好，可以安全用于注册。"
                }
                type={
                  result.disposable || result.score < 30
                    ? "error"
                    : result.score < 70
                    ? "warning"
                    : "success"
                }
                showIcon
              />
            </Card>
          )}
        </Space>
      </Card>
    </div>
  );
};

export default EmailVerificationDemo;
