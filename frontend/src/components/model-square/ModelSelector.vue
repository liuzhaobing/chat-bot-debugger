<template>
  <div class="model-selector-container">
    <!-- Trigger Button -->
    <div class="model-trigger" @click="showModal = true">
      <span class="current-model">{{ currentModelDisplayName }}</span>
      <svg class="arrow" xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M6 9l6 6 6-6"/></svg>
    </div>

    <!-- Modal Overlay -->
    <transition name="fade">
      <div class="modal-overlay" v-if="showModal" @click.self="showModal = false">
        <div class="selector-modal">
          <div class="modal-header">
              <h3>Select Model</h3>
              <button class="close-btn" @click="showModal = false">
                <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>
              </button>
          </div>
          
          <!-- Search Box -->
          <div class="search-box">
            <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"></circle><path d="m21 21-4.35-4.35"></path></svg>
            <input v-model="searchQuery" type="text" placeholder="Search models..." />
          </div>
          
          <div class="modal-body">
              <!-- Provider Tabs -->
              <div class="provider-list">
                  <div 
                      v-for="provider in providers" 
                      :key="provider.id"
                      class="provider-item"
                      :class="{ active: activeProviderId === provider.id }"
                      @click="activeProviderId = provider.id"
                  >
                      {{ provider.name }}
                  </div>
              </div>

              <!-- Model Grid -->
              <div class="model-grid">
                  <div 
                      v-for="model in filteredModels" 
                      :key="model.id"
                      class="model-card"
                      :class="{ selected: isSelected(model) }"
                      @click="selectModel(activeProviderId, model)"
                  >
                      <div class="model-info">
                        <div class="model-name">{{ model.display_name || model.name }}</div>
                        <div class="model-id">{{ model.name }}</div>
                      </div>
                      <div class="check-icon" v-if="isSelected(model)">
                        <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"></polyline></svg>
                      </div>
                  </div>
                  <div v-if="!activeProviderId" class="empty-state">
                      No providers configured. Go to Settings to add one.
                  </div>
                  <div v-else-if="filteredModels.length === 0 && searchQuery" class="empty-state">
                      <p>No models match "{{ searchQuery }}"</p>
                  </div>
                  <div v-else-if="currentProviderModels.length === 0" class="empty-state">
                      <p>No models found for this provider.</p>
                      <button @click="syncCurrentProvider" class="sync-btn-small">Sync Models Now</button>
                      <p class="hint-text">Required: correct API Key in Settings.</p>
                  </div>
              </div>
          </div>
        </div>
      </div>
    </transition>
  </div>
</template>

<script>
import { mapState } from 'vuex'
import axios from 'axios'

export default {
  name: 'ModelSelector',
  data() {
    return {
      showModal: false,
      activeProviderId: null,
      searchQuery: ''
    }
  },
  computed: {
    ...mapState('modelSquare', ['providers', 'selectedModel']),
    currentModelDisplayName() {
        if (!this.selectedModel) return 'Select Model'
        // Find provider name and model display name if possible
        const provider = this.providers.find(p => p.id === this.selectedModel.provider_id)
        if (!provider) return this.selectedModel.model_name
        
        const model = provider.models.find(m => m.name === this.selectedModel.model_name)
        return (model?.display_name || model?.name)
    },
    currentProviderModels() {
        if (!this.activeProviderId) return []
        const provider = this.providers.find(p => p.id === this.activeProviderId)
        return provider ? provider.models : []
    },
    filteredModels() {
        if (!this.searchQuery.trim()) return this.currentProviderModels
        const query = this.searchQuery.toLowerCase()
        return this.currentProviderModels.filter(model => {
            const name = (model.display_name || model.name).toLowerCase()
            const id = model.name.toLowerCase()
            return name.includes(query) || id.includes(query)
        })
    }
  },
  watch: {
    providers: {
        handler(val) {
            if (val.length > 0 && !this.activeProviderId) {
                this.activeProviderId = val[0].id
            }
        },
        immediate: true
    },
    showModal(val) {
        if (val && this.selectedModel) {
            this.activeProviderId = this.selectedModel.provider_id
        }
    }
  },
  methods: {
    isSelected(model) {
        return this.selectedModel && 
               this.selectedModel.provider_id === this.activeProviderId && 
               this.selectedModel.model_name === model.name
    },
    selectModel(providerId, model) {
        this.$store.commit('modelSquare/SET_SELECTED_MODEL', {
            provider_id: providerId,
            model_name: model.name
        })
        this.showModal = false
    },
    async syncCurrentProvider() {
        if (!this.activeProviderId) return
        try {
            const res = await axios.post(`/api/providers/${this.activeProviderId}/refresh_models/`)
            alert(`Synced ${res.data.count} models!`)
            this.$store.dispatch('modelSquare/fetchProviders')
        } catch (e) {
            console.error(e)
            alert('Failed to sync: ' + JSON.stringify(e.response?.data || e.message))
        }
    }
  }
}
</script>

<style scoped>
.model-selector-container {
  display: flex;
  align-items: center;
  z-index: 20;
}

.model-trigger {
  background-color: transparent;
  color: var(--text-secondary);
  padding: 8px 16px;
  border-radius: 8px;
  font-size: 1.1rem;
  font-weight: 600;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 8px;
  transition: all 0.2s;
  white-space: nowrap;
}

.current-model {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 300px; /* Optional cap */
}

.model-trigger:hover {
  background-color: var(--bg-surface);
  color: var(--text-primary);
}

.arrow {
  opacity: 0.7;
}

/* Modal Styles */
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

.selector-modal {
  background: var(--bg-primary);
  width: 800px;
  height: 600px;
  max-width: 95vw;
  max-height: 90vh;
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

/* Search Box */
.search-box {
    padding: 12px 24px;
    border-bottom: 1px solid var(--border-color);
    display: flex;
    align-items: center;
    gap: 10px;
    background: var(--bg-secondary);
}

.search-box svg {
    color: var(--text-tertiary);
    flex-shrink: 0;
}

.search-box input {
    flex: 1;
    background: transparent;
    border: none;
    outline: none;
    color: var(--text-primary);
    font-size: 0.95rem;
}

.search-box input::placeholder {
    color: var(--text-tertiary);
}

.modal-body {
  flex: 1;
  display: flex;
  overflow: hidden;
}

.provider-list {
  width: 220px;
  background: var(--bg-secondary);
  overflow-y: auto;
  border-right: 1px solid var(--border-color);
  flex-shrink: 0;
  padding: 10px;
  gap: 4px;
  display: flex;
  flex-direction: column;
}

.provider-item {
  padding: 12px 16px;
  cursor: pointer;
  border-radius: 6px;
  transition: background 0.2s;
  color: var(--text-secondary);
  font-weight: 500;
}

.provider-item:hover {
  background: var(--bg-hover);
  color: var(--text-primary);
}

.provider-item.active {
  background: var(--bg-surface);
  color: var(--text-primary);
}

.model-grid {
  flex: 1;
  padding: 24px;
  overflow-y: auto;
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
  gap: 16px;
  align-content: start;
}

.model-card {
  background: var(--bg-surface);
  padding: 16px;
  border-radius: 8px;
  border: 1px solid var(--border-color);
  cursor: pointer;
  transition: all 0.2s;
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
}

.model-card:hover {
  transform: translateY(-2px);
  border-color: var(--text-tertiary);
  box-shadow: var(--shadow-sm);
}

.model-card.selected {
  border-color: var(--accent-green);
  background: rgba(16, 163, 127, 0.1);
}

.model-info {
    flex: 1;
    overflow: hidden;
}

.model-name {
  font-weight: 600;
  margin-bottom: 4px;
  color: var(--text-primary);
}

.model-id {
  font-size: 0.8rem;
  color: var(--text-secondary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.check-icon {
    color: var(--accent-green);
    margin-left: 10px;
}

.empty-state {
    grid-column: 1 / -1;
    text-align: center;
    color: var(--text-secondary);
    margin-top: 50px;
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 15px;
}

.sync-btn-small {
    background: var(--accent-blue);
    color: white;
    border: none;
    padding: 8px 16px;
    border-radius: 6px;
    cursor: pointer;
    font-weight: 500;
}

.hint-text {
    font-size: 0.8rem;
    color: var(--text-tertiary);
}

/* Transitions */
.fade-enter-active, .fade-leave-active {
  transition: opacity 0.2s;
}
.fade-enter, .fade-leave-to {
  opacity: 0;
}
</style>
