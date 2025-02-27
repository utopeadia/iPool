<template>
  <div class="health-settings-container">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>健康检查配置</span>
          <el-button type="primary" size="small" @click="saveSettings" :loading="saving">
            保存配置
          </el-button>
        </div>
      </template>
      
      <el-form ref="formRef" :model="form" label-width="180px" :disabled="loading">
        <el-form-item label="启用健康检查" prop="enabled">
          <el-switch v-model="form.enabled" />
          <div class="form-tip">启用后系统将定期检查代理节点的健康状态</div>
        </el-form-item>
        
        <el-divider content-position="left">检测配置</el-divider>
        
        <el-form-item label="检测间隔(秒)" prop="checkInterval">
          <el-input-number 
            v-model="form.checkInterval" 
            :min="30"
            :max="3600"
            :step="30"
            :disabled="!form.enabled"
          />
          <div class="form-tip">每次健康检查的间隔时间，推荐300秒</div>
        </el-form-item>
        
        <el-form-item label="检测超时(秒)" prop="checkTimeout">
          <el-input-number 
            v-model="form.checkTimeout" 
            :min="1"
            :max="60"
            :step="1"
            :disabled="!form.enabled"
          />
          <div class="form-tip">单次检查请求的超时时间</div>
        </el-form-item>
        
        <el-form-item label="检测URL" prop="checkUrls">
          <div v-for="(url, index) in form.checkUrls" :key="index" class="url-item">
            <el-input 
              v-model="form.checkUrls[index]" 
              placeholder="请输入检测URL"
              :disabled="!form.enabled"
            >
              <template #append>
                <el-button @click="removeCheckUrl(index)" :disabled="!form.enabled">
                  <el-icon><Delete /></el-icon>
                </el-button>
              </template>
            </el-input>
          </div>
          <el-button 
            type="primary" 
            plain 
            @click="addCheckUrl"
            :disabled="!form.enabled"
            style="margin-top: 10px;"
          >
            添加检测URL
          </el-button>
          <div class="form-tip">系统会通过代理访问这些URL来检测代理的可用性</div>
        </el-form-item>
        
        <el-divider content-position="left">健康状态评估</el-divider>
        
        <el-form-item label="响应时间阈值(ms)" prop="responseTimeThresholds">
          <div class="threshold-slider">
            <span class="threshold-label good">良好</span>
            <el-slider
              v-model="form.responseTimeThresholds"
              range
              :min="0"
              :max="5000"
              :step="50"
              :disabled="!form.enabled"
            />
            <span class="threshold-label warning">警告</span>
            <span class="threshold-label danger">严重</span>
          </div>
          <div class="threshold-values">
            <span>0ms</span>
            <span>{{ form.responseTimeThresholds[0] }}ms</span>
            <span>{{ form.responseTimeThresholds[1] }}ms</span>
            <span>5000ms</span>
          </div>
          <div class="form-tip">设置响应时间的评估阈值，低于第一个值为良好，高于第二个值为严重</div>
        </el-form-item>
        
        <el-form-item label="成功率阈值(%)" prop="successRateThresholds">
          <div class="threshold-slider">
            <span class="threshold-label danger">严重</span>
            <el-slider
              v-model="form.successRateThresholds"
              range
              :min="0"
              :max="100"
              :step="1"
              :disabled="!form.enabled"
            />
            <span class="threshold-label warning">警告</span>
            <span class="threshold-label good">良好</span>
          </div>
          <div class="threshold-values">
            <span>0%</span>
            <span>{{ form.successRateThresholds[0] }}%</span>
            <span>{{ form.successRateThresholds[1] }}%</span>
            <span>100%</span>
          </div>
          <div class="form-tip">设置成功率的评估阈值，低于第一个值为严重，高于第二个值为良好</div>
        </el-form-item>
        
        <el-divider content-position="left">故障处理</el-divider>
        
        <el-form-item label="自动隔离故障节点" prop="autoIsolate">
          <el-switch v-model="form.autoIsolate" :disabled="!form.enabled" />
          <div class="form-tip">启用后将自动隔离检测失败的代理节点，不再分配新请求</div>
        </el-form-item>
        
        <el-form-item label="故障阈值" prop="failureThreshold">
          <el-input-number 
            v-model="form.failureThreshold" 
            :min="1"
            :max="10"
            :disabled="!form.enabled || !form.autoIsolate"
          />
          <div class="form-tip">连续失败多少次后将节点标记为故障</div>
        </el-form-item>
        
        <el-form-item label="自动恢复时间(分钟)" prop="recoveryTime">
          <el-input-number 
            v-model="form.recoveryTime" 
            :min="0"
            :max="1440"
            :step="5"
            :disabled="!form.enabled || !form.autoIsolate"
          />
          <div class="form-tip">故障节点经过多长时间后自动恢复检测，0表示不自动恢复</div>
        </el-form-item>
        
        <el-form-item label="通知方式" prop="notificationMethods">
          <el-checkbox-group v-model="form.notificationMethods" :disabled="!form.enabled">
            <el-checkbox label="email">邮件通知</el-checkbox>
            <el-checkbox label="webhook">Webhook</el-checkbox>
            <el-checkbox label="sms">短信通知</el-checkbox>
          </el-checkbox-group>
        </el-form-item>
        
        <el-form-item v-if="form.notificationMethods.includes('webhook')" label="Webhook URL" prop="webhookUrl">
          <el-input v-model="form.webhookUrl" placeholder="请输入Webhook URL" :disabled="!form.enabled" />
        </el-form-item>
        
        <el-form-item v-if="form.notificationMethods.includes('email')" label="通知邮箱" prop="notificationEmails">
          <div v-for="(email, index) in form.notificationEmails" :key="index" class="email-item">
            <el-input 
              v-model="form.notificationEmails[index]" 
              placeholder="请输入邮箱地址"
              :disabled="!form.enabled"
            >
              <template #append>
                <el-button @click="removeEmail(index)" :disabled="!form.enabled">
                  <el-icon><Delete /></el-icon>
                </el-button>
              </template>
            </el-input>
          </div>
          <el-button 
            type="primary" 
            plain 
            @click="addEmail"
            :disabled="!form.enabled"
            style="margin-top: 10px;"
          >
            添加邮箱
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script>
import { defineComponent, ref, reactive, onMounted } from 'vue'
import { useStore } from 'vuex'
import { ElMessage } from 'element-plus'

export default defineComponent({
  name: 'HealthSettings',
  setup() {
    const store = useStore()
    const formRef = ref(null)
    const loading = ref(true)
    const saving = ref(false)
    
    const form = reactive({
      enabled: true,
      checkInterval: 300,
      checkTimeout: 10,
      checkUrls: ['https://www.google.com', 'https://www.baidu.com'],
      responseTimeThresholds: [500, 2000],
      successRateThresholds: [70, 95],
      autoIsolate: true,
      failureThreshold: 3,
      recoveryTime: 30,
      notificationMethods: ['email'],
      webhookUrl: '',
      notificationEmails: ['admin@example.com']
    })
    
    const loadSettings = async () => {
      loading.value = true
      try {
        const response = await store.dispatch('settings/getHealthSettings')
        
        if (response && response.data) {
          const { data } = response
          
          // 更新表单数据
          Object.assign(form, data)
        }
      } catch (error) {
        ElMessage.error('加载健康检查配置失败')
      } finally {
        loading.value = false
      }
    }
    
    const saveSettings = async () => {
      saving.value = true
      try {
        await store.dispatch('settings/saveHealthSettings', form)
        ElMessage.success('健康检查配置已保存')
      } catch (error) {
        ElMessage.error('保存健康检查配置失败')
      } finally {
        saving.value = false
      }
    }
    
    const addCheckUrl = () => {
      form.checkUrls.push('')
    }
    
    const removeCheckUrl = (index) => {
      form.checkUrls.splice(index, 1)
    }
    
    const addEmail = () => {
      form.notificationEmails.push('')
    }
    
    const removeEmail = (index) => {
      form.notificationEmails.splice(index, 1)
    }
    
    onMounted(() => {
      loadSettings()
    })
    
    return {
      formRef,
      form,
      loading,
      saving,
      saveSettings,
      addCheckUrl,
      removeCheckUrl,
      addEmail,
      removeEmail
    }
  }
})
</script>

<style lang="scss" scoped>
.health-settings-container {
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
  
  .url-item, .email-item {
    margin-bottom: 10px;
  }
  
  .threshold-slider {
    position: relative;
    padding-top: 20px;
    margin-bottom: 20px;
    
    .threshold-label {
      position: absolute;
      top: 0;
      
      &.good {
        left: 0;
        color: #67C23A;
      }
      
      &.warning {
        left: 50%;
        transform: translateX(-50%);
        color: #E6A23C;
      }
      
      &.danger {
        right: 0;
        color: #F56C6C;
      }
    }
  }
  
  .threshold-values {
    display: flex;
    justify-content: space-between;
    font-size: 12px;
    color: #909399;
    margin-top: -15px;
    margin-bottom: 10px;
  }
}
</style>
