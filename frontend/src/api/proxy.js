import request from './index'

export default {
  // 获取代理节点列表
  getProxyList(params) {
    return request({
      url: '/proxy/list',
      method: 'get',
      params
    })
  },
  
  // 获取单个代理节点详情
  getProxyDetail(id) {
    return request({
      url: `/proxy/${id}`,
      method: 'get'
    })
  },
  
  // 创建代理节点
  createProxy(data) {
    return request({
      url: '/proxy',
      method: 'post',
      data
    })
  },
  
  // 更新代理节点
  updateProxy(id, data) {
    return request({
      url: `/proxy/${id}`,
      method: 'put',
      data
    })
  },
  
  // 删除代理节点
  deleteProxy(id) {
    return request({
      url: `/proxy/${id}`,
      method: 'delete'
    })
  },
  
  // 测试代理节点连通性
  testProxy(id) {
    return request({
      url: `/proxy/${id}/test`,
      method: 'post'
    })
  },
  
  // 批量导入代理
  batchImport(data) {
    return request({
      url: '/proxy/batch',
      method: 'post',
      data
    })
  },
  
  // 导出代理列表
  exportProxies(params) {
    return request({
      url: '/proxy/export',
      method: 'get',
      params,
      responseType: 'blob'
    })
  }
}
