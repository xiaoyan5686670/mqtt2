<template>
  <div>
    <nav aria-label="breadcrumb">
      <ol class="breadcrumb">
        <li class="breadcrumb-item">
          <router-link to="/dashboard">仪表板</router-link>
        </li>
        <li class="breadcrumb-item">
          <router-link to="/devices">设备列表</router-link>
        </li>
        <li class="breadcrumb-item active" aria-current="page">设备详情</li>
      </ol>
    </nav>

    <div v-if="device" class="card">
      <div class="card-header">
        <div class="d-flex justify-content-between align-items-center">
          <h3>{{ device.name }}</h3>
          <div>
            <button class="btn btn-sm btn-outline-secondary me-2">编辑</button>
            <button class="btn btn-sm btn-outline-danger" @click="deleteDevice">删除</button>
          </div>
        </div>
      </div>
      <div class="card-body">
        <div class="row">
          <div class="col-md-6">
            <table class="table">
              <tbody>
                <tr>
                  <th>ID</th>
                  <td>{{ device.id }}</td>
                </tr>
                <tr>
                  <th>名称</th>
                  <td>{{ device.name }}</td>
                </tr>
                <tr>
                  <th>类型</th>
                  <td>{{ device.type }}</td>
                </tr>
                <tr>
                  <th>位置</th>
                  <td>{{ device.location || '未设置' }}</td>
                </tr>
                <tr>
                  <th>状态</th>
                  <td>
                    <span :class="device.is_online ? 'text-success' : 'text-danger'">
                      {{ device.is_online ? '在线' : '离线' }}
                    </span>
                  </td>
                </tr>
                <tr>
                  <th>最后更新</th>
                  <td>{{ formatDate(device.last_seen) }}</td>
                </tr>
              </tbody>
            </table>
          </div>
          <div class="col-md-6">
            <div class="card">
              <div class="card-header">
                <h5>传感器数据</h5>
              </div>
              <div class="card-body">
                <div v-if="device.sensors && device.sensors.length > 0">
                  <div class="sensor-item mb-3" v-for="sensor in device.sensors" :key="sensor.id">
                    <div class="d-flex justify-content-between">
                      <strong>{{ sensor.name }}</strong>
                      <span class="badge bg-primary">{{ sensor.value }} {{ sensor.unit }}</span>
                    </div>
                    <div class="progress mt-1" style="height: 10px;">
                      <div 
                        class="progress-bar" 
                        :style="{ width: getSensorPercentage(sensor) + '%' }"
                        :class="getSensorStatusClass(sensor)"
                      ></div>
                    </div>
                  </div>
                </div>
                <div v-else class="text-muted">暂无传感器数据</div>
              </div>
            </div>
          </div>
        </div>

        <div class="row mt-4" v-if="device.sensors && device.sensors.length > 0">
          <div class="col-12">
            <div class="card">
              <div class="card-header">
                <h5>传感器数据图表</h5>
              </div>
              <div class="card-body">
                <div id="sensorChart" style="height: 400px;"></div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div v-else class="text-center py-5">
      <div class="spinner-border" role="status">
        <span class="visually-hidden">加载中...</span>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import * as echarts from 'echarts'
import axios from 'axios'

export default {
  name: 'DeviceDetail',
  setup() {
    const route = useRoute()
    const router = useRouter()
    const device = ref(null)
    const sensorChart = ref(null)
    let chartInstance = null
    let refreshInterval = null

    const fetchDevice = async () => {
      try {
        const response = await axios.get(`/api/devices/${route.params.id}`)
        device.value = response.data
        updateChart()
      } catch (error) {
        // 如果设备不存在（404错误），跳转回设备列表
        if (error.response && error.response.status === 404) {
          console.warn('设备不存在，跳转回设备列表');
          router.push('/devices');
        } else {
          console.error('获取设备详情失败:', error);
        }
      }
    }

    const deleteDevice = async () => {
      if (!confirm('确定要删除这个设备吗？此操作不可撤销！')) {
        return;
      }

      try {
        const response = await axios.delete(`/api/devices/${route.params.id}`)
        
        if (response.status === 200) {
          alert('设备删除成功');
          router.push('/devices'); // 跳转回设备列表页面
        } else {
          alert('删除设备失败');
        }
      } catch (error) {
        console.error('删除设备失败:', error);
        alert('删除设备失败');
      }
    }

    const formatDate = (dateString) => {
      if (!dateString) return '未知'
      const date = new Date(dateString)
      return date.toLocaleString('zh-CN')
    }

    const getSensorPercentage = (sensor) => {
      // 假设传感器有最小值和最大值用于计算百分比
      if (sensor.min_value !== undefined && sensor.max_value !== undefined) {
        const percentage = ((sensor.value - sensor.min_value) / (sensor.max_value - sensor.min_value)) * 100
        return Math.min(100, Math.max(0, percentage))
      }
      return 50 // 默认50%
    }

    const getSensorStatusClass = (sensor) => {
      // 根据传感器值返回不同的进度条样式
      const percentage = getSensorPercentage(sensor)
      if (percentage < 30) return 'bg-success'
      if (percentage < 70) return 'bg-warning'
      return 'bg-danger'
    }

    const updateChart = () => {
      if (!device.value || !device.value.sensors || !sensorChart.value) return

      if (!chartInstance) {
        chartInstance = echarts.init(sensorChart.value)
      }

      const sensorNames = device.value.sensors.map(sensor => sensor.name)
      const sensorValues = device.value.sensors.map(sensor => sensor.value)

      const option = {
        tooltip: {
          trigger: 'axis',
          axisPointer: {
            type: 'shadow'
          }
        },
        grid: {
          left: '3%',
          right: '4%',
          bottom: '3%',
          containLabel: true
        },
        xAxis: {
          type: 'value',
          boundaryGap: [0, 0.01]
        },
        yAxis: {
          type: 'category',
          data: sensorNames
        },
        series: [
          {
            name: '传感器值',
            type: 'bar',
            data: sensorValues,
            itemStyle: {
              color: '#3498db'
            }
          }
        ]
      }

      chartInstance.setOption(option)
    }

    onMounted(() => {
      fetchDevice()
      
      // 设置定时刷新
      refreshInterval = setInterval(() => {
        // 只有在设备存在的情况下才刷新
        if (device.value) {
          fetchDevice()
        }
      }, 5000)
    })

    onUnmounted(() => {
      if (chartInstance) {
        chartInstance.dispose()
      }
      if (refreshInterval) {
        clearInterval(refreshInterval)
      }
    })

    return {
      device,
      sensorChart,
      deleteDevice,
      formatDate,
      getSensorPercentage,
      getSensorStatusClass
    }
  }
}
</script>

<style scoped>
.sensor-item {
  padding: 8px 0;
}
</style>