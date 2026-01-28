import Vue from 'vue'
import Vuex from 'vuex'
import appSquare from './modules/app-square'
import chatCompletion from './modules/chat-completion'
import dialAgent from './modules/dial-agent'
import modelSquare from './modules/model-square'
import agenticTest from './modules/agentic-test'

Vue.use(Vuex)

export default new Vuex.Store({
  state: {
    theme: localStorage.getItem('theme') || 'light',
    isSidebarCollapsed: false,
    isRightSidebarOpen: false
  },
  mutations: {
    SET_THEME(state, theme) {
      state.theme = theme
      localStorage.setItem('theme', theme)
      document.documentElement.setAttribute('data-theme', theme)
    },
    SET_SIDEBAR_COLLAPSED(state, collapsed) {
      state.isSidebarCollapsed = collapsed
    },
    SET_RIGHT_SIDEBAR_OPEN(state, open) {
      state.isRightSidebarOpen = open
    }
  },
  modules: {
    appSquare,
    chatCompletion,
    dialAgent,
    modelSquare,
    agenticTest
  }
})
