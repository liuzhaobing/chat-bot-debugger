/**
 * 实时音频处理器 - 用于VAD+ASR测试和语音交互
 * 统一的PCM音频采集和处理逻辑
 */

class RealtimeAudioProcessor {
  constructor(options = {}) {
    // 音频配置
    this.sampleRate = options.sampleRate || 16000
    this.channelCount = options.channelCount || 1
    this.bufferSize = options.bufferSize || 256 // 16ms at 16kHz
    this.fftSize = options.fftSize || 2048

    // 音频上下文和节点
    this.audioContext = null
    this.analyser = null
    this.mediaStream = null
    this.audioProcessor = null
    this.dataArray = null
    this.source = null

    // 状态
    this.isActive = false
    this.audioLevel = 0
    this.isVoiceActive = false

    // VAD参数
    this.vadBuffer = []
    this.vadBufferSize = 10
    this.vadThreshold = 0.02

    // 拖尾机制（hangover）- 防止频繁切换
    this.speechFrameCount = 0
    this.silenceFrameCount = 0
    this.minSpeechFrames = 3       // 连续3帧确认语音开始
    this.hangoverFrames = 10       // 连续10帧确认语音结束（拖尾约160ms）

    // 回调函数
    this.onAudioData = null  // (audioBytes: Uint8Array) => void
    this.onAudioLevel = null  // (level: number) => void
    this.onVoiceActivity = null  // (isActive: boolean, level: number) => void
    this.onError = null  // (error: Error) => void
  }

  /**
   * 检查浏览器是否支持音频 API
   */
  checkBrowserSupport() {
    const issues = []

    if (!navigator.mediaDevices) {
      issues.push('navigator.mediaDevices 不存在（需要 HTTPS 或 localhost）')
    } else if (typeof navigator.mediaDevices.getUserMedia !== 'function') {
      issues.push('getUserMedia API 不可用')
    }

    if (!window.AudioContext && !window.webkitAudioContext) {
      issues.push('AudioContext API 不可用')
    }

    return {
      supported: issues.length === 0,
      issues,
      isSecureContext: window.isSecureContext,
      protocol: window.location.protocol,
      hostname: window.location.hostname
    }
  }

  /**
   * 初始化音频处理器
   */
  async initialize() {
    try {
      // 检查浏览器支持
      const support = this.checkBrowserSupport()
      if (!support.supported) {
        throw new Error(`浏览器不支持: ${support.issues.join(', ')}`)
      }

      // 非安全上下文警告
      if (!support.isSecureContext && support.hostname !== 'localhost' && support.hostname !== '127.0.0.1') {
        console.warn('非安全上下文，音频 API 可能受限')
      }

      // 获取麦克风权限
      this.mediaStream = await navigator.mediaDevices.getUserMedia({
        audio: {
          sampleRate: this.sampleRate,
          channelCount: this.channelCount,
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true
        }
      })

      // 创建音频上下文
      const AudioContextClass = window.AudioContext || window.webkitAudioContext
      this.audioContext = new AudioContextClass({ sampleRate: this.sampleRate })
      
      if (this.audioContext.state === 'suspended') {
        await this.audioContext.resume()
      }

      // 创建分析器用于可视化和频谱分析
      this.analyser = this.audioContext.createAnalyser()
      this.analyser.fftSize = this.fftSize
      this.analyser.smoothingTimeConstant = 0.3  // 降低平滑，提高频谱响应速度
      this.dataArray = new Uint8Array(this.analyser.frequencyBinCount)

      // 创建音频源
      this.source = this.audioContext.createMediaStreamSource(this.mediaStream)
      this.source.connect(this.analyser)

      // 创建音频处理器
      this.audioProcessor = this.audioContext.createScriptProcessor(
        this.bufferSize, 
        this.channelCount, 
        this.channelCount
      )
      
      // 设置音频处理回调
      this.audioProcessor.onaudioprocess = (e) => {
        if (!this.isActive) return
        
        const inputData = e.inputBuffer.getChannelData(0)
        
        // 计算音频级别
        let sum = 0
        for (let i = 0; i < inputData.length; i++) {
          sum += Math.abs(inputData[i])
        }
        const average = sum / inputData.length
        this.audioLevel = Math.min(1, average * 10)
        
        // 触发音频级别回调
        if (this.onAudioLevel) {
          this.onAudioLevel(this.audioLevel)
        }
        
        // VAD检测
        this.detectVoiceActivity(average)
        
        // 转换为16位PCM字节数据
        const pcmData = new Int16Array(inputData.length)
        for (let i = 0; i < inputData.length; i++) {
          const s = Math.max(-1, Math.min(1, inputData[i]))
          pcmData[i] = s < 0 ? s * 0x8000 : s * 0x7FFF
        }
        
        // 转换为字节数组
        const audioBytes = new Uint8Array(pcmData.buffer)
        
        // 触发音频数据回调
        if (this.onAudioData) {
          this.onAudioData(audioBytes)
        }
      }
      
      // 连接音频节点
      this.source.connect(this.audioProcessor)
      this.audioProcessor.connect(this.audioContext.destination)
      
      console.log('实时音频处理器初始化成功', {
        sampleRate: this.sampleRate,
        channelCount: this.channelCount,
        bufferSize: this.bufferSize,
        latency: `${this.bufferSize / this.sampleRate * 1000}ms`
      })
      
      return true
    } catch (error) {
      console.error('音频处理器初始化失败:', error)
      if (this.onError) {
        this.onError(error)
      }
      return false
    }
  }

  /**
   * 开始处理音频
   */
  start() {
    if (!this.audioContext || !this.audioProcessor) {
      console.error('音频处理器未初始化')
      return false
    }
    
    this.isActive = true
    console.log('开始音频处理')
    return true
  }

  /**
   * 停止处理音频
   */
  stop() {
    this.isActive = false
    this.audioLevel = 0
    this.isVoiceActive = false
    this.speechFrameCount = 0
    this.silenceFrameCount = 0
    console.log('停止音频处理')
  }

  /**
   * VAD语音活动检测 - 带拖尾机制
   */
  detectVoiceActivity(audioLevel) {
    // 添加到VAD缓冲区
    this.vadBuffer.push(audioLevel)
    if (this.vadBuffer.length > this.vadBufferSize) {
      this.vadBuffer.shift()
    }

    // 计算平均音频级别
    const avgLevel = this.vadBuffer.reduce((sum, level) => sum + level, 0) / this.vadBuffer.length

    // 拖尾机制（hangover）- 防止频繁切换
    const isSpeech = avgLevel > this.vadThreshold
    const wasActive = this.isVoiceActive

    if (isSpeech) {
      this.speechFrameCount++
      this.silenceFrameCount = 0
      // 连续N帧语音才确认语音开始
      if (this.speechFrameCount >= this.minSpeechFrames && !this.isVoiceActive) {
        this.isVoiceActive = true
      }
    } else {
      this.silenceFrameCount++
      // 连续N帧静音才确认语音结束（拖尾）
      if (this.silenceFrameCount >= this.hangoverFrames && this.isVoiceActive) {
        this.isVoiceActive = false
        this.speechFrameCount = 0
      }
    }

    // 触发语音活动变化回调
    if (this.onVoiceActivity && wasActive !== this.isVoiceActive) {
      this.onVoiceActivity(this.isVoiceActive, avgLevel)
    }
  }

  /**
   * 获取频谱数据（用于可视化和频谱分析）
   * @returns {Uint8Array|null} 频谱数据或null（如果不可用）
   */
  getFrequencyData() {
    if (!this.analyser || !this.dataArray || !this.isActive) {
      return null
    }

    try {
      this.analyser.getByteFrequencyData(this.dataArray)
      return this.dataArray
    } catch (e) {
      console.error('获取频谱数据失败:', e)
      return null
    }
  }

  /**
   * 计算人声频率能量占比
   * 利用频谱分析区分人声和噪音
   * @returns {number} 人声能量占比 (0-1)
   */
  calculateVoiceEnergyRatio() {
    const frequencyData = this.getFrequencyData()
    if (!frequencyData) return 0

    // 动态计算人声频段 bin 索引
    // 频率 bin 对应频率 = binIndex * sampleRate / fftSize
    const binWidth = this.sampleRate / this.fftSize
    const voiceStartBin = Math.floor(85 / binWidth)    // ~85Hz (人声低频)
    const voiceEndBin = Math.ceil(3400 / binWidth)     // ~3400Hz (人声高频)

    let voiceEnergy = 0
    let totalEnergy = 0

    for (let i = 0; i < frequencyData.length; i++) {
      const energy = frequencyData[i] * frequencyData[i]
      totalEnergy += energy

      if (i >= voiceStartBin && i <= voiceEndBin) {
        voiceEnergy += energy
      }
    }

    return totalEnergy > 0 ? voiceEnergy / totalEnergy : 0
  }

  /**
   * 获取时域数据（用于波形可视化）
   */
  getTimeDomainData() {
    if (!this.analyser) return null
    
    const timeData = new Uint8Array(this.analyser.fftSize)
    this.analyser.getByteTimeDomainData(timeData)
    return Array.from(timeData)
  }

  /**
   * 设置VAD阈值
   */
  setVADThreshold(threshold) {
    this.vadThreshold = Math.max(0, Math.min(1, threshold))
  }

  /**
   * 销毁音频处理器
   */
  destroy() {
    try {
      console.log('开始销毁音频处理器...')
      
      // 停止处理
      this.stop()

      // 断开音频节点
      if (this.audioProcessor) {
        this.audioProcessor.disconnect()
        this.audioProcessor = null
      }

      if (this.source) {
        this.source.disconnect()
        this.source = null
      }

      // 停止媒体流
      if (this.mediaStream) {
        this.mediaStream.getTracks().forEach(track => {
          console.log(`停止轨道: ${track.kind}, 状态: ${track.readyState}`)
          track.stop()
        })
        this.mediaStream = null
      }

      // 关闭音频上下文
      if (this.audioContext && this.audioContext.state !== 'closed') {
        this.audioContext.close()
        this.audioContext = null
      }

      // 清理变量
      this.analyser = null
      this.dataArray = null
      this.vadBuffer = []
      this.speechFrameCount = 0
      this.silenceFrameCount = 0

      console.log('音频处理器已完全销毁')
    } catch (error) {
      console.error('销毁音频处理器时出错:', error)
    }
  }

  /**
   * 获取当前状态
   */
  getStatus() {
    return {
      isActive: this.isActive,
      audioLevel: this.audioLevel,
      isVoiceActive: this.isVoiceActive,
      hasPermission: !!this.mediaStream,
      contextState: this.audioContext ? this.audioContext.state : 'closed'
    }
  }
}

/**
 * 创建WebSocket音频消息
 * 统一的消息格式，确保前后端一致
 */
export function createAudioMessage(audioBytes, options = {}) {
  // 转换为base64
  let binary = ''
  for (let i = 0; i < audioBytes.length; i++) {
    binary += String.fromCharCode(audioBytes[i])
  }
  const base64 = btoa(binary)
  
  // 统一的消息格式
  return {
    type: 'audio_data',
    timestamp: Math.floor(Date.now()),
    data: {
      audio_data: base64,
      sample_rate: options.sampleRate || 16000,
      channels: options.channels || 1,
      format: options.format || 'pcm',
      size: audioBytes.length
    },
    app_id: options.appId,
    session_id: options.sessionId
  }
}

export default RealtimeAudioProcessor
