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
        <div class="row">
          <!-- 温湿度传感器1 -->
          <div class="col-md-4">
            <div class="card sensor-card">
              <div class="card-header bg-light">
                <h5 class="mb-0">传感器组 1 (Temperature1 & Humidity1)</h5>
              </div>
              <div class="card-body">
                <div id="chart1" style="height: 300px;"></div>
                <div class="sensor-values mt-3">
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
                <div id="chart2" style="height: 300px;"></div>
                <div class="sensor-values mt-3">
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
                <div id="chart3" style="height: 300px;"></div>
                <div class="sensor-values mt-3">
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
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted, onUnmounted } from 'vue'
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
    
    // 图表实例
    let chart1 = null
    let chart2 = null
    let chart3 = null
    
    // 获取设备列表
    const fetchDevices = async () => {
      try {
        const response = await axios.get('/api/devices')
        devices.value = response.data
      } catch (error) {
        console.error('获取设备列表失败:', error)
      }
    }
    
    // 解析传感器数据
    const parseSensorData = (rawData) => {
      // 示例数据格式: "Temperature1: 22.10 C, Humidity1: 16.10 %\nTemperature2: 21.80 C, Humidity2: 23.40 %\nRelay Status: 1\nPB8 Level: 1"
      
      // 解析温度1和湿度1
      const temp1Match = rawData.match(/Temperature1:\s*([\d.]+)\s*C/)
      const hum1Match = rawData.match(/Humidity1:\s*([\d.]+)\s*%/)
      
      // 解析温度2和湿度2
      const temp2Match = rawData.match(/Temperature2:\s*([\d.]+)\s*C/)
      const hum2Match = rawData.match(/Humidity2:\s*([\d.]+)\s*%/)
      
      // 解析继电器状态
      const relayMatch = rawData.match(/Relay Status:\s*(\d)/)
      
      // 解析PB8电平
      const pb8Match = rawData.match(/PB8 Level:\s*(\d)/)
      
      return {
        temp1: temp1Match ? parseFloat(temp1Match[1]) : 0,
        hum1: hum1Match ? parseFloat(hum1Match[1]) : 0,
        temp2: temp2Match ? parseFloat(temp2Match[1]) : 0,
        hum2: hum2Match ? parseFloat(hum2Match[1]) : 0,
        relay: relayMatch ? parseInt(relayMatch[1]) : 0,
        pb8: pb8Match ? parseInt(pb8Match[1]) : 0
      }
    }
    
    // 更新图表
    const updateCharts = () => {
      // 图表1 - 温湿度传感器1
      if (chart1) {
        const option1 = {
          title: {
            text: '温湿度1'
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
            data: ['当前']
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
              data: [sensorData.value.temp1],
              itemStyle: { color: '#FF6384' }
            },
            {
              name: '湿度',
              type: 'line',
              yAxisIndex: 1,
              data: [sensorData.value.hum1],
              itemStyle: { color: '#36A2EB' }
            }
          ]
        }
        chart1.setOption(option1)
      }
      
      // 图表2 - 温湿度传感器2
      if (chart2) {
        const option2 = {
          title: {
            text: '温湿度2'
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
            data: ['当前']
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
              data: [sensorData.value.temp2],
              itemStyle: { color: '#FF6384' }
            },
            {
              name: '湿度',
              type: 'line',
              yAxisIndex: 1,
              data: [sensorData.value.hum2],
              itemStyle: { color: '#36A2EB' }
            }
          ]
        }
        chart2.setOption(option2)
      }
      
      // 图表3 - 继电器和PB8
      if (chart3) {
        const option3 = {
          title: {
            text: '控制状态'
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
            data: ['当前']
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
              data: [sensorData.value.relay],
              itemStyle: { color: '#4CAF50' },
              areaStyle: {}
            },
            {
              name: 'PB8',
              type: 'line',
              step: 'start',
              data: [sensorData.value.pb8],
              itemStyle: { color: '#2196F3' },
              areaStyle: {}
            }
          ]
        }
        chart3.setOption(option3)
      }
    }
    
    // 获取实时数据
    const fetchRealTimeData = async () => {
      if (!selectedDeviceId.value) {
        return
      }
      
      try {
        // 获取指定设备的最新传感器数据
        const response = await axios.get(`/api/devices/${selectedDeviceId.value}/latest-sensors`)
        const sensors = response.data
        
        // 解析传感器数据
        let temp1 = 0, hum1 = 0, temp2 = 0, hum2 = 0, relay = 0, pb8 = 0
        
        for (const sensor of sensors) {
          if (sensor.type === 'Temperature1') {
            temp1 = sensor.value
          } else if (sensor.type === 'Humidity1') {
            hum1 = sensor.value
          } else if (sensor.type === 'Temperature2') {
            temp2 = sensor.value
          } else if (sensor.type === 'Humidity2') {
            hum2 = sensor.value
          } else if (sensor.type === 'Relay Status') {
            relay = sensor.value
          } else if (sensor.type === 'PB8 Level') {
            pb8 = sensor.value
          }
        }
        
        sensorData.value = { temp1, hum1, temp2, hum2, relay, pb8 }
        
        // 更新图表
        updateCharts()
      } catch (error) {
        console.error('获取实时数据失败:', error)
      }
    }
    
    // 设备选择变化时的处理
    const onDeviceChange = () => {
      // 重新获取数据
      fetchRealTimeData()
    }
    
    onMounted(() => {
      // 获取设备列表
      fetchDevices()
      
      // 初始化图表
      chart1 = echarts.init(document.getElementById('chart1'))
      chart2 = echarts.init(document.getElementById('chart2'))
      chart3 = echarts.init(document.getElementById('chart3'))
      
      // 如果已有选中设备，获取数据
      if (selectedDeviceId.value) {
        fetchRealTimeData()
      }
      
      // 设置定时更新（每3秒更新一次）
      const interval = setInterval(fetchRealTimeData, 3000)
      
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
      onDeviceChange
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
}
</style>