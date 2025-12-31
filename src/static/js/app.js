import { createApp } from 'vue'
import { createRouter, createWebHistory } from 'vue-router'
import App from '../../../frontend/src/App.vue'

// 导入所有页面组件
import Dashboard from '../../../frontend/src/views/Dashboard.vue'
import DeviceList from '../../../frontend/src/views/DeviceList.vue'
import DeviceDetail from '../../../frontend/src/views/DeviceDetail.vue'
import DeviceEdit from '../../../frontend/src/views/DeviceEdit.vue'
import MqttConfig from '../../../frontend/src/views/MqttConfig.vue'
import TopicConfig from '../../../frontend/src/views/TopicConfig.vue'
import RealTimeData from '../../../frontend/src/views/RealTimeData.vue'
import Login from '../../../frontend/src/views/Login.vue'
import SubscribeOptions from '../../../frontend/src/views/SubscribeOptions.vue'

// 定义路由
const routes = [
  {
    path: '/login',
    name: 'Login',
    component: Login
  },
  {
    path: '/',
    redirect: '/dashboard'
  },
  {
    path: '/dashboard',
    name: 'Dashboard',
    component: Dashboard
  },
  {
    path: '/devices',
    name: 'DeviceList',
    component: DeviceList
  },
  {
    path: '/devices/:id',
    name: 'DeviceDetail',
    component: DeviceDetail,
    props: true
  },
  {
    path: '/devices/new',
    name: 'DeviceNew',
    component: DeviceEdit
  },
  {
    path: '/devices/:id/edit',
    name: 'DeviceEdit',
    component: DeviceEdit,
    props: true
  },
  {
    path: '/realtime-data',
    name: 'RealTimeData',
    component: RealTimeData
  },
  {
    path: '/mqtt-config',
    name: 'MqttConfig',
    component: MqttConfig
  },
  {
    path: '/topic-config',
    name: 'TopicConfig',
    component: TopicConfig
  },
  {
    path: '/subscribe-options',
    name: 'SubscribeOptions',
    component: SubscribeOptions
  }
]

// 创建路由实例
const router = createRouter({
  history: createWebHistory(),
  routes
})

// 创建Vue应用并使用路由
const app = createApp(App)
app.use(router)
app.mount('#app')