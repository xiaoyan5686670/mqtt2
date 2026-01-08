import { createApp } from 'vue'
import App from './App.vue'
import router from './router'
import { createPinia } from 'pinia'

// 配置axios基础URL，动态使用当前主机的协议、主机名和端口
import axios from 'axios'
// 使用当前页面的协议、主机名和端口作为API的基础URL
axios.defaults.baseURL = `${window.location.protocol}//${window.location.hostname}:8000`

// 请求拦截器：在每个请求中添加JWT令牌
axios.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// 响应拦截器：处理认证错误
axios.interceptors.response.use(
  (response) => {
    return response;
  },
  (error) => {
    if (error.response?.status === 401) {
      // 认证失败，重定向到登录页面
      localStorage.removeItem('token');
      window.location.href = '/#/login';
    }
    return Promise.reject(error);
  }
);

// 创建Vue应用
const app = createApp(App)

app.use(createPinia())
app.use(router)

app.mount('#app')