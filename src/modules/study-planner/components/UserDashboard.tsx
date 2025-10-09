'use client';

import React, { useState, useEffect } from 'react';
import { Card, Row, Col, Statistic, Button, Modal, Typography, Space, Divider, Tag, App } from 'antd';
import { 
  UserOutlined, 
  BarChartOutlined, 
  GiftOutlined, 
  LogoutOutlined,
  CopyOutlined,
  ShareAltOutlined
} from '@ant-design/icons';
import { getApiBaseUrl } from '../config';
import authService, { AuthState } from '../services/authService';
import './UserDashboard.css';

const { Title, Text } = Typography;

interface UserDashboardProps {
  // 不再需要onLogout参数，直接在组件内处理退出登录
}

const UserDashboard: React.FC<UserDashboardProps> = () => {
  const { message } = App.useApp();
  const [authState, setAuthState] = useState<AuthState>(authService.getAuthState());
  const [analysisStats, setAnalysisStats] = useState<any>(null);
  const [invitationInfo, setInvitationInfo] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [showInviteModal, setShowInviteModal] = useState(false);

  useEffect(() => {
    // 监听认证状态变化
    const handleAuthStateChange = (newState: AuthState) => {
      setAuthState(newState);
    };

    authService.addListener(handleAuthStateChange);

    // 加载用户数据
    loadUserData();

    return () => {
      authService.removeListener(handleAuthStateChange);
    };
  }, []);

  const loadUserData = async () => {
    try {
      setLoading(true);
      
      // 刷新用户信息
      await authService.refreshUserInfo();
      
      // 获取分析统计
      const stats = await authService.getAnalysisStats();
      setAnalysisStats(stats);
      
      // 获取邀请信息
      const invitation = await authService.getInvitationInfo();
      setInvitationInfo(invitation);
      
    } catch (error) {
      console.error('Failed to load user data:', error);
      message.error('加载用户数据失败');
    } finally {
      setLoading(false);
    }
  };



  const copyInvitationCode = () => {
    if (invitationInfo?.invitation_code) {
      navigator.clipboard.writeText(invitationInfo.invitation_code);
      message.success('邀请码已复制到剪贴板');
    }
  };

  const shareInvitation = () => {
    if (invitationInfo?.invitation_code) {
      const shareText = `我在使用箴言留学进行个性化留学申请分析，效果很不错！使用我的邀请码 ${invitationInfo.invitation_code} 注册，我们都能获得额外的分析机会。立即体验：https://zhenyan.asia`;
      
      if (navigator.share) {
        navigator.share({
          title: '箴言留学邀请',
          text: shareText,
        });
      } else {
        navigator.clipboard.writeText(shareText);
        message.success('邀请链接已复制到剪贴板');
      }
    }
  };

  const user = authState.user;

  if (!user) {
    return null;
  }

  return (
    <div className="user-dashboard">
      <Card className="user-info-card">
        <Row gutter={[24, 24]}>
          {/* 用户基本信息 */}
          <Col xs={24} lg={8}>
            <div className="user-profile">
              <div className="user-avatar">
                <UserOutlined />
              </div>
              <div className="user-details">
                <Title level={4}>{user.phone}</Title>
                <Text type="secondary">{user.email}</Text>
                <div className="user-status">
                  <Tag color="green">已认证</Tag>
                </div>
              </div>
            </div>
          </Col>

          {/* 分析统计 */}
          <Col xs={24} lg={8}>
            <div className="stats-section">
              <Title level={5}>
                <BarChartOutlined /> 分析统计
              </Title>
              <Row gutter={16}>
                <Col span={12}>
                  <Statistic
                    title="剩余次数"
                    value={analysisStats?.remaining_analyses || user.remaining_analyses}
                    valueStyle={{ color: '#3f8600' }}
                  />
                </Col>
                <Col span={12}>
                  <Statistic
                    title="已使用"
                    value={analysisStats?.total_analyses_used || user.total_analyses_used}
                    valueStyle={{ color: '#cf1322' }}
                  />
                </Col>
              </Row>
            </div>
          </Col>

          {/* 邀请统计 */}
          <Col xs={24} lg={8}>
            <div className="invitation-section">
              <Title level={5}>
                <GiftOutlined /> 邀请奖励
              </Title>
              <Row gutter={16}>
                <Col span={12}>
                  <Statistic
                    title="邀请人数"
                    value={invitationInfo?.invited_count || user.invited_count}
                    valueStyle={{ color: '#1890ff' }}
                  />
                </Col>
                <Col span={12}>
                  <Statistic
                    title="获得次数"
                    value={invitationInfo?.total_rewards || (user.invited_count * 3)}
                    valueStyle={{ color: '#722ed1' }}
                  />
                </Col>
              </Row>
            </div>
          </Col>
        </Row>

        <Divider />

        {/* 操作按钮 */}
        <Row gutter={16} justify="space-between" align="middle">
          <Col>
            <Space>
              <Button 
                type="primary" 
                icon={<GiftOutlined />}
                onClick={() => setShowInviteModal(true)}
              >
                邀请好友
              </Button>
              <Button 
                onClick={loadUserData}
                loading={loading}
              >
                刷新数据
              </Button>
            </Space>
          </Col>
          <Col>
            <Button
              danger
              icon={<LogoutOutlined />}
              onClick={async () => {
                console.log('退出登录按钮被点击');
                try {
                  // 直接调用后端API
                  const response = await fetch(`${getApiBaseUrl()}/api/auth/logout`, {
                    method: 'POST',
                    headers: {
                      'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
                      'Content-Type': 'application/json'
                    }
                  });

                  if (response.ok) {
                    console.log('后端退出登录成功');
                  }

                  // 清除本地存储
                  localStorage.removeItem('access_token');
                  localStorage.removeItem('user_info');
                  console.log('本地存储已清除');

                  // 显示成功消息
                  message.success('已退出登录');

                  // 强制刷新页面回到登录状态
                  setTimeout(() => {
                    window.location.reload();
                  }, 500);

                } catch (error) {
                  console.error('退出登录失败:', error);
                  // 即使API调用失败，也要清除本地状态
                  localStorage.removeItem('access_token');
                  localStorage.removeItem('user_info');
                  message.success('已退出登录');
                  setTimeout(() => {
                    window.location.reload();
                  }, 500);
                }
              }}
            >
              退出登录
            </Button>
          </Col>
        </Row>
      </Card>

      {/* 邀请模态框 */}
      <Modal
        title="邀请好友获得更多分析机会"
        open={showInviteModal}
        onCancel={() => setShowInviteModal(false)}
        footer={null}
        width={500}
      >
        <div className="invite-modal-content">
          <div className="invite-code-section">
            <Title level={4}>您的邀请码</Title>
            <div className="invite-code-display">
              <Text code className="invite-code">
                {invitationInfo?.invitation_code || user.invitation_code}
              </Text>
              <Button 
                type="primary" 
                icon={<CopyOutlined />}
                onClick={copyInvitationCode}
                size="small"
              >
                复制
              </Button>
            </div>
          </div>

          <Divider />

          <div className="invite-rules">
            <Title level={5}>邀请规则</Title>
            <ul>
              <li>每成功邀请一位新用户注册，您将获得 <strong>3次</strong> 额外分析机会</li>
              <li>被邀请用户也将获得初始的 <strong>3次</strong> 分析机会</li>
              <li>邀请码永久有效，可重复使用</li>
              <li>新用户在注册时输入您的邀请码即可</li>
            </ul>
          </div>

          <Divider />

          <div className="invite-stats">
            <Row gutter={16}>
              <Col span={8}>
                <Statistic
                  title="已邀请"
                  value={invitationInfo?.invited_count || user.invited_count}
                  suffix="人"
                />
              </Col>
              <Col span={8}>
                <Statistic
                  title="获得奖励"
                  value={invitationInfo?.total_rewards || (user.invited_count * 3)}
                  suffix="次"
                />
              </Col>
              <Col span={8}>
                <Statistic
                  title="单次奖励"
                  value={3}
                  suffix="次"
                />
              </Col>
            </Row>
          </div>

          <div className="invite-actions">
            <Button 
              type="primary" 
              icon={<ShareAltOutlined />}
              onClick={shareInvitation}
              block
              size="large"
            >
              分享邀请链接
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  );
};

export default UserDashboard;
