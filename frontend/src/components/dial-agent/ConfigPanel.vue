<template>
  <div class="config-panel">
    <div class="panel-header">
      <h3>会话配置</h3>
    </div>

    <div class="panel-content">
      <!-- 服务器配置 -->
      <div class="config-section">
        <h4>服务器配置</h4>
        <div class="form-group">
          <label>服务器地址</label>
          <input 
            v-model="localConfig.serverUrl" 
            type="text" 
            placeholder="ws://118.31.127.156:8000/ws/sessions/start"
            @change="handleChange"
          />
        </div>
      </div>

      <!-- 用户信息 -->
      <div class="config-section">
        <h4>用户信息</h4>
        <div class="form-group">
          <label>用户ID</label>
          <input 
            v-model="localConfig.userId" 
            type="text" 
            placeholder="17744270115"
            @change="handleChange"
          />
        </div>
      </div>

      <!-- Agent配置 -->
      <div class="config-section">
        <h4>Agent配置</h4>
        <div class="form-group">
          <label>Agent类型</label>
          <select v-model="localConfig.agentType" @change="handleChange">
            <option value="robam_workflow">robam_workflow</option>
          </select>
        </div>
        <div class="form-group">
          <label>配置模板</label>
          <select v-model="localConfig.configTemplate" @change="handleChange">
            <option value="ai_telephone">ai_telephone</option>
          </select>
        </div>
      </div>

      <!-- 音频配置 -->
      <div class="config-section">
        <h4>音频配置</h4>
        <div class="form-row">
          <div class="form-group">
            <label>输入采样率</label>
            <input 
              v-model.number="localConfig.inputSampleRate" 
              type="number" 
              placeholder="16000"
              @change="handleChange"
            />
          </div>
          <div class="form-group">
            <label>输入声道数</label>
            <input 
              v-model.number="localConfig.inputChannels" 
              type="number" 
              placeholder="1"
              @change="handleChange"
            />
          </div>
        </div>
        <div class="form-row">
          <div class="form-group">
            <label>输出采样率</label>
            <input 
              v-model.number="localConfig.outputSampleRate" 
              type="number" 
              placeholder="24000"
              @change="handleChange"
            />
          </div>
          <div class="form-group">
            <label>输出声道数</label>
            <input 
              v-model.number="localConfig.outputChannels" 
              type="number" 
              placeholder="1"
              @change="handleChange"
            />
          </div>
        </div>
      </div>

      <!-- 对话设置 -->
      <div class="config-section">
        <h4>对话设置</h4>
        <div class="form-group">
          <label>欢迎消息</label>
          <textarea 
            v-model="localConfig.welcomeMessage" 
            rows="2"
            placeholder="你好，欢迎致电名气，有什么可以帮您？"
            @change="handleChange"
          ></textarea>
        </div>
        <div class="form-group checkbox-group">
          <label>
            <input 
              type="checkbox" 
              v-model="localConfig.allowInterruptions"
              @change="handleChange"
            />
            <span>允许打断</span>
          </label>
        </div>
      </div>

      <!-- 背景音乐配置 -->
      <div class="config-section">
        <h4>背景音乐</h4>
        <div class="form-group checkbox-group">
          <label>
            <input 
              type="checkbox" 
              v-model="localConfig.backgroundMusic.enabled"
              @change="handleChange"
            />
            <span>启用背景音乐</span>
          </label>
        </div>
        <div v-if="localConfig.backgroundMusic.enabled">
          <div class="form-group">
            <label>音乐URL（每行一个）</label>
            <textarea 
              v-model="backgroundMusicUrls" 
              rows="2"
              placeholder="https://example.com/music.wav"
              @change="handleBackgroundMusicUrlsChange"
            ></textarea>
          </div>
          <div class="form-row">
            <div class="form-group">
              <label>音量 (0-1)</label>
              <input 
                v-model.number="localConfig.backgroundMusic.volume" 
                type="number" 
                step="0.01"
                min="0"
                max="1"
                placeholder="0.05"
                @change="handleChange"
              />
            </div>
            <div class="form-group checkbox-group">
              <label>
                <input 
                  type="checkbox" 
                  v-model="localConfig.backgroundMusic.loop"
                  @change="handleChange"
                />
                <span>循环播放</span>
              </label>
            </div>
          </div>
          <div class="form-group checkbox-group">
            <label>
              <input 
                type="checkbox" 
                v-model="localConfig.backgroundMusic.random"
                @change="handleChange"
              />
              <span>随机播放</span>
            </label>
          </div>
        </div>
      </div>

      <!-- 静默提醒配置 -->
      <div class="config-section">
        <h4>静默提醒</h4>
        <div class="form-group checkbox-group">
          <label>
            <input 
              type="checkbox" 
              v-model="localConfig.idleReminderConfig.enabled"
              @change="handleChange"
            />
            <span>启用静默提醒</span>
          </label>
        </div>
        <div v-if="localConfig.idleReminderConfig.enabled">
          <div class="form-group">
            <label>提醒内容类型</label>
            <select v-model="localConfig.idleReminderConfig.reminderContentType" @change="handleChange">
              <option value="llm">llm</option>
            </select>
          </div>
          <div class="form-group">
            <label>提醒消息</label>
            <input 
              v-model="localConfig.idleReminderConfig.message" 
              type="text" 
              placeholder="请问您还在吗？"
              @change="handleChange"
            />
          </div>
          <div class="form-row">
            <div class="form-group">
              <label>间隔时间（秒）</label>
              <input 
                v-model.number="localConfig.idleReminderConfig.intervalSeconds" 
                type="number" 
                placeholder="20"
                @change="handleChange"
              />
            </div>
            <div class="form-group">
              <label>最大提醒次数</label>
              <input 
                v-model.number="localConfig.idleReminderConfig.maxRemindCount" 
                type="number" 
                placeholder="2"
                @change="handleChange"
              />
            </div>
          </div>
        </div>
      </div>

      <!-- VAD插件配置 -->
      <div class="config-section">
        <h4>VAD插件配置</h4>
        <div class="form-row">
          <div class="form-group">
            <label>最小语音时长（秒）</label>
            <input 
              v-model.number="localConfig.pluginConfigs.sileroVad.minSpeechDuration" 
              type="number" 
              step="0.01"
              placeholder="0.05"
              @change="handleChange"
            />
          </div>
          <div class="form-group">
            <label>最小静默时长（秒）</label>
            <input 
              v-model.number="localConfig.pluginConfigs.sileroVad.minSilenceDuration" 
              type="number" 
              step="0.01"
              placeholder="0.2"
              @change="handleChange"
            />
          </div>
        </div>
        <div class="form-row">
          <div class="form-group">
            <label>前缀填充时长（秒）</label>
            <input 
              v-model.number="localConfig.pluginConfigs.sileroVad.prefixPaddingDuration" 
              type="number" 
              step="0.1"
              placeholder="0.5"
              @change="handleChange"
            />
          </div>
          <div class="form-group">
            <label>激活阈值 (0-1)</label>
            <input 
              v-model.number="localConfig.pluginConfigs.sileroVad.activationThreshold" 
              type="number" 
              step="0.01"
              min="0"
              max="1"
              placeholder="0.4"
              @change="handleChange"
            />
          </div>
        </div>
        <div class="form-row">
          <div class="form-group">
            <label>最大缓冲语音（秒）</label>
            <input 
              v-model.number="localConfig.pluginConfigs.sileroVad.maxBufferedSpeech" 
              type="number" 
              placeholder="60.0"
              @change="handleChange"
            />
          </div>
          <div class="form-group">
            <label>中间结果间隔</label>
            <input 
              v-model.number="localConfig.pluginConfigs.sileroVad.intermediateResultInterval" 
              type="number" 
              placeholder="320"
              @change="handleChange"
            />
          </div>
        </div>
      </div>
    </div>

    <div class="panel-footer">
      <button class="btn btn-secondary" @click="reset">重置</button>
      <button class="btn btn-primary" @click="save">保存配置</button>
    </div>
  </div>
</template>

<script>
export default {
  name: 'ConfigPanel',
  props: {
    config: {
      type: Object,
      required: true
    }
  },
  data() {
    return {
      localConfig: null,
      backgroundMusicUrls: ''
    }
  },
  created() {
    this.initLocalConfig()
  },
  watch: {
    config: {
      handler() {
        this.initLocalConfig()
      },
      deep: true
    }
  },
  methods: {
    initLocalConfig() {
      this.localConfig = JSON.parse(JSON.stringify(this.config))
      // 初始化背景音乐URL文本
      if (this.localConfig.backgroundMusic && this.localConfig.backgroundMusic.urls) {
        this.backgroundMusicUrls = this.localConfig.backgroundMusic.urls.join('\n')
      }
    },
    handleChange() {
      // 实时更新配置
      this.$emit('update', this.localConfig)
    },
    handleBackgroundMusicUrlsChange() {
      // 将文本转换为数组
      this.localConfig.backgroundMusic.urls = this.backgroundMusicUrls
        .split('\n')
        .map(url => url.trim())
        .filter(url => url.length > 0)
      this.handleChange()
    },
    save() {
      this.$emit('save', this.localConfig)
    },
    reset() {
      this.localConfig = {
        serverUrl: 'ws://118.31.127.156:8000/ws/sessions/start',
        userId: '17744270115',
        agentType: 'robam_workflow',
        configTemplate: 'ai_telephone',
        welcomeMessage: '你好，欢迎致电名气，有什么可以帮您？',
        allowInterruptions: true,
        inputSampleRate: 16000,
        inputChannels: 1,
        outputSampleRate: 24000,
        outputChannels: 1,
        backgroundMusic: {
          enabled: true,
          urls: ['https://roki-ai-ckb-prod.oss-accelerate.aliyuncs.com/static/test/office_background.wav'],
          volume: 0.05,
          loop: true,
          random: false
        },
        idleReminderConfig: {
          enabled: true,
          reminderContentType: 'llm',
          message: '请问您还在吗？',
          intervalSeconds: 20,
          maxRemindCount: 2
        },
        pluginConfigs: {
          sileroVad: {
            minSpeechDuration: 0.05,
            minSilenceDuration: 0.2,
            prefixPaddingDuration: 0.5,
            maxBufferedSpeech: 60.0,
            activationThreshold: 0.4,
            sampleRate: 16000,
            intermediateResultInterval: 320
          }
        }
      }
      this.backgroundMusicUrls = this.localConfig.backgroundMusic.urls.join('\n')
      this.$emit('save', this.localConfig)
    }
  }
}
</script>

<style scoped>
.config-panel {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: var(--bg-primary);
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.panel-header {
  padding: 20px 24px;
  border-bottom: 1px solid var(--border-color);
  background: var(--bg-primary);
}

.panel-header h3 {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  color: var(--text-primary);
}

.panel-content {
  flex: 1;
  overflow-y: auto;
  padding: 24px;
  background: var(--bg-secondary);
}

.config-section {
  margin-bottom: 32px;
}

.config-section:last-child {
  margin-bottom: 0;
}

.config-section h4 {
  margin: 0 0 16px 0;
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
}

.form-group {
  margin-bottom: 16px;
}

.form-group:last-child {
  margin-bottom: 0;
}

.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
  margin-bottom: 16px;
}

.form-row:last-child {
  margin-bottom: 0;
}

.form-group label {
  display: block;
  margin-bottom: 8px;
  font-size: 14px;
  font-weight: 500;
  color: #475569;
}

.form-group input,
.form-group select,
.form-group textarea {
  width: 100%;
  padding: 10px 14px;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  font-size: 14px;
  color: #1e293b;
  background: white;
  transition: all 0.2s;
  font-family: inherit;
}

.form-group input:focus,
.form-group select:focus,
.form-group textarea:focus {
  outline: none;
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

.form-group input:disabled {
  background: #f1f5f9;
  color: #94a3b8;
  cursor: not-allowed;
}

.form-group textarea {
  resize: vertical;
  min-height: 60px;
}

.checkbox-group {
  margin-bottom: 12px;
}

.checkbox-group label {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  margin-bottom: 0;
}

.checkbox-group input[type="checkbox"] {
  width: auto;
  cursor: pointer;
  margin: 0;
}

.checkbox-group span {
  font-size: 14px;
  color: #1e293b;
}

.panel-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding: 20px 24px;
  border-top: 1px solid var(--border-color);
  background: var(--bg-primary);
}

.btn {
  padding: 10px 24px;
  border: none;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-secondary {
  background: #f1f5f9;
  color: #64748b;
}

.btn-secondary:hover {
  background: #e2e8f0;
  color: #475569;
}

.btn-primary {
  background: #3b82f6;
  color: white;
}

.btn-primary:hover {
  background: #2563eb;
}

.panel-content::-webkit-scrollbar {
  width: 6px;
}

.panel-content::-webkit-scrollbar-track {
  background: transparent;
}

.panel-content::-webkit-scrollbar-thumb {
  background: #cbd5e1;
  border-radius: 3px;
}

.panel-content::-webkit-scrollbar-thumb:hover {
  background: #94a3b8;
}
</style>
