<template>
  <div>
    <h2>实时传感器数据</h2>

    <!-- 设备选择容器，框住所有传感器组 -->
    <div class="device-container card">
      <div class="card-header bg-primary text-white">
        <h4 class="mb-0">
          <i class="fas fa-microchip"></i> 
          当前设备: 
          <select 
            class="device-select" 
            v-model="selectedDeviceId"
            @change="onDeviceChange"
          >
            <option value="">请选择设备</option>
            <option v-for="device in devices" :key="device.id" :value="device.id">
              {{ device.name }} ({{ device.location || '未知位置' }})
            </option>
          </select>
        </h4>
      </div>
      
      <div class="card-body">
        <!-- 数据加载状态指示 -->
        <div v-if="loadingData" class="text-center">
          <div class="spinner-border" role="status">
            <span class="visually-hidden">加载中...</span>
          </div>
          <p>正在加载传感器数据...</p>
        </div>
        
        <!-- 错误信息 -->
        <div v-if="error" class="alert alert-danger">
          {{ error }}
        </div>
        
        <div class="row" v-if="!loadingData">
          <!-- 温湿度传感器1 -->
          <div class="col-md-4">
            <div class="card sensor-card">
              <div class="card-header bg-light">
                <h5 class="mb-0">传感器组 1 (Temperature1 & Humidity1)</h5>
              </div>
              <div class="card-body">
                <div class="sensor-values">
                  <div class="row">
                    <div class="col">
                      <p class="mb-1">温度: <span class="fw-bold">{{ sensorData.temp1 }}°C</span></p>
                      <p class="mb-1">湿度: <span class="fw-bold">{{ sensorData.hum1 }}%</span></p>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- 温湿度传感器2 -->
          <div class="col-md-4">
            <div class="card sensor-card">
              <div class="card-header bg-light">
                <h5 class="mb-0">传感器组 2 (Temperature2 & Humidity2)</h5>
              </div>
              <div class="card-body">
                <div class="sensor-values">
                  <div class="row">
                    <div class="col">
                      <p class="mb-1">温度: <span class="fw-bold">{{ sensorData.temp2 }}°C</span></p>
                      <p class="mb-1">湿度: <span class="fw-bold">{{ sensorData.hum2 }}%</span></p>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- 继电器和PB8 -->
          <div class="col-md-4">
            <div class="card sensor-card">
              <div class="card-header bg-light">
                <h5 class="mb-0">控制组 (Relay & PB8)</h5>
              </div>
              <div class="card-body">
                <div class="sensor-values">
                  <div class="row">
                    <div class="col">
                      <p class="mb-1">继电器状态: 
                        <span class="fw-bold" :class="sensorData.relay === 1 ? 'text-success' : 'text-danger'">
                          {{ sensorData.relay === 1 ? '开启' : '关闭' }}
                        </span>
                      </p>
                      <p class="mb-1">PB8电平: 
                        <span class="fw-bold" :class="sensorData.pb8 === 1 ? 'text-success' : 'text-primary'">
                          {{ sensorData.pb8 === 1 ? '高电平' : '低电平' }}
                        </span>
                      </p>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
        
        <!-- 趋势图区域 - 独立显示 -->
        <div class="trend-charts-section mt-4">
          <div class="row">
            <div class="col-12">
              <div class="card">
                <div class="card-header bg-info text-white">
                  <h5 class="mb-0">
                    <i class="fas fa-chart-line"></i> 传感器数据趋势图
                  </h5>
                </div>
                <div class="card-body">
                  <div class="row">
                    <!-- 温湿度传感器1趋势图 -->
                    <div class="col-md-4">
                      <div class="chart-container">
                        <div ref="chart1Ref" style="height: 300px;"></div>
                      </div>
                    </div>
                    
                    <!-- 温湿度传感器2趋势图 -->
                    <div class="col-md-4">
                      <div class="chart-container">
                        <div ref="chart2Ref" style="height: 300px;"></div>
                      </div>
                    </div>
                    
                    <!-- 继电器和PB8趋势图 -->
                    <div class="col-md-4">
                      <div class="chart-container">
                        <div ref="chart3Ref" style="height: 300px;"></div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted, onUnmounted, nextTick } from 'vue'
import * as echarts from 'echarts'
import axios from 'axios'

export default {
  name: 'RealTimeData',
  setup() {
    // 传感器数据
    const sensorData = ref({
      temp1: 0,
      hum1: 0,
      temp2: 0,
      hum2: 0,
      relay: 0,
      pb8: 0
    })
    
    // 设备列表
    const devices = ref([])
    
    // 当前选中的设备ID
    const selectedDeviceId = ref('')
    
    // 加载状态
    const loadingData = ref(false)
    
    // 错误信息
    const error = ref('')
    
    // 图表引用
    const chart1Ref = ref(null)
    const chart2Ref = ref(null)
    const chart3Ref = ref(null)
    
    // 图表实例
    let chart1 = null
    let chart2 = null
    let chart3 = null
    
    // 图表数据 - 保存最近20个数据点
    const chartData = ref({
      timeStamps: [],
      temp1Data: [],
      hum1Data: [],
      temp2Data: [],
      hum2Data: [],
      relayData: [],
      pb8Data: []
    })
    
    // 获取设备列表
    const fetchDevices = async () => {
      try {
        const response = await axios.get('/api/devices')
        devices.value = response.data
      } catch (error) {
        console.error('获取设备列表失败:', error)
        error.value = '获取设备列表失败: ' + error.message
      }
    }
    
    // 更新图表 - 改为显示时间序列数据
    const updateCharts = () => {
      // 当前时间戳
      const now = new Date().toLocaleTimeString()
      
      // 更新时间轴数据 - 保留最近20个数据点
      chartData.value.timeStamps.push(now)
      if(chartData.value.timeStamps.length > 20) {
        chartData.value.timeStamps.shift()
      }
      
      // 更新传感器数据
      chartData.value.temp1Data.push(sensorData.value.temp1)
      chartData.value.hum1Data.push(sensorData.value.hum1)
      chartData.value.temp2Data.push(sensorData.value.temp2)
      chartData.value.hum2Data.push(sensorData.value.hum2)
      chartData.value.relayData.push(sensorData.value.relay)
      chartData.value.pb8Data.push(sensorData.value.pb8)
      
      // 限制数据长度为20个点
      if(chartData.value.temp1Data.length > 20) chartData.value.temp1Data.shift()
      if(chartData.value.hum1Data.length > 20) chartData.value.hum1Data.shift()
      if(chartData.value.temp2Data.length > 20) chartData.value.temp2Data.shift()
      if(chartData.value.hum2Data.length > 20) chartData.value.hum2Data.shift()
      if(chartData.value.relayData.length > 20) chartData.value.relayData.shift()
      if(chartData.value.pb8Data.length > 20) chartData.value.pb8Data.shift()
      
      // 图表1 - 温湿度传感器1
      if (chart1) {
        const option1 = {
          title: {
            text: '温湿度1趋势'
          },
          tooltip: {
            trigger: 'axis'
          },
          legend: {
            data: ['温度', '湿度']
          },
          xAxis: {
            type: 'category',
            boundaryGap: false,
            data: chartData.value.timeStamps
          },
          yAxis: [
            {
              type: 'value',
              name: '温度 (°C)',
              position: 'left',
              min: 0,
              max: 50
            },
            {
              type: 'value',
              name: '湿度 (%)',
              position: 'right',
              min: 0,
              max: 100
            }
          ],
          series: [
            {
              name: '温度',
              type: 'line',
              yAxisIndex: 0,
              data: chartData.value.temp1Data,
              itemStyle: { color: '#FF6384' },
              smooth: true
            },
            {
              name: '湿度',
              type: 'line',
              yAxisIndex: 1,
              data: chartData.value.hum1Data,
              itemStyle: { color: '#36A2EB' },
              smooth: true
            }
          ]
        }
        chart1.setOption(option1, { notMerge: true })
      }
      
      // 图表2 - 温湿度传感器2
      if (chart2) {
        const option2 = {
          title: {
            text: '温湿度2趋势'
          },
          tooltip: {
            trigger: 'axis'
          },
          legend: {
            data: ['温度', '湿度']
          },
          xAxis: {
            type: 'category',
            boundaryGap: false,
            data: chartData.value.timeStamps
          },
          yAxis: [
            {
              type: 'value',
              name: '温度 (°C)',
              position: 'left',
              min: 0,
              max: 50
            },
            {
              type: 'value',
              name: '湿度 (%)',
              position: 'right',
              min: 0,
              max: 100
            }
          ],
          series: [
            {
              name: '温度',
              type: 'line',
              yAxisIndex: 0,
              data: chartData.value.temp2Data,
              itemStyle: { color: '#FF6384' },
              smooth: true
            },
            {
              name: '湿度',
              type: 'line',
              yAxisIndex: 1,
              data: chartData.value.hum2Data,
              itemStyle: { color: '#36A2EB' },
              smooth: true
            }
          ]
        }
        chart2.setOption(option2, { notMerge: true })
      }
      
      // 图表3 - 继电器和PB8
      if (chart3) {
        const option3 = {
          title: {
            text: '控制状态趋势'
          },
          tooltip: {
            trigger: 'axis'
          },
          legend: {
            data: ['继电器', 'PB8']
          },
          xAxis: {
            type: 'category',
            boundaryGap: false,
            data: chartData.value.timeStamps
          },
          yAxis: {
            type: 'value',
            min: 0,
            max: 1,
            interval: 1
          },
          series: [
            {
              name: '继电器',
              type: 'line',
              step: 'start',
              data: chartData.value.relayData,
              itemStyle: { color: '#4CAF50' },
              areaStyle: {}
            },
            {
              name: 'PB8',
              type: 'line',
              step: 'start',
              data: chartData.value.pb8Data,
              itemStyle: { color: '#2196F3' },
              areaStyle: {}
            }
          ]
        }
        chart3.setOption(option3, { notMerge: true })
      }
    }
    
    // 获取实时数据
    const fetchRealTimeData = async () => {
      if (!selectedDeviceId.value) {
        error.value = '请先选择一个设备'
        return
      }
      
      loadingData.value = true
      error.value = ''
      
      try {
        // 获取指定设备的最新传感器数据
        const response = await axios.get(`/api/devices/${selectedDeviceId.value}/latest-sensors`)
        console.log('API Response:', response.data) // 调试信息
        
        // 临时存储数据，以便在出错时保留旧数据
        const tempSensorData = { ...sensorData.value }
        
        // 重置数据
        tempSensorData.temp1 = 0
        tempSensorData.hum1 = 0
        tempSensorData.temp2 = 0
        tempSensorData.hum2 = 0
        tempSensorData.relay = 0
        tempSensorData.pb8 = 0
        
        const sensors = response.data
        
        for (const sensor of sensors) {
          console.log('Processing sensor:', sensor) // 调试信息
          if (sensor.type === 'Temperature1') {
            tempSensorData.temp1 = sensor.value
          } else if (sensor.type === 'Humidity1') {
            tempSensorData.hum1 = sensor.value
          } else if (sensor.type === 'Temperature2') {
            tempSensorData.temp2 = sensor.value
          } else if (sensor.type === 'Humidity2') {
            tempSensorData.hum2 = sensor.value
          } else if (sensor.type === 'Relay Status') {
            tempSensorData.relay = sensor.value
          } else if (sensor.type === 'PB8 Level') {
            tempSensorData.pb8 = sensor.value
          }
        }
        
        // 只有在成功处理完数据后才更新实际的数据
        sensorData.value = tempSensorData
        
        console.log('Updated sensor data:', sensorData.value) // 调试信息
        
        // 更新图表
        updateCharts()
      } catch (err) {
        console.error('获取实时数据失败:', err)
        error.value = `获取数据失败: ${err.message || '未知错误'}`
        
        // 不要清空现有数据，保留最后一次有效数据
      } finally {
        loadingData.value = false
      }
    }
    
    // 设备选择变化时的处理
    const onDeviceChange = () => {
      // 保存设备选择到本地存储
      localStorage.setItem('selectedDeviceId', selectedDeviceId.value)
      
      // 清空图表数据，准备显示新设备的数据
      chartData.value = {
        timeStamps: [],
        temp1Data: [],
        hum1Data: [],
        temp2Data: [],
        hum2Data: [],
        relayData: [],
        pb8Data: []
      }
      
      // 重新获取数据
      fetchRealTimeData()
    }
    
    // 从本地存储加载设备选择
    const loadSelectedDevice = () => {
      const savedDeviceId = localStorage.getItem('selectedDeviceId')
      if (savedDeviceId && devices.value.some(device => device.id == savedDeviceId)) {
        selectedDeviceId.value = savedDeviceId
      }
    }
    
    // 初始化图表
    const initCharts = async () => {
      await nextTick() // 确保DOM已更新
      
      if (chart1Ref.value) {
        chart1 = echarts.init(chart1Ref.value)
      }
      if (chart2Ref.value) {
        chart2 = echarts.init(chart2Ref.value)
      }
      if (chart3Ref.value) {
        chart3 = echarts.init(chart3Ref.value)
      }
      
      // 如果已有选中设备，获取数据
      if (selectedDeviceId.value) {
        fetchRealTimeData()
      }
    }
    
    onMounted(async () => {
      // 获取设备列表
      await fetchDevices()
      
      // 等待设备列表加载完成后再加载选中的设备
      loadSelectedDevice()
      
      // 初始化图表
      await initCharts()
      
      // 设置定时更新（每3秒更新一次）
      const interval = setInterval(() => {
        if (selectedDeviceId.value) {
          fetchRealTimeData()
        }
      }, 3000)
      
      // 保存interval ID以便在组件卸载时清理
      window.realtimeInterval = interval
    })
    
    onUnmounted(() => {
      // 清理定时器
      if (window.realtimeInterval) {
        clearInterval(window.realtimeInterval)
        window.realtimeInterval = null
      }
      
      // 销毁图表实例
      if (chart1) chart1.dispose()
      if (chart2) chart2.dispose()
      if (chart3) chart3.dispose()
    })
    
    return {
      sensorData,
      devices,
      selectedDeviceId,
      loadingData,
      error,
      onDeviceChange,
      chart1Ref,
      chart2Ref,
      chart3Ref
    }
  }
}
</script>

<style scoped>
.device-container {
  margin-top: 20px;
  border: 2px solid #007bff;
  border-radius: 10px;
  box-shadow: 0 4px 8px rgba(0,0,0,0.1);
}

.device-select {
  margin-left: 10px;
  padding: 5px 10px;
  border-radius: 5px;
  border: 1px solid #ced4da;
  background-color: white;
  color: #495057;
  font-size: 16px;
  min-width: 300px;
}

.sensor-card {
  height: 100%;
  transition: transform 0.3s ease;
}

.sensor-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 6px 12px rgba(0,0,0,0.15);
}

.card-header {
  font-weight: bold;
}

.sensor-values {
  text-align: center;
}

.card-body {
  padding: 1.25rem;
}

.trend-charts-section {
  margin-top: 20px;
}

.chart-container {
  background-color: #f8f9fa;
  border-radius: 8px;
  padding: 10px;
  height: 100%;
}

@media (max-width: 768px) {
  .device-select {
    display: block;
    width: 100%;
    margin-top: 10px;
    min-width: auto;
  }
  
  .col-md-4 {
    margin-bottom: 1.5rem;
  }
  
  .col-md-4 .chart-container {
    margin-top: 15px;
  }
}
</style>