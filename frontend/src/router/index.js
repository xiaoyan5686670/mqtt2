import { createRouter, createWebHistory } from 'vue-router'
import Dashboard from '../views/Dashboard.vue'
import DeviceList from '../views/DeviceList.vue'
import DeviceDetail from '../views/DeviceDetail.vue'
import MqttConfig from '../views/MqttConfig.vue'
import TopicConfig from '../views/TopicConfig.vue'
import Login from '../views/Login.vue'

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
    path: '/mqtt-config',
    name: 'MqttConfig',
    component: MqttConfig
  },
  {
    path: '/topic-config',
    name: 'TopicConfig',
    component: TopicConfig
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router