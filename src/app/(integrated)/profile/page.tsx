'use client';

import { useCallback, useEffect, useMemo, useState } from 'react';
import Link from 'next/link';
import Image from 'next/image';
import {
  ConfigProvider,
  App as AntdApp,
  Card,
  Row,
  Col,
  Typography,
  Space,
  Button,
  Alert,
  Form,
  InputNumber,
  Input,
  message,
} from 'antd';
import zhCN from 'antd/locale/zh_CN';

import UserDashboard from '@/modules/study-planner/components/UserDashboard';
import authService, { type AuthState as PlannerAuthState } from '@/modules/study-planner/services/authService';
import apiService from '@/modules/study-planner/services/api';
import errorHandler from '@/modules/study-planner/services/ErrorHandler';
import { useAuthStore } from '@/lib/store';
import { authAPI } from '@/lib/api';

const { Title, Text } = Typography;

const themeTokens = {
  token: {
    colorPrimary: '#4f46e5',
    colorInfo: '#4f46e5',
    colorSuccess: '#059669',
    colorWarning: '#d97706',
    colorError: '#dc2626',
    borderRadius: 12,
    fontSize: 14,
    fontFamily: 'var(--font-geist-sans)',
    controlHeight: 42,
    colorBgLayout: '#f5f7ff',
  },
  components: {
    Card: {
      borderRadiusLG: 16,
      paddingLG: 24,
      boxShadow:
        '0 12px 32px rgba(79, 70, 229, 0.08), 0 4px 16px rgba(79, 70, 229, 0.04)',
      colorBorderSecondary: '#e0e7ff',
    },
    Button: {
      borderRadius: 999,
      controlHeight: 44,
      paddingInline: 20,
      controlHeightLG: 52,
    },
    Statistic: {
      titleFontSize: 14,
      titleFontWeight: 500,
      contentFontSize: 28,
    },
  },
};

interface IELTSProfileFormValues {
  target_score?: number;
  current_level?: number;
  exam_date?: string;
}

export default function ProfilePage() {
  const [plannerAuthState, setPlannerAuthState] = useState<PlannerAuthState>(authService.getAuthState());
  const essayUser = useAuthStore((state) => state.user);
  const essayIsAuthenticated = useAuthStore((state) => state.isAuthenticated);
  const setEssayUser = useAuthStore((state) => state.setUser);
  const [form] = Form.useForm<IELTSProfileFormValues>();
  const [isClient, setIsClient] = useState(false);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [refreshError, setRefreshError] = useState<string | null>(null);
  const [isSaving, setIsSaving] = useState(false);

  useEffect(() => {
    setIsClient(true);
  }, []);

  useEffect(() => {
    const handleAuthChange = (nextState: PlannerAuthState) => {
      setPlannerAuthState(nextState);
    };

    authService.addListener(handleAuthChange);
    return () => {
      authService.removeListener(handleAuthChange);
    };
  }, []);

  const refreshProfile = useCallback(async () => {
    if (!plannerAuthState.isAuthenticated) {
      return;
    }

    setIsRefreshing(true);
    try {
      const ok = await authService.refreshUserInfo();
      if (!ok) {
        setRefreshError('无法刷新个人信息，请稍后重试');
      } else {
        setRefreshError(null);
      }
    } catch (error) {
      console.error('Failed to refresh profile info:', error);
      setRefreshError('无法刷新个人信息，请稍后重试');
    } finally {
      setIsRefreshing(false);
    }
  }, [plannerAuthState.isAuthenticated]);

  useEffect(() => {
    refreshProfile();
  }, [refreshProfile]);

  const showProfileContent = plannerAuthState.isAuthenticated || essayIsAuthenticated;

  const initialIeltsFormValues = useMemo<IELTSProfileFormValues>(() => {
    return {
      target_score:
        typeof essayUser?.target_score === 'number' ? essayUser.target_score : undefined,
      current_level:
        typeof essayUser?.current_level === 'number' ? essayUser.current_level : undefined,
      exam_date: essayUser?.exam_date ? essayUser.exam_date.slice(0, 10) : undefined,
    };
  }, [essayUser]);

  useEffect(() => {
    form.setFieldsValue(initialIeltsFormValues);
  }, [form, initialIeltsFormValues]);

  const handleIeltsProfileSubmit = async (values: IELTSProfileFormValues) => {
    if (!essayIsAuthenticated) {
      message.error('请先登录后再更新雅思信息');
      return;
    }

    const payload: IELTSProfileFormValues = {
      target_score:
        typeof values.target_score === 'number' ? values.target_score : undefined,
      current_level:
        typeof values.current_level === 'number' ? values.current_level : undefined,
      exam_date: values.exam_date || undefined,
    };

    setIsSaving(true);
    try {
      const updatedEssayUser = await authAPI.updateProfile({
        target_score: payload.target_score,
        current_level: payload.current_level,
        exam_date: payload.exam_date,
      });

      setEssayUser(updatedEssayUser);

      let plannerSyncSucceeded = false;

      if (authService.isAuthenticated()) {
        try {
          const supabasePayload = {
            target_score: payload.target_score ?? null,
            current_level: payload.current_level ?? null,
            exam_date: payload.exam_date ?? null,
            language_target_total_score: payload.target_score ?? null,
            language_total_score: payload.current_level ?? null,
            language_expected_test_date: payload.exam_date ?? null,
          };

          const updatedPlannerUser = await apiService.saveUserProfile(supabasePayload);
          authService.updateUserInfo(updatedPlannerUser);
          plannerSyncSucceeded = true;
        } catch (syncError) {
          const { userMessage } = errorHandler.buildUserFacingError(syncError, {
            component: 'ProfilePage',
            action: 'saveIeltsProfile',
            userData: payload,
          });
          message.warning(`已更新雅思账号，但同步到留学档案失败：${userMessage.title}`);
        }
      }

      if (!plannerSyncSucceeded) {
        const plannerUser = authService.getCurrentUser();
        if (plannerUser) {
          const mergedProfileData = {
            ...(plannerUser.profile_data ?? {}),
            target_score: payload.target_score ?? null,
            current_level: payload.current_level ?? null,
            exam_date: payload.exam_date ?? null,
            language_target_total_score: payload.target_score ?? null,
            language_total_score: payload.current_level ?? null,
            language_expected_test_date: payload.exam_date ?? null,
          };
          authService.updateUserInfo({
            profile_data: mergedProfileData,
          });
        }
      }

      message.success('雅思作文批改信息已更新');
    } catch (error: unknown) {
      console.error('Failed to update IELTS profile:', error);
      const apiMessage =
        (error as { response?: { data?: { detail?: string } } })?.response?.data?.detail ||
        (error as { message?: string })?.message ||
        '更新失败，请稍后重试';
      message.error(apiMessage);
    } finally {
      setIsSaving(false);
    }
  };

  const handleClearIeltsProfile = () => {
    form.setFieldsValue({
      target_score: undefined,
      current_level: undefined,
      exam_date: undefined,
    });
  };

  return (
    <ConfigProvider locale={zhCN} theme={themeTokens}>
      <AntdApp>
        <div className="min-h-screen bg-gradient-to-br from-indigo-100 via-white to-slate-50 py-12">
          <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 space-y-8">
            <header className="text-center space-y-4">
              <span className="inline-flex items-center rounded-full bg-indigo-100 px-4 py-1 text-sm font-medium text-indigo-600 shadow-sm">
                账户与个人信息
              </span>
              <h1 className="text-3xl sm:text-4xl font-bold text-slate-900">
                个人中心
              </h1>
              <p className="max-w-3xl mx-auto text-base sm:text-lg text-slate-600">
                查看或管理您的账户资料、分析次数以及雅思作文批改设置。
              </p>
            </header>

            {!isClient && (
              <Card>
                <Text>加载中...</Text>
              </Card>
            )}

            {isClient && !showProfileContent && (
              <Card className="border border-indigo-50 bg-white/90 backdrop-blur shadow-none text-center space-y-4">
                <Title level={4}>请先登录后再查看个人信息</Title>
                <Text type="secondary">
                  登录或注册后，可查看留学规划与雅思批改相关的个人资料与统计信息。
                </Text>
                <Space size="middle" style={{ marginTop: 16 }}>
                  <Link href="/auth?mode=login&redirect=/profile">
                    <Button type="primary">登录</Button>
                  </Link>
                  <Link href="/auth?mode=register&redirect=/profile">
                    <Button type="default">注册新账号</Button>
                  </Link>
                </Space>
              </Card>
            )}

            {isClient && showProfileContent && (
              <div className="space-y-6">
                {refreshError && (
                  <Alert
                    type="warning"
                    showIcon
                    message={refreshError}
                    action={
                      <Button type="link" onClick={refreshProfile} loading={isRefreshing}>
                        重新尝试
                      </Button>
                    }
                  />
                )}

                <UserDashboard />

                <Card
                  title={
                    <Space direction="vertical" size={2}>
                      <Title level={5} style={{ margin: 0 }}>
                        雅思作文批改信息
                      </Title>
                      <Text type="secondary">
                        在此设置目标分数、当前水平与考试时间，方便系统输出更贴合的批改建议。
                      </Text>
                    </Space>
                  }
                  className="border border-indigo-50/70 bg-white/90 backdrop-blur shadow-none"
                  extra={
                    <Link href="/ielts/dashboard" className="text-indigo-600 text-sm font-medium">
                      前往雅思作文批改
                    </Link>
                  }
                >
                  <Form
                    layout="vertical"
                    form={form}
                    initialValues={initialIeltsFormValues}
                    onFinish={handleIeltsProfileSubmit}
                  >
                    <Row gutter={[24, 24]}>
                      <Col xs={24} md={8}>
                        <Form.Item
                          label="目标分数"
                          name="target_score"
                          tooltip="用于设定期望达到的 IELTS 写作总分，可输入 0-9 的分数，支持 0.5 间隔。"
                          rules={[
                            {
                              type: 'number',
                              min: 0,
                              max: 9,
                              message: '目标分数需在 0 - 9 之间',
                            },
                          ]}
                        >
                          <InputNumber
                            min={0}
                            max={9}
                            step={0.5}
                            precision={1}
                            placeholder="未设置"
                            style={{ width: '100%' }}
                          />
                        </Form.Item>
                      </Col>
                      <Col xs={24} md={8}>
                        <Form.Item
                          label="当前水平"
                          name="current_level"
                          tooltip="填写最近一次考试或模拟测评成绩，便于系统评估差距。"
                          rules={[
                            {
                              type: 'number',
                              min: 0,
                              max: 9,
                              message: '当前水平需在 0 - 9 之间',
                            },
                          ]}
                        >
                          <InputNumber
                            min={0}
                            max={9}
                            step={0.5}
                            precision={1}
                            placeholder="未设置"
                            style={{ width: '100%' }}
                          />
                        </Form.Item>
                      </Col>
                      <Col xs={24} md={8}>
                        <Form.Item
                          label="考试时间"
                          name="exam_date"
                          tooltip="选择计划参加考试的日期，可用于反推学习节奏。"
                        >
                          <Input type="date" placeholder="未设置" />
                        </Form.Item>
                      </Col>
                    </Row>

                    <Space size="middle" style={{ marginTop: 16 }}>
                      <Button type="primary" htmlType="submit" loading={isSaving}>
                        保存设置
                      </Button>
                      <Button onClick={handleClearIeltsProfile} disabled={isSaving}>
                        清空
                      </Button>
                      <Button onClick={() => form.setFieldsValue(initialIeltsFormValues)} disabled={isSaving}>
                        恢复已保存值
                      </Button>
                    </Space>

                    <Text type="secondary" style={{ display: 'block', marginTop: 16 }}>
                      保存后，雅思作文批改模块将使用这些参数定制反馈。字段留空则视为未设置。
                    </Text>
                    {isRefreshing && (
                      <Text type="secondary" style={{ display: 'block', marginTop: 8 }}>
                        正在同步最新资料...
                      </Text>
                    )}
                  </Form>
                </Card>

                <Card className="border border-indigo-50/70 bg-white/90 backdrop-blur shadow-none">
                  <div className="flex flex-col md:flex-row items-center gap-6">
                    <div className="text-center md:text-left space-y-2">
                      <Title level={4} style={{ margin: 0 }}>
                        微信客服福利
                      </Title>
                      <Text type="secondary">
                        添加微信客服免费获取 10 次使用次数、雅思保分手册、香港本土机构一对一择校定位服务等超值资料包
                      </Text>
                    </div>
                    <div className="flex-shrink-0">
                      <Image
                        src="/data/service.JPG"
                        alt="扫码添加微信客服领取资料包"
                        width={240}
                        height={240}
                        className="rounded-xl shadow-lg"
                      />
                    </div>
                  </div>
                </Card>
              </div>
            )}
          </div>
        </div>
      </AntdApp>
    </ConfigProvider>
  );
}
