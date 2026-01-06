<template>
  <div class="real-time-data">
    <div class="container-fluid">
      <div class="d-flex justify-content-between align-items-center mb-4">
        <h2 class="page-title">
          <i class="fas fa-chart-line me-2"></i>
          实时传感器数据
        </h2>
        <div class="status-indicator">
          <span :class="['status-dot', { 'status-active': selectedDeviceId }]"></span>
          <span v-if="selectedDeviceId" class="status-text text-success">已连接</span>
          <span v-else class="status-text text-muted">未选择设备</span>
        </div>
      </div>

      <!-- 设备选择卡片 -->
      <div class="device-selector-card card shadow-sm">
        <div class="card-body p-4">
          <div class="d-flex flex-column flex-md-row align-items-center">
            <div class="device-icon me-3 mb-3 mb-md-0">
              <i class="fas fa-microchip fa-2x text-primary"></i>
            </div>
            <div class="w-100">
              <label for="device-select" class="device-label mb-2">选择要监控的设备</label>
              <div class="d-flex">
                <select 
                  id="device-select"
                  class="form-select form-select-lg flex-grow-1 me-3" 
                  v-model="selectedDeviceId"
                  @change="onDeviceChange"
                >
                  <option value="">请选择一个设备...</option>
                  <option v-for="device in devices" :key="device.id" :value="device.id">
                    {{ device.name }} ({{ device.location || '未知位置' }})
                  </option>
                </select>
                <button 
                  class="btn btn-primary btn-lg d-flex align-items-center"
                  :disabled="!selectedDeviceId"
                  @click="refreshData"
                >
                  <i class="fas fa-sync-alt me-1"></i> 刷新
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
      
      <!-- 数据加载状态指示 -->
      <div v-if="loadingData" class="loading-container text-center my-5 py-5">
        <div class="spinner-border text-primary" style="width: 3rem; height: 3rem;" role="status">
          <span class="visually-hidden">加载中...</span>
        </div>
        <h5 class="mt-3">正在加载传感器数据...</h5>
        <p class="text-muted">从设备获取最新信息</p>
      </div>
      
      <!-- 错误信息 -->
      <div v-if="error" class="alert alert-danger alert-dismissible fade show" role="alert">
        <i class="fas fa-exclamation-triangle me-2"></i>
        {{ error }}
        <button type="button" class="btn-close" @click="error = ''"></button>
      </div>
      
      <!-- 传感器数据显示区域 -->
      <div class="sensors-container" v-if="!loadingData && selectedDeviceId">
        <div class="row g-4">
          <!-- 温湿度传感器1 -->
          <div class="col-xl-4 col-md-6">
            <div class="sensor-card card h-100 border-0 shadow-sm">
              <div class="card-body sensor-gradient-1 p-4 text-white">
                <div class="d-flex justify-content-between align-items-start">
                  <div>
                    <h5 class="card-title mb-3">
                      <i class="fas fa-thermometer-half me-2"></i>
                      传感器组 1
                    </h5>
                    <div class="sensor-data">
                      <div class="d-flex justify-content-between mb-2">
                        <span>温度</span>
                        <span class="fw-bold fs-5">
                          <i class="fas fa-temperature-high me-1"></i>
                          {{ sensorData.temp1 }}°C
                        </span>
                      </div>
                      <div class="d-flex justify-content-between">
                        <span>湿度</span>
                        <span class="fw-bold fs-5">
                          <i class="fas fa-tint me-1"></i>
                          {{ sensorData.hum1 }}%
                        </span>
                      </div>
                    </div>
                  </div>
                  <div class="sensor-icon-large">
                    <i class="fas fa-thermometer-half"></i>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- 温湿度传感器2 -->
          <div class="col-xl-4 col-md-6">
            <div class="sensor-card card h-100 border-0 shadow-sm">
              <div class="card-body sensor-gradient-2 p-4 text-white">
                <div class="d-flex justify-content-between align-items-start">
                  <div>
                    <h5 class="card-title mb-3">
                      <i class="fas fa-thermometer-half me-2"></i>
                      传感器组 2
                    </h5>
                    <div class="sensor-data">
                      <div class="d-flex justify-content-between mb-2">
                        <span>温度</span>
                        <span class="fw-bold fs-5">
                          <i class="fas fa-temperature-high me-1"></i>
                          {{ sensorData.temp2 }}°C
                        </span>
                      </div>
                      <div class="d-flex justify-content-between">
                        <span>湿度</span>
                        <span class="fw-bold fs-5">
                          <i class="fas fa-tint me-1"></i>
                          {{ sensorData.hum2 }}%
                        </span>
                      </div>
                    </div>
                  </div>
                  <div class="sensor-icon-large">
                    <i class="fas fa-thermometer-half"></i>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- 继电器和PB8 -->
          <div class="col-xl-4 col-md-6">
            <div class="sensor-card card h-100 border-0 shadow-sm">
              <div class="card-body sensor-gradient-3 p-4 text-white">
                <div class="d-flex justify-content-between align-items-start">
                  <div>
                    <h5 class="card-title mb-3">
                      <i class="fas fa-toggle-on me-2"></i>
                      控制组
                    </h5>
                    <div class="sensor-data">
                      <div class="d-flex justify-content-between mb-2">
                        <span>继电器状态</span>
                        <span class="fw-bold fs-5">
                          <i class="fas fa-power-off me-1" 
                             :class="sensorData.relay === 1 ? 'text-warning' : 'text-light'"></i>
                          <span :class="sensorData.relay === 1 ? 'text-warning' : 'text-light'">
                            {{ sensorData.relay === 1 ? '开启' : '关闭' }}
                          </span>
                        </span>
                      </div>
                      <div class="d-flex justify-content-between">
                        <span>PB8电平</span>
                        <span class="fw-bold fs-5">
                          <i class="fas fa-bolt me-1" 
                             :class="sensorData.pb8 === 1 ? 'text-warning' : 'text-light'"></i>
                          <span :class="sensorData.pb8 === 1 ? 'text-warning' : 'text-light'">
                            {{ sensorData.pb8 === 1 ? '高电平' : '低电平' }}
                          </span>
                        </span>
                      </div>
                    </div>
                  </div>
                  <div class="sensor-icon-large">
                    <i class="fas fa-toggle-on"></i>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
        
        <!-- 趋势图区域 -->
        <div class="trend-charts-section mt-5">
          <div class="chart-card card shadow-sm">
            <div class="card-header bg-white py-4">
              <h5 class="mb-0 d-flex align-items-center">
                <i class="fas fa-chart-area me-2 text-primary"></i>
                传感器数据趋势图
              </h5>
            </div>
            <div class="card-body">
              <div class="row g-4">
                <!-- 温湿度传感器1趋势图 -->
                <div class="col-xl-4 col-md-12">
                  <div class="chart-container card h-100 border-0 shadow-sm">
                    <div class="card-body p-3">
                      <h6 class="chart-title text-center mb-3">温湿度1趋势</h6>
                      <div ref="chart1Ref" class="chart-wrapper"></div>
                    </div>
                  </div>
                </div>
                
                <!-- 温湿度传感器2趋势图 -->
                <div class="col-xl-4 col-md-12">
                  <div class="chart-container card h-100 border-0 shadow-sm">
                    <div class="card-body p-3">
                      <h6 class="chart-title text-center mb-3">温湿度2趋势</h6>
                      <div ref="chart2Ref" class="chart-wrapper"></div>
                    </div>
                  </div>
                </div>
                
                <!-- 继电器和PB8趋势图 -->
                <div class="col-xl-4 col-md-12">
                  <div class="chart-container card h-100 border-0 shadow-sm">
                    <div class="card-body p-3">
                      <h6 class="chart-title text-center mb-3">控制状态趋势</h6>
                      <div ref="chart3Ref" class="chart-wrapper"></div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
      
      <!-- 提示信息，当未选择设备时显示 -->
      <div v-if="!selectedDeviceId && !loadingData" class="no-device-selected text-center my-5 py-5">
        <div class="empty-state-icon mx-auto mb-4">
          <i class="fas fa-microchip fa-3x text-light"></i>
        </div>
        <h5 class="text-muted">请选择一个设备以开始监控</h5>
        <p class="text-muted mb-4">从上方下拉菜单中选择一个设备，以查看其实时传感器数据和趋势图</p>
        <div class="empty-state-features d-flex justify-content-center flex-wrap gap-3">
          <div class="feature-item px-3 py-2">
            <i class="fas fa-chart-line me-1"></i> 实时数据
          </div>
          <div class="feature-item px-3 py-2">
            <i class="fas fa-history me-1"></i> 历史趋势
          </div>
          <div class="feature-item px-3 py-2">
            <i class="fas fa-plug me-1"></i> 设备控制
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
      
      // 确保DOM已更新后再初始化或更新图表
      nextTick(() => {
        // 图表1 - 温湿度传感器1
        if (chart1Ref.value) {
          if (!chart1) {
            chart1 = echarts.init(chart1Ref.value)
          }
          const option1 = {
            title: {
              text: '温湿度1趋势',
              left: 'center',
              textStyle: { fontSize: 14 }
            },
            tooltip: {
              trigger: 'axis'
            },
            legend: {
              data: ['温度', '湿度'],
              top: 20
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
                max: 100,
                axisLabel: {
                  show: true
                }
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
        if (chart2Ref.value) {
          if (!chart2) {
            chart2 = echarts.init(chart2Ref.value)
          }
          const option2 = {
            title: {
              text: '温湿度2趋势',
              left: 'center',
              textStyle: { fontSize: 14 }
            },
            tooltip: {
              trigger: 'axis'
            },
            legend: {
              data: ['温度', '湿度'],
              top: 20
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
                max: 100,
                axisLabel: {
                  show: true
                }
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
        if (chart3Ref.value) {
          if (!chart3) {
            chart3 = echarts.init(chart3Ref.value)
          }
          const option3 = {
            title: {
              text: '控制状态趋势',
              left: 'center',
              textStyle: { fontSize: 14 }
            },
            tooltip: {
              trigger: 'axis'
            },
            legend: {
              data: ['继电器', 'PB8'],
              top: 20
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
      })
    }
    
    // 获取实时数据
    const fetchRealTimeData = async () => {
      if (!selectedDeviceId.value) {
        error.value = '请先选择一个设备'
        return
      }
      
      // 只在首次加载时显示loading状态
      if (chartData.value.timeStamps.length === 0) {
        loadingData.value = true
      }
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
        
        console.log(`找到 ${sensors.length} 个传感器数据`) // 调试信息
        
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
        
        // 检查是否有传感器数据
        if (sensors.length === 0) {
          console.log('没有找到任何传感器数据')
          error.value = '该设备暂无传感器数据，请确认设备是否正常发送数据'
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
        // 但仍然需要更新图表，以确保时间轴继续前进
        const now = new Date().toLocaleTimeString()
        
        // 添加时间戳，但保持现有数据不变
        chartData.value.timeStamps.push(now)
        if(chartData.value.timeStamps.length > 20) {
          chartData.value.timeStamps.shift()
        }
        
        // 添加当前传感器值，保持趋势线的连续性
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
        
        // 仍然需要更新图表以显示时间的前进
        nextTick(() => {
          if (chart1) chart1.setOption({
            xAxis: {
              data: chartData.value.timeStamps
            },
            series: [
              { data: chartData.value.temp1Data },
              { data: chartData.value.hum1Data }
            ]
          }, { notMerge: true })
          
          if (chart2) chart2.setOption({
            xAxis: {
              data: chartData.value.timeStamps
            },
            series: [
              { data: chartData.value.temp2Data },
              { data: chartData.value.hum2Data }
            ]
          }, { notMerge: true })
          
          if (chart3) chart3.setOption({
            xAxis: {
              data: chartData.value.timeStamps
            },
            series: [
              { data: chartData.value.relayData },
              { data: chartData.value.pb8Data }
            ]
          }, { notMerge: true })
        })
      } finally {
        // 只在首次加载时隐藏loading状态
        if (chartData.value.timeStamps.length === 1) {
          loadingData.value = false
        }
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
      
      // 如果已有选中设备，获取数据
      if (selectedDeviceId.value) {
        fetchRealTimeData()
      }
    }
    
    // 手动刷新数据
    const refreshData = () => {
      fetchRealTimeData()
    }
    
    // 处理窗口大小变化
    const handleResize = () => {
      if (chart1) chart1.resize()
      if (chart2) chart2.resize()
      if (chart3) chart3.resize()
    }
    
    onMounted(async () => {
      // 获取设备列表
      await fetchDevices()
      
      // 等待设备列表加载完成后再加载选中的设备
      loadSelectedDevice()
      
      // 初始化图表
      await initCharts()
      
      // 如果有选中的设备，立即获取数据
      if (selectedDeviceId.value) {
        fetchRealTimeData()
      }
      
      // 监听窗口大小变化
      window.addEventListener('resize', handleResize)
      
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
      
      // 移除事件监听器
      window.removeEventListener('resize', handleResize)
      
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
      chart3Ref,
      refreshData
    }
  }
}
</script>

<style scoped>
.real-time-data {
  padding: 20px;
  background-color: #f8f9fa;
  min-height: 100vh;
}

.container-fluid {
  max-width: 1400px;
}

.page-title {
  color: #2c3e50;
  font-weight: 600;
  font-size: 1.8rem;
  margin-bottom: 0;
}

.status-indicator {
  display: flex;
  align-items: center;
  gap: 8px;
}

.status-dot {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  display: inline-block;
}

.status-active {
  background-color: #28a745;
  box-shadow: 0 0 10px #28a745;
}

.status-text {
  font-size: 0.9rem;
  font-weight: 500;
}

.device-selector-card {
  border-radius: 12px;
  margin-bottom: 30px;
  border: none;
  background: white;
}

.device-icon {
  width: 60px;
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(0, 123, 255, 0.1);
  border-radius: 12px;
}

.device-label {
  font-weight: 500;
  color: #495057;
  display: block;
  margin-bottom: 0.5rem;
  font-size: 1.1rem;
}

.form-select-lg {
  padding: 0.75rem 1rem;
  font-size: 1.1rem;
  border-radius: 8px;
  border: 2px solid #e9ecef;
}

.loading-container {
  background: white;
  border-radius: 12px;
  box-shadow: 0 4px 12px rgba(0,0,0,0.05);
}

.sensors-container {
  margin-top: 20px;
}

.sensor-card {
  border-radius: 12px;
  overflow: hidden;
  transition: all 0.3s ease;
  height: 100%;
}

.sensor-gradient-1 {
  background: linear-gradient(135deg, #6a11cb 0%, #2575fc 100%);
}

.sensor-gradient-2 {
  background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
}

.sensor-gradient-3 {
  background: linear-gradient(135deg, #ff416c 0%, #ff4b2b 100%);
}

.sensor-data {
  background: rgba(255, 255, 255, 0.2);
  border-radius: 8px;
  padding: 12px;
  margin-top: 15px;
}

.sensor-icon-large {
  width: 60px;
  height: 60px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.2);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.5rem;
}

.chart-card {
  border: none;
  border-radius: 12px;
  overflow: hidden;
}

.chart-container {
  border-radius: 10px;
  overflow: hidden;
  background-color: white;
}

.chart-title {
  font-weight: 600;
  color: #495057;
  padding-bottom: 10px;
  border-bottom: 1px solid #eee;
}

.chart-wrapper {
  height: 300px;
  width: 100%;
}

.trend-charts-section {
  margin-top: 30px;
}

.no-device-selected {
  background-color: white;
  border-radius: 12px;
  padding: 40px 20px;
  margin-top: 20px;
  box-shadow: 0 4px 12px rgba(0,0,0,0.05);
}

.empty-state-icon {
  width: 100px;
  height: 100px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f8f9fa;
  margin-left: auto;
  margin-right: auto;
}

.empty-state-features {
  max-width: 600px;
}

.feature-item {
  background: #f8f9fa;
  border-radius: 8px;
  font-size: 0.9rem;
  color: #6c757d;
  border: 1px solid #e9ecef;
}

.alert {
  border-radius: 8px;
}

.shadow-sm {
  box-shadow: 0 2px 10px rgba(0,0,0,0.05) !important;
}

.me-1 {
  margin-right: 0.25rem;
}

.me-2 {
  margin-right: 0.5rem;
}

.me-3 {
  margin-right: 1rem;
}

.mb-2 {
  margin-bottom: 0.5rem;
}

.mb-3 {
  margin-bottom: 1rem;
}

.mb-4 {
  margin-bottom: 1.5rem;
}

.mb-5 {
  margin-bottom: 3rem;
}

.mt-3 {
  margin-top: 1rem;
}

.mt-5 {
  margin-top: 3rem;
}

.my-5 {
  margin-top: 3rem;
  margin-bottom: 3rem;
}

.py-5 {
  padding-top: 3rem;
  padding-bottom: 3rem;
}

.g-4 {
  gap: 1.5rem;
}

.text-light {
  color: #f8f9fa !important;
}

.text-warning {
  color: #ffc107 !important;
}

.text-success {
  color: #28a745 !important;
}

.text-muted {
  color: #6c757d !important;
}

.fw-bold {
  font-weight: 700 !important;
}

.fs-5 {
  font-size: 1.25rem !important;
}

.d-flex {
  display: flex !important;
}

.justify-content-between {
  justify-content: space-between !important;
}

.justify-content-center {
  justify-content: center !important;
}

.align-items-center {
  align-items: center !important;
}

.align-items-start {
  align-items: flex-start !important;
}

.w-100 {
  width: 100% !important;
}

.h-100 {
  height: 100% !important;
}

.border-0 {
  border: 0 !important;
}

.p-4 {
  padding: 1.5rem !important;
}

.p-3 {
  padding: 1rem !important;
}

@media (max-width: 768px) {
  .real-time-data {
    padding: 15px;
  }
  
  .page-title {
    font-size: 1.5rem;
  }
  
  .d-flex {
    flex-direction: column;
  }
  
  .flex-md-row {
    flex-direction: column !important;
  }
  
  .me-3 {
    margin-right: 0 !important;
  }
  
  .mb-md-0 {
    margin-bottom: 1rem !important;
  }
  
  .form-select {
    margin-bottom: 1rem;
  }
  
  .status-indicator {
    margin-top: 1rem;
  }
  
  .sensor-icon-large {
    display: none;
  }
}
</style>