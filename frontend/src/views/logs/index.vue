<template>
  <div class="logs-container">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>系统日志</span>
          <div class="header-actions">
            <el-button type="danger" @click="handleClearLogs" :loading="clearLoading">
              <el-icon><Delete /></el-icon>
              <span>清除日志</span>
            </el-button>
            <el-button type="primary" @click="handleExportLogs" :loading="exportLoading">
              <el-icon><Download /></el-icon>
              <span>导出日志</span>
            </el-button>
          </div>
        </div>
      </template>
      
      <!-- 过滤条件 -->
      <el-form :inline="true" :model="filterForm" class="filter-form">
        <el-form-item label="日志级别">
          <el-select v-model="filterForm.level" placeholder="选择日志级别" clearable>
            <el-option
              v-for="item in levelOptions"
              :key="item.value"
              :label="item.label"
              :value="item.value"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="时间范围">
          <el-date-picker
            v-model="dateRange"
            type="daterange"
            range-separator="至"
            start-placeholder="开始日期"
            end-placeholder="结束日期"
            value-format="YYYY-MM-DD"
          />
        </el-form-item>
        <el-form-item label="关键字">
          <el-input v-model="filterForm.keyword" placeholder="搜索关键字" clearable />
        </el-form-item>
        <el-form-item label="模块">
          <el-select v-model="filterForm.module" placeholder="选择模块" clearable>
            <el-option
              v-for="item in moduleOptions"
              :key="item.value"
              :label="item.label"
              :value="item.value"
            />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleFilter">
            <el-icon><Search /></el-icon>
            <span>搜索</span>
          </el-button>
          <el-button @click="resetFilter">
            <el-icon><Refresh /></el-icon>
            <span>重置</span>
          </el-button>
        </el-form-item>
      </el-form>
      
      <!-- 日志表格 -->
      <el-table
        :data="logs"
        style="width: 100%"
        v-loading="loading"
        height="calc(100vh - 330px)"
      >
        <el-table-column type="expand">
          <template #default="props">
            <div class="log-detail">
              <div class="detail-item">
                <span class="label">完整消息:</span>
                <div class="value log-message">{{ props.row.message }}</div>
              </div>
              <div v-if="props.row.stackTrace" class="detail-item">
                <span class="label">堆栈跟踪:</span>
                <div class="value stack-trace">{{ props.row.stackTrace }}</div>
              </div>
              <div v-if="props.row.context" class="detail-item">
                <span class="label">上下文:</span>
                <div class="value context">
                  <pre>{{ JSON.stringify(props.row.context, null, 2) }}</pre>
                </div>
              </div>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="timestamp" label="时间" width="180" sortable>
          <template #default="scope">
            {{ formatDate(scope.row.timestamp) }}
          </template>
        </el-table-column>
        <el-table-column prop="level" label="级别" width="100">
          <template #default="scope">
            <el-tag :type="getLevelType(scope.row.level)" size="small">
              {{ scope.row.level }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="module" label="模块" width="150" />
        <el-table-column prop="shortMessage" label="消息" min-width="300">
          <template #default="scope">
            <el-tooltip
              :content="scope.row.message"
              placement="top"
              :hide-after="3000"
              :show-after="500"
              :effect="scope.row.level === 'ERROR' ? 'light' : 'dark'"
            >
              <span :class="{ 'error-message': scope.row.level === 'ERROR' }">
                {{ scope.row.shortMessage }}
              </span>
            </el-tooltip>
          </template>
        </el-table-column>
        <el-table-column prop="ip" label="IP地址" width="150" />
        <el-table-column prop="userId" label="用户ID" width="100" />
        <el-table-column label="操作" width="120" fixed="right">
          <template #default="scope">
            <el-button type="primary" link size="small" @click="copyLogEntry(scope.row)">
              复制
            </el-button>
          </template>
        </el-table-column>
      </el-table>
      
      <div class="pagination-container">
        <el-pagination
          v-model:current-page="pagination.currentPage"
          v-model:page-size="pagination.pageSize"
          :page-sizes="[20, 50, 100, 200]"
          layout="total, sizes, prev, pager, next, jumper"
          :total="total"
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
        />
      </div>
    </el-card>
    
    <!-- 清除日志确认对话框 -->
    <el-dialog
      v-model="clearDialogVisible"
      title="清除日志"
      width="400px"
    >
      <div class="clear-dialog-content">
        <p>请选择要清除的日志范围：</p>
        <el-form label-width="100px">
          <el-form-item label="清除范围">
            <el-radio-group v-model="clearOption">
              <el-radio label="all">所有日志</el-radio>
              <el-radio label="filtered">当前筛选结果</el-radio>
              <el-radio label="date">指定日期前</el-radio>
            </el-radio-group>
          </el-form-item>
          <el-form-item v-if="clearOption === 'date'" label="日期">
            <el-date-picker
              v-model="clearBeforeDate"
              type="date"
              placeholder="选择日期"
              value-format="YYYY-MM-DD"
            />
          </el-form-item>
        </el-form>
        <div class="warning-text">
          <el-alert
            title="警告：此操作不可恢复，请谨慎操作！"
            type="warning"
            :closable="false"
            show-icon
          />
        </div>
      </div>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="clearDialogVisible = false">取消</el-button>
          <el-button type="danger" @click="confirmClearLogs">确认清除</el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script>
import { defineComponent, ref, reactive, computed, onMounted, watch } from 'vue'
import { useStore } from 'vuex'
import { ElMessage, ElMessageBox } from 'element-plus'
import dayjs from 'dayjs'

export default defineComponent({
  name: 'LogsView',
  setup() {
    const store = useStore()
    
    // 状态
    const loading = computed(() => store.state.logs.loading)
    const logs = computed(() => store.state.logs.logs)
    const total = computed(() => store.state.logs.total)
    const clearLoading = ref(false)
    const exportLoading = ref(false)
    const clearDialogVisible = ref(false)
    const clearOption = ref('all')
    const clearBeforeDate = ref('')
    
    // 过滤条件
    const dateRange = ref([])
    const filterForm = reactive({
      level: '',
      keyword: '',
      module: ''
    })
    
    // 分页
    const pagination = reactive({
      currentPage: 1,
      pageSize: 20
    })
    
    // 选项
    const levelOptions = [
      { label: '错误', value: 'ERROR' },
      { label: '警告', value: 'WARN' },
      { label: '信息', value: 'INFO' },
      { label: '调试', value: 'DEBUG' },
      { label: '跟踪', value: 'TRACE' }
    ]
    
    const moduleOptions = [
      { label: '代理服务', value: 'proxy' },
      { label: '健康检查', value: 'health' },
      { label: '调度系统', value: 'scheduler' },
      { label: '系统', value: 'system' },
      { label: '安全', value: 'security' },
      { label: 'API', value: 'api' }
    ]
    
    // 加载日志数据
    const fetchLogs = async () => {
      const params = {
        page: pagination.currentPage,
        limit: pagination.pageSize,
        ...filterForm
      }
      
      if (dateRange.value && dateRange.value.length === 2) {
        params.startDate = dateRange.value[0]
        params.endDate = dateRange.value[1]
      }
      
      await store.dispatch('logs/getLogs', params)
    }
    
    // 过滤日志
    const handleFilter = () => {
      pagination.currentPage = 1
      fetchLogs()
    }
    
    // 重置过滤条件
    const resetFilter = () => {
      Object.keys(filterForm).forEach(key => {
        filterForm[key] = ''
      })
      dateRange.value = []
      pagination.currentPage = 1
      fetchLogs()
    }
    
    // 分页处理
    const handleSizeChange = (val) => {
      pagination.pageSize = val
      fetchLogs()
    }
    
    const handleCurrentChange = (val) => {
      pagination.currentPage = val
      fetchLogs()
    }
    
    // 清除日志
    const handleClearLogs = () => {
      clearDialogVisible.value = true
    }
    
    const confirmClearLogs = async () => {
      const params = {
        option: clearOption.value
      }
      
      if (clearOption.value === 'filtered') {
        if (dateRange.value && dateRange.value.length === 2) {
          params.startDate = dateRange.value[0]
          params.endDate = dateRange.value[1]
        }
        params.level = filterForm.level
        params.keyword = filterForm.keyword
        params.module = filterForm.module
      } else if (clearOption.value === 'date') {
        if (!clearBeforeDate.value) {
          ElMessage.warning('请选择日期')
          return
        }
        params.beforeDate = clearBeforeDate.value
      }
      
      try {
        clearLoading.value = true
        clearDialogVisible.value = false
        
        await store.dispatch('logs/clearLogs', params)
        ElMessage.success('日志清除成功')
        fetchLogs()
      } catch (error) {
        ElMessage.error('清除日志失败')
      } finally {
        clearLoading.value = false
      }
    }
    
    // 导出日志
    const handleExportLogs = async () => {
      try {
        exportLoading.value = true
        
        const params = { ...filterForm }
        
        if (dateRange.value && dateRange.value.length === 2) {
          params.startDate = dateRange.value[0]
          params.endDate = dateRange.value[1]
        }
        
        await store.dispatch('logs/exportLogs', params)
        ElMessage.success('日志导出成功')
      } catch (error) {
        ElMessage.error('导出日志失败')
      } finally {
        exportLoading.value = false
      }
    }
    
    // 复制日志条目
    const copyLogEntry = (log) => {
      const text = `[${formatDate(log.timestamp)}] [${log.level}] [${log.module}] ${log.message}`
      navigator.clipboard.writeText(text).then(() => {
        ElMessage.success('日志已复制到剪贴板')
      }, () => {
        ElMessage.error('复制失败，请检查浏览器权限')
      })
    }
    
    // 格式化日期
    const formatDate = (timestamp) => {
      return dayjs(timestamp).format('YYYY-MM-DD HH:mm:ss')
    }
    
    // 获取日志级别对应的样式类型
    const getLevelType = (level) => {
      const typeMap = {
        'ERROR': 'danger',
        'WARN': 'warning',
        'INFO': '',
        'DEBUG': 'info',
        'TRACE': 'info'
      }
      return typeMap[level] || ''
    }
    
    // 生命周期
    onMounted(() => {
      fetchLogs()
    })
    
    return {
      loading,
      logs,
      total,
      clearLoading,
      exportLoading,
      dateRange,
      filterForm,
      pagination,
      levelOptions,
      moduleOptions,
      clearDialogVisible,
      clearOption,
      clearBeforeDate,
      handleFilter,
      resetFilter,
      handleSizeChange,
      handleCurrentChange,
      handleClearLogs,
      confirmClearLogs,
      handleExportLogs,
      copyLogEntry,
      formatDate,
      getLevelType
    }
  }
})
</script>

<style lang="scss" scoped>
.logs-container {
  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    
    .header-actions {
      display: flex;
      gap: 16px;
    }
  }
  
  .filter-form {
    margin-bottom: 20px;
  }
  
  .log-detail {
    padding: 12px;
    background-color: #f8f8f8;
    border-radius: 4px;
    
    .detail-item {
      margin-bottom: 12px;
      
      &:last-child {
        margin-bottom: 0;
      }
      
      .label {
        font-weight: bold;
        display: block;
        margin-bottom: 4px;
      }
      
      .value {
        line-height: 1.5;
        
        &.log-message {
          white-space: pre-wrap;
          word-break: break-all;
        }
        
        &.stack-trace {
          font-family: monospace;
          white-space: pre-wrap;
          background-color: #f0f0f0;
          padding: 8px;
          border-radius: 4px;
          color: #d63031;
          max-height: 300px;
          overflow-y: auto;
        }
        
        &.context {
          pre {
            background-color: #f0f0f0;
            padding: 8px;
            border-radius: 4px;
            max-height: 300px;
            overflow-y: auto;
            margin: 0;
          }
        }
      }
    }
  }
  
  .error-message {
    color: #f56c6c;
  }
  
  .pagination-container {
    margin-top: 20px;
    display: flex;
    justify-content: flex-end;
  }
  
  .clear-dialog-content {
    .warning-text {
      margin-top: 20px;
    }
  }
}
</style>
