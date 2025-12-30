<template>
  <div>
    <h2>MQTT配置管理</h2>

    <div class="row mb-4">
      <div class="col-md-12">
        <div class="card">
          <div class="card-header d-flex justify-content-between align-items-center">
            <h5>配置列表</h5>
            <button class="btn btn-primary" @click="showAddForm = true; resetForm()">添加配置</button>
          </div>
          <div class="card-body">
            <div class="table-responsive">
              <table class="table table-striped">
                <thead>
                  <tr>
                    <th>名称</th>
                    <th>服务器</th>
                    <th>端口</th>
                    <th>客户端ID</th>
                    <th>状态</th>
                    <th>操作</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="config in configs" :key="config.id">
                    <td>{{ config.name }}</td>
                    <td>{{ config.server }}</td>
                    <td>{{ config.port }}</td>
                    <td>{{ config.client_id }}</td>
                    <td>
                      <span :class="config.is_active ? 'text-success' : 'text-muted'">
                        {{ config.is_active ? '激活' : '未激活' }}
                      </span>
                    </td>
                    <td>
                      <button 
                        class="btn btn-sm btn-outline-primary me-1" 
                        @click="editConfig(config)"
                      >
                        编辑
                      </button>
                      <button 
                        class="btn btn-sm" 
                        :class="config.is_active ? 'btn-secondary' : 'btn-success'" 
                        @click="activateConfig(config)"
                        :disabled="config.is_active"
                      >
                        {{ config.is_active ? '当前激活' : '激活' }}
                      </button>
                      <button 
                        class="btn btn-sm btn-outline-success me-1" 
                        @click="testConnection(config)"
                      >
                        测试
                      </button>
                      <button 
                        class="btn btn-sm btn-outline-danger" 
                        @click="deleteConfig(config.id)"
                      >
                        删除
                      </button>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 配置编辑表单 -->
    <div class="row" v-if="showAddForm || editingConfig">
      <div class="col-md-8">
        <div class="card">
          <div class="card-header">
            <h5>{{ editingConfig ? '编辑配置' : '添加配置' }}</h5>
          </div>
          <div class="card-body">
            <form @submit.prevent="saveConfig">
              <div class="mb-3">
                <label for="name" class="form-label">配置名称 *</label>
                <input
                  type="text"
                  class="form-control"
                  id="name"
                  v-model="currentConfig.name"
                  :disabled="!!editingConfig"
                  required
                />
                <div class="form-text">配置名称必须唯一，用于区分不同MQTT服务器</div>
              </div>
              <div class="mb-3">
                <label for="server" class="form-label">服务器地址</label>
                <input
                  type="text"
                  class="form-control"
                  id="server"
                  v-model="currentConfig.server"
                  required
                />
              </div>
              <div class="mb-3">
                <label for="port" class="form-label">端口</label>
                <input
                  type="number"
                  class="form-control"
                  id="port"
                  v-model.number="currentConfig.port"
                  required
                />
              </div>
              <div class="mb-3">
                <label for="username" class="form-label">用户名</label>
                <input
                  type="text"
                  class="form-control"
                  id="username"
                  v-model="currentConfig.username"
                />
              </div>
              <div class="mb-3">
                <label for="password" class="form-label">密码</label>
                <input
                  type="password"
                  class="form-control"
                  id="password"
                  v-model="currentConfig.password"
                />
              </div>
              <div class="mb-3">
                <label for="client_id" class="form-label">客户端ID</label>
                <input
                  type="text"
                  class="form-control"
                  id="client_id"
                  v-model="currentConfig.client_id"
                />
              </div>
              <div class="mb-3">
                <label for="keepalive" class="form-label">Keep Alive (秒)</label>
                <input
                  type="number"
                  class="form-control"
                  id="keepalive"
                  v-model.number="currentConfig.keepalive"
                  min="10"
                  max="300"
                />
              </div>
              <div class="mb-3">
                <label for="will_topic" class="form-label">遗嘱主题</label>
                <input
                  type="text"
                  class="form-control"
                  id="will_topic"
                  v-model="currentConfig.will_topic"
                />
              </div>
              <div class="mb-3">
                <label for="will_payload" class="form-label">遗嘱消息</label>
                <input
                  type="text"
                  class="form-control"
                  id="will_payload"
                  v-model="currentConfig.will_payload"
                />
              </div>
              <div class="form-check mb-3">
                <input
                  type="checkbox"
                  class="form-check-input"
                  id="use_tls"
                  v-model="currentConfig.use_tls"
                />
                <label class="form-check-label" for="use_tls">使用TLS</label>
              </div>
              
              <div class="d-grid gap-2 d-md-flex justify-content-md-end">
                <button type="button" class="btn btn-secondary me-2" @click="showAddForm = false; editingConfig = null">
                  取消
                </button>
                <button type="submit" class="btn btn-primary">
                  {{ editingConfig ? '更新配置' : '保存配置' }}
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
            
            <div class="mt-3" v-if="selectedConfigForTest">
              <h6>当前测试配置:</h6>
              <p>{{ selectedConfigForTest.name }} ({{ selectedConfigForTest.server }}:{{ selectedConfigForTest.port }})</p>
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
    const configs = ref([])
    const currentConfig = ref({
      id: null,
      name: '',
      server: 'localhost',
      port: 1883,
      username: '',
      password: '',
      client_id: 'mqtt_frontend_client',
      keepalive: 60,
      timeout: 10,
      use_tls: false,
      ca_certs: null,
      certfile: null,
      keyfile: null,
      will_topic: 'clients/python_client_status',
      will_payload: 'Client is offline',
      will_qos: 1
    })
    
    const showAddForm = ref(false)
    const editingConfig = ref(null)
    const selectedConfigForTest = ref(null)
    
    const connectionStatus = ref({
      connected: false,
      message: '',
      success: false
    })
    
    const history = ref([])

    const loadConfigs = async () => {
      try {
        const response = await axios.get('/api/mqtt-configs')
        configs.value = response.data
      } catch (error) {
        console.error('加载MQTT配置列表失败:', error)
        addToHistory('加载配置列表失败', false)
      }
    }

    const saveConfig = async () => {
      try {
        let response
        if (editingConfig.value) {
          // 更新现有配置
          response = await axios.put(`/api/mqtt-configs/${currentConfig.value.id}`, currentConfig.value)
          addToHistory(`配置 "${currentConfig.value.name}" 更新成功`, true)
        } else {
          // 创建新配置
          response = await axios.post('/api/mqtt-configs', currentConfig.value)
          addToHistory(`配置 "${currentConfig.value.name}" 保存成功`, true)
        }
        
        // 重新加载配置列表
        await loadConfigs()
        showAddForm.value = false
        editingConfig.value = null
      } catch (error) {
        console.error('保存MQTT配置失败:', error)
        addToHistory(`配置保存失败: ${error.message}`, false)
      }
    }

    const editConfig = (config) => {
      currentConfig.value = { ...config }
      editingConfig.value = config.id
      showAddForm.value = true
    }

    const resetForm = () => {
      currentConfig.value = {
        id: null,
        name: '',
        server: 'localhost',
        port: 1883,
        username: '',
        password: '',
        client_id: 'mqtt_frontend_client',
        keepalive: 60,
        timeout: 10,
        use_tls: false,
        ca_certs: null,
        certfile: null,
        keyfile: null,
        will_topic: 'clients/python_client_status',
        will_payload: 'Client is offline',
        will_qos: 1
      }
      editingConfig.value = null
    }

    const deleteConfig = async (id) => {
      if (!confirm('确定要删除此配置吗？')) return
      
      try {
        const configToDelete = configs.value.find(c => c.id === id)
        await axios.delete(`/api/mqtt-configs/${id}`)
        addToHistory(`配置 "${configToDelete.name}" 已删除`, true)
        loadConfigs() // 重新加载配置列表
      } catch (error) {
        console.error('删除MQTT配置失败:', error)
        addToHistory(`配置删除失败: ${error.message}`, false)
      }
    }

    const activateConfig = async (config) => {
      try {
        await axios.post(`/api/mqtt-configs/${config.id}/activate`)
        addToHistory(`配置 "${config.name}" 激活成功`, true)
        await loadConfigs()
      } catch (error) {
        console.error('激活MQTT配置失败:', error)
        addToHistory(`配置激活失败: ${error.message}`, false)
      }
    }

    const testConnection = async (config) => {
      selectedConfigForTest.value = config
      try {
        const response = await axios.post(`/api/mqtt-configs/${config.id}/test`)
        connectionStatus.value = {
          connected: response.data.message.includes('成功'),
          message: response.data.message,
          success: true
        }
        addToHistory(`${config.name}: ${response.data.message}`, true)
      } catch (error) {
        console.error('测试连接失败:', error)
        connectionStatus.value = {
          connected: false,
          message: `连接测试失败: ${error.message}`,
          success: false
        }
        addToHistory(`${config.name}: 连接测试失败`, false)
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
      loadConfigs()
    })

    return {
      configs,
      currentConfig,
      showAddForm,
      editingConfig,
      connectionStatus,
      history,
      selectedConfigForTest,
      saveConfig,
      editConfig,
      deleteConfig,
      activateConfig,
      testConnection,
      addToHistory,
      formatDate,
      resetForm
    }
  }
}
</script>