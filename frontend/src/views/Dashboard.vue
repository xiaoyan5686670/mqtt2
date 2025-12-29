<template>
  <div>
    <h2>设备仪表板</h2>
    
    <div class="row">
      <div class="col-md-12">
        <div class="card">
          <div class="card-header">
            <h5>设备状态概览</h5>
          </div>
          <div class="card-body">
            <div class="row text-center">
              <div class="col-md-3 mb-3">
                <div class="card bg-primary text-white">
                  <div class="card-body">
                    <h3>{{ devices.length }}</h3>
                    <p>总设备数</p>
                  </div>
                </div>
              </div>
              <div class="col-md-3 mb-3">
                <div class="card bg-success text-white">
                  <div class="card-body">
                    <h3>{{ onlineDevices }}</h3>
                    <p>在线设备</p>
                  </div>
                </div>
              </div>
              <div class="col-md-3 mb-3">
                <div class="card bg-warning text-white">
                  <div class="card-body">
                    <h3>{{ offlineDevices }}</h3>
                    <p>离线设备</p>
                  </div>
                </div>
              </div>
              <div class="col-md-3 mb-3">
                <div class="card bg-info text-white">
                  <div class="card-body">
                    <h3>{{ sensorCount }}</h3>
                    <p>传感器总数</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div class="row mt-4">
      <div class="col-md-6">
        <div class="card">
          <div class="card-header">
            <h5>设备列表</h5>
          </div>
          <div class="card-body">
            <div class="table-responsive">
              <table class="table table-striped">
                <thead>
                  <tr>
                    <th>ID</th>
                    <th>名称</th>
                    <th>类型</th>
                    <th>状态</th>
                    <th>操作</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="device in devices" :key="device.id">
                    <td>{{ device.id }}</td>
                    <td>{{ device.name }}</td>
                    <td>{{ device.type }}</td>
                    <td>
                      <span :class="device.is_online ? 'text-success' : 'text-danger'">
                        {{ device.is_online ? '在线' : '离线' }}
                      </span>
                    </td>
                    <td>
                      <router-link :to="`/devices/${device.id}`" class="btn btn-sm btn-outline-primary">
                        查看详情
                      </router-link>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </div>

      <div class="col-md-6">
        <div class="card">
          <div class="card-header">
            <h5>传感器数据</h5>
          </div>
          <div class="card-body">
            <div id="sensorChart" style="height: 400px;"></div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted, onUnmounted, watch } from 'vue'
import * as echarts from 'echarts'
import axios from 'axios'

export default {
  name: 'Dashboard',
  setup() {
    const devices = ref([])
    const sensorChart = ref(null)
    let chartInstance = null
    let refreshInterval = null

    // 计算属性
    const onlineDevices = () => devices.value.filter(d => d.is_online).length
    const offlineDevices = () => devices.value.filter(d => !d.is_online).length
    const sensorCount = () => {
      return devices.value.reduce((count, device) => {
        return count + (device.sensors ? device.sensors.length : 0)
      }, 0)
    }

    // 获取设备数据
    const fetchDevices = async () => {
      try {
        const response = await axios.get('/api/devices')
        devices.value = response.data
      } catch (error) {
        console.error('获取设备数据失败:', error)
      }
    }

    // 初始化图表
    const initChart = () => {
      if (sensorChart.value) {
        chartInstance = echarts.init(sensorChart.value)
        updateChart()
      }
    }

    // 更新图表
    const updateChart = () => {
      if (!chartInstance) return

      // 准备图表数据
      const sensorData = []
      devices.value.forEach(device => {
        if (device.sensors) {
          device.sensors.forEach(sensor => {
            sensorData.push({
              name: `${device.name}-${sensor.name}`,
              value: sensor.value
            })
          })
        }
      })

      const option = {
        tooltip: {
          trigger: 'item'
        },
        legend: {
          top: '5%',
          left: 'center'
        },
        series: [{
          name: '传感器数据',
          type: 'pie',
          radius: ['40%', '70%'],
          avoidLabelOverlap: false,
          itemStyle: {
            borderRadius: 10,
            borderColor: '#fff',
            borderWidth: 2
          },
          label: {
            show: true,
            formatter: '{b}: {c}'
          },
          emphasis: {
            label: {
              show: true,
              fontSize: '18',
              fontWeight: 'bold'
            }
          },
          labelLine: {
            show: true
          },
          data: sensorData
        }]
      }

      chartInstance.setOption(option)
    }

    onMounted(() => {
      fetchDevices()
      initChart()

      // 设置定时刷新
      refreshInterval = setInterval(() => {
        fetchDevices()
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

    // 监听设备数据变化，更新图表
    watch(devices, () => {
      if (chartInstance) {
        updateChart()
      }
    }, { deep: true })

    return {
      devices,
      sensorChart,
      onlineDevices: onlineDevices(),
      offlineDevices: offlineDevices(),
      sensorCount: sensorCount()
    }
  }
}
</script>