<template>
  <div id="app">
    <nav class="navbar navbar-expand-lg navbar-dark bg-dark">
      <div class="container-fluid">
        <a class="navbar-brand" href="/">MQTT IoT 管理系统</a>
        <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav">
          <span class="navbar-toggler-icon"></span>
        </button>
        <div class="collapse navbar-collapse" id="navbarNav">
          <nav class="navbar-nav me-auto mb-2 mb-lg-0">
            <li class="nav-item">
              <router-link class="nav-link" to="/dashboard">首页</router-link>
            </li>
            <li class="nav-item">
              <router-link class="nav-link" to="/devices">设备管理</router-link>
            </li>
            <li class="nav-item">
              <router-link class="nav-link" to="/realtime-data">实时数据</router-link>
            </li>
            <li class="nav-item">
              <router-link class="nav-link" to="/mqtt-config">MQTT配置管理</router-link>
            </li>
            <li class="nav-item">
              <router-link class="nav-link" to="/topic-config">消费&生产主题配置</router-link>
            </li>
            <li class="nav-item">
              <router-link class="nav-link" to="/subscribe-options">订阅选项</router-link>
            </li>
          </nav>
        </div>
      </div>
    </nav>
    <div class="container-fluid">
      <router-view></router-view>
    </div>
  </div>
</template>

<script>
import { RouterView } from 'vue-router'

export default {
  name: 'App',
  components: {
    RouterView
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