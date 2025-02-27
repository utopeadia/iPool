import { createStore } from 'vuex'
import proxy from './modules/proxy'
import settings from './modules/settings'
import statistics from './modules/statistics'
import logs from './modules/logs'

export default createStore({
  state: {
    sidebar: {
      opened: true
    },
    loading: false
  },
  mutations: {
    TOGGLE_SIDEBAR: state => {
      state.sidebar.opened = !state.sidebar.opened
    },
    SET_LOADING: (state, isLoading) => {
      state.loading = isLoading
    }
  },
  actions: {
    toggleSidebar({ commit }) {
      commit('TOGGLE_SIDEBAR')
    },
    setLoading({ commit }, isLoading) {
      commit('SET_LOADING', isLoading)
    }
  },
  modules: {
    proxy,
    settings,
    statistics,
    logs
  }
})
