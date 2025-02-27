import request from './index'

export default {
  // 获取流量数据
  getTrafficData(timeRange = 'daily', params = {}) {
    return request({
      url: `/statistics/traffic/${timeRange}`,
      method: 'get',
      params
    })
  },
  
  // 获取代理统计数据
  getProxyStats(params) {
    return request({
      url: '/statistics/proxy',
      method: 'get',
      params
    })
  },
  
  // 获取特定代理的详细统计
  getProxyDetail(id, timeRange = 'daily') {
    return request({
      url: `/statistics/proxy/${id}/${timeRange}`,
      method: 'get'
    })
  },
  
  // 导出统计数据
  exportStatistics(params) {
    return request({
      url: '/statistics/export',
      method: 'get',
      params,
      responseType: 'blob'
    })
  }
}
