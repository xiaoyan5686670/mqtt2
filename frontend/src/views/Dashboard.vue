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

    <!-- 传感器数据组件与设备状态概览组件水平对齐 -->
    <div class="row mt-4">
      <div class="col-md-12">
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

    // 获取传感器数据
    const fetchSensors = async () => {
      try {
        const response = await axios.get('/api/sensors')
        return response.data
      } catch (error) {
        console.error('获取传感器数据失败:', error)
        return []
      }
    }

    // 初始化图表
    const initChart = async () => {
      if (sensorChart.value) {
        chartInstance = echarts.init(sensorChart.value)
        
        // 获取传感器数据并更新图表
        const sensors = await fetchSensors()
        updateChart(sensors)
      }
    }

    // 更新图表
    const updateChart = (sensors) => {
      if (!chartInstance) return

      // 准备图表数据 - 按设备分组显示传感器数据
      const groupedData = {}
      sensors.forEach(sensor => {
        const deviceKey = sensor.device_id
        if (!groupedData[deviceKey]) {
          groupedData[deviceKey] = []
        }
        groupedData[deviceKey].push(sensor)
      })

      // 为每个设备创建一个图表系列
      const seriesData = []
      for (const [deviceId, deviceSensors] of Object.entries(groupedData)) {
        const device = devices.value.find(d => d.id == deviceId)
        const deviceName = device ? device.name : `设备${deviceId}`
        
        deviceSensors.forEach(sensor => {
          seriesData.push({
            name: `${deviceName}-${sensor.type}`,
            value: sensor.value,
            unit: sensor.unit
          })
        })
      }

      const option = {
        tooltip: {
          trigger: 'item',
          formatter: '{a} <br/>{b}: {c} {d}'
        },
        legend: {
          top: '5%',
          left: 'center'
        },
        series: [{
          name: '传感器数据',
          type: 'pie',
          radius: ['30%', '60%'],
          avoidLabelOverlap: false,
          itemStyle: {
            borderRadius: 10,
            borderColor: '#fff',
            borderWidth: 2
          },
          label: {
            show: true,
            formatter: '{b}: {c} {d}%'
          },
          emphasis: {
            label: {
              show: true,
              fontSize: '14',
              fontWeight: 'bold'
            }
          },
          labelLine: {
            show: true
          },
          data: seriesData
        }]
      }

      chartInstance.setOption(option, true) // 使用true参数进行完整重绘
    }

    onMounted(async () => {
      await fetchDevices()
      await initChart()

      // 设置定时刷新
      refreshInterval = setInterval(async () => {
        await fetchDevices()
        const sensors = await fetchSensors()
        updateChart(sensors)
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
    watch(devices, async () => {
      if (chartInstance) {
        const sensors = await fetchSensors()
        updateChart(sensors)
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