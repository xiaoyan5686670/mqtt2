<template>
  <div class="container-fluid">
    <nav aria-label="breadcrumb">
      <ol class="breadcrumb">
        <li class="breadcrumb-item">
          <router-link to="/dashboard">仪表板</router-link>
        </li>
        <li class="breadcrumb-item">
          <router-link to="/devices">设备列表</router-link>
        </li>
        <li class="breadcrumb-item active" aria-current="page">{{ isEditing ? '编辑设备' : '添加设备' }}</li>
      </ol>
    </nav>

    <div class="card">
      <div class="card-header">
        <h3>{{ isEditing ? '编辑设备' : '添加设备' }}</h3>
      </div>
      <div class="card-body">
        <form @submit.prevent="saveDevice">
          <div class="mb-3">
            <label for="deviceName" class="form-label">设备名称 *</label>
            <input
              type="text"
              class="form-control"
              id="deviceName"
              v-model="deviceForm.name"
              required
            />
          </div>
          
          <div class="mb-3">
            <label for="deviceType" class="form-label">设备类型 *</label>
            <input
              type="text"
              class="form-control"
              id="deviceType"
              v-model="deviceForm.device_type"
              required
            />
          </div>
          
          <div class="mb-3">
            <label for="deviceLocation" class="form-label">设备位置</label>
            <input
              type="text"
              class="form-control"
              id="deviceLocation"
              v-model="deviceForm.location"
            />
          </div>
          
          <div class="mb-3">
            <label for="mqttConfig" class="form-label">MQTT配置</label>
            <select
              class="form-control"
              id="mqttConfig"
              v-model="deviceForm.mqtt_config_id"
            >
              <option value="">请选择MQTT配置</option>
              <option v-for="config in mqttConfigs" :key="config.id" :value="config.id">
                {{ config.name }} ({{ config.server }}:{{ config.port }})
              </option>
            </select>
            <div class="form-text">选择用于此设备通信的MQTT配置</div>
          </div>
          
          <div class="mb-3">
            <label for="topicConfig" class="form-label">主题配置</label>
            <select
              class="form-control"
              id="topicConfig"
              v-model="deviceForm.topic_config_id"
            >
              <option value="">请选择主题配置</option>
              <option v-for="config in topicConfigs" :key="config.id" :value="config.id">
                {{ config.name }}
              </option>
            </select>
            <div class="form-text">选择用于此设备数据订阅/发布的主题配置</div>
          </div>
          
          <div class="d-grid gap-2 d-md-flex justify-content-md-end">
            <router-link to="/devices" class="btn btn-secondary me-2">取消</router-link>
            <button type="submit" class="btn btn-primary">
              {{ isEditing ? '更新设备' : '添加设备' }}
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import axios from 'axios'

export default {
  name: 'DeviceEdit',
  setup() {
    const route = useRoute()
    const router = useRouter()
    const isEditing = ref(!!route.params.id)
    const mqttConfigs = ref([])
    const topicConfigs = ref([])
    
    const deviceForm = ref({
      name: '',
      device_type: '',  // 改为与后端API匹配的字段名
      location: '',
      mqtt_config_id: null,
      topic_config_id: null
    })

    // 加载MQTT配置列表
    const loadMqttConfigs = async () => {
      try {
        const response = await axios.get('/api/mqtt-configs')
        mqttConfigs.value = Array.isArray(response.data) ? response.data : []
      } catch (error) {
        console.error('加载MQTT配置失败:', error)
        mqttConfigs.value = []
      }
    }

    // 加载主题配置列表
    const loadTopicConfigs = async () => {
      try {
        const response = await axios.get('/api/topic-configs')
        topicConfigs.value = Array.isArray(response.data) ? response.data : []
      } catch (error) {
        console.error('加载主题配置失败:', error)
        topicConfigs.value = []
      }
    }

    // 加载设备详情（编辑模式）
    const loadDevice = async () => {
      try {
        const response = await axios.get(`/api/devices/${route.params.id}`)
        const device = response.data
        deviceForm.value = {
          name: device.name,
          device_type: device.device_type,  // 映射到正确的字段
          location: device.location,
          mqtt_config_id: device.mqtt_config_id || null,
          topic_config_id: device.topic_config_id || null
        }
      } catch (error) {
        console.error('加载设备详情失败:', error)
      }
    }

    // 保存设备
    const saveDevice = async () => {
      try {
        if (isEditing.value) {
          // 更新设备
          await axios.put(`/api/devices/${route.params.id}`, deviceForm.value)
          alert('设备更新成功')
        } else {
          // 添加设备
          await axios.post('/api/devices', deviceForm.value)
          alert('设备添加成功')
        }
        
        // 跳转回设备列表
        router.push('/devices')
      } catch (error) {
        console.error(isEditing.value ? '更新设备失败:' : '添加设备失败:', error)
        alert(isEditing.value ? '更新设备失败' : '添加设备失败')
      }
    }

    onMounted(async () => {
      await loadMqttConfigs()
      await loadTopicConfigs()
      
      if (isEditing.value) {
        await loadDevice()
      }
    })

    return {
      isEditing,
      deviceForm,
      mqttConfigs,
      topicConfigs,
      saveDevice
    }
  }
}
</script>