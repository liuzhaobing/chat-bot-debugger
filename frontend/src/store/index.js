import Vue from 'vue'
import Vuex from 'vuex'
import axios from 'axios'

Vue.use(Vuex)

const API_BASE = '/api'

export default new Vuex.Store({
    state: {
        conversations: [],
        currentConversationId: null,
        messages: [],
        providers: [],
        selectedModel: null, // { provider_id, model_name }
        isStreaming: false,
        inputMessage: '',
        theme: localStorage.getItem('theme') || 'dark',
        providerFetchError: null,
        conversationsNextPage: null,
        conversationsLoading: false
    },
    mutations: {
        SET_PROVIDER_ERROR(state, error) {
            state.providerFetchError = error
        },
        SET_THEME(state, theme) {
            state.theme = theme
            localStorage.setItem('theme', theme)
            // Apply to document immediately for responsiveness
            document.documentElement.setAttribute('data-theme', theme)
        },
        SET_CONVERSATIONS(state, conversations) {
            state.conversations = conversations
        },
        SET_CONVERSATIONS_NEXT_PAGE(state, url) {
            state.conversationsNextPage = url
        },
        SET_CONVERSATIONS_LOADING(state, loading) {
            state.conversationsLoading = loading
        },
        APPEND_CONVERSATIONS(state, conversations) {
            // Filter out duplicates to be safe
            const existingIds = new Set(state.conversations.map(c => c.id))
            const newConvs = conversations.filter(c => !existingIds.has(c.id))
            state.conversations = [...state.conversations, ...newConvs]
        },
        SET_CURRENT_CONVERSATION(state, id) {
            state.currentConversationId = id
        },
        SET_MESSAGES(state, messages) {
            state.messages = messages
        },
        SET_INPUT_MESSAGE(state, message) {
            state.inputMessage = message
        },
        SET_PROVIDERS(state, providers) {
            state.providers = providers
        },
        SET_SELECTED_MODEL(state, model) {
            state.selectedModel = model
        },
        ADD_MESSAGE(state, message) {
            state.messages.push(message)
        },
        UPDATE_LAST_MESSAGE(state, content) {
            if (state.messages.length > 0) {
                const index = state.messages.length - 1
                const lastMsg = state.messages[index]
                if (lastMsg.role === 'assistant') {
                    // Create a new object to ensure reactivity
                    const newMsg = { ...lastMsg, content: content }
                    // Use splice to trigger array reactivity in Vue 2
                    state.messages.splice(index, 1, newMsg)
                }
            }
        },
        SET_STREAMING(state, status) {
            state.isStreaming = status
        },
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
        },
        async fetchConversations({ commit, state }, { append = false } = {}) {
            if (state.conversationsLoading) return

            let url = `${API_BASE}/conversations/`
            if (append && state.conversationsNextPage) {
                url = state.conversationsNextPage
            } else if (append && !state.conversationsNextPage) {
                return
            }

            commit('SET_CONVERSATIONS_LOADING', true)
            try {
                const res = await axios.get(url)
                // Handle both paginated and flat response for safety during transition
                const data = res.data.results || res.data
                const next = res.data.next || null

                if (append) {
                    commit('APPEND_CONVERSATIONS', data)
                } else {
                    commit('SET_CONVERSATIONS', data)
                }
                commit('SET_CONVERSATIONS_NEXT_PAGE', next)
            } catch (e) {
                console.error("Failed to fetch conversations", e)
            } finally {
                commit('SET_CONVERSATIONS_LOADING', false)
            }
        },
        async loadConversation({ commit }, id) {
            commit('SET_CURRENT_CONVERSATION', id)
            try {
                const res = await axios.get(`${API_BASE}/conversations/${id}/messages/`)
                commit('SET_MESSAGES', res.data)
            } catch (e) {
                console.error("Failed to fetch messages", e)
            }
        },
        async deleteConversation({ dispatch, state, commit }, id) {
            try {
                await axios.delete(`${API_BASE}/conversations/${id}/`)
                if (state.currentConversationId === id) {
                    commit('SET_CURRENT_CONVERSATION', null)
                    commit('SET_MESSAGES', [])
                }
                dispatch('fetchConversations')
            } catch (e) {
                console.error("Failed to delete conversation", e)
            }
        },
        async createNewChat({ commit }) {
            commit('SET_CURRENT_CONVERSATION', null)
            commit('SET_MESSAGES', [])
        },
        async sendMessage({ commit, state, dispatch }, content) {
            if (!content.trim()) return

            const userMsg = { role: 'user', content, created_at: new Date().toISOString() }
            commit('ADD_MESSAGE', userMsg)
            commit('SET_INPUT_MESSAGE', '')

            const assistantMsg = { role: 'assistant', content: '', created_at: new Date().toISOString() }
            commit('ADD_MESSAGE', assistantMsg)
            commit('SET_STREAMING', true)

            // We need to implement streaming manually with fetch or axios + onDownloadProgress
            // Standard axios doesn't support streaming easily in browser, fetch is better for streams

            try {
                const payload = {
                    content,
                    model: state.selectedModel?.model_name,
                    provider_id: state.selectedModel?.provider_id,
                    conversation_id: state.currentConversationId
                }

                const response = await fetch(`${API_BASE}/chat/completions`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(payload)
                })

                if (!response.ok) {
                    const errorText = await response.text()
                    let invalidJson = false
                    try {
                        const errObj = JSON.parse(errorText)
                        if (errObj.error) throw new Error(errObj.error)
                    } catch (e) {
                        if (e.message !== 'Network response was not ok' && !invalidJson) {
                            // If JSON parse worked but no .error field, or JSON parse failed
                            // We use the raw text
                        }
                    }
                    throw new Error(`Server Error (${response.status}): ${errorText}`)
                }

                const reader = response.body.getReader()
                const decoder = new TextDecoder()
                let assistantContent = ''
                let buffer = ''

                // eslint-disable-next-line no-constant-condition
                while (true) {
                    const { done, value } = await reader.read()
                    if (done) break

                    buffer += decoder.decode(value, { stream: true })

                    // Split by double newline as backend sends \n\n
                    // But standard SSE usually splits by \n. 
                    // Our backend sends `yield line_text + "\n\n"`. 
                    // So we can split by \n\n safely, OR just split by \n and ignore empty lines.
                    // Let's rely on the \n\n delimiter or just \n.
                    // Safer: split by \n, process lines starting with data:

                    const lines = buffer.split('\n')
                    // Keep the last part in buffer as it might be incomplete
                    buffer = lines.pop()

                    for (const line of lines) {
                        const trimmed = line.trim()
                        if (trimmed.startsWith('data: ')) {
                            const jsonStr = trimmed.slice(6)
                            if (jsonStr === '[DONE]') continue
                            try {
                                const data = JSON.parse(jsonStr)
                                if (data.choices && data.choices[0].delta.content) {
                                    assistantContent += data.choices[0].delta.content
                                    commit('UPDATE_LAST_MESSAGE', assistantContent)
                                }
                            } catch (e) {
                                // console.warn('JSON Parse Error', e)
                            }
                        }
                    }
                }

                // Refresh conversations list to show new chat if it was created
                if (!state.currentConversationId) {
                    await dispatch('fetchConversations')
                    if (state.conversations.length > 0) {
                        commit('SET_CURRENT_CONVERSATION', state.conversations[0].id)
                    }
                }

            } catch (e) {
                console.error("Streaming error", e)
                commit('UPDATE_LAST_MESSAGE', `Error: ${e.message}`)
            } finally {
                commit('SET_STREAMING', false)
            }
        }
    }
})
