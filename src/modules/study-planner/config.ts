// 获取API基础URL
export const getApiBaseUrl = (): string => {
  const envUrl =
    process.env.NEXT_PUBLIC_PLANNER_API_URL ||
    process.env.NEXT_PUBLIC_API_URL ||
    process.env.NEXT_PUBLIC_BACKEND_URL ||
    process.env.REACT_APP_API_URL;

  if (envUrl) {
    return envUrl;
  }

  if (typeof window !== 'undefined') {
    const { hostname } = window.location;

    if (hostname === 'zhenyan.asia' || hostname === 'www.zhenyan.asia') {
      return 'https://api.zhenyan.asia';
    }

    if (hostname.includes('.pages.dev') || (hostname !== 'localhost' && hostname !== '127.0.0.1')) {
      return 'https://zhenyan-backend.fly.dev';
    }
  }

  return 'http://localhost:8000';
};
