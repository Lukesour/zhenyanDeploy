import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { User, Essay, GradingResult } from './api';

interface AuthState {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  setUser: (user: User) => void;
  setToken: (token: string) => void;
  logout: () => void;
}

interface EssayState {
  essays: Essay[];
  currentEssay: Essay | null;
  gradingResult: GradingResult | null;
  isLoading: boolean;
  setEssays: (essays: Essay[]) => void;
  addEssay: (essay: Essay) => void;
  setCurrentEssay: (essay: Essay | null) => void;
  setGradingResult: (result: GradingResult | null) => void;
  setLoading: (loading: boolean) => void;
  updateEssayStatus: (essayId: number, status: string, isGraded?: boolean) => void;
}

// 认证状态管理
export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      token: null,
      isAuthenticated: false,
      setUser: (user) => set({ user, isAuthenticated: true }),
      setToken: (token) => {
        localStorage.setItem('access_token', token);
        set({ token, isAuthenticated: true });
      },
      logout: () => {
        localStorage.removeItem('access_token');
        set({ user: null, token: null, isAuthenticated: false });
      },
    }),
    {
      name: 'auth-storage',
      partialize: (state) => ({ 
        user: state.user, 
        token: state.token, 
        isAuthenticated: state.isAuthenticated 
      }),
    }
  )
);

// 作文状态管理
export const useEssayStore = create<EssayState>((set, _get) => ({
  essays: [],
  currentEssay: null,
  gradingResult: null,
  isLoading: false,
  setEssays: (essays) => set({ essays }),
  addEssay: (essay) => set((state) => ({ essays: [essay, ...state.essays] })),
  setCurrentEssay: (essay) => set({ currentEssay: essay }),
  setGradingResult: (result) => set({ gradingResult: result }),
  setLoading: (loading) => set({ isLoading: loading }),
  updateEssayStatus: (essayId, status, isGraded) => {
    set((state) => ({
      essays: state.essays.map((essay) =>
        essay.id === essayId
          ? { ...essay, grading_status: status, is_graded: isGraded ?? essay.is_graded }
          : essay
      ),
      currentEssay: state.currentEssay?.id === essayId
        ? { ...state.currentEssay, grading_status: status, is_graded: isGraded ?? state.currentEssay.is_graded }
        : state.currentEssay,
    }));
  },
}));
