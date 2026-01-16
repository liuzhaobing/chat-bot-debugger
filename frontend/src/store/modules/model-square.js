import axios from 'axios'

const API_BASE = '/api'

export default {
  namespaced: true,
  state: {
    providers: [],
    selectedModel: null, // { provider_id, model_name }
    providerFetchError: null
  },
  mutations: {
    SET_PROVIDER_ERROR(state, error) {
      state.providerFetchError = error
    },
    SET_PROVIDERS(state, providers) {
      state.providers = providers
    },
    SET_SELECTED_MODEL(state, model) {
      state.selectedModel = model
    }
  },
  actions: {
    async fetchProviders({ commit }) {
      try {
        commit('SET_PROVIDER_ERROR', null)
        const res = await axios.get(`${API_BASE}/providers/`)
        console.log("Fetch Providers Success:", res.data)
        commit('SET_PROVIDERS', res.data)
        // Set default model if not set
        if (res.data.length > 0) {
          let targetModel = null
          let targetProviderId = null

          // 1. Try to find Qwen/Qwen3-8B
          for (const p of res.data) {
            const qwen = p.models.find(m => m.name === 'Qwen/Qwen3-8B')
            if (qwen) {
              targetModel = qwen
              targetProviderId = p.id
              break
            }
          }

          // 2. Fallback to first provider first model
          if (!targetModel && res.data[0].models.length > 0) {
            targetProviderId = res.data[0].id
            targetModel = res.data[0].models[0]
          }

          if (targetModel) {
            commit('SET_SELECTED_MODEL', {
              provider_id: targetProviderId,
              model_name: targetModel.name
            })
          }
        }
      } catch (e) {
        console.error("Failed to fetch providers", e)
        commit('SET_PROVIDER_ERROR', e.message + (e.response ? ` (${e.response.status})` : ''))
      }
    }
  }
}
