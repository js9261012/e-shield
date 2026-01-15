<template>
  <div class="queue-status">
    <div v-if="loading" class="loading">載入中...</div>
    
    <div v-else-if="error" class="error card">{{ error }}</div>
    
    <div v-else-if="queueStatus" class="queue-info card">
      <h2>排隊狀態</h2>
      
      <div class="status-section">
        <div class="status-badge" :class="statusClass">
          {{ statusText }}
        </div>
        
        <div v-if="queueStatus.status === 'waiting'" class="waiting-info">
          <p class="position-info">
            您在排隊區的位置: <strong>第 {{ queueStatus.queue_position_waiting + 1 }} 位</strong>
          </p>
          <p class="total-info">
            排隊區總人數: {{ queueStatus.total_in_waiting }} 人
          </p>
          <p class="wait-time">
            預估等待時間: <strong>{{ formatWaitTime(queueStatus.estimated_wait_time) }}</strong>
          </p>
        </div>
        
        <div v-else-if="queueStatus.status === 'ready_to_purchase' || queueStatus.status === 'active'" class="ready-info">
          <p class="ready-message">🎉 您已在搖滾區！可以開始購買</p>
          <p class="position-info">
            您在搖滾區的位置: <strong>第 {{ queueStatus.queue_position_active + 1 }} 位</strong>
          </p>
          <p class="total-info">
            搖滾區總人數: {{ queueStatus.total_in_active }} 人（最多 10 人）
          </p>
          <button class="btn btn-success btn-large" @click="goToPurchase">
            立即購買
          </button>
        </div>
        
        <div v-else-if="queueStatus.status === 'purchased'" class="purchased-info">
          <p class="success-message">✓ 購買完成</p>
          <button class="btn btn-primary" @click="goToResult">
            查看購買結果
          </button>
        </div>
      </div>
      
      <div class="progress-bar">
        <div class="progress-fill" :style="{ width: progressPercentage + '%' }"></div>
      </div>
      
      <button class="btn btn-primary" @click="goHome" style="margin-top: 20px;">
        返回商品列表
      </button>
    </div>
  </div>
</template>

<script>
import api from '../services/api'
import SSEService from '../services/sse'

export default {
  name: 'QueueStatus',
  data() {
    return {
      queueStatus: null,
      loading: true,
      error: null,
      eventSource: null,
      pollInterval: null
    }
  },
  computed: {
    statusClass() {
      if (!this.queueStatus) return ''
      const status = this.queueStatus.status
      return {
        'status-waiting': status === 'waiting',
        'status-active': status === 'active',
        'status-ready': status === 'ready_to_purchase',
        'status-purchased': status === 'purchased'
      }
    },
    
    statusText() {
      if (!this.queueStatus) return ''
      const statusMap = {
        'waiting': '排隊中',
        'active': '搖滾區等待中',
        'ready_to_purchase': '可以購買',
        'purchased': '已購買',
        'expired': '已過期'
      }
      return statusMap[this.queueStatus.status] || '未知狀態'
    },
    
    progressPercentage() {
      if (!this.queueStatus) return 0
      
      if (this.queueStatus.status === 'ready_to_purchase') {
        return 100
      } else if (this.queueStatus.status === 'active') {
        const total = this.queueStatus.total_in_active
        const position = this.queueStatus.queue_position_active
        return total > 0 ? ((total - position) / total) * 100 : 0
      } else if (this.queueStatus.status === 'waiting') {
        // 簡化計算，假設需要進入搖滾區才算進度
        return 10
      }
      
      return 0
    }
  },
  mounted() {
    this.loadQueueStatus()
    this.startSSE()
  },
  beforeUnmount() {
    if (this.eventSource) {
      this.eventSource.close()
    }
    if (this.pollInterval) {
      clearInterval(this.pollInterval)
    }
  },
  methods: {
    async loadQueueStatus() {
      const sessionId = localStorage.getItem('session_id')
      const productId = this.$route.params.productId || localStorage.getItem('product_id')
      
      if (!sessionId || !productId) {
        this.error = '缺少會話資訊，請重新加入佇列'
        return
      }
      
      try {
        this.loading = true
        this.queueStatus = await api.getQueueStatus(sessionId, productId)
      } catch (error) {
        this.error = error.detail?.message || '載入佇列狀態失敗'
        console.error('載入佇列狀態失敗:', error)
      } finally {
        this.loading = false
      }
    },
    
    startSSE() {
      const sessionId = localStorage.getItem('session_id')
      const productId = this.$route.params.productId || localStorage.getItem('product_id')
      
      if (!sessionId || !productId) {
        return
      }
      
      // 使用 SSE 即時更新
      const sseUrl = `/api/queue/stream?session_id=${sessionId}&product_id=${productId}`
      
      this.eventSource = new SSEService(sseUrl)
      this.eventSource
        .on('queue_update', (data) => {
          // 更新佇列狀態
          if (this.queueStatus) {
            this.queueStatus.queue_position_waiting = data.queue_position_waiting
            this.queueStatus.queue_position_active = data.queue_position_active
            this.queueStatus.total_in_waiting = data.total_in_waiting
            this.queueStatus.total_in_active = data.total_in_active
            this.queueStatus.estimated_wait_time = data.estimated_wait_time
            this.queueStatus.status = data.status
            
            // 如果狀態變為可以購買，提示使用者
            if (data.status === 'ready_to_purchase') {
              // 可以顯示通知或自動跳轉
            }
          }
        })
        .on('error', (data) => {
          console.error('SSE 錯誤:', data)
          // 如果 SSE 失敗，回退到輪詢
          this.pollQueueStatus()
        })
        .connect()
    },
    
    pollQueueStatus() {
      // 輪詢備用方案（當 SSE 不可用時）
      if (this.pollInterval) {
        clearInterval(this.pollInterval)
      }
      this.pollInterval = setInterval(() => {
        this.loadQueueStatus()
      }, 5000) // 每 5 秒輪詢一次
    },
    
    goToPurchase() {
      const productId = this.$route.params.productId || localStorage.getItem('product_id')
      this.$router.push(`/purchase/${productId}`)
    },
    
    goToResult() {
      this.$router.push('/result')
    },
    
    goHome() {
      this.$router.push('/')
    },
    
    formatWaitTime(seconds) {
      if (seconds < 60) {
        return `${seconds} 秒`
      } else if (seconds < 3600) {
        const minutes = Math.floor(seconds / 60)
        return `${minutes} 分鐘`
      } else {
        const hours = Math.floor(seconds / 3600)
        const minutes = Math.floor((seconds % 3600) / 60)
        return `${hours} 小時 ${minutes} 分鐘`
      }
    }
  }
}
</script>

<style scoped>
.status-section {
  margin: 24px 0;
}

.status-badge {
  display: inline-block;
  padding: 8px 16px;
  border-radius: 20px;
  font-weight: bold;
  margin-bottom: 20px;
}

.status-waiting {
  background-color: #ffc107;
  color: #000;
}

.status-active {
  background-color: #17a2b8;
  color: #fff;
}

.status-ready {
  background-color: #28a745;
  color: #fff;
}

.status-purchased {
  background-color: #6c757d;
  color: #fff;
}

.position-info, .total-info, .wait-time {
  font-size: 18px;
  margin: 12px 0;
}

.ready-message {
  font-size: 24px;
  color: #28a745;
  margin: 20px 0;
  text-align: center;
}

.success-message {
  font-size: 20px;
  color: #28a745;
  margin: 20px 0;
  text-align: center;
}

.progress-bar {
  width: 100%;
  height: 20px;
  background-color: #e9ecef;
  border-radius: 10px;
  overflow: hidden;
  margin: 20px 0;
}

.progress-fill {
  height: 100%;
  background-color: #007bff;
  transition: width 0.3s ease;
}

.btn-large {
  width: 100%;
  padding: 16px;
  font-size: 18px;
  margin-top: 20px;
}
</style>
