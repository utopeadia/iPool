import request from './index'

export default {
  // 获取日志列表
  getLogs(params) {
    return request({
      url: '/logs',
      method: 'get',
      params
    })
  },
  
  // 清除日志
  clearLogs(params) {
    return request({
      url: '/logs/clear',
      method: 'post',
      data: params
    })
  },
  
  // 导出日志
  exportLogs(params) {
    return request({
      url: '/logs/export',
      method: 'get',
      params,
      responseType: 'blob'
    })
  }
}
