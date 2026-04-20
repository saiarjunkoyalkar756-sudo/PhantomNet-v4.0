// dashboard_frontend/src/services/api.js
import axios from 'axios';
import useAuthStore from '../store/authStore';

/**
 * Standardized API Client for PhantomNet.
 * Handles the unified response envelope: { success, data, error, request_id }
 */
const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:3001/api',
});

// Request interceptor for Auth
api.interceptors.request.use(
  (config) => {
    const { accessToken } = useAuthStore.getState();
    if (accessToken) {
      config.headers.Authorization = `Bearer ${accessToken}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor for Envelope Handling & Token Refresh
let isRefreshing = false;
let failedQueue = [];

const processQueue = (error, token = null) => {
  failedQueue.forEach(prom => {
    if (error) {
      prom.reject(error);
    } else {
      prom.resolve(token);
    }
  });
  failedQueue = [];
};

api.interceptors.response.use(
  (response) => {
    // Handle successful response envelope
    const { success, data, error, request_id } = response.data;
    
    if (success) {
      // Unpack the data for the application
      return data;
    } else {
      // If success is false, it's a domain error handled by the backend
      const customError = new Error(error?.message || 'API Error');
      customError.code = error?.code;
      customError.details = error?.details;
      customError.request_id = request_id;
      return Promise.reject(customError);
    }
  },
  async (error) => {
    const originalRequest = error.config;
    const { refreshToken, setTokens, logout } = useAuthStore.getState();

    // 1. Handle HTTP 401 Unauthorized (Token Expired)
    if (error.response?.status === 401 && !originalRequest._retry) {
      if (isRefreshing) {
        return new Promise((resolve, reject) => {
          failedQueue.push({ resolve, reject });
        })
          .then(token => {
            originalRequest.headers['Authorization'] = 'Bearer ' + token;
            return api(originalRequest);
          })
          .catch(err => Promise.reject(err));
      }

      originalRequest._retry = true;
      isRefreshing = true;

      try {
        // Refresh token endpoint returns the same envelope
        const refreshResponse = await axios.post(`${api.defaults.baseURL}/auth/refresh`, { refreshToken });
        const { success, data } = refreshResponse.data;
        
        if (success && data.access_token) {
          setTokens(data);
          originalRequest.headers.Authorization = `Bearer ${data.access_token}`;
          processQueue(null, data.access_token);
          return api(originalRequest);
        } else {
          throw new Error('Refresh failed');
        }
      } catch (refreshError) {
        processQueue(refreshError, null);
        logout();
        window.location = '/login';
        return Promise.reject(refreshError);
      } finally {
        isRefreshing = false;
      }
    }

    // 2. Handle fallback for non-envelope errors (e.g. Network errors)
    const normalizedError = {
      message: error.response?.data?.error?.message || error.message || 'Network error',
      code: error.response?.data?.error?.code || 'NETWORK_ERROR',
      request_id: error.response?.data?.request_id || null
    };

    return Promise.reject(normalizedError);
  }
);

export default api;
