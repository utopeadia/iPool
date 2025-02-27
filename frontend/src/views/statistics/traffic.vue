<template>
  <div class="traffic-statistics-container">
    <!-- 流量概览卡片 -->
    <el-row :gutter="20">
      <el-col :span="6" v-for="(card, index) in statisticsCards" :key="index">
        <el-card shadow="hover" class="statistics-card">
          <div class="card-content">
            <div class="card-icon" :style="{ backgroundColor: card.color }">
              <el-icon :size="24"><component :is="card.icon" /></el-icon>
            </div>
            <div class="card-info">
              <div class="card-title">{{ card.title }}</div>
              <div class="card-value">{{ card.value }}</div>
              <div class="card-trend" :class="{ 'up': card.trend > 0, 'down': card.trend < 0 }">
                <el-icon v-if="card.trend > 0"><ArrowUp /></el-icon>
                <el-icon v-else-if="card.trend < 0"><ArrowDown /></el-icon>
                <span>{{ Math.abs(card.trend) }}% 较上周</span>
              </div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 流量趋势图 -->
    <el-card shadow="hover" class="chart-card">
      <template #header>
        <div class="chart-header">
          <span>流量趋势分析</span>
          <div class="chart-actions">
            <el-radio-group v-model="trafficTimeRange" size="small" @change="loadTrafficChart">
              <el-radio-button label="daily">今日</el-radio-button>
              <el-radio-button label="weekly">本周</el-radio-button>
              <el-radio-button label="monthly">本月</el-radio-button>
            </el-radio-group>
            <el-button type="primary" size="small" @click="exportTrafficData">
              <el-icon><Download /></el-icon> 导出数据
            </el-button>
          </div>
        </div>
      </template>
      <div class="chart-wrapper">
        <div id="traffic-trend-chart" class="chart-container" v-loading="chartLoading"></div>
      </div>
    </el-card>

    <!-- 代理节点统计表格 -->
    <el-card shadow="hover" class="proxy-stats-card">
      <template #header>
        <div class="card-header">
          <span>代理节点使用统计</span>
          <div class="header-actions">
            <el-input
              v-model="proxySearch"
              placeholder="搜索代理节点"
              prefix-icon="Search"
              clearable
              style="width: 200px;"
              @input="handleProxySearch"
            />
            <el-select v-model="sortOrder" style="width: 150px;" @change="handleSortChange">
              <el-option label="流量降序" value="traffic-desc" />
              <el-option label="流量升序" value="traffic-asc" />
              <el-option label="请求数降序" value="requests-desc" />
              <el-option label="请求数升序" value="requests-asc" />
            </el-select>
          </div>
        </div>
      </template>
      
      <el-table
        :data="proxyStats"
        style="width: 100%"
        v-loading="tableLoading"
        @sort-change="handleTableSortChange"
      >
        <el-table-column prop="ip" label="IP地址" width="160" />
        <el-table-column prop="port" label="端口" width="100" />
        <el-table-column prop="protocol" label="协议" width="100" />
        <el-table-column label="状态" width="100">
          <template #default="scope">
            <el-tag :type="getStatusType(scope.row.status)">{{ getStatusLabel(scope.row.status) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="requestCount" label="请求数" sortable width="120" />
        <el-table-column prop="trafficMB" label="流量(MB)" sortable width="120" />
        <el-table-column prop="avgResponseTime" label="平均响应(ms)" sortable width="150" />
        <el-table-column prop="successRate" label="成功率" width="180">
          <template #default="scope">
            <el-progress 
              :percentage="scope.row.successRate" 
              :color="getSuccessRateColor(scope.row.successRate)"
            />
          </template>
        </el-table-column>
        <el-table-column label="操作" width="120">
          <template #default="scope">
            <el-button type="primary" size="small" plain @click="showProxyDetail(scope.row)">
              详情
            </el-button>
          </template>
        </el-table-column>
      </el-table>
      
      <div class="pagination-container">
        <el-pagination
          v-model:current-page="pagination.currentPage"
          v-model:page-size="pagination.pageSize"
          :page-sizes="[10, 20, 50, 100]"
          layout="total, sizes, prev, pager, next, jumper"
          :total="pagination.total"
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
        />
      </div>
    </el-card>

    <!-- 代理详情对话框 -->
    <el-dialog
      v-model="proxyDetailVisible"
      title="代理节点详细统计"
      width="80%"
      destroy-on-close
    >
      <div class="proxy-detail-content" v-loading="detailLoading">
        <div class="proxy-info">
          <div class="info-item">
            <span class="label">IP地址:</span>
            <span class="value">{{ currentProxy.ip }}</span>
          </div>
          <div class="info-item">
            <span class="label">端口:</span>
            <span class="value">{{ currentProxy.port }}</span>
          </div>
          <div class="info-item">
            <span class="label">协议:</span>
            <span class="value">{{ currentProxy.protocol }}</span>
          </div>
          <div class="info-item">
            <span class="label">位置:</span>
            <span class="value">{{ currentProxy.location || '未知' }}</span>
          </div>
        </div>
        
        <el-divider />
        
        <el-tabs v-model="detailActiveTab" @tab-change="handleDetailTabChange">
          <el-tab-pane label="流量统计" name="traffic">
            <div id="proxy-traffic-chart" class="proxy-chart"></div>
          </el-tab-pane>
          <el-tab-pane label="响应时间" name="response">
            <div id="proxy-response-chart" class="proxy-chart"></div>
          </el-tab-pane>
          <el-tab-pane label="请求分布" name="distribution">
            <div id="proxy-distribution-chart" class="proxy-chart"></div>
          </el-tab-pane>
        </el-tabs>
        
        <el-divider />
        
        <div class="detail-summary">
          <div class="summary-item">
            <div class="summary-title">总请求数</div>
            <div class="summary-value">{{ proxyDetail.totalRequests || 0 }}</div>
          </div>
          <div class="summary-item">
            <div class="summary-title">总流量</div>
            <div class="summary-value">{{ proxyDetail.totalTraffic || 0 }} MB</div>
          </div>
          <div class="summary-item">
            <div class="summary-title">平均响应时间</div>
            <div class="summary-value">{{ proxyDetail.avgResponseTime || 0 }} ms</div>
          </div>
          <div class="summary-item">
            <div class="summary-title">成功率</div>
            <div class="summary-value">{{ proxyDetail.successRate || 0 }}%</div>
          </div>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script>
import { defineComponent, ref, reactive, onMounted, computed, nextTick, watch } from 'vue'
import { useStore } from 'vuex'
import * as echarts from 'echarts'
import { ElMessage } from 'element-plus'

export default defineComponent({
  name: 'TrafficStatistics',
  setup() {
    const store = useStore()
    
    // 统计概览卡片数据
    const statisticsCards = ref([
      { title: '今日请求', value: '0', icon: 'Connection', color: '#409EFF', trend: 0 },
      { title: '今日流量', value: '0 MB', icon: 'DataLine', color: '#67C23A', trend: 0 },
      { title: '平均响应时间', value: '0 ms', icon: 'Timer', color: '#E6A23C', trend: 0 },
      { title: '成功率', value: '0%', icon: 'Check', color: '#F56C6C', trend: 0 },
    ])
    
    // 流量图表相关
    const trafficTimeRange = ref('daily')
    const chartLoading = ref(false)
    const trafficChart = ref(null)
    
    // 代理统计表格相关
    const tableLoading = ref(false)
    const proxyStats = ref([])
    const proxySearch = ref('')
    const sortOrder = ref('traffic-desc')
    
    // 分页配置
    const pagination = reactive({
      currentPage: 1,
      pageSize: 10,
      total: 0
    })
    
    // 代理详情相关
    const proxyDetailVisible = ref(false)
    const detailLoading = ref(false)
    const detailActiveTab = ref('traffic')
    const currentProxy = ref({})
    const proxyDetail = ref({})
    const proxyTrafficChart = ref(null)
    const proxyResponseChart = ref(null)
    const proxyDistributionChart = ref(null)
    
    // 加载统计概览数据
    const loadStatisticsOverview = async () => {
      try {
        const { data } = await store.dispatch('statistics/getTrafficData', 'daily')
        
        if (data) {
          // 更新统计卡片
          statisticsCards.value[0].value = `${data.totalRequests.toLocaleString()}`;
          statisticsCards.value[1].value = `${data.totalTraffic.toLocaleString()} MB`;
          statisticsCards.value[2].value = `${data.avgResponseTime.toLocaleString()} ms`;
          statisticsCards.value[3].value = `${data.successRate.toFixed(2)}%`;
          
          // 更新趋势
          statisticsCards.value[0].trend = data.requestsTrend || 0;
          statisticsCards.value[1].trend = data.trafficTrend || 0;
          statisticsCards.value[2].trend = data.responseTrend || 0;
          statisticsCards.value[3].trend = data.successTrend || 0;
        }
      } catch (error) {
        console.error('Failed to load statistics overview', error)
      }
    }
    
    // 加载流量趋势图表
    const loadTrafficChart = async () => {
      chartLoading.value = true
      try {
        const { data } = await store.dispatch('statistics/getTrafficData', trafficTimeRange.value)
        
        if (!trafficChart.value) {
          trafficChart.value = echarts.init(document.getElementById('traffic-trend-chart'))
        }
        
        const times = data.times || []
        const requests = data.requests || []
        const traffic = data.traffic || []
        
        const option = {
          tooltip: {
            trigger: 'axis',
            axisPointer: {
              type: 'cross',
              label: {
                backgroundColor: '#6a7985'
              }
            }
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
          xAxis: [
            {
              type: 'category',
              boundaryGap: false,
              data: times
            }
          ],
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
              stack: 'Total',
              smooth: true,
              lineStyle: {
                width: 3
              },
              areaStyle: {
                opacity: 0.3
              },
              emphasis: {
                focus: 'series'
              },
              data: requests
            },
            {
              name: '流量(MB)',
              type: 'line',
              stack: 'Total',
              smooth: true,
              yAxisIndex: 1,
              lineStyle: {
                width: 3
              },
              areaStyle: {
                opacity: 0.3
              },
              emphasis: {
                focus: 'series'
              },
              data: traffic
            }
          ]
        }
        
        trafficChart.value.setOption(option)
      } catch (error) {
        console.error('Failed to load traffic chart', error)
        ElMessage.error('加载流量趋势图表失败')
      } finally {
        chartLoading.value = false
      }
    }
    
    // 加载代理统计表格
    const loadProxyStats = async () => {
      tableLoading.value = true
      try {
        const [sortField, sortOrder] = sortOrder.value.split('-')
        
        const params = {
          page: pagination.currentPage,
          limit: pagination.pageSize,
          search: proxySearch.value,
          sortField,
          sortOrder,
          timeRange: trafficTimeRange.value
        }
        
        const data = await store.dispatch('statistics/getProxyStats', params)
        
        proxyStats.value = data.items || []
        pagination.total = data.total || 0
      } catch (error) {
        console.error('Failed to load proxy stats', error)
        ElMessage.error('加载代理节点统计数据失败')
      } finally {
        tableLoading.value = false
      }
    }
    
    // 处理表格排序
    const handleSortChange = () => {
      pagination.currentPage = 1
      loadProxyStats()
    }
    
    // 处理表格内置排序
    const handleTableSortChange = ({ prop, order }) => {
      if (prop && order) {
        const sortField = {
          'requestCount': 'requests',
          'trafficMB': 'traffic',
          'avgResponseTime': 'response'
        }[prop] || prop
        
        const sortDirection = order === 'descending' ? 'desc' : 'asc'
        sortOrder.value = `${sortField}-${sortDirection}`
        loadProxyStats()
      }
    }
    
    // 搜索代理
    const handleProxySearch = () => {
      pagination.currentPage = 1
      loadProxyStats()
    }
    
    // 分页相关
    const handleSizeChange = (val) => {
      pagination.pageSize = val
      loadProxyStats()
    }
    
    const handleCurrentChange = (val) => {
      pagination.currentPage = val
      loadProxyStats()
    }
    
    // 代理详情
    const showProxyDetail = async (proxy) => {
      currentProxy.value = proxy
      proxyDetailVisible.value = true
      detailLoading.value = true
      
      try {
        const { data } = await store.dispatch('statistics/getProxyDetail', { 
          id: proxy.id, 
          timeRange: trafficTimeRange.value 
        })
        
        proxyDetail.value = data
        
        nextTick(() => {
          initProxyDetailCharts()
        })
      } catch (error) {
        console.error('Failed to load proxy detail', error)
        ElMessage.error('加载代理详情失败')
      } finally {
        detailLoading.value = false
      }
    }
    
    // 初始化详情页图表
    const initProxyDetailCharts = () => {
      const data = proxyDetail.value
      
      // 初始化流量图表
      if (!proxyTrafficChart.value) {
        proxyTrafficChart.value = echarts.init(document.getElementById('proxy-traffic-chart'))
      }
      
      proxyTrafficChart.value.setOption({
        tooltip: {
          trigger: 'axis'
        },
        legend: {
          data: ['请求数', '流量(MB)']
        },
        xAxis: {
          type: 'category',
          data: data.times || []
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
            type: 'bar',
            data: data.requests || []
          },
          {
            name: '流量(MB)',
            type: 'bar',
            yAxisIndex: 1,
            data: data.traffic || []
          }
        ]
      })
      
      // 初始化响应时间图表
      if (!proxyResponseChart.value) {
        proxyResponseChart.value = echarts.init(document.getElementById('proxy-response-chart'))
      }
      
      proxyResponseChart.value.setOption({
        tooltip: {
          trigger: 'axis'
        },
        xAxis: {
          type: 'category',
          data: data.times || []
        },
        yAxis: {
          type: 'value',
          name: '响应时间 (ms)'
        },
        series: [
          {
            name: '响应时间',
            type: 'line',
            smooth: true,
            data: data.responseTimes || [],
            markLine: {
              data: [
                {
                  name: '平均值',
                  type: 'average'
                }
              ]
            }
          }
        ]
      })
      
      // 初始化请求分布图表
      if (!proxyDistributionChart.value) {
        proxyDistributionChart.value = echarts.init(document.getElementById('proxy-distribution-chart'))
      }
      
      proxyDistributionChart.value.setOption({
        tooltip: {
          trigger: 'item'
        },
        legend: {
          orient: 'vertical',
          left: 'left'
        },
        series: [
          {
            name: '请求分布',
            type: 'pie',
            radius: '50%',
            data: [
              { value: data.successCount || 0, name: '成功请求' },
              { value: data.errorCount || 0, name: '失败请求' },
              { value: data.timeoutCount || 0, name: '超时请求' }
            ],
            emphasis: {
              itemStyle: {
                shadowBlur: 10,
                shadowOffsetX: 0,
                shadowColor: 'rgba(0, 0, 0, 0.5)'
              }
            }
          }
        ]
      })
    }
    
    // 标签页切换
    const handleDetailTabChange = () => {
      nextTick(() => {
        if (detailActiveTab.value === 'traffic' && proxyTrafficChart.value) {
          proxyTrafficChart.value.resize()
        } else if (detailActiveTab.value === 'response' && proxyResponseChart.value) {
          proxyResponseChart.value.resize()
        } else if (detailActiveTab.value === 'distribution' && proxyDistributionChart.value) {
          proxyDistributionChart.value.resize()
        }
      })
    }
    
    // 导出流量数据
    const exportTrafficData = async () => {
      try {
        await store.dispatch('statistics/exportStatistics', {
          type: 'traffic',
          timeRange: trafficTimeRange.value
        })
        ElMessage.success('导出成功')
      } catch (error) {
        ElMessage.error('导出失败')
      }
    }
    
    // 工具函数
    const getStatusType = (status) => {
      const map = {
        active: 'success',
        warning: 'warning',
        error: 'danger',
        timeout: 'info'
      }
      return map[status] || 'info'
    }
    
    const getStatusLabel = (status) => {
      const map = {
        active: '活跃',
        warning: '警告',
        error: '错误',
        timeout: '超时'
      }
      return map[status] || '未知'
    }
    
    const getSuccessRateColor = (rate) => {
      if (rate >= 90) return '#67C23A'
      if (rate >= 70) return '#E6A23C'
      return '#F56C6C'
    }
    
    // 窗口大小改变时重置图表大小
    const handleResize = () => {
      if (trafficChart.value) {
        trafficChart.value.resize()
      }
    }
    
    // 生命周期钩子
    onMounted(() => {
      loadStatisticsOverview()
      loadTrafficChart()
      loadProxyStats()
      window.addEventListener('resize', handleResize)
    })
    
    watch(trafficTimeRange, () => {
      loadTrafficChart()
    })
    
    return {
      statisticsCards,
      trafficTimeRange,
      chartLoading,
      tableLoading,
      proxyStats,
      proxySearch,
      sortOrder,
      pagination,
      proxyDetailVisible,
      detailLoading,
      detailActiveTab,
      currentProxy,
      proxyDetail,
      loadTrafficChart,
      handleSortChange,
      handleTableSortChange,
      handleProxySearch,
      handleSizeChange,
      handleCurrentChange,
      showProxyDetail,
      handleDetailTabChange,
      exportTrafficData,
      getStatusType,
      getStatusLabel,
      getSuccessRateColor
    }
  }
})
</script>

<style lang="scss" scoped>
.traffic-statistics-container {
  .statistics-card {
    margin-bottom: 20px;
    
    .card-content {
      display: flex;
      align-items: center;
      
      .card-icon {
        width: 48px;
        height: 48px;
        border-radius: 8px;
        display: flex;
        justify-content: center;
        align-items: center;
        margin-right: 16px;
        color: white;
      }
      
      .card-info {
        flex: 1;
        
        .card-title {
          font-size: 14px;
          color: #606266;
          margin-bottom: 6px;
        }
        
        .card-value {
          font-size: 24px;
          font-weight: bold;
          color: #303133;
          margin-bottom: 6px;
        }
        
        .card-trend {
          font-size: 13px;
          display: flex;
          align-items: center;
          
          &.up {
            color: #67C23A;
          }
          
          &.down {
            color: #F56C6C;
          }
        }
      }
    }
  }
  
  .chart-card {
    margin-bottom: 20px;
    
    .chart-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      
      .chart-actions {
        display: flex;
        align-items: center;
        gap: 16px;
      }
    }
    
    .chart-wrapper {
      .chart-container {
        height: 400px;
      }
    }
  }
  
  .proxy-stats-card {
    .card-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      
      .header-actions {
        display: flex;
        gap: 16px;
      }
    }
    
    .pagination-container {
      margin-top: 20px;
      display: flex;
      justify-content: flex-end;
    }
  }
  
  .proxy-detail-content {
    .proxy-info {
      display: flex;
      flex-wrap: wrap;
      
      .info-item {
        width: 25%;
        margin-bottom: 16px;
        
        .label {
          font-weight: bold;
          margin-right: 8px;
        }
      }
    }
    
    .proxy-chart {
      height: 400px;
    }
    
    .detail-summary {
      display: flex;
      justify-content: space-around;
      
      .summary-item {
        text-align: center;
        
        .summary-title {
          font-size: 14px;
          color: #606266;
          margin-bottom: 8px;
        }
        
        .summary-value {
          font-size: 24px;
          font-weight: bold;
          color: #303133;
        }
      }
    }
  }
}
</style>
