'use client';

import { useCallback, useEffect, useState } from 'react';
import { ConfigProvider, App as AntdApp, message } from 'antd';
import zhCN from 'antd/locale/zh_CN';

import UserForm from '@/modules/study-planner/components/UserForm';
import AnalysisReport from '@/modules/study-planner/components/AnalysisReport';
import ProgressDisplay from '@/modules/study-planner/components/ProgressDisplay';
import ErrorDisplay from '@/modules/study-planner/components/ErrorDisplay';
import SystemTest from '@/modules/study-planner/components/SystemTest';
import EmailVerificationDemo from '@/modules/study-planner/components/EmailVerificationDemo';
import DebugPanel from '@/modules/study-planner/components/DebugPanel';
import SchoolMajorList from '@/modules/study-planner/components/SchoolMajorList';
import MajorDetail from '@/modules/study-planner/components/MajorDetail';
import MainNavigation from '@/modules/study-planner/components/MainNavigation';
import AuthForm from '@/modules/study-planner/components/AuthForm';
import authService, { AuthState } from '@/modules/study-planner/services/authService';
import apiService, {
  UserBackground,
  AnalysisReport as AnalysisReportType,
} from '@/modules/study-planner/services/api';
import errorHandler from '@/modules/study-planner/services/ErrorHandler';

type Step =
  | 'auth'
  | 'form'
  | 'progress'
  | 'report'
  | 'error'
  | 'school-majors'
  | 'major-detail';

interface AppStateData {
  currentStep: Step;
  analysisReport: AnalysisReportType | null;
  isLoading: boolean;
  isProgressActive: boolean;
  errorMessage: string;
  userBackground: UserBackground | null;
  authState: AuthState;
  selectedSchool: string | null;
  selectedMajorId: string | null;
}

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
    Tabs: {
      inkBarColor: '#4f46e5',
      itemSelectedColor: '#4f46e5',
      itemHoverColor: '#4338ca',
      titleFontSize: 16,
      horizontalItemGutter: 20,
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

const PENDING_BACKGROUND_KEY = 'planner:pendingBackground';

export default function StudyPlannerPage() {
  const [queryState, setQueryState] = useState({
    resume: null as string | null,
    test: false,
    emailDemo: false,
    debug: false,
  });

  const [isClient, setIsClient] = useState(false);

  const [appState, setAppState] = useState<AppStateData>({
    currentStep: 'form',
    analysisReport: null,
    isLoading: false,
    isProgressActive: false,
    errorMessage: '',
    userBackground: null,
    authState: authService.getAuthState(),
    selectedSchool: null,
    selectedMajorId: null,
  });

  const updateAppState = useCallback((updates: Partial<AppStateData>) => {
    setAppState((prev) => ({ ...prev, ...updates }));
  }, []);

  useEffect(() => {
    setIsClient(true);
  }, []);

  useEffect(() => {
    if (typeof window === 'undefined') {
      return;
    }

    const params = new URLSearchParams(window.location.search);
    setQueryState({
      resume: params.get('resume'),
      test: params.get('test') === 'true',
      emailDemo: params.get('email-demo') === 'true',
      debug: params.get('debug') === 'true',
    });
  }, []);

  useEffect(() => {
    const handleAuthStateChange = (newAuthState: AuthState) => {
      setAppState((prev) => {
        if (prev.currentStep === 'progress' || prev.currentStep === 'report') {
          return { ...prev, authState: newAuthState };
        }

        return {
          ...prev,
          authState: newAuthState,
        };
      });
    };

    authService.addListener(handleAuthStateChange);
    const initialAuthState = authService.getAuthState();
    updateAppState({
      authState: initialAuthState,
      currentStep: 'form',
    });

    return () => {
      authService.removeListener(handleAuthStateChange);
    };
  }, [updateAppState]);

  useEffect(() => {
    if (appState.currentStep === 'progress' && !appState.userBackground) {
      updateAppState({ currentStep: 'form' });
    }
  }, [appState.currentStep, appState.userBackground, updateAppState]);

  useEffect(() => {
    if (!appState.authState.isAuthenticated) {
      return;
    }

    if (queryState.resume !== 'analysis') {
      return;
    }

    if (typeof window === 'undefined') {
      return;
    }

    const rawBackground = window.sessionStorage.getItem(PENDING_BACKGROUND_KEY);
    if (!rawBackground) {
      setQueryState((prev) => ({ ...prev, resume: null }));
      const { pathname, hash } = window.location;
      window.history.replaceState(null, '', hash ? `${pathname}${hash}` : pathname);
      return;
    }

    try {
      const parsedBackground = JSON.parse(rawBackground) as UserBackground;
      window.sessionStorage.removeItem(PENDING_BACKGROUND_KEY);
      updateAppState({
        userBackground: parsedBackground,
        currentStep: 'progress',
        isProgressActive: true,
        isLoading: true,
        errorMessage: '',
      });
    } catch {
      window.sessionStorage.removeItem(PENDING_BACKGROUND_KEY);
    } finally {
      setQueryState((prev) => ({ ...prev, resume: null }));
      if (typeof window !== 'undefined') {
        const { pathname, hash } = window.location;
        window.history.replaceState(null, '', hash ? `${pathname}${hash}` : pathname);
      }
    }
  }, [appState.authState.isAuthenticated, queryState.resume, updateAppState]);

  const handleFormSubmit = useCallback(
    (userBackground: UserBackground) => {
      if (!appState.authState.isAuthenticated) {
        if (typeof window !== 'undefined') {
          try {
            window.sessionStorage.setItem(
              PENDING_BACKGROUND_KEY,
              JSON.stringify(userBackground)
            );
          } catch (error) {
            console.warn('Failed to persist pending background:', error);
          }
        }

        updateAppState({
          currentStep: 'auth',
          userBackground,
          errorMessage: '',
        });
        return;
      }

      updateAppState({
        userBackground,
        isLoading: true,
        currentStep: 'progress',
        isProgressActive: true,
      });
    },
    [appState.authState.isAuthenticated, updateAppState]
  );

  const handleAuthSuccess = useCallback(
    async (_userInfo: any, passedUserBackground?: UserBackground | null) => {
      let newAuthState = authService.getAuthState();

      let background: UserBackground | null =
        passedUserBackground ?? appState.userBackground;

      if (!background && typeof window !== 'undefined') {
        const rawBackground = window.sessionStorage.getItem(PENDING_BACKGROUND_KEY);
        if (rawBackground) {
          try {
            background = JSON.parse(rawBackground) as UserBackground;
          } catch {
            background = null;
          }
        }
      }

      if (background) {
        try {
          const updatedUser = await apiService.saveUserProfile(background);
          authService.updateUserInfo(updatedUser);
          newAuthState = authService.getAuthState();
          message.success('个人信息已保存');
        } catch (error) {
          const { userMessage } = errorHandler.buildUserFacingError(error, {
            component: 'StudyPlannerPage',
            action: 'saveProfileAfterAuth',
            userData: background,
          });
          message.error(userMessage.title);
          updateAppState({
            currentStep: 'form',
            authState: newAuthState,
            isLoading: false,
            isProgressActive: false,
            errorMessage: userMessage.title,
          });
          return;
        }

        if (typeof window !== 'undefined') {
          window.sessionStorage.removeItem(PENDING_BACKGROUND_KEY);
        }

        const finalBackground = background;
        setTimeout(() => {
          updateAppState({
            currentStep: 'progress',
            isProgressActive: true,
            isLoading: true,
            authState: newAuthState,
            userBackground: finalBackground,
            errorMessage: '',
          });
        }, 100);
        return;
      }

      updateAppState({
        authState: newAuthState,
        currentStep: 'form',
        isLoading: false,
        isProgressActive: false,
        errorMessage: '',
      });
    },
    [appState.userBackground, updateAppState]
  );

  const handleBackToForm = () => {
    if (typeof window !== 'undefined') {
      window.sessionStorage.removeItem(PENDING_BACKGROUND_KEY);
    }

    updateAppState({
      currentStep: 'form',
      analysisReport: null,
      isLoading: false,
      isProgressActive: false,
      errorMessage: '',
      userBackground: null,
      selectedSchool: null,
      selectedMajorId: null,
    });
  };

  const handleRetry = () => {
    if (appState.userBackground) {
      handleFormSubmit(appState.userBackground);
    }
  };

  const handleSelectSchool = (schoolName: string) => {
    updateAppState({
      currentStep: 'school-majors',
      selectedSchool: schoolName,
      selectedMajorId: null,
    });
  };

  const handleSelectMajor = (majorId: string) => {
    updateAppState({
      currentStep: 'major-detail',
      selectedMajorId: majorId,
    });
  };

  const renderCurrentStep = () => {
    switch (appState.currentStep) {
      case 'form':
        return (
          <div className="space-y-6">
            <MainNavigation
              onFormSubmit={handleFormSubmit}
              onSelectSchool={handleSelectSchool}
              onSelectMajor={handleSelectMajor}
            />
          </div>
        );

      case 'progress':
        if (!appState.userBackground) {
          return (
            <div className="space-y-6">
              <UserForm onSubmit={handleFormSubmit} />
            </div>
          );
        }

        return (
          <div className="space-y-6">
            <ProgressDisplay
              isActive={appState.isProgressActive}
              userBackground={appState.userBackground}
              onComplete={(result) =>
                updateAppState({
                  currentStep: 'report',
                  analysisReport: result,
                  isLoading: false,
                  isProgressActive: false,
                })
              }
              onError={(error) =>
                updateAppState({
                  currentStep: 'error',
                  errorMessage: error,
                  isLoading: false,
                  isProgressActive: false,
                })
              }
            />
          </div>
        );

      case 'report':
        return (
          <div className="space-y-6">
            <AnalysisReport
              report={appState.analysisReport!}
              onBackToForm={handleBackToForm}
            />
          </div>
        );

      case 'auth':
        return (
          <div className="space-y-6">
            <AuthForm
              onAuthSuccess={handleAuthSuccess}
              onBackToForm={handleBackToForm}
              userBackground={appState.userBackground}
            />
          </div>
        );

      case 'error':
        return (
          <div className="space-y-6">
            <ErrorDisplay
              errorMessage={appState.errorMessage}
              onRetry={handleRetry}
              onBackToForm={handleBackToForm}
            />
          </div>
        );

      case 'school-majors':
        return (
          <div className="space-y-6">
            <SchoolMajorList
              schoolName={appState.selectedSchool!}
              onSelectMajor={handleSelectMajor}
              onBack={handleBackToForm}
              onBackToHome={handleBackToForm}
            />
          </div>
        );

      case 'major-detail':
        return (
          <div className="space-y-6">
            <MajorDetail
              majorId={appState.selectedMajorId!}
              onBack={() => {
                if (appState.selectedSchool) {
                  updateAppState({ currentStep: 'school-majors' });
                } else {
                  updateAppState({ currentStep: 'form' });
                }
              }}
            />
          </div>
        );

      default:
        return (
          <div className="space-y-6">
            <MainNavigation
              onFormSubmit={handleFormSubmit}
              onSelectSchool={handleSelectSchool}
              onSelectMajor={handleSelectMajor}
            />
          </div>
        );
    }
  };

  const showTestPage = queryState.test;
  const showEmailDemo = queryState.emailDemo;
  const showDebug = queryState.debug;

  return (
    <ConfigProvider locale={zhCN} theme={themeTokens}>
      <AntdApp>
        <div className="min-h-screen bg-gradient-to-br from-indigo-100 via-white to-slate-50 py-12">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 space-y-10">
            {!showTestPage && !showEmailDemo && (
              <header className="text-center space-y-4">
                <span className="inline-flex items-center rounded-full bg-indigo-100 px-4 py-1 text-sm font-medium text-indigo-600 shadow-sm">
                  海量、真实案例驱动的留学规划服务
                </span>
                <h1 className="text-3xl sm:text-4xl font-bold text-slate-900">
                  箴言留学规划与评估中心
                </h1>
                <p className="max-w-3xl mx-auto text-base sm:text-lg text-slate-600">
                  先让AI初步评估、再用海量数据给出院校推荐、最后专业老师，免费给出择校定位建议
                </p>
              </header>
            )}

            <div className="space-y-8">
              {showTestPage ? (
                <SystemTest />
              ) : showEmailDemo ? (
                <EmailVerificationDemo />
              ) : (
                renderCurrentStep()
              )}
            </div>
          </div>
          <DebugPanel visible={showDebug} />
        </div>
      </AntdApp>
    </ConfigProvider>
  );
}
