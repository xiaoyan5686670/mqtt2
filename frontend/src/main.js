import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import router from './router'

// 导入Bootstrap CSS
import 'bootstrap/dist/css/bootstrap.min.css'

// 移除JS导入，改为在index.html中引入

// 配置axios基础URL
import axios from 'axios'
axios.defaults.baseURL = 'http://localhost:8000'

const app = createApp(App)

app.use(createPinia())
app.use(router)

app.mount('#app')