import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { apiClient, setAuthToken, clearAuthToken } from '@/lib/api-client';
import { API_ENDPOINTS } from '@/lib/constants';
import { User, LoginResponse } from '@/types/api';

interface AuthStore {
  user: User | null;
  isAuthenticated: boolean;
  isCheckingAuth: boolean; // For checking existing auth on mount
  error: string | null;
  _hasHydrated: boolean;
  
  login: (email: string, password: string) => Promise<boolean>;
  logout: () => void;
  checkAuth: () => Promise<void>;
  clearError: () => void;
  setHasHydrated: (state: boolean) => void;
}

export const useAuthStore = create<AuthStore>()(
  persist(
    (set, get) => ({
      user: null,
      isAuthenticated: false,
      isCheckingAuth: false, // Not checking until explicitly called
      error: null,
      _hasHydrated: false,
      
      setHasHydrated: (state) => set({ _hasHydrated: state }),
      
      login: async (email: string, password: string) => {
        set({ error: null });
        
        try {
          // FastAPI expects form data for OAuth2
          const formData = new URLSearchParams();
          formData.append('username', email);
          formData.append('password', password);
          
          const response = await apiClient.post<LoginResponse>(
            API_ENDPOINTS.LOGIN,
            formData,
            {
              headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
              },
            }
          );
          
          const { access_token } = response.data;
          setAuthToken(access_token);
          
          // Fetch user info
          await get().checkAuth();
          
          return true;
        } catch (err) {
          const message = err instanceof Error ? err.message : 'Login failed';
          set({ error: message });
          return false;
        }
      },
      
      logout: () => {
        clearAuthToken();
        set({ user: null, isAuthenticated: false, error: null });
      },
      
      checkAuth: async () => {
        set({ isCheckingAuth: true });
        
        try {
          const response = await apiClient.get<User>(API_ENDPOINTS.ME);
          set({
            user: response.data,
            isAuthenticated: true,
            isCheckingAuth: false,
          });
        } catch {
          clearAuthToken();
          set({
            user: null,
            isAuthenticated: false,
            isCheckingAuth: false,
          });
        }
      },
      
      clearError: () => set({ error: null }),
    }),
    {
      name: 'auth-storage',
      partialize: (state) => ({
        isAuthenticated: state.isAuthenticated,
        user: state.user,
      }),
      onRehydrateStorage: () => (state) => {
        state?.setHasHydrated(true);
      },
    }
  )
);

// Selector hooks
export const useUser = () => useAuthStore((state) => state.user);
export const useIsAuthenticated = () => useAuthStore((state) => state.isAuthenticated);
export const useIsCheckingAuth = () => useAuthStore((state) => state.isCheckingAuth);
export const useAuthError = () => useAuthStore((state) => state.error);
export const useHasHydrated = () => useAuthStore((state) => state._hasHydrated);
