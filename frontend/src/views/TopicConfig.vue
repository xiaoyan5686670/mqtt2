<template>
  <div>
    <h2>消费&生产主题配置</h2>

    <div class="row mb-4">
      <div class="col-md-12">
        <div class="card">
          <div class="card-header d-flex justify-content-between align-items-center">
            <h5>主题配置列表</h5>
            <button class="btn btn-primary" @click="showAddForm = true; resetForm()">添加配置</button>
          </div>
          <div class="card-body">
            <div class="table-responsive">
              <table class="table table-striped">
                <thead>
                  <tr>
                    <th>名称</th>
                    <th>关联MQTT配置</th>
                    <th>订阅主题</th>
                    <th>发布主题</th>
                    <th>数据格式</th>
                    <th>状态</th>
                    <th>操作</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="config in configs" :key="config.id">
                    <td>{{ config.name }}</td>
                    <td>{{ mqttConfigName(config.mqtt_config_id) }}</td>
                    <td>
                      <div v-if="config.subscribe_topics">
                        <span 
                          v-for="topic in parseTopics(config.subscribe_topics)" 
                          :key="topic" 
                          class="badge bg-secondary me-1 mb-1"
                        >
                          {{ topic }}
                        </span>
                      </div>
                      <span v-else class="text-muted">无</span>
                    </td>
                    <td>{{ config.publish_topic || '-' }}</td>
                    <td>{{ config.data_format || 'JSON' }}</td>
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
                <div class="form-text">配置名称必须唯一，用于区分不同主题配置</div>
              </div>
              
              <div class="mb-3">
                <label for="mqtt_config_id" class="form-label">关联MQTT配置 *</label>
                <select
                  class="form-control"
                  id="mqtt_config_id"
                  v-model.number="currentConfig.mqtt_config_id"
                  required
                >
                  <option value="" disabled>请选择MQTT配置</option>
                  <option 
                    v-for="mqttConfig in mqttConfigs" 
                    :key="mqttConfig.id" 
                    :value="mqttConfig.id"
                  >
                    {{ mqttConfig.name }} ({{ mqttConfig.server }}:{{ mqttConfig.port }})
                  </option>
                </select>
              </div>
              
              <div class="mb-3">
                <label for="subscribe_topics" class="form-label">订阅主题</label>
                <textarea
                  class="form-control"
                  id="subscribe_topics"
                  rows="3"
                  placeholder="每行一个主题，例如：device/+/temperature&#10;device/+/humidity"
                  v-model="currentConfig.subscribe_topics"
                ></textarea>
                <div class="form-text">每行一个订阅主题，支持通配符 (+ 和 #)</div>
              </div>
              
              <div class="mb-3">
                <label for="publish_topic" class="form-label">发布主题</label>
                <input
                  type="text"
                  class="form-control"
                  id="publish_topic"
                  placeholder="例如：commands/device1/control"
                  v-model="currentConfig.publish_topic"
                />
              </div>
              
              <div class="mb-3">
                <label for="data_format" class="form-label">数据格式</label>
                <select
                  class="form-control"
                  id="data_format"
                  v-model="currentConfig.data_format"
                >
                  <option value="JSON">JSON</option>
                  <option value="CSV">CSV</option>
                  <option value="PLAIN">纯文本</option>
                </select>
              </div>
              
              <div class="mb-3">
                <label for="device_mapping" class="form-label">设备映射规则</label>
                <textarea
                  class="form-control"
                  id="device_mapping"
                  rows="4"
                  placeholder='例如：{"device/+/temperature": {"type": "temperature", "unit": "°C"}}'
                  v-model="currentConfig.device_mapping"
                ></textarea>
                <div class="form-text">定义如何将收到的主题数据映射到设备和传感器</div>
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
            <h5>配置说明</h5>
          </div>
          <div class="card-body">
            <h6>订阅主题</h6>
            <p>仪表盘将从这些主题消费数据，用于显示实时传感器数据。</p>
            
            <h6>发布主题</h6>
            <p>用于向设备发送控制命令或配置信息。</p>
            
            <h6>数据格式</h6>
            <p>指定消息的格式，系统将按此格式解析数据。</p>
            
            <h6>设备映射规则</h6>
            <p>定义如何将收到的消息与系统中的设备和传感器关联。</p>
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
  name: 'TopicConfig',
  setup() {
    const configs = ref([])
    const mqttConfigs = ref([])
    const showAddForm = ref(false)
    const editingConfig = ref(null)
    const currentConfig = ref({
      id: null,
      name: '',
      mqtt_config_id: null,
      subscribe_topics: '',
      publish_topic: '',
      data_format: 'JSON',
      device_mapping: ''
    })

    const loadConfigs = async () => {
      try {
        const response = await axios.get('/api/topic-configs')
        configs.value = response.data
      } catch (error) {
        console.error('加载主题配置失败:', error)
      }
    }

    const loadMqttConfigs = async () => {
      try {
        const response = await axios.get('/api/mqtt-configs')
        mqttConfigs.value = response.data
      } catch (error) {
        console.error('加载MQTT配置失败:', error)
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
        console.error('保存主题配置失败:', error)
        alert(`保存失败: ${error.message}`)
      }
    }

    const editConfig = (config) => {
      // 如果subscribe_topics是JSON字符串，解析为换行分隔的字符串
      let subscribe_topics = config.subscribe_topics || ''
      try {
        const parsed = JSON.parse(subscribe_topics)
        if (Array.isArray(parsed)) {
          subscribe_topics = parsed.join('\n')
        }
      } catch (e) {
        // 如果不是JSON格式，保持原样
      }
      
      currentConfig.value = { 
        ...config,
        subscribe_topics: subscribe_topics
      }
      editingConfig.value = config.id
      showAddForm.value = true
    }

    const deleteConfig = async (configId) => {
      if (!confirm('确定要删除这个主题配置吗？此操作不可撤销！')) {
        return
      }

      try {
        await axios.delete(`/api/topic-configs/${configId}`)
        await loadConfigs()
        alert('主题配置删除成功')
      } catch (error) {
        console.error('删除主题配置失败:', error)
        alert(`删除失败: ${error.message}`)
      }
    }

    const activateConfig = async (config) => {
      try {
        await axios.post(`/api/topic-configs/${config.id}/activate`)
        await loadConfigs()
        alert(`配置 "${config.name}" 激活成功`)
      } catch (error) {
        console.error('激活主题配置失败:', error)
        alert(`激活失败: ${error.message}`)
      }
    }

    const mqttConfigName = (mqttConfigId) => {
      const config = mqttConfigs.value.find(c => c.id === mqttConfigId)
      return config ? config.name : '未知配置'
    }

    const parseTopics = (topicsStr) => {
      if (!topicsStr) return []
      try {
        // 尝试解析为JSON数组
        const parsed = JSON.parse(topicsStr)
        if (Array.isArray(parsed)) {
          return parsed
        }
      } catch (e) {
        // 如果不是JSON格式，则按换行符分割
        return topicsStr.split('\n').filter(t => t.trim() !== '')
      }
      return []
    }

    const resetForm = () => {
      currentConfig.value = {
        id: null,
        name: '',
        mqtt_config_id: null,
        subscribe_topics: '',
        publish_topic: '',
        data_format: 'JSON',
        device_mapping: ''
      }
      editingConfig.value = null
    }

    onMounted(async () => {
      await Promise.all([
        loadConfigs(),
        loadMqttConfigs()
      ])
    })

    return {
      configs,
      mqttConfigs,
      showAddForm,
      editingConfig,
      currentConfig,
      saveConfig,
      editConfig,
      deleteConfig,
      activateConfig,
      mqttConfigName,
      parseTopics,
      resetForm
    }
  }
}
</script>