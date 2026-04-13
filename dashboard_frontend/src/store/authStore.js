import { create } from 'zustand';
import Cookies from 'js-cookie';
import api from '../services/api';

const useAuthStore = create((set, get) => ({
  user: null,
  role: null,
  accessToken: Cookies.get('accessToken') || null,
  refreshToken: Cookies.get('refreshToken') || null,
  permissions: [],
  loading: true,

  login: (data) => {
    const { user, access_token, refresh_token } = data;
    Cookies.set('accessToken', access_token, { secure: true, sameSite: 'strict', expires: 7 });
    Cookies.set('refreshToken', refresh_token, { secure: true, sameSite: 'strict', expires: 30 });
    api.defaults.headers.Authorization = `Bearer ${access_token}`;
    set({
      user,
      role: user.role,
      accessToken: access_token,
      refreshToken: refresh_token,
      permissions: user.permissions,
      loading: false,
    });
  },

  logout: () => {
    Cookies.remove('accessToken');
    Cookies.remove('refreshToken');
    delete api.defaults.headers.Authorization;
    set({
      user: null,
      role: null,
      accessToken: null,
      refreshToken: null,
      permissions: [],
      loading: false,
    });
    // Redirect to login page
    window.location.href = '/login';
  },
  
  hydrate: async () => {
    const accessToken = Cookies.get('accessToken');
    if (!accessToken) {
        set({ loading: false });
        return;
    }
    try {
        // Use the /auth/me endpoint to get user data from the token
        const { data: user } = await api.get('/auth/me');
        set({
            user,
            role: user.role,
            permissions: user.permissions,
            loading: false,
        });
    } catch (error) {
        // If token is invalid, logout
        get().logout();
    }
  },
  
  setTokens: (tokens) => {
    const { access_token, refresh_token } = tokens;
    Cookies.set('accessToken', access_token, { secure: true, sameSite: 'strict', expires: 7 });
    if (refresh_token) {
        Cookies.set('refreshToken', refresh_token, { secure: true, sameSite: 'strict', expires: 30 });
    }
    api.defaults.headers.Authorization = `Bearer ${access_token}`;
    set({
      accessToken: access_token,
      refreshToken: refresh_token || get().refreshToken,
    });
  },
}));

// Initialize the store and hydrate the state
useAuthStore.getState().hydrate();

export default useAuthStore;