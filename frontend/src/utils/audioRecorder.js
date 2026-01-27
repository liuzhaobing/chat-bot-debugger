/**
 * 音频录制工具类
 * 提供跨浏览器兼容的音频录制功能，确保输出格式与后端兼容
 */

class AudioRecorder {
  constructor() {
    this.mediaRecorder = null
    this.audioChunks = []
    this.stream = null
    this.isRecording = false
    this.onDataAvailable = null
    this.onStop = null
    this.onError = null
    this.audioContext = null
  }

  /**
   * 获取支持的音频格式
   * @returns {string} 支持的MIME类型
   */
  getSupportedMimeType() {
    const types = [
      'audio/wav',
      'audio/webm;codecs=pcm',
      'audio/webm;codecs=opus',
      'audio/webm',
      'audio/mp4',
      'audio/ogg;codecs=opus'
    ]

    for (const type of types) {
      if (MediaRecorder.isTypeSupported(type)) {
        console.log('Using audio format:', type)
        return type
      }
    }

    console.warn('No supported audio format found, using default')
    return 'audio/webm' // 默认格式
  }

  /**
   * 从MIME类型提取格式名称
   * @param {string} mimeType - MIME类型
   * @returns {string} 格式名称
   */
  extractFormatFromMimeType(mimeType) {
    if (mimeType.includes('wav')) return 'wav'
    if (mimeType.includes('webm')) return 'webm'
    if (mimeType.includes('mp4')) return 'mp4'
    if (mimeType.includes('ogg')) return 'ogg'
    return 'webm' // 默认
  }

  /**
   * 将WebM音频转换为WAV格式
   * @param {Blob} webmBlob - WebM音频Blob
   * @returns {Promise<Blob>} WAV格式的Blob
   */
  async convertWebMToWAV(webmBlob) {
    try {
      // 创建音频上下文
      if (!this.audioContext) {
        this.audioContext = new (window.AudioContext || window.webkitAudioContext)()
      }

      // 将Blob转换为ArrayBuffer
      const arrayBuffer = await webmBlob.arrayBuffer()
      
      // 解码音频数据
      const audioBuffer = await this.audioContext.decodeAudioData(arrayBuffer)
      
      // 转换为WAV格式
      const wavBlob = this.audioBufferToWav(audioBuffer)
      
      console.log('WebM转WAV成功:', {
        originalSize: webmBlob.size,
        convertedSize: wavBlob.size,
        sampleRate: audioBuffer.sampleRate,
        channels: audioBuffer.numberOfChannels,
        duration: audioBuffer.duration
      })
      
      return wavBlob
    } catch (error) {
      console.error('WebM转WAV失败:', error)
      // 如果转换失败，返回原始Blob
      return webmBlob
    }
  }

  /**
   * 将AudioBuffer转换为WAV格式的Blob
   * @param {AudioBuffer} audioBuffer - 音频缓冲区
   * @returns {Blob} WAV格式的Blob
   */
  audioBufferToWav(audioBuffer) {
    const numberOfChannels = audioBuffer.numberOfChannels
    const sampleRate = audioBuffer.sampleRate
    const format = 1 // PCM
    const bitDepth = 16

    const bytesPerSample = bitDepth / 8
    const blockAlign = numberOfChannels * bytesPerSample
    const byteRate = sampleRate * blockAlign
    const dataSize = audioBuffer.length * blockAlign
    const bufferSize = 44 + dataSize

    const arrayBuffer = new ArrayBuffer(bufferSize)
    const view = new DataView(arrayBuffer)

    // WAV文件头
    const writeString = (offset, string) => {
      for (let i = 0; i < string.length; i++) {
        view.setUint8(offset + i, string.charCodeAt(i))
      }
    }

    writeString(0, 'RIFF')
    view.setUint32(4, bufferSize - 8, true)
    writeString(8, 'WAVE')
    writeString(12, 'fmt ')
    view.setUint32(16, 16, true) // fmt chunk size
    view.setUint16(20, format, true)
    view.setUint16(22, numberOfChannels, true)
    view.setUint32(24, sampleRate, true)
    view.setUint32(28, byteRate, true)
    view.setUint16(32, blockAlign, true)
    view.setUint16(34, bitDepth, true)
    writeString(36, 'data')
    view.setUint32(40, dataSize, true)

    // 写入音频数据
    let offset = 44
    for (let i = 0; i < audioBuffer.length; i++) {
      for (let channel = 0; channel < numberOfChannels; channel++) {
        const sample = Math.max(-1, Math.min(1, audioBuffer.getChannelData(channel)[i]))
        const intSample = sample < 0 ? sample * 0x8000 : sample * 0x7FFF
        view.setInt16(offset, intSample, true)
        offset += 2
      }
    }

    return new Blob([arrayBuffer], { type: 'audio/wav' })
  }

  /**
   * 开始录音
   * @returns {Promise<void>}
   */
  async startRecording() {
    try {
      // 获取音频流
      this.stream = await navigator.mediaDevices.getUserMedia({ 
        audio: {
          sampleRate: 16000,  // 尝试设置采样率为16kHz
          channelCount: 1,    // 单声道
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true
        } 
      })

      // 获取支持的格式
      const mimeType = this.getSupportedMimeType()
      
      // 创建MediaRecorder
      const options = { mimeType }
      this.mediaRecorder = new MediaRecorder(this.stream, options)
      
      // 重置音频块数组
      this.audioChunks = []

      // 设置事件处理器
      this.mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          this.audioChunks.push(event.data)
          if (this.onDataAvailable) {
            this.onDataAvailable(event.data)
          }
        }
      }

      this.mediaRecorder.onstop = async () => {
        const actualMimeType = this.mediaRecorder.mimeType || mimeType
        let audioBlob = new Blob(this.audioChunks, { type: actualMimeType })
        
        // 停止所有音频轨道
        if (this.stream) {
          this.stream.getTracks().forEach(track => track.stop())
          this.stream = null
        }

        let formatName = this.extractFormatFromMimeType(actualMimeType)
        
        // 如果不是WAV格式，尝试转换为WAV
        if (formatName !== 'wav') {
          console.log('尝试将', formatName, '转换为WAV格式')
          const convertedBlob = await this.convertWebMToWAV(audioBlob)
          if (convertedBlob !== audioBlob) {
            audioBlob = convertedBlob
            formatName = 'wav'
            console.log('格式转换成功，现在使用WAV格式')
          }
        }
        
        console.log('录音完成:', {
          format: formatName,
          mimeType: actualMimeType,
          size: audioBlob.size,
          duration: this.audioChunks.length * 0.1 // 估算时长
        })

        if (this.onStop) {
          this.onStop(audioBlob, formatName)
        }

        this.isRecording = false
      }

      this.mediaRecorder.onerror = (event) => {
        console.error('MediaRecorder error:', event.error)
        if (this.onError) {
          this.onError(event.error)
        }
        this.isRecording = false
      }

      // 开始录音
      this.mediaRecorder.start(100) // 每100ms收集一次数据
      this.isRecording = true

      console.log('录音开始，格式:', mimeType)

    } catch (error) {
      console.error('启动录音失败:', error)
      if (this.onError) {
        this.onError(error)
      }
      throw error
    }
  }

  /**
   * 停止录音
   */
  stopRecording() {
    if (this.mediaRecorder && this.isRecording) {
      this.mediaRecorder.stop()
    }
  }

  /**
   * 检查是否正在录音
   * @returns {boolean}
   */
  getIsRecording() {
    return this.isRecording
  }

  /**
   * 清理资源
   */
  cleanup() {
    if (this.mediaRecorder && this.isRecording) {
      this.mediaRecorder.stop()
    }
    
    if (this.stream) {
      this.stream.getTracks().forEach(track => track.stop())
      this.stream = null
    }
    
    if (this.audioContext) {
      this.audioContext.close()
      this.audioContext = null
    }
    
    this.audioChunks = []
    this.isRecording = false
  }
}

export default AudioRecorder