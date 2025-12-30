<template>
  <div>
    <div class="d-flex justify-content-between align-items-center mb-3">
      <h2>设备列表</h2>
      <button class="btn btn-primary" @click="addDevice">添加设备</button>
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
                  <router-link :to="`/devices/${device.id}/edit`" class="btn btn-sm btn-outline-secondary me-1">
                    编辑
                  </router-link>
                  <button class="btn btn-sm btn-outline-danger" @click="deleteDevice(device.id)">删除</button>
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
import { useRouter } from 'vue-router'
import axios from 'axios'

export default {
  name: 'DeviceList',
  setup() {
    const devices = ref([])
    const router = useRouter()

    const fetchDevices = async () => {
      try {
        const response = await axios.get('/api/devices')
        devices.value = response.data
      } catch (error) {
        console.error('获取设备列表失败:', error)
      }
    }

    const deleteDevice = async (deviceId) => {
      if (!confirm('确定要删除这个设备吗？此操作不可撤销！')) {
        return;
      }

      try {
        const response = await axios.delete(`/api/devices/${deviceId}`)
        
        if (response.status === 200) {
          // 从列表中移除已删除的设备
          devices.value = devices.value.filter(device => device.id !== deviceId);
          alert('设备删除成功');
        } else {
          alert('删除设备失败');
        }
      } catch (error) {
        console.error('删除设备失败:', error);
        alert('删除设备失败');
      }
    }

    const addDevice = () => {
      router.push('/devices/new')
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
      deleteDevice,
      addDevice,
      formatDate
    }
  }
}
</script>