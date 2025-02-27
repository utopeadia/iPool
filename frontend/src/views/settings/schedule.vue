<template>
  <div class="schedule-settings-container">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>调度策略配置</span>
          <el-button type="primary" size="small" @click="saveSettings" :loading="saving">
            保存配置
          </el-button>
        </div>
      </template>
      
      <el-form ref="formRef" :model="form" label-width="180px" :disabled="loading">
        <el-form-item label="当前调度策略" prop="currentStrategy">
          <el-select v-model="form.currentStrategy" style="width: 100%">
            <el-option 
              v-for="strategy in strategyOptions" 
              :key="strategy.value" 
              :label="strategy.label" 
              :value="strategy.value"
            />
          </el-select>
        </el-form-item>
        
        <el-divider content-position="left">策略参数配置</el-divider>
        
        <!-- 随机策略配置 -->
        <template v-if="form.currentStrategy === 'random'">
          <el-alert
            type="info"
            show-icon
            :closable="false"
          >
            随机策略会从所有可用的代理节点中随机选择一个作为当前请求的代理。
          </el-alert>
          
          <el-form-item label="仅使用活跃节点" prop="random.activeOnly">
            <el-switch v-model="form.random.activeOnly" />
            <div class="form-tip">启用后只会从状态为"活跃"的节点中选择代理</div>
          </el-form-item>
        </template>
        
        <!-- 轮询策略配置 -->
        <template v-if="form.currentStrategy === 'roundRobin'">
          <el-alert
            type="info"
            show-icon
            :closable="false"
          >
            轮询策略按照代理节点的添加顺序依次选择，并考虑节点的权重值。
          </el-alert>
          
          <el-form-item label="考虑节点权重" prop="roundRobin.weighted">
            <el-switch v-model="form.roundRobin.weighted" />
            <div class="form-tip">启用后会根据代理节点设置的权重值进行加权选择</div>
          </el-form-item>
          
          <el-form-item label="跳过不可用节点" prop="roundRobin.skipUnavailable">
            <el-switch v-model="form.roundRobin.skipUnavailable" />
            <div class="form-tip">启用后会自动跳过状态不为"活跃"的节点</div>
          </el-form-item>
        </template>
        
        <!-- 健康优先策略配置 -->
        <template v-if="form.currentStrategy === 'health'">
          <el-alert
            type="info"
            show-icon
            :closable="false"
          >
            健康优先策略会综合考虑代理节点的响应时间、成功率等因素，选择当前最健康的节点。
          </el-alert>
          
          <el-form-item label="响应时间权重" prop="health.responseTimeWeight">
            <el-slider v-model="form.health.responseTimeWeight" :min="1" :max="10" show-stops />
            <div class="form-tip">响应时间在评分中所占的权重，值越大表示响应时间的重要性越高</div>
          </el-form-item>
          
          <el-form-item label="成功率权重" prop="health.successRateWeight">
            <el-slider v-model="form.health.successRateWeight" :min="1" :max="10" show-stops />
            <div class="form-tip">成功率在评分中所占的权重，值越大表示成功率的重要性越高</div>
          </el-form-item>
          
          <el-form-item label="评分缓存时间(秒)" prop="health.scoreCacheTTL">
            <el-input-number v-model="form.health.scoreCacheTTL" :min="1" :max="3600" />
            <div class="form-tip">代理健康评分的缓存时间，避免频繁计算</div>
          </el-form-item>
        </template>
        
        <!-- 自定义规则策略配置 -->
        <template v-if="form.currentStrategy === 'custom'">
          <el-alert
            type="info"
            show-icon
            :closable="false"
          >
            自定义规则策略可以根据特定条件选择代理节点，支持基于 URL、请求头、IP 等条件的匹配规则。
          </el-alert>
          
          <el-form-item label="规则脚本" prop="custom.scriptEnabled">
            <el-switch v-model="form.custom.scriptEnabled" />
            <div class="form-tip">启用自定义规则脚本</div>
          </el-form-item>
          
          <el-form-item v-if="form.custom.scriptEnabled" label="规则定义">
            <el-input
              type="textarea"
              v-model="form.custom.script"
              :rows="10"
              :placeholder="scriptPlaceholder"
            />
            <div class="form-tip">使用 JavaScript 编写规则，函数接收请求信息返回选择的代理索引</div>
          </el-form-item>
          
          <el-form-item label="默认回退策略" prop="custom.fallbackStrategy">
            <el-select v-model="form.custom.fallbackStrategy" style="width: 100%">
              <el-option label="随机策略" value="random" />
              <el-option label="轮询策略" value="roundRobin" />
              <el-option label="健康优先" value="health" />
            </el-select>
            <div class="form-tip">当自定义规则无法匹配或出错时使用的默认策略</div>
          </el-form-item>
        </template>
        
        <el-divider content-position="left">全局配置</el-divider>
        
        <el-form-item label="代理失败重试" prop="maxRetries">
          <el-input-number v-model="form.maxRetries" :min="0" :max="10" />
          <div class="form-tip">当代理连接失败时最大重试次数，0 表示不重试</div>
        </el-form-item>
        
        <el-form-item label="重试等待时间(ms)" prop="retryDelay">
          <el-input-number v-model="form.retryDelay" :min="0" :max="10000" :step="100" />
          <div class="form-tip">每次重试之间的等待时间</div>
        </el-form-item>
        
        <el-form-item label="禁用策略黑名单" prop="blacklist">
          <el-tag
            v-for="ip in form.blacklist"
            :key="ip"
            closable
            type="danger"
            @close="handleRemoveBlacklist(ip)"
            class="tag-item"
          >
            {{ ip }}
          </el-tag>
          <el-input
            v-if="blacklistInputVisible"
            ref="blacklistInputRef"
            v-model="blacklistInputValue"
            class="tag-input"
            size="small"
            @keyup.enter="handleAddBlacklist"
            @blur="handleAddBlacklist"
          />
          <el-button v-else size="small" @click="showBlacklistInput">+ 添加IP</el-button>
          <div class="form-tip">黑名单中的IP将不会被分配代理</div>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script>
import { defineComponent, ref, reactive, onMounted, nextTick, computed } from 'vue'
import { useStore } from 'vuex'
import { ElMessage } from 'element-plus'
import { validateIP } from '@/utils/validate'

export default defineComponent({
  name: 'ScheduleSettings',
  setup() {
    const store = useStore()
    const formRef = ref(null)
    const loading = ref(true)
    const saving = ref(false)
    
    // 黑名单管理
    const blacklistInputRef = ref(null)
    const blacklistInputVisible = ref(false)
    const blacklistInputValue = ref('')
    
    const scriptPlaceholder = ref(`// 示例规则脚本
// 输入: request - 当前请求的信息
// 输出: 返回选择的代理索引，或 null 表示使用默认策略
function selectProxy(request, availableProxies) {
  // 根据请求URL选择特定国家的代理
  if (request.url.includes('example.com')) {
    // 查找美国代理
    for (let i = 0; i < availableProxies.length; i++) {
      if (availableProxies[i].location.includes('US')) {
        return i;
      }
    }
  }
  
  // 根据请求来源IP选择代理
  if (request.clientIp.startsWith('192.168.')) {
    // 对内网IP使用高速代理
    for (let i = 0; i < availableProxies.length; i++) {
      if (availableProxies[i].tags.includes('highspeed')) {
        return i;
      }
    }
  }
  
  // 默认返回null，使用备选策略
  return null;
}`);
    
    const strategyOptions = [
      { label: '随机策略 (Random)', value: 'random' },
      { label: '轮询策略 (Round-Robin)', value: 'roundRobin' },
      { label: '健康优先 (Health First)', value: 'health' },
      { label: '自定义规则 (Custom Rules)', value: 'custom' }
    ]
    
    const form = reactive({
      currentStrategy: 'random',
      random: {
        activeOnly: true
      },
      roundRobin: {
        weighted: true,
        skipUnavailable: true
      },
      health: {
        responseTimeWeight: 5,
        successRateWeight: 7,
        scoreCacheTTL: 60
      },
      custom: {
        scriptEnabled: false,
        script: '',
        fallbackStrategy: 'random'
      },
      maxRetries: 3,
      retryDelay: 1000,
      blacklist: []
    })
    
    // 加载设置
    const loadSettings = async () => {
      loading.value = true
      try {
        const response = await store.dispatch('settings/getScheduleSettings')
        
        if (response && response.data) {
          const { data } = response
          
          // 更新表单数据
          form.currentStrategy = data.currentStrategy || 'random'
          form.maxRetries = data.maxRetries !== undefined ? data.maxRetries : 3
          form.retryDelay = data.retryDelay || 1000
          form.blacklist = data.blacklist || []
          
          // 更新各策略配置
          if (data.random) {
            form.random = { ...form.random, ...data.random }
          }
          
          if (data.roundRobin) {
            form.roundRobin = { ...form.roundRobin, ...data.roundRobin }
          }
          
          if (data.health) {
            form.health = { ...form.health, ...data.health }
          }
          
          if (data.custom) {
            form.custom = { ...form.custom, ...data.custom }
          }
        }
      } catch (error) {
        ElMessage.error('加载调度策略配置失败')
      } finally {
        loading.value = false
      }
    }
    
    // 保存设置
    const saveSettings = async () => {
      saving.value = true
      try {
        await store.dispatch('settings/saveScheduleSettings', form)
        ElMessage.success('调度策略配置已保存')
      } catch (error) {
        ElMessage.error('保存调度策略配置失败')
      } finally {
        saving.value = false
      }
    }
    
    // 黑名单管理
    const handleRemoveBlacklist = (ip) => {
      form.blacklist = form.blacklist.filter(item => item !== ip)
    }
    
    const showBlacklistInput = () => {
      blacklistInputVisible.value = true
      nextTick(() => {
        blacklistInputRef.value.focus()
      })
    }
    
    const handleAddBlacklist = () => {
      const ip = blacklistInputValue.value.trim()
      if (ip) {
        if (!validateIP(ip)) {
          ElMessage.warning('请输入有效的IP地址')
          return
        }
        
        if (!form.blacklist.includes(ip)) {
          form.blacklist.push(ip)
        }
      }
      blacklistInputVisible.value = false
      blacklistInputValue.value = ''
    }
    
    onMounted(() => {
      loadSettings()
    })
    
    return {
      formRef,
      form,
      loading,
      saving,
      strategyOptions,
      scriptPlaceholder,
      blacklistInputRef,
      blacklistInputVisible,
      blacklistInputValue,
      saveSettings,
      handleRemoveBlacklist,
      showBlacklistInput,
      handleAddBlacklist
    }
  }
})
</script>

<style lang="scss" scoped>
.schedule-settings-container {
  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }
  
  .form-tip {
    color: #909399;
    font-size: 12px;
    line-height: 1.5;
    margin-top: 5px;
  }
  
  .tag-item {
    margin-right: 10px;
    margin-bottom: 10px;
  }
  
  .tag-input {
    width: 180px;
    margin-right: 10px;
    vertical-align: bottom;
  }
  
  .el-alert {
    margin-bottom: 20px;
  }
}
</style>
