import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor to add JWT token
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

// Response interceptor to handle 401 and refresh token
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    // If 401 and not already retried
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;

      try {
        const refreshToken = localStorage.getItem('refresh_token');
        
        if (!refreshToken) {
          // No refresh token, redirect to login
          localStorage.removeItem('access_token');
          localStorage.removeItem('refresh_token');
          localStorage.removeItem('user');
          window.location.href = '/login';
          return Promise.reject(error);
        }

        // Try to refresh the token
        const response = await axios.post(`${API_BASE_URL}/api/v1/auth/refresh`, {
          refresh_token: refreshToken,
        });

        const { access_token } = response.data;
        localStorage.setItem('access_token', access_token);

        // Retry the original request with new token
        originalRequest.headers.Authorization = `Bearer ${access_token}`;
        return api(originalRequest);
      } catch (refreshError) {
        // Refresh failed, redirect to login
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        localStorage.removeItem('user');
        window.location.href = '/login';
        return Promise.reject(refreshError);
      }
    }

    return Promise.reject(error);
  }
);

// Auth endpoints
export const authAPI = {
  register: (email, password) =>
    api.post('/api/v1/auth/register', { email, password }),
  
  login: (email, password) =>
    api.post('/api/v1/auth/login', { email, password }),
  
  refreshToken: (refreshToken) =>
    api.post('/api/v1/auth/refresh', { refresh_token: refreshToken }),
};

// Product endpoints
export const productAPI = {
  list: (page = 1, pageSize = 20) =>
    api.get('/api/v1/products', { params: { page, page_size: pageSize } }),
  
  get: (productId) =>
    api.get(`/api/v1/products/${productId}`),
  
  create: (formData) =>
    api.post('/api/v1/products', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    }),
  
  update: (productId, data) =>
    api.put(`/api/v1/products/${productId}`, data),
  
  delete: (productId) =>
    api.delete(`/api/v1/products/${productId}`),
};

// Campaign endpoints
export const campaignAPI = {
  list: (page = 1, pageSize = 20, statusFilter = null) =>
    api.get('/api/v1/campaigns', {
      params: { page, page_size: pageSize, status_filter: statusFilter },
    }),
  
  get: (campaignId) =>
    api.get(`/api/v1/campaigns/${campaignId}`),
  
  schedule: (campaignId, scheduledTime) =>
    api.post(`/api/v1/campaigns/${campaignId}/schedule`, {
      scheduled_time: scheduledTime,
    }),
  
  cancel: (campaignId) =>
    api.post(`/api/v1/campaigns/${campaignId}/cancel`),
};

// Instagram endpoints
export const instagramAPI = {
  getAuthUrl: () =>
    api.get('/api/v1/instagram/authorize'),
  
  handleCallback: (code, state) =>
    api.get('/api/v1/instagram/callback', { params: { code, state } }),
};

// Analytics endpoints
export const analyticsAPI = {
  getSummary: (startDate, endDate) =>
    api.get('/api/v1/analytics', {
      params: {
        start_date: startDate,
        end_date: endDate,
      },
    }),
};

export default api;
