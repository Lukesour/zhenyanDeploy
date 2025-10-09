import axios from 'axios';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// 创建axios实例
const api = axios.create({
  baseURL: `${API_BASE_URL}/api/v1`,
  headers: {
    'Content-Type': 'application/json',
  },
});

// 请求拦截器 - 添加认证token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// 响应拦截器 - 处理认证错误
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401 || error.response?.status === 403) {
      if (typeof window !== 'undefined') {
        localStorage.removeItem('access_token');
        const redirectPath = encodeURIComponent(window.location.pathname + window.location.search);
        window.location.href = `/auth?mode=login&redirect=${redirectPath}`;
      }
    }
    return Promise.reject(error);
  }
);

// 类型定义
export interface User {
  id: number;
  username: string;
  email: string;
  target_score?: number;
  current_level?: number;
  exam_date?: string;
  remaining_analyses?: number;
  total_analyses_used?: number;
  is_active: boolean;
  created_at: string;
}

export interface Essay {
  id: number;
  task_type: string;
  essay_type?: string;
  title: string;
  content: string;
  word_count: number;
  is_graded: boolean;
  status?: string;
  grading_status: string;
  created_at: string;
  report_skeleton?: Record<string, any>;
}

export interface GradingResult {
  id: number;
  essay_id: number;
  tr_score: number;
  cc_score: number;
  lr_score: number;
  gra_score: number;
  overall_score: number;
  tr_analysis?: any;
  cc_analysis?: any;
  lr_analysis?: any;
  gra_analysis?: any;
  overall_comment?: string;
  improvement_suggestions?: any[];
  model_used: string;
  processing_time?: number;
  created_at: string;
}

export interface SubmitEssayResponse {
  essay: Essay;
  remaining_analyses: number;
  total_analyses_used: number;
}

// API函数
export const authAPI = {
  register: async (userData: {
    username: string;
    email: string;
    password: string;
    target_score?: number;
    current_level?: number;
    exam_date?: string;
  }) => {
    const response = await api.post('/auth/register', userData);
    return response.data;
  },

  login: async (credentials: { email: string; password: string }) => {
    const response = await api.post('/auth/login', credentials);
    return response.data;
  },

  getCurrentUser: async (): Promise<User> => {
    const response = await api.get('/auth/me');
    return response.data;
  },

  updateProfile: async (profileData: {
    target_score?: number;
    current_level?: number;
    exam_date?: string;
  }) => {
    const response = await api.put('/auth/profile', profileData);
    return response.data;
  },
};

export const essayAPI = {
  submitEssay: async (essayData: {
    task_type: string;
    essay_type?: string;
    title: string;
    content: string;
  }): Promise<SubmitEssayResponse> => {
    const response = await api.post('/essays/submit', essayData);
    return response.data;
  },

  getUserEssays: async (skip = 0, limit = 20): Promise<Essay[]> => {
    const response = await api.get(`/essays/?skip=${skip}&limit=${limit}`);
    return response.data;
  },

  getEssay: async (essayId: number): Promise<Essay> => {
    const response = await api.get(`/essays/${essayId}`);
    return response.data;
  },

  getGradingResult: async (essayId: number): Promise<GradingResult> => {
    const response = await api.get(`/essays/${essayId}/result`);
    return response.data;
  },

  deleteEssay: async (essayId: number) => {
    const response = await api.delete(`/essays/${essayId}`);
    return response.data;
  },
};

// 超详细改进建议API
export const improvementAPI = {
  generateDetailedImprovements: async (data: {
    essay_content: string;
    essay_title: string;
    dimension_scores: Record<string, number>;
    overall_score: number;
    target_score?: number;
    analysis_type?: string;
  }) => {
    const response = await api.post('/ultra-improvements/generate', {
      ...data,
      analysis_type: data.analysis_type || 'comprehensive'
    });
    return response.data;
  },

  getAnalysisTypes: async () => {
    const response = await api.get('/ultra-improvements/analysis-types');
    return response.data;
  },

  getDataResources: async () => {
    const response = await api.get('/ultra-improvements/data-resources');
    return response.data;
  },

  quickAnalysis: async (data: {
    essay_content: string;
    essay_title: string;
    dimension_scores: Record<string, number>;
    overall_score: number;
    target_score?: number;
  }) => {
    const response = await api.post('/ultra-improvements/quick-analysis', data);
    return response.data;
  },

  generateSummary: async (data: {
    essay_content: string;
    essay_title: string;
    dimension_scores: Record<string, number>;
    overall_score: number;
  }) => {
    const response = await api.post('/ultra-improvements/summary', data);
    return response.data;
  }
};

export default api;
