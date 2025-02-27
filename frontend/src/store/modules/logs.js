import api from '@/api/logs'

const state = {
  logs: [],
  total: 0,
  loading: false
}

const mutations = {
  SET_LOGS: (state, logs) => {
    state.logs = logs
  },
  SET_TOTAL: (state, total) => {
    state.total = total
  },
  SET_LOADING: (state, loading) => {
    state.loading = loading
  },
  CLEAR_LOGS: (state) => {
    state.logs = []
    state.total = 0
  }
}

const actions = {
  async getLogs({ commit }, params) {
    commit('SET_LOADING', true)
    try {
      const { data } = await api.getLogs(params)
      commit('SET_LOGS', data.items || [])
      commit('SET_TOTAL', data.total || 0)
      return data
    } finally {
      commit('SET_LOADING', false)
    }
  },
  
  async clearLogs({ commit }, params) {
    const { data } = await api.clearLogs(params)
    commit('CLEAR_LOGS')
    return data
  },
  
  async exportLogs(_, params) {
    return await api.exportLogs(params)
  }
}

export default {
  namespaced: true,
  state,
  mutations,
  actions
}
