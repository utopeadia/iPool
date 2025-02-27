<template>
  <div class="dashboard-container">
    <el-row :gutter="20">
      <el-col :span="6" v-for="(card, index) in overviewCards" :key="index">
        <el-card shadow="hover" class="overview-card">
          <div class="card-header">
            <el-icon :size="24" :color="card.iconColor">
              <component :is="card.icon" />
            </el-icon>
            <span class="title">{{ card.title }}</span>
          </div>
          <div class="card-content">
            <span class="count">{{ card.value }}</span>
            <span class="unit">{{ card.unit }}</span>
          </div>
          <div v-if="card.change !== undefined" class="card-footer">
            <el-tag :type="card.change >= 0 ? 'success' : 'danger'" size="small" effect="light">
              {{ card.change >= 0 ? '+' : '' }}{{ card.change }}% 较上周
            </el-tag>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20" class="chart-row">
      <el-col :span="16">
        <el-card shadow="hover" class="chart-card">
          <template #header>
            <div class="chart-header">
              <span>代理流量统计</span>
              <el-radio-group v-model="trafficTimeRange" size="small">
                <el-radio-button label="day">今日</el-radio-button>
                <el-radio-button label="week">本周</el-radio-button>
                <el-radio-button label="month">本月</el-radio-button>
              </el-radio-group>
            </div>
          </template>
          <div id="traffic-chart" class="chart-container"></div>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card shadow="hover" class="chart-card">
          <template #header>
            <div class="chart-header">
              <span>代理状态分布</span>
            </div>
          </template>
          <div id="status-chart" class="chart-container pie-chart"></div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20" class="top-proxies-row">
      <el-col :span="24">
        <el-card shadow="hover">
          <template #header>
            <div class="between-header">
              <span>代理节点性能排行</span>
              <el-button type="primary" size="small" @click="refreshTopProxies">
                <el-icon><Refresh /></el-icon>刷新
              </el-button>
            </div>
          </template>
          <el-table :data="topProxies" stripe style="width: 100%" v-loading="loading">
            <el-table-column prop="ip" label="IP地址" width="180" />
            <el-table-column prop="port" label="端口" width="100" />
            <el-table-column prop="protocol" label="协议" width="100" />
            <el-table-column label="状态" width="120">
              <template #default="scope">
                <el-tag :type="getStatusType(scope.row.status)">{{ scope.row.status }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="responseTime" label="响应时间" width="120">
              <template #default="scope">
                {{ scope.row.responseTime }} ms
              </template>
            </el-table-column>
            <el-table-column prop="successRate" label="成功率" width="120">
              <template #default="scope">
                <el-progress :percentage="scope.row.successRate" :color="getSuccessRateColor(scope.row.successRate)" />
              </template>
            </el-table-column>
            <el-table-column prop="uptime" label="正常运行时间" />
          </el-table>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script>
import { defineComponent, ref, onMounted, reactive, toRefs, nextTick, watch } from 'vue'
import * as echarts from 'echarts'
import { useStore } from 'vuex'

export default defineComponent({
  name: 'Dashboard',
  setup() {
    const store = useStore()
    const trafficTimeRange = ref('day')
    const loading = ref(false)
    
    const state = reactive({
      overviewCards: [
        { 
          title: '总代理数', 
          value: 0, 
          unit: '个', 
          icon: 'Connection', 
          iconColor: '#409EFF' 
        },
        { 
          title: '活跃代理', 
          value: 0, 
          unit: '个', 
          icon: 'Select', 
          iconColor: '#67C23A',
          change: 5
        },
        { 
          title: '今日流量', 
          value: 0, 
          unit: 'MB', 
          icon: 'DataLine', 
          iconColor: '#E6A23C',
          change: 12
        },
        { 
          title: '平均响应', 
          value: 0, 
          unit: 'ms', 
          icon: 'Timer', 
          iconColor: '#F56C6C',
          change: -3
        }
      ],
      topProxies: [],
      trafficChart: null,
      statusChart: null
    })

    // 模拟数据
    const fetchDashboardData = async () => {
      loading.value = true
      try {
        // 实际项目中这里应该从API获取数据
        await new Promise(resolve => setTimeout(resolve, 800))
        
        // 模拟数据
        state.overviewCards[0].value = 128
        state.overviewCards[1].value = 98
        state.overviewCards[2].value = 1258
        state.overviewCards[3].value = 320
        
        state.topProxies = [
          { ip: '192.168.1.100', port: 8080, protocol: 'HTTP', status: 'active', responseTime: 120, successRate: 99.5, uptime: '30天12小时' },
          { ip: '192.168.1.101', port: 1080, protocol: 'SOCKS5', status: 'active', responseTime: 135, successRate: 98.2, uptime: '15天8小时' },
          { ip: '192.168.1.102', port: 3128, protocol: 'HTTP', status: 'warning', responseTime: 210, successRate: 85.7, uptime: '7天3小时' },
          { ip: '192.168.1.103', port: 8888, protocol: 'HTTP', status: 'error', responseTime: 450, successRate: 65.3, uptime: '2天5小时' },
          { ip: '192.168.1.104', port: 1080, protocol: 'SOCKS5', status: 'active', responseTime: 155, successRate: 97.8, uptime: '21天9小时' }
        ]
        
        initCharts()
      } finally {
        loading.value = false
      }
    }

    const initCharts = () => {
      nextTick(() => {
        // 初始化流量图表
        if (!state.trafficChart) {
          state.trafficChart = echarts.init(document.getElementById('traffic-chart'))
        }
        
        // 初始化状态饼图
        if (!state.statusChart) {
          state.statusChart = echarts.init(document.getElementById('status-chart'))
        }
        
        updateTrafficChart()
        updateStatusChart()
        
        window.addEventListener('resize', () => {
          state.trafficChart && state.trafficChart.resize()
          state.statusChart && state.statusChart.resize()
        })
      })
    }

    const updateTrafficChart = () => {
      const timeRange = {
        day: ['00:00', '04:00', '08:00', '12:00', '16:00', '20:00', '24:00'],
        week: ['周一', '周二', '周三', '周四', '周五', '周六', '周日'],
        month: ['1日', '5日', '10日', '15日', '20日', '25日', '30日']
      }
      
      const option = {
        tooltip: {
          trigger: 'axis'
        },
        legend: {
          data: ['请求数', '流量(MB)']
        },
        grid: {
          left: '3%',
          right: '4%',
          bottom: '3%',
          containLabel: true
        },
        xAxis: {
          type: 'category',
          boundaryGap: false,
          data: timeRange[trafficTimeRange.value]
        },
        yAxis: [
          {
            type: 'value',
            name: '请求数',
            position: 'left'
          },
          {
            type: 'value',
            name: '流量(MB)',
            position: 'right'
          }
        ],
        series: [
          {
            name: '请求数',
            type: 'line',
            smooth: true,
            data: [150, 230, 450, 380, 720, 620, 380]
          },
          {
            name: '流量(MB)',
            type: 'line',
            yAxisIndex: 1,
            smooth: true,
            data: [82, 124, 201, 174, 310, 290, 150]
          }
        ]
      }
      
      state.trafficChart.setOption(option)
    }

    const updateStatusChart = () => {
      const option = {
        tooltip: {
          trigger: 'item',
          formatter: '{a} <br/>{b}: {c} ({d}%)'
        },
        legend: {
          orient: 'vertical',
          left: 10,
          data: ['活跃', '警告', '错误', '超时']
        },
        series: [
          {
            name: '代理状态',
            type: 'pie',
            radius: ['50%', '70%'],
            avoidLabelOverlap: false,
            label: {
              show: false,
              position: 'center'
            },
            emphasis: {
              label: {
                show: true,
                fontSize: '18',
                fontWeight: 'bold'
              }
            },
            labelLine: {
              show: false
            },
            data: [
              { value: 98, name: '活跃', itemStyle: { color: '#67C23A' } },
              { value: 15, name: '警告', itemStyle: { color: '#E6A23C' } },
              { value: 10, name: '错误', itemStyle: { color: '#F56C6C' } },
              { value: 5, name: '超时', itemStyle: { color: '#909399' } }
            ]
          }
        ]
      }
      
      state.statusChart.setOption(option)
    }

    const refreshTopProxies = () => {
      fetchDashboardData()
    }

    const getStatusType = (status) => {
      const statusMap = {
        'active': 'success',
        'warning': 'warning',
        'error': 'danger',
        'timeout': 'info'
      }
      return statusMap[status] || 'info'
    }

    const getSuccessRateColor = (rate) => {
      if (rate >= 90) return '#67C23A'
      if (rate >= 75) return '#E6A23C'
      return '#F56C6C'
    }

    watch(trafficTimeRange, () => {
      updateTrafficChart()
    })

    onMounted(() => {
      fetchDashboardData()
    })

    return {
      ...toRefs(state),
      trafficTimeRange,
      loading,
      refreshTopProxies,
      getStatusType