<template>
  <div>
    <h2>MQTT配置</h2>

    <div class="row">
      <div class="col-md-8">
        <div class="card">
          <div class="card-header">
            <h5>MQTT服务器配置</h5>
          </div>
          <div class="card-body">
            <form @submit.prevent="saveConfig">
              <div class="mb-3">
                <label for="server" class="form-label">服务器地址</label>
                <input
                  type="text"
                  class="form-control"
                  id="server"
                  v-model="config.server"
                  required
                />
              </div>
              <div class="mb-3">
                <label for="port" class="form-label">端口</label>
                <input
                  type="number"
                  class="form-control"
                  id="port"
                  v-model.number="config.port"
                  required
                />
              </div>
              <div class="mb-3">
                <label for="username" class="form-label">用户名</label>
                <input
                  type="text"
                  class="form-control"
                  id="username"
                  v-model="config.username"
                />
              </div>
              <div class="mb-3">
                <label for="password" class="form-label">密码</label>
                <input
                  type="password"
                  class="form-control"
                  id="password"
                  v-model="config.password"
                />
              </div>
              <div class="mb-3">
                <label for="client_id" class="form-label">客户端ID</label>
                <input
                  type="text"
                  class="form-control"
                  id="client_id"
                  v-model="config.client_id"
                />
              </div>
              <div class="mb-3">
                <label for="keepalive" class="form-label">Keep Alive (秒)</label>
                <input
                  type="number"
                  class="form-control"
                  id="keepalive"
                  v-model.number="config.keepalive"
                  min="10"
                  max="300"
                />
              </div>
              <div class="d-grid">
                <button type="submit" class="btn btn-primary me-2">保存配置</button>
                <button type="button" class="btn btn-success mt-2" @click="testConnection">
                  测试连接
                </button>
              </div>
            </form>
          </div>
        </div>
      </div>

      <div class="col-md-4">
        <div class="card">
          <div class="card-header">
            <h5>连接状态</h5>
          </div>
          <div class="card-body">
            <div class="d-grid">
              <button 
                class="btn" 
                :class="connectionStatus.connected ? 'btn-success' : 'btn-danger'"
                disabled
              >
                {{ connectionStatus.connected ? '已连接' : '未连接' }}
              </button>
            </div>
            
            <div class="mt-3" v-if="connectionStatus.message">
              <h6>状态信息:</h6>
              <p :class="connectionStatus.success ? 'text-success' : 'text-danger'">
                {{ connectionStatus.message }}
              </p>
            </div>
          </div>
        </div>

        <div class="card mt-3">
          <div class="card-header">
            <h5>操作历史</h5>
          </div>
          <div class="card-body">
            <ul class="list-group list-group-flush" v-if="history.length > 0">
              <li class="list-group-item" v-for="(item, index) in history" :key="index">
                <small>{{ formatDate(item.timestamp) }}</small>
                <div :class="item.success ? 'text-success' : 'text-danger'">
                  {{ item.message }}
                </div>
              </li>
            </ul>
            <p v-else class="text-muted">暂无操作历史</p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted } from 'vue'
import axios from 'axios'

export default {
  name: 'MqttConfig',
  setup() {
    const config = ref({
      id: 1,
      server: 'localhost',
      port: 1883,
      username: '',
      password: '',
      client_id: 'mqtt_frontend_client',
      keepalive: 60
    })
    
    const connectionStatus = ref({
      connected: false,
      message: '',
      success: false
    })
    
    const history = ref([])

    const loadConfig = async () => {
      try {
        const response = await axios.get('/api/mqtt-configs/1')
        config.value = response.data
      } catch (error) {
        console.error('加载MQTT配置失败:', error)
        // 使用默认配置
      }
    }

    const saveConfig = async () => {
      try {
        await axios.put(`/api/mqtt-configs/${config.value.id}`, config.value)
        addToHistory('配置保存成功', true)
      } catch (error) {
        console.error('保存MQTT配置失败:', error)
        addToHistory(`配置保存失败: ${error.message}`, false)
      }
    }

    const testConnection = async () => {
      try {
        const response = await axios.post(`/api/mqtt-configs/${config.value.id}/test`)
        connectionStatus.value = {
          connected: response.data.message.includes('成功'),
          message: response.data.message,
          success: true
        }
        addToHistory(response.data.message, true)
      } catch (error) {
        console.error('测试连接失败:', error)
        connectionStatus.value = {
          connected: false,
          message: `连接测试失败: ${error.message}`,
          success: false
        }
        addToHistory(`连接测试失败: ${error.message}`, false)
      }
    }

    const addToHistory = (message, success) => {
      history.value.unshift({
        timestamp: new Date(),
        message,
        success
      })
      
      // 只保留最近10条记录
      if (history.value.length > 10) {
        history.value = history.value.slice(0, 10)
      }
    }

    const formatDate = (date) => {
      return new Date(date).toLocaleString('zh-CN')
    }

    onMounted(() => {
      loadConfig()
    })

    return {
      config,
      connectionStatus,
      history,
      saveConfig,
      testConnection,
      addToHistory,
      formatDate
    }
  }
}
</script>