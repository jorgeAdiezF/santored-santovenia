import axios, { AxiosError } from 'axios';
import { useAuthStore } from '../store/auth';

const BASE_URL = import.meta.env.VITE_API_URL || '';

const apiClient = axios.create({
  baseURL: BASE_URL,
  headers: { 'Content-Type': 'application/json' },
});

// Attach JWT to every request
apiClient.interceptors.request.use((config) => {
  const token = useAuthStore.getState().token;
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Silent token refresh on 401
let isRefreshing = false;
let pendingQueue: Array<{ resolve: (token: string) => void; reject: (err: unknown) => void }> = [];

const flushQueue = (token: string | null, error: unknown = null) => {
  pendingQueue.forEach(({ resolve, reject }) => {
    if (token) resolve(token);
    else reject(error);
  });
  pendingQueue = [];
};

apiClient.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const original = error.config as typeof error.config & { _retry?: boolean };

    if (error.response?.status !== 401 || original?._retry) {
      return Promise.reject(error);
    }

    const { refreshToken, logout, setToken } = useAuthStore.getState();

    if (!refreshToken) {
      logout();
      window.location.href = '/login';
      return Promise.reject(error);
    }

    if (isRefreshing) {
      return new Promise((resolve, reject) => {
        pendingQueue.push({
          resolve: (token) => {
            if (original) {
              original.headers = original.headers ?? {};
              original.headers.Authorization = `Bearer ${token}`;
            }
            resolve(apiClient(original!));
          },
          reject,
        });
      });
    }

    isRefreshing = true;
    original!._retry = true;

    try {
      const { data } = await axios.post(`/api/auth/refresh`, {
        refresh_token: refreshToken,
      });
      const newToken: string = data.access_token;
      setToken(newToken);
      flushQueue(newToken);
      if (original) {
        original.headers = original.headers ?? {};
        original.headers.Authorization = `Bearer ${newToken}`;
      }
      return apiClient(original!);
    } catch (refreshError) {
      flushQueue(null, refreshError);
      logout();
      window.location.href = '/login';
      return Promise.reject(refreshError);
    } finally {
      isRefreshing = false;
    }
  }
);

export default apiClient;
