<template>
  <transition name="fade">
    <div class="modal-overlay" @click.self="$emit('close')">
      <div class="modal-content">
        <div class="modal-header">
          <h3>Settings</h3>
          <button class="close-btn" @click="$emit('close')">
            <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>
          </button>
        </div>
        
        <div class="tabs">
          <button :class="{ active: activeTab === 'providers' }" @click="activeTab = 'providers'">Providers</button>
          <button :class="{ active: activeTab === 'models' }" @click="activeTab = 'models'">Models</button>
        </div>

        <div class="tab-content" v-if="activeTab === 'providers'">
          <div class="section-header">
            <h4>Configured Providers</h4>
          </div>
          <ul class="list">
            <li v-for="p in providers" :key="p.id">
              <div class="info">
                <span class="name">{{ p.name }}</span>
                <span class="url">{{ p.base_url }}</span>
              </div>
              <div class="actions">
                  <button class="icon-btn sync" @click="syncProvider(p.id)" title="Sync Models">
                    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21.5 2v6h-6M2.5 22v-6h6M2 11.5a10 10 0 0 1 18.8-4.3M22 12.5a10 10 0 0 1-18.8 4.3"/></svg>
                  </button>
                  <button class="icon-btn delete" @click="deleteProvider(p.id)" title="Delete">
                    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="3 6 5 6 21 6"></polyline><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path></svg>
                  </button>
              </div>
            </li>
          </ul>
          <div class="add-form">
            <h4>Add New Provider</h4>
            <div class="form-group">
                <input v-model="newProvider.name" placeholder="Name (e.g. OpenAI)" />
                <input v-model="newProvider.base_url" placeholder="Base URL" />
            </div>
            <div class="form-group">
                <input v-model="newProvider.api_key" placeholder="API Key" type="password" />
                <button @click="addProvider" class="primary-btn">Add Provider</button>
            </div>
          </div>
        </div>

        <div class="tab-content" v-if="activeTab === 'models'">
          <div class="section-header">
            <h4>Cached Models</h4>
            <p class="hint">Sync via Providers tab to update list.</p>
          </div>
          <ul class="list">
            <li v-for="m in allModels" :key="m.id">
              <div class="info">
                <span class="name">{{ m.name }}</span>
                <span class="sub">{{ getProviderName(m.provider) }}</span>
              </div>
              <button class="icon-btn delete" @click="deleteModel(m.id)">
                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="3 6 5 6 21 6"></polyline><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path></svg>
              </button>
            </li>
          </ul>
        </div>

      </div>
    </div>
  </transition>
</template>

<script>
import { mapState } from 'vuex'
import axios from 'axios'

export default {
  name: 'SettingsModal',
  data() {
    return {
      activeTab: 'providers',
      newProvider: { name: '', base_url: '', api_key: '' },
      newModel: { provider: null, name: '', display_name: '' },
      allModels: []
    }
  },
  computed: {
    ...mapState(['providers', 'providerFetchError'])
  },
  created() {
      this.fetchModels()
      this.$store.dispatch('fetchProviders')
  },
  methods: {
    getProviderName(id) {
        const p = this.providers.find(p => p.id === id)
        return p ? p.name : 'Unknown'
    },
    async fetchModels() {
        try {
            const res = await axios.get('/api/models/')
            this.allModels = res.data
        } catch(e) { console.error(e) }
    },
    async addProvider() {
      try {
        if (!this.newProvider.name || !this.newProvider.base_url) {
            alert("Name and Base URL are required")
            return
        }
        console.log("Adding provider:", this.newProvider)
        const payload = { ...this.newProvider }
        await axios.post('/api/providers/', payload)
        this.newProvider = { name: '', base_url: '', api_key: '' }
        this.$store.dispatch('fetchProviders')
      } catch (e) { 
        console.error(e)
        alert('Failed to add provider: ' + JSON.stringify(e.response?.data || e.message))
      }
    },
    async deleteProvider(id) {
      if(!confirm('Delete provider?')) return
      try {
        await axios.delete(`/api/providers/${id}/`)
        this.$store.dispatch('fetchProviders')
      } catch (e) { alert('Failed to delete provider') }
    },
    async addModel() {
      try {
        await axios.post('/api/models/', this.newModel)
        this.newModel = { provider: null, name: '', display_name: '' }
        this.fetchModels()
        this.$store.dispatch('fetchProviders') // models are nested in provider list for selector
      } catch (e) { alert('Failed to add model') }
    },
    async syncProvider(id) {
        try {
            const res = await axios.post(`/api/providers/${id}/refresh_models/`)
            alert(`Synced ${res.data.count} models!`)
            this.fetchModels()
            this.$store.dispatch('fetchProviders')
        } catch (e) {
            console.error(e)
            alert('Failed to sync: ' + JSON.stringify(e.response?.data || e.message))
        }
    },
    async deleteModel(id) {
       if(!confirm('Delete model?')) return
       try {
        await axios.delete(`/api/models/${id}/`)
        this.fetchModels()
        this.$store.dispatch('fetchProviders')
      } catch (e) { alert('Failed to delete model') }
    }
  }
}
</script>

<style scoped>
.modal-overlay {
  position: fixed;
  top: 0; left: 0; right: 0; bottom: 0;
  background: rgba(0,0,0,0.7);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 100;
  backdrop-filter: blur(2px);
}
.modal-content {
  background: var(--bg-primary);
  width: 600px;
  max-width: 90vw;
  max-height: 80vh;
  border-radius: 12px;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  color: var(--text-primary);
  box-shadow: var(--shadow-lg);
  border: 1px solid var(--border-color);
}
.modal-header {
  padding: 16px 24px;
  border-bottom: 1px solid var(--border-color);
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.modal-header h3 {
    margin: 0;
    font-size: 1.1rem;
}
.close-btn {
  background: none;
  border: none;
  color: var(--text-secondary);
  cursor: pointer;
  padding: 4px;
  display: flex;
  border-radius: 4px;
}
.close-btn:hover {
    background: var(--bg-hover);
    color: var(--text-primary);
}
.tabs {
  display: flex;
  border-bottom: 1px solid var(--border-color);
  background: var(--bg-secondary);
}
.tabs button {
  flex: 1;
  padding: 14px;
  background: none;
  border: none;
  color: var(--text-secondary);
  cursor: pointer;
  font-weight: 500;
  transition: all 0.2s;
}
.tabs button:hover {
    color: var(--text-primary);
    background: rgba(255,255,255,0.03);
}
.tabs button.active {
  border-bottom: 2px solid var(--accent-blue);
  color: var(--text-primary);
  background: var(--bg-primary);
}
.tab-content {
  padding: 24px;
  overflow-y: auto;
  flex: 1;
}
.section-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 16px;
}
.section-header h4 {
    margin: 0;
}
.hint {
    font-size: 0.8rem;
    color: var(--text-tertiary);
    margin: 0;
}
.list {
  list-style: none;
  padding: 0;
}
.list li {
  background: var(--bg-secondary);
  margin-bottom: 8px;
  padding: 12px 16px;
  border-radius: 6px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  border: 1px solid transparent;
}
.list li:hover {
    border-color: var(--border-color);
}
.list li .info {
    display: flex;
    flex-direction: column;
}
.list li .name {
    font-weight: 500;
}
.list li .url, .list li .sub {
    font-size: 0.8rem;
    color: var(--text-secondary);
}
.list li .actions {
    display: flex;
    gap: 8px;
}
.icon-btn {
    background: transparent;
    border: none;
    color: var(--text-secondary);
    cursor: pointer;
    padding: 6px;
    border-radius: 4px;
    display: flex;
}
.icon-btn:hover {
    background: var(--bg-hover);
    color: var(--text-primary);
}
.icon-btn.sync:hover {
    color: var(--accent-blue);
    background: rgba(37, 99, 235, 0.1);
}
.icon-btn.delete:hover {
    color: #ef4444;
    background: rgba(239, 68, 68, 0.1);
}

.add-form {
  margin-top: 24px;
  padding-top: 24px;
  border-top: 1px solid var(--border-color);
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.form-group {
    display: flex;
    gap: 12px;
}
.form-group input {
    flex: 1;
}
input {
  padding: 10px;
  background: var(--bg-input);
  border: 1px solid var(--border-color);
  color: var(--text-primary);
  border-radius: 6px;
  outline: none;
}
input:focus {
    border-color: var(--accent-blue);
}
.primary-btn {
  padding: 10px 20px;
  background: var(--accent-blue);
  border: 1px solid transparent;
  color: white;
  border-radius: 6px;
  cursor: pointer;
  font-weight: 500;
  transition: opacity 0.2s;
}
.primary-btn:hover {
    opacity: 0.9;
}

/* Transitions */
.fade-enter-active, .fade-leave-active {
  transition: opacity 0.2s;
}
.fade-enter, .fade-leave-to {
  opacity: 0;
}
</style>
