'use client';

import React, { useEffect, useState } from 'react';
import { Form, Input, Button, Card, Row, Col, Typography, Space, Tabs, Divider, App } from 'antd';
import { MailOutlined, PhoneOutlined, SafetyOutlined, GiftOutlined } from '@ant-design/icons';

import { UserBackground } from '../services/api';
import { getApiBaseUrl } from '../config';
import authService from '../services/authService';
import './AuthForm.css';

const { Title, Text } = Typography;

interface AuthFormProps {
  onAuthSuccess: (userInfo: any, userBackground?: UserBackground | null) => void | Promise<void>;
  onBackToForm?: () => void;
  userBackground?: UserBackground | null; // 添加用户背景数据，用于注册时保存
  initialTab?: 'login' | 'register';
}

interface UserInfo {
  id: number;
  phone: string;
  email: string;
  status: string;
  remaining_analyses: number;
  total_analyses_used: number;
  invitation_code: string;
  invited_count: number;
  created_at: string;
  last_login_at?: string;
  profile_data?: any;
}

interface LoginResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
  user_info: UserInfo;
}

const AuthForm: React.FC<AuthFormProps> = ({
  onAuthSuccess,
  onBackToForm,
  userBackground,
  initialTab = 'login'
}) => {
  const { message } = App.useApp();
  const [loginForm] = Form.useForm();
  const [registerForm] = Form.useForm();
  const [activeTab, setActiveTab] = useState<'login' | 'register'>(initialTab);
  const [isLoading, setIsLoading] = useState(false);
  const [isCodeSent, setIsCodeSent] = useState(false);
  const [countdown, setCountdown] = useState(0);

  useEffect(() => {
    setActiveTab(initialTab);
  }, [initialTab]);

  // 发送验证码
  const sendVerificationCode = async (email: string, phone: string) => {
    try {
      const response = await fetch(`${getApiBaseUrl()}/api/auth/send-verification-code`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          email,
          phone
        }),
      });

      const data = await response.json();

      if (response.ok) {
        message.success('验证码已发送到您的邮箱，请查收');
        setIsCodeSent(true);
        startCountdown();
        return true;
      } else {
        message.error(data.detail || '发送验证码失败');
        return false;
      }
    } catch (_error) {
      message.error('网络错误，请稍后重试');
      return false;
    }
  };

  // 倒计时
  const startCountdown = () => {
    setCountdown(60);
    const timer = setInterval(() => {
      setCountdown((prev) => {
        if (prev <= 1) {
          clearInterval(timer);
          setIsCodeSent(false);
          return 0;
        }
        return prev - 1;
      });
    }, 1000);
  };

  // 用户注册
  const handleRegister = async (values: any) => {
    try {
      setIsLoading(true);

      const response = await fetch(`${getApiBaseUrl()}/api/auth/register`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          phone: values.phone,
          email: values.email,
          verification_code: values.verification_code,
          invitation_code: values.invitation_code || null,
          profile_data: userBackground || null, // 添加个人信息数据
        }),
      });

      if (response.ok) {
        const data: LoginResponse = await response.json();
        message.success('注册成功！欢迎使用箴言留学');

        // 使用authService设置认证状态，这会同时更新localStorage和内部状态
        authService.setAuthState(data);

        // 等待一小段时间确保状态更新完成，然后调用成功回调
        setTimeout(() => {
          onAuthSuccess(data.user_info, userBackground);
        }, 100);
      } else {
        const errorData = await response.json();
        message.error(errorData.detail || '注册失败');
      }
    } catch (_error) {
      message.error('网络错误，请稍后重试');
    } finally {
      setIsLoading(false);
    }
  };

  // 用户登录
  const handleLogin = async (values: any) => {
    try {
      setIsLoading(true);

      const response = await fetch(`${getApiBaseUrl()}/api/auth/login`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          phone: values.phone,
          email: values.email,
          verification_code: values.verification_code,
          profile_data: userBackground || null, // 添加个人信息数据，用于自动创建账户时保存
        }),
      });

      if (response.ok) {
        const data: LoginResponse = await response.json();

        // 检查是否是新创建的用户
        if ((data as any).is_new_user) {
          message.success('欢迎！已为您自动创建账户并登录成功！', 6);
        } else {
          message.success('登录成功！');
        }

        // 使用authService设置认证状态，这会同时更新localStorage和内部状态
        authService.setAuthState(data);

        // 等待一小段时间确保状态更新完成，然后调用成功回调
        setTimeout(() => {
          onAuthSuccess(data.user_info, userBackground);
        }, 100);
      } else {
        const errorData = await response.json();
        console.log('登录错误响应:', errorData); // 添加调试日志

        // 获取错误信息，支持多种响应格式
        const errorMessage = errorData.detail || errorData.message || '登录失败';

        message.error(errorMessage);
      }
    } catch (_error) {
      message.error('网络错误，请稍后重试');
    } finally {
      setIsLoading(false);
    }
  };



  // 发送验证码按钮点击
  const handleSendCode = async () => {
    try {
      if (activeTab === 'register') {
        const values = await registerForm.validateFields(['email', 'phone']);
        await sendVerificationCode(values.email, values.phone);
      } else {
        const values = await loginForm.validateFields(['email', 'phone']);
        await sendVerificationCode(values.email, values.phone);
      }
    } catch (_error) {
      // 表单验证失败
    }
  };



  return (
    <div className="auth-container">
      <div className="auth-content">
        <Row gutter={[48, 24]} align="middle" justify="center">
          {/* 左侧：客服信息 */}
          <Col xs={24} lg={12}>
            <Card className="contact-card">
              <div className="contact-content">
                <div className="contact-header">
                  <Title level={4} className="contact-title">
                    免费一对一定位，匹配所有的院校专业！
                  </Title>
                  <Text type="secondary" className="contact-subtitle">
                    联系我们的客服团队
                  </Text>
                </div>

                <div className="contact-image-container">
                  <div className="contact-service-container">
                    <img
                      src="/data/service.JPG"
                      alt="箴言留学客服团队"
                      className="contact-service-image"
                    />
                  </div>
                  <Text className="contact-image-caption">扫码或留言，我们随时为您服务</Text>
                </div>

                <div className="contact-details">
                  <Space direction="vertical" size="middle" style={{ width: '100%' }}>
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
                  </Space>
                </div>
              </div>
            </Card>
          </Col>

          {/* 右侧：登录注册表单 */}
          <Col xs={24} lg={12}>
            <Card className="auth-card">
              <div className="auth-header">
                <Title level={2} className="auth-title">
                  箴言留学
                </Title>
                <Text type="secondary" className="auth-subtitle">
                  请登录或注册以开始您的留学申请分析
                </Text>
              </div>

              <Tabs
                activeKey={activeTab}
                centered
                onChange={(key) => setActiveTab(key as 'login' | 'register')}
                items={[
                  {
                    key: 'login',
                    label: '登录',
                    children: (
                      <Form
                        form={loginForm}
                        onFinish={handleLogin}
                        layout="vertical"
                        className="auth-form"
                      >
                        <Form.Item
                          name="phone"
                          label="手机号"
                          rules={[
                            { required: true, message: '请输入手机号' },
                            { pattern: /^1[3-9]\d{9}$/, message: '请输入有效的手机号' }
                          ]}
                        >
                          <Input
                            prefix={<PhoneOutlined />}
                            placeholder="请输入手机号"
                            size="large"
                          />
                        </Form.Item>

                        <Form.Item
                          name="email"
                          label="邮箱"
                          rules={[
                            { required: true, message: '请输入邮箱' },
                            { type: 'email', message: '请输入有效的邮箱地址' }
                          ]}
                        >
                          <Input
                            prefix={<MailOutlined />}
                            placeholder="请输入注册时使用的邮箱"
                            size="large"
                          />
                        </Form.Item>

                        <Form.Item
                          name="verification_code"
                          label="邮箱验证码"
                          rules={[
                            { required: true, message: '请输入验证码' },
                            { len: 6, message: '验证码为6位数字' }
                          ]}
                        >
                          <Input
                            prefix={<SafetyOutlined />}
                            placeholder="请输入邮箱验证码"
                            size="large"
                            maxLength={6}
                            suffix={
                              <Button
                                type="link"
                                size="small"
                                onClick={handleSendCode}
                                disabled={isCodeSent}
                              >
                                {isCodeSent ? `${countdown}s后重发` : '发送验证码'}
                              </Button>
                            }
                          />
                        </Form.Item>

                        <Form.Item>
                          <Button
                            type="primary"
                            htmlType="submit"
                            size="large"
                            loading={isLoading}
                            block
                          >
                            登录
                          </Button>
                        </Form.Item>
                      </Form>
                    ),
                  },
                  {
                    key: 'register',
                    label: '注册',
                    children: (
                      <Form
                        form={registerForm}
                        onFinish={handleRegister}
                        layout="vertical"
                        className="auth-form"
                      >
                        <Form.Item
                          name="phone"
                          label="手机号"
                          rules={[
                            { required: true, message: '请输入手机号' },
                            { pattern: /^1[3-9]\d{9}$/, message: '请输入有效的手机号' }
                          ]}
                        >
                          <Input
                            prefix={<PhoneOutlined />}
                            placeholder="请输入手机号"
                            size="large"
                          />
                        </Form.Item>

                        <Form.Item
                          name="email"
                          label="邮箱"
                          rules={[
                            { required: true, message: '请输入邮箱' },
                            { type: 'email', message: '请输入有效的邮箱地址' }
                          ]}
                        >
                          <Input
                            prefix={<MailOutlined />}
                            placeholder="请输入邮箱地址"
                            size="large"
                          />
                        </Form.Item>

                        <Form.Item
                          name="verification_code"
                          label="邮箱验证码"
                          rules={[
                            { required: true, message: '请输入验证码' },
                            { len: 6, message: '验证码为6位数字' }
                          ]}
                        >
                          <Input
                            prefix={<SafetyOutlined />}
                            placeholder="请输入邮箱验证码"
                            size="large"
                            maxLength={6}
                            suffix={
                              <Button
                                type="link"
                                size="small"
                                onClick={handleSendCode}
                                disabled={isCodeSent}
                              >
                                {isCodeSent ? `${countdown}s后重发` : '发送验证码'}
                              </Button>
                            }
                          />
                        </Form.Item>

                        <Form.Item
                          name="invitation_code"
                          label="邀请码（可选）"
                        >
                          <Input
                            prefix={<GiftOutlined />}
                            placeholder="输入邀请码可获得额外分析机会"
                            size="large"
                          />
                        </Form.Item>

                        <Form.Item>
                          <Button
                            type="primary"
                            htmlType="submit"
                            size="large"
                            loading={isLoading}
                            block
                          >
                            注册
                          </Button>
                        </Form.Item>
                      </Form>
                    ),
                  },
                ]}
              />

              <Divider />

              <div className="auth-tips">
                <Text type="secondary">
                  <ul>
                    <li>注册即可获得3次免费分析机会</li>
                    <li>每邀请一位新用户注册，您将获得3次额外分析机会</li>
                    <li>如遇问题，请联系客服获取帮助</li>
                  </ul>
                </Text>
              </div>
            </Card>
          </Col>
        </Row>
      </div>
    </div>
  );
};

export default AuthForm;
