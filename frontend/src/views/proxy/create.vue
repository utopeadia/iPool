<template>
  <div class="proxy-create-container">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>{{ isEdit ? '编辑代理节点' : '新增代理节点' }}</span>
        </div>
      </template>
      
      <el-form 
        ref="proxyFormRef" 
        :model="proxyForm" 
        :rules="rules" 
        label-width="120px"
        class="proxy-form"
      >
        <el-form-item label="IP地址" prop="ip">
          <el-input v-model="proxyForm.ip" placeholder="请输入代理IP地址" />
        </el-form-item>
        
        <el-form-item label="端口" prop="port">
          <el-input-number v-model="proxyForm.port" :min="1" :max="65535" placeholder="请输入端口号" />
        </el-form-item>
        
        <el-form-item label="协议类型" prop="protocol">
          <el-select v-model="proxyForm.protocol" placeholder="请选择协议类型" style="width: 100%">
            <el-option label="HTTP" value="HTTP" />
            <el-option label="HTTPS" value="HTTPS" />
            <el-option label="SOCKS5" value="SOCKS5" />
          </el-select>
        </el-form-item>
        
        <el-form-item label="代理位置" prop="location">
          <el-input v-model="proxyForm.location" placeholder="请输入代理位置信息（可选）" />
        </el-form-item>
        
        <el-form-item>
          <el-divider content-position="left">认证信息（可选）</el-divider>
        </el-form-item>
        
        <el-form-item label="用户名">
          <el-input v-model="proxyForm.username" placeholder="请输入认证用户名（可选）" />
        </el-form-item>
        
        <el-form-item label="密码">
          <el-input v-model="proxyForm.password" type="password" placeholder="请输入认证密码（可选）" show-password />
        </el-form-item>
        
        <el-form-item>
          <el-divider content-position="left">高级设置</el-divider>
        </el-form-item>
        
        <el-form-item label="权重" prop="weight">
          <el-input-number v-model="proxyForm.weight" :min="1" :max="100" :step="1" placeholder="请设置代理权重" />
          <div class="form-tip">权重值越高，在轮询策略中被选中的概率越大</div>
        </el-form-item>
        
        <el-form-item label="最大连接数" prop="maxConnections">
          <el-input-number v-model="proxyForm.maxConnections" :min="1" :max="1000" placeholder="单个代理最大连接数" />
        </el-form-item>
        
        <el-form-item label="连接超时(ms)" prop="connectionTimeout">
          <el-input-number v-model="proxyForm.connectionTimeout" :min="100" :max="60000" :step="100" placeholder="连接超时时间" />
        </el-form-item>
        
        <el-form-item label="标签">
          <el-tag
            v-for="tag in proxyForm.tags"
            :key="tag"
            closable
            @close="handleRemoveTag(tag)"
            class="tag-item"
          >
            {{ tag }}
          </el-tag>
          <el-input
            v-if="inputTagVisible"
            ref="tagInputRef"
            v-model="inputTagValue"
            class="tag-input"
            size="small"
            @keyup.enter="handleAddTag"
            @blur="handleAddTag"
          />
          <el-button v-else size="small" @click="showTagInput">+ 添加标签</el-button>
          <div class="form-tip">添加标签可以更方便地进行分组和筛选</div>
        </el-form-item>
        
        <el-form-item>
          <el-button type="primary" @click="submitForm" :loading="submitting">{{ isEdit ? '保存修改' : '创建代理' }}</el-button>
          <el-button @click="resetForm">重置</el-button>
          <el-button v-if="!isEdit" @click="quickTest" :loading="testing">快速测试</el-button>
          <el-button @click="goBack">返回</el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script>
import { defineComponent, reactive, ref, computed, onMounted, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useStore } from 'vuex'
import { ElMessage } from 'element-plus'
import { validateIP, validatePort } from '@/utils/validate'

export default defineComponent({
  name: 'ProxyCreate',
  setup() {
    const route = useRoute()
    const router = useRouter()
    const store = useStore()
    
    const proxyId = computed(() => route.params.id)
    const isEdit = computed(() => !!proxyId.value)
    
    const proxyFormRef = ref(null)
    const tagInputRef = ref(null)
    const inputTagVisible = ref(false)
    const inputTagValue = ref('')
    const submitting = ref(false)
    const testing = ref(false)
    
    const proxyForm = reactive({
      id: undefined,
      ip: '',
      port: 8080,
      protocol: 'HTTP',
      location: '',
      username: '',
      password: '',
      weight: 10,
      maxConnections: 100,
      connectionTimeout: 5000,
      tags: []
    })
    
    const rules = {
      ip: [
        { required: true, message: '请输入IP地址', trigger: 'blur' },
        { validator: (rule, value, callback) => {
          if (!validateIP(value)) {
            callback(new Error('请输入有效的IP地址'))
          } else {
            callback()
          }
        }, trigger: 'blur' }
      ],
      port: [
        { required: true, message: '请输入端口号', trigger: 'blur' },
        { validator: (rule, value, callback) => {
          if (!validatePort(value)) {
            callback(new Error('端口号必须在1-65535之间'))
          } else {
            callback()
          }
        }, trigger: 'blur' }
      ],
      protocol: [
        { required: true, message: '请选择协议类型', trigger: 'change' }
      ],
      weight: [
        { required: true, message: '请设置代理权重', trigger: 'blur' }
      ],
      maxConnections: [
        { required: true, message: '请设置最大连接数', trigger: 'blur' }
      ],
      connectionTimeout: [
        { required: true, message: '请设置连接超时时间', trigger: 'blur' }
      ]
    }
    
    // 如果是编辑模式，加载代理数据
    const loadProxyData = async () => {
      if (isEdit.value) {
        try {
          const { data } = await store.dispatch('proxy/getProxyDetail', proxyId.value)
          Object.assign(proxyForm, data)
        } catch (error) {
          ElMessage.error('加载代理数据失败')
          goBack()
        }
      }
    }
    
    // 表单提交
    const submitForm = async () => {
      if (!proxyFormRef.value) return
      
      await proxyFormRef.value.validate(async (valid) => {
        if (valid) {
          submitting.value = true
          try {
            if (isEdit.value) {
              await store.dispatch('proxy/updateProxy', proxyForm)
              ElMessage.success('代理节点更新成功')
            } else {
              await store.dispatch('proxy/createProxy', proxyForm)
              ElMessage.success('代理节点创建成功')
            }
            goBack()
          } catch (error) {
            ElMessage.error(isEdit.value ? '更新代理节点失败' : '创建代理节点失败')
          } finally {
            submitting.value = false
          }
        }
      })
    }
    
    // 重置表单
    const resetForm = () => {
      proxyFormRef.value && proxyFormRef.value.resetFields()
      if (!isEdit.value) {
        proxyForm.tags = []
      } else {
        loadProxyData()
      }
    }
    
    // 快速测试代理
    const quickTest = async () => {
      if (!proxyFormRef.value) return
      
      await proxyFormRef.value.validate(async (valid) => {
        if (valid) {
          testing.value = true
          try {
            const testData = {
              ip: proxyForm.ip,
              port: proxyForm.port,
              protocol: proxyForm.protocol,
              username: proxyForm.username,
              password: proxyForm.password
            }
            
            const response = await store.dispatch('proxy/quickTest', testData)
            ElMessage.success(`测试成功，响应时间: ${response.responseTime}ms`)
          } catch (error) {
            ElMessage.error('代理测试失败')
          } finally {
            testing.value = false
          }
        }
      })
    }
    
    // 返回列表页
    const goBack = () => {
      router.push('/proxy/list')
    }
    
    // 标签相关
    const handleRemoveTag = (tag) => {
      proxyForm.tags = proxyForm.tags.filter(t => t !== tag)
    }
    
    const showTagInput = () => {
      inputTagVisible.value = true
      nextTick(() => {
        tagInputRef.value.focus()
      })
    }
    
    const handleAddTag = () => {
      const tag = inputTagValue.value.trim()
      if (tag) {
        if (!proxyForm.tags.includes(tag)) {
          proxyForm.tags.push(tag)
        }
      }
      inputTagVisible.value = false
      inputTagValue.value = ''
    }
    
    onMounted(() => {
      loadProxyData()
    })
    
    return {
      proxyFormRef,
      proxyForm,
      rules,
      isEdit,
      submitting,
      testing,
      tagInputRef,
      inputTagVisible,
      inputTagValue,
      submitForm,
      resetForm,
      quickTest,
      goBack,
      handleRemoveTag,
      showTagInput,
      handleAddTag
    }
  }
})
</script>

<style lang="scss" scoped>
.proxy-create-container {
  .proxy-form {
    max-width: 800px;
    margin: 0 auto;
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
    width: 100px;
    margin-right: 10px;
    vertical-align: bottom;
  }
}
</style>
