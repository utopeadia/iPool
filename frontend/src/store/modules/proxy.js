import api from '@/api/proxy'

const state = {
  proxyList: [],
  totalProxyCount: 0,
  activeProxyCount: 0,
  loading: false
}

const mutations = {
  SET_PROXY_LIST: (state, proxyList) => {
    state.proxyList = proxyList
  },
  SET_TOTAL_COUNT: (state, count) => {
    state.totalProxyCount = count
  },
  SET_ACTIVE_COUNT: (state, count) => {
    state.activeProxyCount = count
  },
  SET_LOADING: (state, loading) => {
    state.loading = loading
  },
  ADD_PROXY: (state, proxy) => {
    state.proxyList.push(proxy)
    state.totalProxyCount++
    if (proxy.status === 'active') {
      state.activeProxyCount++
    }
  },
  UPDATE_PROXY: (state, updatedProxy) => {
    const index = state.proxyList.findIndex(item => item.id === updatedProxy.id)
    if (index > -1) {
      const oldStatus = state.proxyList[index].status
      const newStatus = updatedProxy.status
      
      if (oldStatus === 'active' && newStatus !== 'active') {
        state.activeProxyCount--
      } else if (oldStatus !== 'active' && newStatus === 'active') {
        state.activeProxyCount++
      }
      
      state.proxyList.splice(index, 1, updatedProxy)
    }
  },
  REMOVE_PROXY: (state, id) => {
    const index = state.proxyList.findIndex(item => item.id === id)
    if (index > -1) {
      if (state.proxyList[index].status === 'active') {
        state.activeProxyCount--
      }
      state.proxyList.splice(index, 1)
      state.totalProxyCount--
    }
  }
}

const actions = {
  async getProxyList({ commit }, params) {
    commit('SET_LOADING', true)
    try {
      const { data } = await api.getProxyList(params)
      commit('SET_PROXY_LIST', data.items || [])
      commit('SET_TOTAL_COUNT', data.total || 0)
      commit('SET_ACTIVE_COUNT', data.activeCount || 0)
    } finally {
      commit('SET_LOADING', false)
    }
  },
  async createProxy({ commit }, proxyData) {
    const { data } = await api.createProxy(proxyData)
    commit('ADD_PROXY', data)
    return data
  },
  async updateProxy({ commit }, proxyData) {
    const { data } = await api.updateProxy(proxyData.id, proxyData)
    commit('UPDATE_PROXY', data)
    return data
  },
  async deleteProxy({ commit }, id) {
    await api.deleteProxy(id)
    commit('REMOVE_PROXY', id)
  },
  async testProxy(_, id) {
    const { data } = await api.testProxy(id)
    return data
  }
}

export default {
  namespaced: true,
  state,
  mutations,
  actions
}
