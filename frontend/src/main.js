import { createApp } from 'vue'
import App from './App.vue'
import router from './router'
import { createPinia } from 'pinia'

// 配置axios基础URL
import axios from 'axios'
axios.defaults.baseURL = 'http://localhost:8080'  // 后端API运行在8080端口

// 创建Vue应用
const app = createApp(App)

app.use(createPinia())
app.use(router)

app.mount('#app')