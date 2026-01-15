/**
 * SSE (Server-Sent Events) 服務
 */
export class SSEService {
  constructor(url, options = {}) {
    this.url = url
    this.options = options
    this.eventSource = null
    this.listeners = new Map()
  }
  
  connect() {
    if (this.eventSource) {
      this.close()
    }
    
    this.eventSource = new EventSource(this.url)
    
    // 監聽訊息
    this.eventSource.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data)
        this.emit('message', data)
      } catch (e) {
        console.error('解析 SSE 訊息失敗:', e)
      }
    }
    
    // 監聽自訂事件
    this.eventSource.addEventListener('queue_update', (event) => {
      try {
        const data = JSON.parse(event.data)
        this.emit('queue_update', data)
      } catch (e) {
        console.error('解析 queue_update 事件失敗:', e)
      }
    })
    
    this.eventSource.addEventListener('error', (event) => {
      try {
        const data = JSON.parse(event.data)
        this.emit('error', data)
      } catch (e) {
        console.error('解析 error 事件失敗:', e)
      }
    })
    
    // 連線錯誤處理
    this.eventSource.onerror = (error) => {
      console.error('SSE 連線錯誤:', error)
      this.emit('error', { error: 'CONNECTION_ERROR' })
    }
    
    return this
  }
  
  on(event, callback) {
    if (!this.listeners.has(event)) {
      this.listeners.set(event, [])
    }
    this.listeners.get(event).push(callback)
    return this
  }
  
  off(event, callback) {
    if (this.listeners.has(event)) {
      const callbacks = this.listeners.get(event)
      const index = callbacks.indexOf(callback)
      if (index > -1) {
        callbacks.splice(index, 1)
      }
    }
    return this
  }
  
  emit(event, data) {
    if (this.listeners.has(event)) {
      this.listeners.get(event).forEach(callback => {
        callback(data)
      })
    }
  }
  
  close() {
    if (this.eventSource) {
      this.eventSource.close()
      this.eventSource = null
    }
    this.listeners.clear()
  }
}

export default SSEService
