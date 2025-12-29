<template>
  <div>
    <div class="d-flex justify-content-between align-items-center mb-3">
      <h2>设备列表</h2>
      <button class="btn btn-primary">添加设备</button>
    </div>

    <div class="card">
      <div class="card-body">
        <div class="table-responsive">
          <table class="table table-striped">
            <thead>
              <tr>
                <th>ID</th>
                <th>名称</th>
                <th>类型</th>
                <th>位置</th>
                <th>状态</th>
                <th>最后更新</th>
                <th>操作</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="device in devices" :key="device.id">
                <td>{{ device.id }}</td>
                <td>{{ device.name }}</td>
                <td>{{ device.type }}</td>
                <td>{{ device.location || '未知' }}</td>
                <td>
                  <span :class="device.is_online ? 'text-success' : 'text-danger'">
                    {{ device.is_online ? '在线' : '离线' }}
                  </span>
                </td>
                <td>{{ formatDate(device.last_seen) }}</td>
                <td>
                  <router-link :to="`/devices/${device.id}`" class="btn btn-sm btn-outline-primary me-1">
                    查看
                  </router-link>
                  <button class="btn btn-sm btn-outline-secondary me-1">编辑</button>
                  <button class="btn btn-sm btn-outline-danger">删除</button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted } from 'vue'
import axios from 'axios'

export default {
  name: 'DeviceList',
  setup() {
    const devices = ref([])

    const fetchDevices = async () => {
      try {
        const response = await axios.get('/api/devices')
        devices.value = response.data
      } catch (error) {
        console.error('获取设备列表失败:', error)
      }
    }

    const formatDate = (dateString) => {
      if (!dateString) return '未知'
      const date = new Date(dateString)
      return date.toLocaleString('zh-CN')
    }

    onMounted(() => {
      fetchDevices()
    })

    return {
      devices,
      formatDate
    }
  }
}
</script>