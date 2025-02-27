import axios from 'axios'
import { ElMessage, ElLoading } from 'element-plus'

// 创建axios实例
const service = axios.create({
  baseURL: process.env.VUE_APP_API_URL || '/api',
  timeout: 15000
})

let loadingInstance = null

// 请求拦截器
service.interceptors.request.use(
  config => {
    // 全局loading
    if (config.loading !== false) {
      loadingInstance = ElLoading.service({
        lock: true,
        text: '加载中...',
        background: 'rgba(0, 0, 0, 0.7)'
      })
    }
    return config
  },
  error => {
    console.error('Request error:', error)
    return Promise.reject(error)
  }
)

// 响应拦截器
service.interceptors.response.use(
  response => {
    if (loadingInstance) {
      loadingInstance.close()
    }
    
    const res = response.data
    
    // 这里约定服务器返回的数据格式
    if (res.code && res.code !== 0) {
      ElMessage({
        message: res.message || '接口请求错误',
        type: 'error',
        duration: 5 * 1000
      })
      return Promise.reject(new Error(res.message || '接口请求错误'))
    } else {
      return res
    }
  },
  error => {
    if (loadingInstance) {
      loadingInstance.close()
    }
    
    console.error('Response error:', error)
    const message = error.response?.data?.message || '网络请求失败，请稍后重试'
    
    ElMessage({
      message,
      type: 'error',
      duration: 5 * 1000
    })
    
    return Promise.reject(error)
  }
)

export default service
