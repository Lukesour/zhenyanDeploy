'use client';

import React, { useState } from 'react';
import { Form, Input, Button, Card, Row, Col, Typography, Space, App } from 'antd';
import { WechatOutlined, CheckCircleOutlined } from '@ant-design/icons';
import './VerificationForm.css';

const { Title, Text } = Typography;

interface VerificationFormProps {
  onVerificationSuccess: () => void;
  onBackToForm: () => void;
}

// 开发者预设的验证码列表（会不断增长）
const DEVELOPER_VERIFICATION_CODES = [
  'ABC123DEF4',
  'XYZ789GHI0',
  'MNO456PQR7',
  'STU890VWX1',
  'KLM234NOP5',
  'QRS678TUV2',
  'WXY012ZAB8',
  'CDE345FGH9',
  'IJK567LMN3',
  'OPQ901RST6',
  'UVW234XYZ7',
  'ABC567DEF8',
  'GHI901JKL2',
  'MNO345PQR6',
  'STU789VWX4'
];

const VerificationForm: React.FC<VerificationFormProps> = ({
  onVerificationSuccess,
  onBackToForm
}) => {
  const { message } = App.useApp();
  const [form] = Form.useForm();
  const [isVerifying, setIsVerifying] = useState(false);
  const [verificationAttempts, setVerificationAttempts] = useState(0);
  const [showSuccessMessage, setShowSuccessMessage] = useState(false);

  // 验证码输入处理
  const handleVerification = async (values: { verificationCode: string }) => {
    const { verificationCode } = values;
    
    if (!verificationCode || verificationCode.length !== 10) {
      message.error('请输入10位验证码');
      return;
    }

    setIsVerifying(true);
    
    // 模拟验证过程
    setTimeout(() => {
      const isValidCode = DEVELOPER_VERIFICATION_CODES.includes(verificationCode.toUpperCase());
      
      if (isValidCode) {
        setShowSuccessMessage(true);
        message.success('验证码验证成功！');
        
        // 延迟跳转，让用户看到成功消息
        setTimeout(() => {
          onVerificationSuccess();
        }, 1500);
      } else {
        setVerificationAttempts(prev => prev + 1);
        message.error('验证码错误，请重新输入');
        form.setFieldsValue({ verificationCode: '' });
        
        if (verificationAttempts >= 2) {
          message.warning('验证失败次数过多，请联系客服获取正确验证码');
        }
      }
      setIsVerifying(false);
    }, 1000);
  };

  // 处理返回表单（按钮已注释，暂不使用）

  return (
    <div className="verification-container">
      <div className="verification-content">
        <Row gutter={[48, 24]} align="middle" justify="center">
          {/* 左侧：验证码输入 */}
          <Col xs={24} lg={12}>
            <Card className="verification-card">
              <div className="verification-header">
                {/* <Button 
                  type="text" 
                  icon={<ArrowLeftOutlined />} 
                  onClick={handleBackToForm}
                  className="back-button"
                >
                  返回修改
                </Button> */}
                <Title level={3} className="verification-title">
                  为避免滥用，以及不良中介未经允许利用本网站进行牟利
                </Title>
                <Title level={3} className="verification-title">
                  请关注公众号，免费、自动获取验证码
                </Title>                
                <Text type="secondary" className="verification-subtitle">
                  请输入验证码以开始分析
                </Text>
              </div>

              <Form
                form={form}
                onFinish={handleVerification}
                layout="vertical"
                className="verification-form"
              >
                <Form.Item
                  name="verificationCode"
                  label="验证码"
                  rules={[
                    { required: true, message: '请输入验证码' },
                    { len: 10, message: '验证码必须是10位' }
                  ]}
                >
                  <Input
                    placeholder="请输入验证码"
                    size="large"
                    maxLength={10}
                    className="verification-input"
                    autoFocus
                  />
                </Form.Item>

                <Form.Item>
                  <Button
                    type="primary"
                    htmlType="submit"
                    size="large"
                    loading={isVerifying}
                    className="verify-button"
                    block
                  >
                    {isVerifying ? '验证中...' : '验证并开始分析'}
                  </Button>
                </Form.Item>
              </Form>

              {showSuccessMessage && (
                <div className="success-message">
                  <CheckCircleOutlined className="success-icon" />
                  <Text strong>验证成功！正在跳转...</Text>
                </div>
              )}

              <div className="verification-tips">
                <Text type="secondary">
                  <ul>
                    <li>如遇问题，请联系客服获取最新验证码</li>
                  </ul>
                </Text>
              </div>
            </Card>
          </Col>

          {/* 右侧：客服微信引导 */}
          <Col xs={24} lg={12}>
            <Card className="wechat-card">
              <div className="wechat-content">
                <div className="wechat-header">
                  <WechatOutlined className="wechat-icon" />
                  <Title level={4} className="wechat-title">
                    关注公众号，自动获取验证码
                  </Title>
                  <Text type="secondary" className="wechat-subtitle">
                    免费、自动获取验证码
                  </Text>
                </div>

                <div className="wechat-image-container">
                  <div className="wechat-qr-container">
                    <img 
                      src="/wechat-qr.jpg" 
                      alt="客服微信二维码" 
                      className="wechat-qr-image"
                    />
                    <Text className="qr-caption">扫描二维码添加公众号</Text>
                  </div>
                </div>

                <div className="wechat-info">
                  <Space direction="vertical" size="small" className="wechat-details">
                    <Text strong>公众号名称：</Text>
                    <Text copyable className="wechat-id">箴言留学</Text>

                    <Text strong>客服微信号1：</Text>
                    <Text copyable className="wechat-id">Godeternitys</Text>

                    <Text strong>客服微信号2：</Text>
                    <Text copyable className="wechat-id">MalachiSuan</Text>

                    <Text strong>客服服务时间：</Text>
                    <Text>周一至周日 9:00-21:00</Text>
                    

                  </Space>
                </div>

                {/* <div className="wechat-actions">
                  <Button 
                    type="primary" 
                    icon={<WechatOutlined />}
                    size="large"
                    className="contact-button"
                    block
                  >
                    联系客服获取验证码
                  </Button>
                </div> */}
              </div>
            </Card>
          </Col>
        </Row>
      </div>
    </div>
  );
};

export default VerificationForm;
