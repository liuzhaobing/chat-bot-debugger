<template>
  <div v-if="visible" class="modal-overlay" @click="$emit('close')">
    <div class="modal-content hire-modal" @click.stop>
      <div class="modal-header">
        <h3>{{ modalTitle }}</h3>
        <div v-if="mode === 'hire'" class="step-indicator">
          <span class="step" :class="{ active: currentStep >= 1 }">1</span>
          <span class="step-line" :class="{ active: currentStep >= 2 }"></span>
          <span class="step" :class="{ active: currentStep >= 2 }">2</span>
        </div>
        <button class="close-btn" @click="$emit('close')">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <line x1="18" y1="6" x2="6" y2="18"></line>
            <line x1="6" y1="6" x2="18" y2="18"></line>
          </svg>
        </button>
      </div>

      <!-- Hire Mode: Step 1 - 选择数字员工配置 -->
      <div v-if="mode === 'hire' && currentStep === 1" class="modal-body step-1-body">
        <p class="step-hint">配置您的数字员工：选择TTS音色和3D形象</p>

        <!-- 员工名称 -->
        <div class="form-group">
          <label>员工名称 <span class="required">*</span></label>
          <input
            v-model="employeeForm.name"
            type="text"
            placeholder="给数字员工起个名字..."
            maxlength="50"
          />
        </div>

        <!-- TTS音色选择 -->
        <div class="form-section">
          <label>TTS音色 <span class="required">*</span></label>
          <div class="voice-list">
            <div
              v-for="voice in ttsVoices"
              :key="voice.speaker"
              class="voice-item"
              :class="{ selected: selectedVoice?.speaker === voice.speaker }"
              @click="selectVoice(voice)"
            >
              <div class="voice-info">
                <span class="voice-name">{{ voice.name || voice.speaker }}</span>
                <span class="voice-id">{{ voice.speaker }}</span>
              </div>
              <button
                class="voice-play-btn"
                @click.stop="previewVoice(voice)"
                :disabled="previewingVoiceId === voice.speaker"
                title="试听音色"
              >
                <svg v-if="previewingVoiceId === voice.speaker" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="spin">
                  <path d="M21 12a9 9 0 11-6.219-8.56"/>
                </svg>
                <svg v-else width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <polygon points="5 3 19 12 5 21 5 3"></polygon>
                </svg>
              </button>
            </div>
          </div>
        </div>

        <!-- 3D形象选择 -->
        <div class="form-section">
          <label>3D形象</label>
          <div class="avatar-selector">
            <div
              v-for="(avatar, index) in avatarOptions"
              :key="index"
              class="avatar-option"
              :class="{ selected: employeeForm.avatar_index === index }"
              @click="employeeForm.avatar_index = index"
            >
              <Avatar3D animation-state="idle" size="small" :character-index="index" />
            </div>
          </div>
        </div>

        <div v-if="ttsVoices.length === 0 && !isLoadingVoices" class="empty-voices">
          <p>暂无可用的TTS音色</p>
        </div>

        <div v-if="isLoadingVoices" class="loading-voices">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="spin">
            <path d="M21 12a9 9 0 11-6.219-8.56"/>
          </svg>
          <p>加载音色列表...</p>
        </div>
      </div>

      <!-- Hire Mode: Step 2 - 创建成功 -->
      <div v-if="mode === 'hire' && currentStep === 2" class="modal-body step-2-body">
        <div class="success-state">
          <div class="success-avatar">
            <Avatar3D
              animation-state="idle"
              size="hero"
              :character-index="createdEmployee?.avatar_index || 0"
            />
          </div>
          <h4>数字员工创建成功！</h4>
          <p class="employee-name">{{ createdEmployee?.name }}</p>
          <p class="hint">是否立即为TA派发任务？</p>
        </div>

        <div class="task-form">
          <div class="form-group">
            <label>任务名称</label>
            <input
              v-model="taskForm.name"
              type="text"
              placeholder="输入任务名称（可选）..."
              maxlength="100"
            />
          </div>

          <div class="form-group">
            <label>PRD/需求描述</label>
            <textarea
              v-model="taskForm.prd_content"
              rows="3"
              placeholder="输入产品PRD文档内容或一句话需求描述..."
              maxlength="2000"
            ></textarea>
          </div>

          <div class="form-group">
            <label>IOT设备协议</label>
            <select v-model="taskForm.iot_protocol_id">
              <option value="">请选择设备协议（可选）</option>
              <option v-for="protocol in deviceProtocols" :key="protocol.id" :value="protocol.id">
                {{ protocol.category }} - {{ protocol.id }}
              </option>
            </select>
          </div>
        </div>
      </div>

      <!-- Dispatch Mode - 派发任务 -->
      <div v-if="mode === 'dispatch'" class="modal-body dispatch-body">
        <div class="dispatch-layout">
          <!-- 左侧：数字员工形象 -->
          <div class="dispatch-avatar">
            <Avatar3D
              animation-state="idle"
              size="normal"
              :character-index="employee?.avatar_index || 0"
            />
            <div class="dispatch-employee-info">
              <span class="name">{{ employee?.name }}</span>
              <span class="voice">{{ employee?.tts_voice?.name || '未配置音色' }}</span>
            </div>
          </div>

          <!-- 右侧：表单 -->
          <div class="dispatch-form">
            <div class="form-group">
              <label>任务名称 <span class="required">*</span></label>
              <input
                v-model="taskForm.name"
                type="text"
                placeholder="请输入任务名称..."
                maxlength="100"
              />
            </div>

            <div class="form-group">
              <label>PRD/需求描述</label>
              <textarea
                v-model="taskForm.prd_content"
                rows="4"
                placeholder="请输入产品PRD文档内容或一句话需求描述..."
                maxlength="2000"
              ></textarea>
              <span class="char-count">{{ taskForm.prd_content.length }}/2000</span>
            </div>

            <div class="form-group">
              <label>IOT设备协议</label>
              <select v-model="taskForm.iot_protocol_id">
                <option value="">请选择设备协议（可选）</option>
                <option v-for="protocol in deviceProtocols" :key="protocol.id" :value="protocol.id">
                  {{ protocol.category }} - {{ protocol.id }}
                </option>
              </select>
            </div>
          </div>
        </div>
      </div>

      <div class="modal-footer">
        <!-- Hire Mode Footer -->
        <template v-if="mode === 'hire'">
          <button v-if="currentStep === 1" class="btn btn-secondary" @click="$emit('close')">
            取消
          </button>
          <button v-if="currentStep === 2" class="btn btn-secondary" @click="skipTask">
            稍后再说
          </button>

          <button
            v-if="currentStep === 1"
            class="btn btn-primary"
            :disabled="!canCreateEmployee || isCreating"
            @click="createEmployee"
          >
            <svg v-if="isCreating" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="spin">
              <path d="M21 12a9 9 0 11-6.219-8.56"/>
            </svg>
            {{ isCreating ? '创建中...' : '创建员工' }}
          </button>

          <button
            v-if="currentStep === 2"
            class="btn btn-primary"
            :disabled="!taskForm.name.trim() || isCreatingTask"
            @click="createTask"
          >
            <svg v-if="isCreatingTask" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="spin">
              <path d="M21 12a9 9 0 11-6.219-8.56"/>
            </svg>
            {{ isCreatingTask ? '派发中...' : '派发任务' }}
          </button>
        </template>

        <!-- Dispatch Mode Footer -->
        <template v-if="mode === 'dispatch'">
          <button class="btn btn-secondary" @click="$emit('close')">
            取消
          </button>
          <button
            class="btn btn-primary"
            :disabled="!canCreateTask || isCreatingTask"
            @click="createTask"
          >
            <svg v-if="isCreatingTask" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="spin">
              <path d="M21 12a9 9 0 11-6.219-8.56"/>
            </svg>
            {{ isCreatingTask ? '派发中...' : '派发任务' }}
          </button>
        </template>
      </div>
    </div>
  </div>
</template>

<script>
import Avatar3D from './Avatar3D.vue'
import sceneTestService from '@/services/sceneTestService'

export default {
  name: 'HireEmployeeModal',
  components: {
    Avatar3D
  },
  props: {
    visible: {
      type: Boolean,
      default: false
    },
    mode: {
      type: String,
      default: 'hire', // 'hire' 或 'dispatch'
      validator: (val) => ['hire', 'dispatch'].includes(val)
    },
    employee: {
      type: Object,
      default: null
    }
  },
  data() {
    return {
      currentStep: 1,
      selectedVoice: null,
      ttsVoices: [],
      deviceProtocols: [],
      isLoadingVoices: false,
      previewingVoiceId: null,
      isCreating: false,
      isCreatingTask: false,
      createdEmployee: null,
      employeeForm: {
        name: '',
        avatar_index: 0,
        tts_voice_id: null
      },
      taskForm: {
        name: '',
        prd_content: '',
        iot_protocol_id: ''
      },
      avatarOptions: ['橙色半圆', '紫色方块', '黑色方块', '黄色圆角']
    }
  },
  computed: {
    modalTitle() {
      if (this.mode === 'dispatch') return '派发任务'
      return this.currentStep === 1 ? '雇佣数字员工' : '派发任务'
    },
    canCreateEmployee() {
      return this.employeeForm.name.trim().length > 0 && this.selectedVoice
    },
    canCreateTask() {
      return this.taskForm.name.trim().length > 0
    }
  },
  watch: {
    visible(val) {
      if (val) {
        this.loadTTSVoices()
        this.loadDeviceProtocols()
      } else {
        this.resetForm()
      }
    }
  },
  methods: {
    generateUUID() {
      return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, c => {
        const r = Math.random() * 16 | 0
        return (c === 'x' ? r : (r & 0x3 | 0x8)).toString(16)
      })
    },
    async loadTTSVoices() {
      this.isLoadingVoices = true
      try {
        this.ttsVoices = await sceneTestService.getTTSVoices()
      } catch (error) {
        console.error('加载TTS音色失败:', error)
        window.$message?.error('加载TTS音色失败')
      } finally {
        this.isLoadingVoices = false
      }
    },
    async loadDeviceProtocols() {
      try {
        this.deviceProtocols = await sceneTestService.getDeviceProtocols()
      } catch (error) {
        console.error('加载设备协议失败:', error)
      }
    },
    selectVoice(voice) {
      this.selectedVoice = voice
      this.employeeForm.tts_voice_id = voice.speaker
    },
    async previewVoice(voice) {
      if (this.previewingVoiceId === voice.speaker) return

      this.previewingVoiceId = voice.speaker
      try {
        const audioBase64 = await sceneTestService.previewTTS(
          voice.speaker,
          '你好，我是你的AI烹饪伙伴食神'
        )
        const audioBytes = atob(audioBase64)
        const audioArray = new Uint8Array(audioBytes.length)
        for (let i = 0; i < audioBytes.length; i++) {
          audioArray[i] = audioBytes.charCodeAt(i)
        }
        const audioBlob = new Blob([audioArray], { type: 'audio/wav' })
        const audioUrl = URL.createObjectURL(audioBlob)

        const audio = new Audio(audioUrl)
        audio.onended = () => {
          URL.revokeObjectURL(audioUrl)
          this.previewingVoiceId = null
        }
        audio.onerror = () => {
          URL.revokeObjectURL(audioUrl)
          this.previewingVoiceId = null
        }
        await audio.play()
      } catch (error) {
        console.error('TTS试听失败:', error)
        window.$message?.error('TTS试听失败')
        this.previewingVoiceId = null
      }
    },
    async createEmployee() {
      if (!this.canCreateEmployee || this.isCreating) return

      this.isCreating = true
      try {
        const employee = await sceneTestService.createDigitalEmployee({
          name: this.employeeForm.name,
          tts_voice_id: this.selectedVoice.speaker,
          avatar_index: this.employeeForm.avatar_index
        })
        this.createdEmployee = employee
        this.currentStep = 2
        this.$emit('created', employee)
      } catch (error) {
        console.error('创建数字员工失败:', error)
        window.$message?.error('创建数字员工失败')
      } finally {
        this.isCreating = false
      }
    },
    async createTask() {
      if (!this.canCreateTask || this.isCreatingTask) return

      const employeeId = this.mode === 'dispatch' ? this.employee?.id : this.createdEmployee?.id
      if (!employeeId) return

      this.isCreatingTask = true
      try {
        // 生成 job_instance_id（关键：前端生成并传递）
        const jobInstanceId = this.generateUUID()

        const task = await sceneTestService.createTestTask({
          name: this.taskForm.name,
          prd_content: this.taskForm.prd_content,
          employee_id: employeeId,
          iot_protocol_id: this.taskForm.iot_protocol_id || null,
          job_instance_id: jobInstanceId  // 传递 job_instance_id
        })

        // 通过事件通知父组件启动 WebSocket 并执行任务
        // 确保 task 包含 job_instance_id（如果后端返回的不包含，使用前端生成的）
        this.$emit('task-created-and-start', {
          task: { ...task, job_instance_id: task.job_instance_id || jobInstanceId },
          employee: this.mode === 'dispatch' ? this.employee : this.createdEmployee
        })
        this.resetForm()
      } catch (error) {
        console.error('创建任务失败:', error)
        window.$message?.error('创建任务失败')
      } finally {
        this.isCreatingTask = false
      }
    },
    skipTask() {
      this.$emit('close')
    },
    resetForm() {
      this.currentStep = 1
      this.selectedVoice = null
      this.createdEmployee = null
      this.employeeForm = {
        name: '',
        avatar_index: 0,
        tts_voice_id: null
      }
      this.taskForm = {
        name: '',
        prd_content: '',
        iot_protocol_id: ''
      }
      this.previewingVoiceId = null
    }
  }
}
</script>

<style scoped>
/* 弹窗样式 */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.6);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: 20px;
}

.modal-content {
  background: var(--bg-surface, #161b22);
  border: 1px solid var(--border-color, #30363d);
  border-radius: 12px;
  width: 100%;
  max-width: 720px;
  max-height: 85vh;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  box-shadow: 0 16px 48px rgba(0, 0, 0, 0.4);
}

.modal-header {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px 20px;
  border-bottom: 1px solid var(--border-color, #30363d);
}

.modal-header h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary, #f0f6fc);
  flex: 1;
}

.step-indicator {
  display: flex;
  align-items: center;
  gap: 6px;
}

.step {
  width: 20px;
  height: 20px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 11px;
  font-weight: 600;
  background: var(--bg-secondary, #21262d);
  color: var(--text-tertiary, #6e7681);
  border: 1px solid var(--border-color, #30363d);
  transition: all 0.2s ease;
}

.step.active {
  background: #3b82f6;
  border-color: #3b82f6;
  color: white;
}

.step-line {
  width: 20px;
  height: 2px;
  background: var(--border-color, #30363d);
  transition: background 0.2s ease;
}

.step-line.active {
  background: #3b82f6;
}

.close-btn {
  width: 28px;
  height: 28px;
  border: none;
  background: transparent;
  border-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  color: var(--text-secondary, #8b949e);
  transition: all 0.15s ease;
}

.close-btn:hover {
  background: var(--bg-hover, #30363d);
  color: var(--text-primary, #f0f6fc);
}

.modal-body {
  padding: 16px 20px;
  overflow-y: auto;
  flex: 1;
}

.step-1-body {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.step-hint {
  margin: 0;
  font-size: 13px;
  color: var(--text-secondary, #8b949e);
  text-align: center;
}

/* 表单样式 */
.form-group {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.form-group label,
.form-section label {
  font-size: 13px;
  font-weight: 500;
  color: var(--text-primary, #f0f6fc);
}

.form-group label .required {
  color: #ef4444;
}

.form-group input,
.form-group textarea,
.form-group select {
  padding: 8px 10px;
  border: 1px solid var(--border-color, #30363d);
  border-radius: 6px;
  font-size: 13px;
  background: var(--bg-primary, #0d1117);
  color: var(--text-primary, #f0f6fc);
  transition: border-color 0.15s ease;
}

.form-group input:focus,
.form-group textarea:focus,
.form-group select:focus {
  outline: none;
  border-color: #3b82f6;
}

.form-group input::placeholder,
.form-group textarea::placeholder {
  color: var(--text-tertiary, #6e7681);
}

.form-group textarea {
  resize: vertical;
  min-height: 70px;
}

.char-count {
  font-size: 10px;
  color: var(--text-tertiary, #6e7681);
  text-align: right;
}

.form-section {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

/* TTS音色列表 */
.voice-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
  max-height: 200px;
  overflow-y: auto;
  padding: 4px;
}

.voice-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 12px;
  background: var(--bg-primary, #0d1117);
  border: 1px solid var(--border-color, #30363d);
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.voice-item:hover {
  border-color: #3b82f6;
  background: rgba(59, 130, 246, 0.05);
}

.voice-item.selected {
  border-color: #3b82f6;
  background: rgba(59, 130, 246, 0.1);
}

.voice-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.voice-name {
  font-size: 13px;
  font-weight: 500;
  color: var(--text-primary, #f0f6fc);
}

.voice-id {
  font-size: 11px;
  color: var(--text-tertiary, #6e7681);
}

.voice-play-btn {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  border: 1px solid var(--border-color, #30363d);
  background: var(--bg-secondary, #21262d);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.15s ease;
  color: var(--text-secondary, #8b949e);
}

.voice-play-btn:hover:not(:disabled) {
  background: #3b82f6;
  border-color: #3b82f6;
  color: white;
}

.voice-play-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* 3D形象选择 */
.avatar-selector {
  display: flex;
  gap: 8px;
  justify-content: center;
  padding: 12px;
  background: var(--bg-primary, #0d1117);
  border-radius: 8px;
}

.avatar-option {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: flex-end;
  padding: 8px 4px;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.avatar-option:hover {
  background: rgba(59, 130, 246, 0.08);
}

.avatar-option.selected {
  background: rgba(59, 130, 246, 0.12);
}

/* Step 2 样式 */
.step-2-body {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.success-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  padding: 20px;
  background: rgba(16, 185, 129, 0.05);
  border-radius: 10px;
  border: 1px solid rgba(16, 185, 129, 0.2);
}

.success-avatar {
  width: 120px;
  height: 120px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.success-state h4 {
  margin: 0;
  font-size: 16px;
  color: #10b981;
}

.success-state .employee-name {
  font-size: 14px;
  font-weight: 500;
  color: var(--text-primary, #f0f6fc);
}

.success-state .hint {
  margin: 0;
  font-size: 12px;
  color: var(--text-tertiary, #6e7681);
}

/* Dispatch Mode 样式 */
.dispatch-body {
  padding: 0;
}

.dispatch-layout {
  display: flex;
  min-height: 400px;
}

/* 左侧：数字员工形象 */
.dispatch-avatar {
  width: 200px;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 20px;
  background: var(--bg-primary, #0d1117);
  border-right: 1px solid var(--border-color, #30363d);
}

.dispatch-employee-info {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  margin-top: 16px;
}

.dispatch-employee-info .name {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary, #f0f6fc);
}

.dispatch-employee-info .voice {
  font-size: 11px;
  color: var(--text-tertiary, #6e7681);
}

/* 右侧：表单 */
.dispatch-form {
  flex: 1;
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

/* 底部按钮 */
.modal-footer {
  display: flex;
  gap: 8px;
  padding: 12px 20px;
  border-top: 1px solid var(--border-color, #30363d);
  justify-content: flex-end;
}

.btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 8px 14px;
  border-radius: 6px;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.15s ease;
}

.btn-primary {
  background: #238636;
  border: 1px solid #238636;
  color: #fff;
}

.btn-primary:hover:not(:disabled) {
  background: #2ea043;
}

.btn-secondary {
  background: var(--bg-secondary, #21262d);
  border: 1px solid var(--border-color, #30363d);
  color: var(--text-secondary, #8b949e);
}

.btn-secondary:hover:not(:disabled) {
  background: var(--bg-hover, #30363d);
  color: var(--text-primary, #f0f6fc);
}

.btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* 加载和空状态 */
.loading-voices,
.empty-voices {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 24px;
  color: var(--text-tertiary, #6e7681);
  gap: 8px;
  font-size: 13px;
}

/* 动画 */
.spin {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

/* 响应式 */
@media (max-width: 600px) {
  .avatar-selector {
    flex-wrap: wrap;
    gap: 4px;
  }

  .avatar-option {
    padding: 6px 2px;
  }

  .dispatch-layout {
    flex-direction: column;
  }

  .dispatch-avatar {
    width: 100%;
    border-right: none;
    border-bottom: 1px solid var(--border-color, #30363d);
    padding: 16px;
  }
}
</style>