import api from '@/api/statistics'

const state = {
  trafficData: {
    daily: {},
    weekly: {},
    monthly: {}
  },
  proxyStats: [],
  loading: false
}

const mutations = {
  SET_TRAFFIC_DATA: (state, { timeRange, data }) => {
    state.trafficData[timeRange] = data
  },
  SET_PROXY_STATS: (state, stats) => {
    state.proxyStats = stats
  },
  SET_LOADING: (state, loading) => {
    state.loading = loading
  }
}

const actions = {
  async getTrafficData({ commit }, timeRange = 'daily') {
    commit('SET_LOADING', true)
    try {
      const { data } = await api.getTrafficData(timeRange)
      commit('SET_TRAFFIC_DATA', { timeRange, data })
      return data
    } finally {
      commit('SET_LOADING', false)
    }
  },
  
  async getProxyStats({ commit }, params) {
    commit('SET_LOADING', true)
    try {
      const { data } = await api.getProxyStats(params)
      commit('SET_PROXY_STATS', data)
      return data
    } finally {
      commit('SET_LOADING', false)
    }
  }
}

export default {
  namespaced: true,
  state,
  mutations,
  actions
}
