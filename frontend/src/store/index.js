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
        theme: localStorage.getItem('theme') || 'light',
        providerFetchError: null,
        conversationsNextPage: null,
        conversationsLoading: false,
        systemPrompt: 'You are a helpful assistant.',
        temperature: 0.7,
        maxTokens: 1024,
        isSidebarCollapsed: false,
        isRightSidebarOpen: false
    },
    mutations: {
        SET_SYSTEM_PROMPT(state, prompt) {
            state.systemPrompt = prompt
        },
        SET_TEMPERATURE(state, temp) {
            state.temperature = temp
        },
        SET_MAX_TOKENS(state, val) {
            state.maxTokens = val
        },
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
            // 保证多模态消息为响应式对象，避免直接引用导致视图不更新
            let msg = message
            if (Array.isArray(message.content)) {
                msg = { ...message, content: JSON.parse(JSON.stringify(message.content)) }
            }
            state.messages.push(msg)
        },
        UPDATE_LAST_MESSAGE(state, { content, reasoning_content, usage }) {
            if (state.messages.length > 0) {
                const index = state.messages.length - 1
                const lastMsg = state.messages[index]
                if (lastMsg.role === 'assistant') {
                    // Create a new object to ensure reactivity
                    const newMsg = { 
                        ...lastMsg, 
                        content: content, 
                        reasoning_content: reasoning_content,
                        usage: usage || lastMsg.usage
                    }
                    // Use splice to trigger array reactivity in Vue 2
                    state.messages.splice(index, 1, newMsg)
                }
            }
        },
        SET_STREAMING(state, status) {
            state.isStreaming = status
        },
        SET_SIDEBAR_COLLAPSED(state, collapsed) {
            state.isSidebarCollapsed = collapsed
        },
        SET_RIGHT_SIDEBAR_OPEN(state, open) {
            state.isRightSidebarOpen = open
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
        async sendMessage({ commit, state, dispatch }, messages) {
            // 支持messages为字符串或数组
            let msgArr = []
            if (Array.isArray(messages)) {
                msgArr = messages
            } else if (typeof messages === 'string' && messages.trim()) {
                msgArr = [{ role: 'user', content: messages.trim() }]
            } else {
                return
            }

            // 展示用户消息（最后一条）
            const lastUserMsg = msgArr[msgArr.length - 1]
            if (lastUserMsg.role === 'user') {
                commit('ADD_MESSAGE', { ...lastUserMsg, created_at: new Date().toISOString() })
            }
            commit('SET_INPUT_MESSAGE', '')

            // 预置assistant消息用于流式更新
            const assistantMsg = { role: 'assistant', content: '', reasoning_content: '', usage: null, created_at: new Date().toISOString() }
            commit('ADD_MESSAGE', assistantMsg)
            commit('SET_STREAMING', true)

            try {
                const payload = {
                    messages: msgArr,
                    model: state.selectedModel?.model_name,
                    provider_id: state.selectedModel?.provider_id,
                    conversation_id: state.currentConversationId,
                    system_prompt: state.systemPrompt,
                    temperature: state.temperature,
                    max_tokens: state.maxTokens
                }
                // 兼容localStorage system_prompt
                if (!payload.system_prompt && window && window.localStorage) {
                    payload.system_prompt = window.localStorage.getItem('systemPrompt') || ''
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
                    throw new Error(`Server Error (${response.status}): ${errorText}`)
                }

                const reader = response.body.getReader()
                const decoder = new TextDecoder()
                let assistantContent = ''
                let assistantReasoningContent = ''
                let assistantUsage = null
                let buffer = ''
                for (; ;) {
                    const { done, value } = await reader.read()
                    if (done) break
                    buffer += decoder.decode(value, { stream: true })
                    const lines = buffer.split('\n')
                    buffer = lines.pop()
                    for (const line of lines) {
                        const trimmed = line.trim()
                        if (trimmed.startsWith('data: ')) {
                            const jsonStr = trimmed.slice(6)
                            if (jsonStr === '[DONE]') continue
                            try {
                                const data = JSON.parse(jsonStr)
                                if (data.choices && data.choices[0].delta.reasoning_content) {
                                    assistantReasoningContent += data.choices[0].delta.reasoning_content
                                    commit('UPDATE_LAST_MESSAGE', { 
                                        content: assistantContent, 
                                        reasoning_content: assistantReasoningContent,
                                        usage: assistantUsage
                                    })
                                }
                                if (data.choices && data.choices[0].delta.content) {
                                    assistantContent += data.choices[0].delta.content
                                    commit('UPDATE_LAST_MESSAGE', { 
                                        content: assistantContent, 
                                        reasoning_content: assistantReasoningContent,
                                        usage: assistantUsage
                                    })
                                }
                                // 收集 usage 信息（通常在最后一个 chunk）
                                if (data.usage) {
                                    assistantUsage = data.usage
                                    commit('UPDATE_LAST_MESSAGE', { 
                                        content: assistantContent, 
                                        reasoning_content: assistantReasoningContent,
                                        usage: assistantUsage
                                    })
                                }
                            } catch (e) {
                                // 忽略流式解析错误
                            }
                        }
                    }
                }
                if (!state.currentConversationId) {
                    await dispatch('fetchConversations')
                    if (state.conversations.length > 0) {
                        commit('SET_CURRENT_CONVERSATION', state.conversations[0].id)
                    }
                }
            } catch (e) {
                console.error("Streaming error", e)
                commit('UPDATE_LAST_MESSAGE', { content: `Error: ${e.message}`, reasoning_content: '', usage: null })
            } finally {
                commit('SET_STREAMING', false)
            }
        }
    }
})
