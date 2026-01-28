/**
 * 音频处理工具类
 * 处理音频录制、实时音频分析、WebRTC音频处理等
 */

class AudioProcessor {
  constructor() {
    this.mediaRecorder = null
    this.audioContext = null
    this.analyser = null
    this.microphone = null
    this.dataArray = null
    this.isRecording = false
    this.stream = null
    this.audioChunks = []
    
    // 音频分析相关
    this.audioLevel = 0
    this.isVoiceActive = false
    this.silenceThreshold = 0.01
    this.voiceThreshold = 0.02
    this.silenceTimeout = null
    this.voiceTimeout = null
    
    // 回调函数
    this.onAudioLevel = null
    this.onVoiceStart = null
    this.onVoiceEnd = null
    this.onAudioData = null
    this.onError = null
    
    // VAD (Voice Activity Detection) 参数
    this.vadBufferSize = 10
    this.vadBuffer = []
    this.vadSensitivity = 0.5
  }

  /**
   * 初始化音频处理器
   */
  async initialize() {
    try {
      // 请求麦克风权限
      this.stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true,
          sampleRate: 16000,
          channelCount: 1
        }
      })

      // 创建音频上下文
      this.audioContext = new (window.AudioContext || window.webkitAudioContext)({
        sampleRate: 16000
      })

      // 创建分析器
      this.analyser = this.audioContext.createAnalyser()
      this.analyser.fftSize = 2048
      this.analyser.smoothingTimeConstant = 0.8

      // 连接麦克风到分析器
      this.microphone = this.audioContext.createMediaStreamSource(this.stream)
      this.microphone.connect(this.analyser)

      // 创建数据数组
      this.dataArray = new Uint8Array(this.analyser.frequencyBinCount)

      // 创建媒体录制器
      this.mediaRecorder = new MediaRecorder(this.stream, {
        mimeType: this.getSupportedMimeType(),
        audioBitsPerSecond: 16000
      })

      this.setupMediaRecorderEvents()

      console.log('音频处理器初始化成功')
      return true
    } catch (error) {
      console.error('音频处理器初始化失败:', error)
      if (this.onError) {
        this.onError('microphone_permission_denied', error)
      }
      return false
    }
  }

  /**
   * 获取支持的MIME类型
   */
  getSupportedMimeType() {
    const types = [
      'audio/webm;codecs=opus',
      'audio/webm',
      'audio/mp4',
      'audio/ogg;codecs=opus'
    ]
    
    for (const type of types) {
      if (MediaRecorder.isTypeSupported(type)) {
        return type
      }
    }
    
    return 'audio/webm' // 默认类型
  }

  /**
   * 设置媒体录制器事件
   */
  setupMediaRecorderEvents() {
    this.mediaRecorder.ondataavailable = (event) => {
      if (event.data.size > 0) {
        this.audioChunks.push(event.data)
        
        // 实时发送音频数据
        if (this.onAudioData) {
          this.onAudioData(event.data)
        }
      }
    }

    this.mediaRecorder.onstop = () => {
      const audioBlob = new Blob(this.audioChunks, { 
        type: this.getSupportedMimeType() 
      })
      this.audioChunks = []
      
      if (this.onAudioData) {
        this.onAudioData(audioBlob, true) // true 表示录制结束
      }
    }

    this.mediaRecorder.onerror = (event) => {
      console.error('MediaRecorder错误:', event.error)
      if (this.onError) {
        this.onError('recording_error', event.error)
      }
    }
  }

  /**
   * 开始录制
   */
  startRecording() {
    if (!this.mediaRecorder || this.isRecording) {
      return false
    }

    try {
      this.audioChunks = []
      this.mediaRecorder.start(100) // 每100ms发送一次数据
      this.isRecording = true
      this.startAudioAnalysis()
      
      console.log('开始录制音频')
      return true
    } catch (error) {
      console.error('开始录制失败:', error)
      if (this.onError) {
        this.onError('start_recording_failed', error)
      }
      return false
    }
  }

  /**
   * 停止录制
   */
  stopRecording() {
    if (!this.mediaRecorder || !this.isRecording) {
      return false
    }

    try {
      this.mediaRecorder.stop()
      this.isRecording = false
      this.stopAudioAnalysis()
      
      console.log('停止录制音频')
      return true
    } catch (error) {
      console.error('停止录制失败:', error)
      if (this.onError) {
        this.onError('stop_recording_failed', error)
      }
      return false
    }
  }

  /**
   * 开始音频分析
   */
  startAudioAnalysis() {
    if (!this.analyser) return

    const analyze = () => {
      if (!this.isRecording) return

      this.analyser.getByteFrequencyData(this.dataArray)
      
      // 计算音频级别
      let sum = 0
      for (let i = 0; i < this.dataArray.length; i++) {
        sum += this.dataArray[i]
      }
      this.audioLevel = sum / this.dataArray.length / 255

      // 语音活动检测
      this.detectVoiceActivity()

      // 回调音频级别
      if (this.onAudioLevel) {
        this.onAudioLevel(this.audioLevel)
      }

      requestAnimationFrame(analyze)
    }

    analyze()
  }

  /**
   * 停止音频分析
   */
  stopAudioAnalysis() {
    this.audioLevel = 0
    this.isVoiceActive = false
    
    if (this.silenceTimeout) {
      clearTimeout(this.silenceTimeout)
      this.silenceTimeout = null
    }
    
    if (this.voiceTimeout) {
      clearTimeout(this.voiceTimeout)
      this.voiceTimeout = null
    }
  }

  /**
   * 语音活动检测 (VAD)
   */
  detectVoiceActivity() {
    // 添加到VAD缓冲区
    this.vadBuffer.push(this.audioLevel)
    if (this.vadBuffer.length > this.vadBufferSize) {
      this.vadBuffer.shift()
    }

    // 计算平均音频级别
    const avgLevel = this.vadBuffer.reduce((sum, level) => sum + level, 0) / this.vadBuffer.length

    // 判断语音活动
    if (avgLevel > this.voiceThreshold) {
      if (!this.isVoiceActive) {
        this.isVoiceActive = true
        
        // 清除静音超时
        if (this.silenceTimeout) {
          clearTimeout(this.silenceTimeout)
          this.silenceTimeout = null
        }
        
        // 延迟触发语音开始事件，避免误触发
        if (this.voiceTimeout) {
          clearTimeout(this.voiceTimeout)
        }
        
        this.voiceTimeout = setTimeout(() => {
          if (this.isVoiceActive && this.onVoiceStart) {
            this.onVoiceStart()
          }
        }, 100)
      }
    } else if (avgLevel < this.silenceThreshold) {
      if (this.isVoiceActive) {
        // 延迟触发语音结束事件，避免短暂停顿被误判
        if (this.silenceTimeout) {
          clearTimeout(this.silenceTimeout)
        }
        
        this.silenceTimeout = setTimeout(() => {
          if (this.isVoiceActive) {
            this.isVoiceActive = false
            if (this.onVoiceEnd) {
              this.onVoiceEnd()
            }
          }
        }, 500) // 500ms静音后才认为语音结束
      }
    }
  }

  /**
   * 设置VAD敏感度
   * @param {number} sensitivity 0-1之间的值，越大越敏感
   */
  setVADSensitivity(sensitivity) {
    this.vadSensitivity = Math.max(0, Math.min(1, sensitivity))
    this.voiceThreshold = 0.01 + (this.vadSensitivity * 0.05)
    this.silenceThreshold = this.voiceThreshold * 0.5
  }

  /**
   * 获取音频频谱数据
   */
  getFrequencyData() {
    if (!this.analyser || !this.dataArray) return null
    
    this.analyser.getByteFrequencyData(this.dataArray)
    return Array.from(this.dataArray)
  }

  /**
   * 获取音频时域数据
   */
  getTimeDomainData() {
    if (!this.analyser) return null
    
    const timeData = new Uint8Array(this.analyser.fftSize)
    this.analyser.getByteTimeDomainData(timeData)
    return Array.from(timeData)
  }

  /**
   * 暂停录制
   */
  pauseRecording() {
    if (this.mediaRecorder && this.isRecording && this.mediaRecorder.state === 'recording') {
      this.mediaRecorder.pause()
      return true
    }
    return false
  }

  /**
   * 恢复录制
   */
  resumeRecording() {
    if (this.mediaRecorder && this.isRecording && this.mediaRecorder.state === 'paused') {
      this.mediaRecorder.resume()
      return true
    }
    return false
  }

  /**
   * 获取当前状态
   */
  getStatus() {
    return {
      isRecording: this.isRecording,
      audioLevel: this.audioLevel,
      isVoiceActive: this.isVoiceActive,
      hasPermission: !!this.stream,
      recorderState: this.mediaRecorder ? this.mediaRecorder.state : 'inactive'
    }
  }

  /**
   * 销毁音频处理器
   */
  destroy() {
    try {
      console.log('开始销毁音频处理器...')
      
      // 停止录制
      if (this.isRecording) {
        console.log('停止录制中...')
        this.stopRecording()
      }

      // 清除超时
      if (this.silenceTimeout) {
        clearTimeout(this.silenceTimeout)
        this.silenceTimeout = null
      }
      
      if (this.voiceTimeout) {
        clearTimeout(this.voiceTimeout)
        this.voiceTimeout = null
      }

      // 断开音频连接
      if (this.microphone) {
        console.log('断开麦克风连接...')
        this.microphone.disconnect()
        this.microphone = null
      }

      // 停止媒体流 - 这是关键步骤，必须先停止所有轨道
      if (this.stream) {
        console.log('停止媒体流轨道...')
        this.stream.getTracks().forEach(track => {
          console.log(`停止轨道: ${track.kind}, 状态: ${track.readyState}`)
          track.stop()
        })
        this.stream = null
      }

      // 关闭音频上下文
      if (this.audioContext && this.audioContext.state !== 'closed') {
        console.log('关闭音频上下文...')
        this.audioContext.close()
        this.audioContext = null
      }

      // 清理MediaRecorder
      if (this.mediaRecorder) {
        if (this.mediaRecorder.state === 'recording') {
          this.mediaRecorder.stop()
        }
        this.mediaRecorder = null
      }

      // 清理变量
      this.analyser = null
      this.dataArray = null
      this.audioChunks = []
      this.vadBuffer = []
      this.isRecording = false
      this.isVoiceActive = false
      this.audioLevel = 0

      console.log('音频处理器已完全销毁')
    } catch (error) {
      console.error('销毁音频处理器时出错:', error)
    }
  }

  /**
   * 检查浏览器支持
   */
  static checkSupport() {
    const support = {
      getUserMedia: !!(navigator.mediaDevices && navigator.mediaDevices.getUserMedia),
      mediaRecorder: !!window.MediaRecorder,
      audioContext: !!(window.AudioContext || window.webkitAudioContext),
      webRTC: !!(window.RTCPeerConnection || window.webkitRTCPeerConnection || window.mozRTCPeerConnection)
    }

    const isSupported = Object.values(support).every(Boolean)
    
    return {
      isSupported,
      support,
      missingFeatures: Object.keys(support).filter(key => !support[key])
    }
  }

  /**
   * 请求麦克风权限
   */
  static async requestMicrophonePermission() {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      stream.getTracks().forEach(track => track.stop()) // 立即停止，只是为了获取权限
      return true
    } catch (error) {
      console.error('麦克风权限请求失败:', error)
      return false
    }
  }
}

export default AudioProcessor