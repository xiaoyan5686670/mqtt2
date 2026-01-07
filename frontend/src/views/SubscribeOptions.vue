<template>
  <div class="container-fluid">
    <h2>MQTT消费选项</h2>
    
    <div class="row mb-4">
      <div class="col-md-12">
        <div class="card">
          <div class="card-header d-flex justify-content-between align-items-center">
            <h5>消费主题管理</h5>
            <button class="btn btn-primary" @click="showAddForm = true; resetForm()">新增消费配置</button>
          </div>
          <div class="card-body">
            <div class="table-responsive">
              <table class="table table-striped">
                <thead>
                  <tr>
                    <th>配置名称</th>
                    <th>消费主题</th>
                    <th>关联MQTT配置</th>
                    <th>状态</th>
                    <th>操作</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="config in configs" :key="config.id">
                    <td>{{ config.name }}</td>
                    <td>{{ config.subscribe_topics }}</td>
                    <td>{{ mqttConfigName(config.mqtt_config_id) }}</td>
                    <td>
                      <span :class="config.is_active ? 'text-success' : 'text-muted'">
                        {{ config.is_active ? '活动中' : '未激活' }}
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
                        :class="config.is_active ? 'btn-warning' : 'btn-success'" 
                        @click="toggleConfig(config)"
                      >
                        {{ config.is_active ? '停止' : '开启' }}
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
            <h5>{{ editingConfig ? '编辑消费配置' : '新增消费配置' }}</h5>
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
                <div class="form-text">配置名称必须唯一，用于区分不同消费配置</div>
              </div>
              
              <div class="mb-3">
                <label for="subscribe_topic" class="form-label">消费主题 *</label>
                <input
                  type="text"
                  class="form-control"
                  id="subscribe_topic"
                  v-model="currentConfig.subscribe_topics"
                  required
                />
                <div class="form-text">请输入要消费的MQTT主题，如 pc/1</div>
              </div>
              
              <div class="mb-3">
                <label for="mqtt_config_id" class="form-label">关联MQTT配置</label>
                <select
                  class="form-select"
                  id="mqtt_config_id"
                  v-model="currentConfig.mqtt_config_id"
                >
                  <option value="">请选择MQTT配置</option>
                  <option v-for="config in mqttConfigs" :key="config.id" :value="config.id">
                    {{ config.name }} ({{ config.server }}:{{ config.port }})
                  </option>
                </select>
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
    </div>

    <!-- 消费数据显示区域 -->
    <div class="row mt-4" v-if="isConsuming">
      <div class="col-md-12">
        <div class="card">
          <div class="card-header d-flex justify-content-between align-items-center">
            <h5>消费数据</h5>
            <button class="btn btn-danger" @click="stopConsuming">停止消费</button>
          </div>
          <div class="card-body">
            <div class="table-responsive">
              <table class="table table-striped">
                <thead>
                  <tr>
                    <th>时间</th>
                    <th>主题</th>
                    <th>消息内容</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="(message, index) in messages" :key="index">
                    <td>{{ formatDate(message.timestamp) }}</td>
                    <td>{{ message.topic }}</td>
                    <td>{{ message.payload }}</td>
                  </tr>
                </tbody>
              </table>
            </div>
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
  name: 'SubscribeOptions',
  setup() {
    const configs = ref([])
    const mqttConfigs = ref([])
    const showAddForm = ref(false)
    const editingConfig = ref(null)
    const isConsuming = ref(false)
    const messages = ref([])
    const consumptionInterval = ref(null)
    
    const currentConfig = ref({
      id: null,
      name: '',
      subscribe_topics: '',
      mqtt_config_id: null
    })

    const loadConfigs = async () => {
      try {
        const response = await axios.get('/api/topic-configs')
        configs.value = response.data
      } catch (error) {
        console.error('加载消费配置失败:', error)
      }
    }

    const loadMqttConfigs = async () => {
      try {
        const response = await axios.get('/api/mqtt-configs')
        mqttConfigs.value = Array.isArray(response.data) ? response.data : []
      } catch (error) {
        console.error('加载MQTT配置失败:', error)
        mqttConfigs.value = []
      }
    }

    // 获取主题配置
    const loadTopicConfigs = async () => {
      try {
        const response = await axios.get('/api/topic-configs')
        configs.value = response.data
      } catch (error) {
        console.error('加载主题配置失败:', error)
      }
    }

    const saveConfig = async () => {
      try {
        let response
        if (editingConfig.value) {
          // 更新现有配置
          response = await axios.put(`/api/topic-configs/${currentConfig.value.id}`, currentConfig.value)
        } else {
          // 创建新配置
          response = await axios.post('/api/topic-configs', currentConfig.value)
        }
        
        // 重新加载配置列表
        await loadConfigs()
        showAddForm.value = false
        editingConfig.value = null
      } catch (error) {
        console.error('保存消费配置失败:', error)
        alert(`保存失败: ${error.message}`)
      }
    }

    const editConfig = (config) => {
      currentConfig.value = { ...config }
      editingConfig.value = config.id
      showAddForm.value = true
    }

    const deleteConfig = async (configId) => {
      if (!confirm('确定要删除这个消费配置吗？此操作不可撤销！')) {
        return
      }

      try {
        await axios.delete(`/api/topic-configs/${configId}`)
        await loadConfigs()
        alert('消费配置删除成功')
      } catch (error) {
        console.error('删除消费配置失败:', error)
        alert(`删除失败: ${error.message}`)
      }
    }

    const toggleConfig = async (config) => {
      try {
        if (config.is_active) {
          // 如果是激活状态，停用配置
          // 先停止消费（如果正在消费）
          if (isConsuming.value) {
            stopConsuming()
          }
          
          // 将配置设为非激活状态
          const updatedConfig = { ...config, is_active: false }
          await axios.put(`/api/topic-configs/${config.id}`, updatedConfig)
          await loadConfigs()
          alert(`已停用配置 "${config.name}"`)
        } else {
          // 如果是非激活状态，激活它
          // 直接激活当前配置，不处理其他配置的状态
          const updatedConfig = { ...config, is_active: true }
          await axios.put(`/api/topic-configs/${config.id}`, updatedConfig)
          await loadConfigs()
          alert(`已激活配置 "${config.name}"`)
        }
      } catch (error) {
        console.error('切换配置状态失败:', error)
        alert(`操作失败: ${error.message}`)
      }
    }

    const mqttConfigName = (mqttConfigId) => {
      const config = mqttConfigs.value.find(c => c.id === mqttConfigId)
      return config ? config.name : '未关联'
    }

    const resetForm = () => {
      currentConfig.value = {
        id: null,
        name: '',
        subscribe_topics: '',
        mqtt_config_id: null
      }
      editingConfig.value = null
    }

    // 真实的消费数据功能
    const startConsuming = async (config) => {
      if (!config) {
        // 如果没有提供配置，尝试使用激活的配置
        const activeConfig = configs.value.find(c => c.is_active)
        if (!activeConfig) {
          alert('没有激活的消费配置')
          return
        }
        config = activeConfig
      }

      try {
        // 调用后端API订阅主题
        await axios.post('/api/subscribe-topic', {
          topic: config.subscribe_topics,
          mqtt_config_id: config.mqtt_config_id
        })
        
        isConsuming.value = true
        
        // 定时获取消费数据
        if (consumptionInterval.value) {
          clearInterval(consumptionInterval.value)
        }
        
        consumptionInterval.value = setInterval(async () => {
          if (!isConsuming.value) {
            clearInterval(consumptionInterval.value)
            return
          }
          
          try {
            const response = await axios.get('/api/mqtt-messages', {
              params: { limit: 20 }
            })
            
            messages.value = response.data
          } catch (error) {
            console.error('获取MQTT消息失败:', error)
          }
        }, 2000)
        
        alert(`开始消费主题: ${config.subscribe_topics}`)
      } catch (error) {
        console.error('启动消费失败:', error)
        alert(`启动消费失败: ${error.message}`)
      }
    }

    const stopConsuming = async () => {
      try {
        // 如果有激活的配置，停止订阅
        const activeConfig = configs.value.find(c => c.is_active)
        if (activeConfig) {
          await axios.post('/api/unsubscribe-topic', {
            topic: activeConfig.subscribe_topics
          })
        }
        
        isConsuming.value = false
        if (consumptionInterval.value) {
          clearInterval(consumptionInterval.value)
          consumptionInterval.value = null
        }
        
        messages.value = []
        alert('已停止消费')
      } catch (error) {
        console.error('停止消费失败:', error)
        alert(`停止消费失败: ${error.message}`)
      }
    }

    onMounted(async () => {
      await Promise.all([
        loadConfigs(),
        loadMqttConfigs()
      ])
    })

    const formatDate = (date) => {
      return new Date(date).toLocaleString('zh-CN')
    }

    return {
      configs,
      mqttConfigs,
      showAddForm,
      editingConfig,
      isConsuming,
      messages,
      currentConfig,
      saveConfig,
      editConfig,
      deleteConfig,
      toggleConfig,
      mqttConfigName,
      resetForm,
      startConsuming,
      stopConsuming,
      formatDate
    }
  }
}
</script>