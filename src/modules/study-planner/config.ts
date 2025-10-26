const KOYEB_PUBLIC_URL = 'https://rigid-ysabel-zhenyan-46e67ce8.koyeb.app';
const LOCAL_API_URL = 'http://localhost:8000';

const stripTrailingSlashes = (url: string): string => {
  if (url === '/') {
    return '';
  }

  return url.replace(/\/+$/, '');
};

// 获取API基础URL
export const getApiBaseUrl = (): string => {
  const envUrl =
    process.env.NEXT_PUBLIC_PLANNER_API_URL ||
    process.env.NEXT_PUBLIC_API_URL ||
    process.env.NEXT_PUBLIC_BACKEND_URL ||
    process.env.REACT_APP_API_URL;

  if (envUrl) {
    return stripTrailingSlashes(envUrl);
  }

  const defaultUrl = process.env.NODE_ENV === 'production' ? KOYEB_PUBLIC_URL : LOCAL_API_URL;

  if (typeof window !== 'undefined') {
    const { hostname } = window.location;
    const isLocalhost = hostname === 'localhost' || hostname === '127.0.0.1';

    if (hostname === 'zhenyan.asia' || hostname === 'www.zhenyan.asia') {
      return stripTrailingSlashes(KOYEB_PUBLIC_URL);
    }

    if (hostname.includes('.pages.dev') || !isLocalhost) {
      return stripTrailingSlashes(KOYEB_PUBLIC_URL);
    }
  }

  return stripTrailingSlashes(defaultUrl);
};
