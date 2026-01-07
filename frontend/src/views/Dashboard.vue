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
            <h5>传感器数据趋势</h5>
          </div>
          <div class="card-body">
            <div id="sensorChart" ref="sensorChartRef" style="height: 400px;"></div>
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
    const sensorChartRef = ref(null)
    let chartInstance = null
    let refreshInterval = null
    
    // 图表数据 - 从 localStorage 加载或初始化
    const loadChartData = () => {
      const savedData = localStorage.getItem('dashboardChartData')
      if (savedData) {
        try {
          const parsed = JSON.parse(savedData)
          return {
            timeStamps: parsed.timeStamps || [],
            sensorData: parsed.sensorData || {}
          }
        } catch (e) {
          console.error('加载图表数据失败:', e)
          return {
            timeStamps: [],
            sensorData: {}
          }
        }
      }
      return {
        timeStamps: [],
        sensorData: {}
      }
    }
    
    // 保存图表数据到 localStorage
    const saveChartData = (data) => {
      try {
        localStorage.setItem('dashboardChartData', JSON.stringify(data))
      } catch (e) {
        console.error('保存图表数据失败:', e)
      }
    }
    
    // 初始化图表数据
    const chartData = loadChartData()

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

    // 获取所有传感器的最新数据
    const fetchLatestSensors = async () => {
      try {
        const response = await axios.get('/api/latest-sensors')
        return response.data
      } catch (error) {
        console.error('获取最新传感器数据失败:', error)
        return []
      }
    }

    // 初始化图表
    const initChart = async () => {
      if (sensorChartRef.value) {
        chartInstance = echarts.init(sensorChartRef.value)
        
        // 获取传感器数据并更新图表
        const sensors = await fetchLatestSensors()
        updateChart(sensors)
      }
    }

    // 更新图表
    const updateChart = (sensorGroups) => {
      if (!chartInstance) return

      // 当前时间戳
      const now = new Date().toLocaleTimeString()
      
      // 更新时间轴数据 - 保留最近20个数据点
      chartData.timeStamps.push(now)
      if(chartData.timeStamps.length > 20) {
        chartData.timeStamps.shift()
      }

      // 准备图表数据 - 按传感器类型分组
      const seriesData = []
      const legendData = []
      
      // 遍历所有设备的传感器数据
      sensorGroups.forEach(deviceData => {
        const deviceName = deviceData.device_name || `设备${deviceData.device_id}`
        
        deviceData.sensors.forEach(sensor => {
          const sensorKey = `${deviceName}-${sensor.type}`
          
          // 初始化传感器数据数组
          if (!chartData.sensorData[sensorKey]) {
            chartData.sensorData[sensorKey] = []
          }
          
          // 添加当前值到传感器数据数组
          chartData.sensorData[sensorKey].push(sensor.value)
          
          // 限制数据长度为20个点
          if(chartData.sensorData[sensorKey].length > 20) {
            chartData.sensorData[sensorKey].shift()
          }
          
          // 添加到图例
          legendData.push(sensorKey)
          
          // 添加到系列数据
          seriesData.push({
            name: sensorKey,
            type: 'line',
            data: chartData.sensorData[sensorKey],
            smooth: true,
            symbol: 'none', // 不显示数据点标记
            lineStyle: {
              width: 2
            }
          })
        })
      })

      const option = {
        tooltip: {
          trigger: 'axis',
          formatter: function(params) {
            if (params.length === 0) return ''
            let result = params[0].axisValue + '<br/>'
            params.forEach(param => {
              result += param.marker + ' ' + param.seriesName + ': ' + param.data + '<br/>'
            })
            return result
          }
        },
        legend: {
          data: legendData,
          type: 'scroll', // 启用滚动功能
          orient: 'horizontal',
          top: '10px',
          left: 'center'
        },
        grid: {
          left: '3%',
          right: '4%',
          bottom: '3%',
          top: '15%',
          containLabel: true
        },
        xAxis: {
          type: 'category',
          boundaryGap: false,
          data: chartData.timeStamps
        },
        yAxis: {
          type: 'value',
          min: function(value) {
            // 确保Y轴最小值略低于数据最小值
            return Math.min(0, value.min * 0.9)
          }
        },
        series: seriesData
      }

      chartInstance.setOption(option, true) // 使用true参数进行完整重绘
      
      // 保存图表数据到 localStorage
      saveChartData(chartData)
    }

    onMounted(async () => {
      await fetchDevices()
      await initChart()

      // 设置定时刷新
      refreshInterval = setInterval(async () => {
        await fetchDevices()
        const sensors = await fetchLatestSensors()
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
      // 保存数据到 localStorage
      saveChartData(chartData)
    })

    // 监听设备数据变化，更新图表
    watch(devices, async () => {
      if (chartInstance) {
        const sensors = await fetchLatestSensors()
        updateChart(sensors)
      }
    }, { deep: true })

    return {
      devices,
      sensorChartRef,
      onlineDevices: onlineDevices(),
      offlineDevices: offlineDevices(),
      sensorCount: sensorCount()
    }
  }
}
</script>