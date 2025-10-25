'use client';

import { useCallback, useEffect, useMemo } from 'react';
import { useRouter } from 'next/navigation';

import { ConfigProvider, App as AntdApp } from 'antd';
import zhCN from 'antd/locale/zh_CN';
import AuthForm from '@/modules/study-planner/components/AuthForm';
import authService, { mapUserInfoToEssayUser } from '@/modules/study-planner/services/authService';
import { useAuthStore } from '@/lib/store';
import { authAPI, User } from '@/lib/api';
import type { UserBackground } from '@/modules/study-planner/services/api';

const PENDING_BACKGROUND_KEY = 'planner:pendingBackground';

const sanitizeRedirect = (redirect: string | null): string => {
  if (!redirect) return '/study-planner';
  if (!redirect.startsWith('/')) {
    return '/study-planner';
  }
  return redirect;
};

export default function UnifiedAuthPage() {
  const router = useRouter();
  const searchParams = useMemo(() => {
    if (typeof window === 'undefined') {
      return new URLSearchParams('');
    }
    return new URLSearchParams(window.location.search);
  }, []);
  const initialTab = searchParams.get('mode') === 'register' ? 'register' : 'login';
  const redirectParam = sanitizeRedirect(searchParams.get('redirect'));

  const { setToken, setUser } = useAuthStore();

  const pendingBackground = useMemo<UserBackground | null>(() => {
    if (typeof window === 'undefined') {
      return null;
    }
    const raw = window.sessionStorage.getItem(PENDING_BACKGROUND_KEY);
    if (!raw) return null;
    try {
      return JSON.parse(raw);
    } catch {
      return null;
    }
  }, []);

  const syncStores = useCallback(
    async (userInfoOverride?: any) => {
      const token = authService.getAccessToken();
      if (token) {
        setToken(token);
      }

      let plannerUser = userInfoOverride || authService.getCurrentUser();
      if (!plannerUser) {
        await authService.refreshUserInfo();
        plannerUser = authService.getCurrentUser();
      }

      if (plannerUser) {
        setUser(mapUserInfoToEssayUser(plannerUser));
        return;
      }

      if (token) {
        try {
          const user = await authAPI.getCurrentUser();
          setUser(user);
          return;
        } catch {
          // fall back to minimal user info when API 不可用
          setUser({
            id: 0,
            username: '已登录用户',
            email: '',
            is_active: true,
            created_at: new Date().toISOString(),
          } as User);
        }
      }
    },
    [setToken, setUser]
  );

  useEffect(() => {
    if (authService.isAuthenticated()) {
      syncStores();
      router.replace(redirectParam);
    }
  }, [redirectParam, router, syncStores]);

  const handleAuthSuccess = useCallback(
    async (userInfo: any) => {
      await syncStores(userInfo);
      if (typeof window !== 'undefined') {
        window.sessionStorage.removeItem(PENDING_BACKGROUND_KEY);
      }
      router.push(redirectParam);
    },
    [redirectParam, router, syncStores]
  );

  return (
    <ConfigProvider locale={zhCN}>
      <AntdApp>
        <AuthForm
          onAuthSuccess={handleAuthSuccess}
          userBackground={pendingBackground}
          initialTab={initialTab}
        />
      </AntdApp>
    </ConfigProvider>
  );
}
