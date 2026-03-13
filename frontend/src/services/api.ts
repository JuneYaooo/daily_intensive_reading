import axios from 'axios';

// Create axios instance with default config
const api = axios.create({
  baseURL: '', // 使用相对路径，让Vite代理处理
  headers: {
    'Content-Type': 'application/json',
  },
  // Don't follow redirects, to avoid CORS issues
  maxRedirects: 0,
  // Allow credentials for cross-origin requests
  withCredentials: true,
  // Add longer timeout for network operations (50 minutes)
  timeout: 3000000
});

// Request interceptor for adding auth token
api.interceptors.request.use(
  (config) => {
    // Log request
    console.log(`发起请求: ${config.method?.toUpperCase()} ${config.baseURL}${config.url}`);
    
    // Add auth token if needed
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor for error handling
api.interceptors.response.use(
  (response) => response,
  (error) => {
    // Handle common errors
    if (error.response) {
      const { status, data } = error.response;
      
      console.error(`API错误 (${status}):`, data);
      
      if (status === 401) {
        // Handle unauthorized
        console.error('未授权访问');
        // Redirect to login or show notification
      }
      
      if (status === 404) {
        console.error('资源未找到:', data);
        // Let the 404 propagate to show our prompt dialog
      }
      
      if (status === 500) {
        console.error('服务器错误:', data);
      }
    } else if (error.request) {
      // Request was made but no response received
      console.error('没有响应:', error.request);
    } else {
      // Error setting up request
      console.error('请求错误:', error.message);
    }
    return Promise.reject(error);
  }
);

export default api; 