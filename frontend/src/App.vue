<template>
  <div id="app">
    <nav class="navbar navbar-expand-lg navbar-dark bg-dark">
      <div class="container">
        <router-link class="navbar-brand" to="/">MQTT IoT Dashboard</router-link>
        <div class="navbar-nav">
          <router-link class="nav-link" to="/dashboard">仪表板</router-link>
          <router-link class="nav-link" to="/devices">设备列表</router-link>
          <router-link class="nav-link" to="/realtime-data">实时数据</router-link>
          <router-link class="nav-link" to="/mqtt-config">MQTT配置</router-link>
          <router-link class="nav-link" to="/topic-config">主题配置</router-link>
          <a class="nav-link" href="#" @click="logout">退出</a>
        </div>
      </div>
    </nav>

    <main class="container-fluid mt-3">
      <router-view />
    </main>
  </div>
</template>

<script>
import { useAuthStore } from './stores/auth'

export default {
  name: 'App',
  methods: {
    logout() {
      const authStore = useAuthStore()
      authStore.logout()
      this.$router.push('/login')
    }
  }
}
</script>

<style>
#app {
  font-family: Avenir, Helvetica, Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  color: #2c3e50;
}
</style>