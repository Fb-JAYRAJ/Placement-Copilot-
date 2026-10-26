import { create } from 'zustand';
import api from '@/lib/api/client';

/**
 * Authentication and session store.
 * Manages active user record, in-memory access token, and login/register/logout actions.
 */
export const useAuthStore = create((set) => ({
  user: null,
  accessToken: null,
  isAuthenticated: false,
  isLoading: true,

  /**
   * Authenticates candidate with credentials and sets active bearer token.
   * @param {string} email
   * @param {string} password
   */
  login: async (email, password) => {
    const data = await api.post('/auth/login', { email, password });
    api.setAccessToken(data.access_token);
    if (typeof window !== 'undefined') {
      localStorage.setItem('has_session', 'true');
    }
    set({
      user: data.user,
      accessToken: data.access_token,
      isAuthenticated: true,
      isLoading: false,
    });
  },

  /**
   * Registers a new candidate profile and logs them in immediately.
   * @param {Object} payload
   * @param {string} payload.email
   * @param {string} payload.name
   * @param {string} payload.password
   * @param {string} [payload.college]
   * @param {number} [payload.grad_year]
   * @param {string} [payload.target_role]
   */
  register: async (payload) => {
    const data = await api.post('/auth/register', payload);
    api.setAccessToken(data.access_token);
    if (typeof window !== 'undefined') {
      localStorage.setItem('has_session', 'true');
    }
    set({
      user: data.user,
      accessToken: data.access_token,
      isAuthenticated: true,
      isLoading: false,
    });
  },

  /**
   * Revokes refresh token on backend and clears client authentication state.
   */
  logout: async () => {
    try {
      await api.post('/auth/logout');
    } catch {
      // Ignore network errors during logout to guarantee client cleanup
    } finally {
      if (typeof window !== 'undefined') {
        localStorage.removeItem('has_session');
      }
      api.setAccessToken(null);
      set({
        user: null,
        accessToken: null,
        isAuthenticated: false,
        isLoading: false,
      });
    }
  },

  /**
   * Validates active session on application boot using HTTP-only refresh cookie.
   * Single-flight, skips refresh if access token is already in memory or if browser has no session flag.
   */
  checkAuth: async () => {
    // 1. Do not refresh right after login when an access token is already in memory
    const state = useAuthStore.getState();
    if (state.isAuthenticated && api.getAccessToken()) {
      set({ isLoading: false });
      return;
    }

    // 2. Skip bootstrap refresh when the browser has never had a session
    const hasSession = typeof window !== 'undefined' && localStorage.getItem('has_session') === 'true';
    if (!hasSession) {
      set({
        user: null,
        accessToken: null,
        isAuthenticated: false,
        isLoading: false,
      });
      return;
    }

    // 3. Single-flight refresh token attempt
    try {
      set({ isLoading: true });
      const newToken = await api.tryRefreshToken();
      if (newToken) {
        const user = await api.get('/users/me');
        set({
          user,
          accessToken: newToken,
          isAuthenticated: true,
          isLoading: false,
        });
        return;
      }
    } catch {
      // Refresh failed or not authenticated
    }

    if (typeof window !== 'undefined') {
      localStorage.removeItem('has_session');
    }
    api.setAccessToken(null);
    set({
      user: null,
      accessToken: null,
      isAuthenticated: false,
      isLoading: false,
    });
  },

  setUser: (user) => set({ user }),
}));

// Listen to expired auth events dispatched from API client
if (typeof window !== 'undefined') {
  window.addEventListener('auth:expired', () => {
    useAuthStore.getState().logout();
  });
}

export default useAuthStore;
