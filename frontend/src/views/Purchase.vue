<template>
  <div class="purchase">
    <div v-if="loading" class="loading">載入中...</div>
    
    <div v-else-if="error" class="error card">{{ error }}</div>
    
    <div v-else-if="product" class="purchase-form card">
      <h2>確認購買</h2>
      
      <div class="product-summary">
        <img :src="product.image_url" :alt="product.name" class="product-image" />
        <div class="product-info">
          <h3>{{ product.name }}</h3>
          <p class="price">NT$ {{ formatPrice(product.price) }}</p>
          <p class="quantity">購買數量: 1 雙（每人限購 1 雙）</p>
        </div>
      </div>
      
      <div class="total-section">
        <p class="total">總計: <strong>NT$ {{ formatPrice(product.price) }}</strong></p>
      </div>
      
      <div v-if="queuePosition !== null" class="position-warning">
        <p class="ready-message">
          ✓ 您在搖滾區第 {{ queuePosition + 1 }} 位，可以購買
        </p>
      </div>
      
      <button
        class="btn btn-success btn-large"
        :disabled="purchasing"
        @click="confirmPurchase"
      >
        {{ purchasing ? '處理中...' : '確認購買' }}
      </button>
      
      <div v-if="purchaseError" class="error">{{ purchaseError }}</div>
      
      <button class="btn btn-primary" @click="goBack" style="margin-top: 16px;">
        返回
      </button>
    </div>
  </div>
</template>

<script>
import api from '../services/api'

export default {
  name: 'Purchase',
  data() {
    return {
      product: null,
      loading: true,
      error: null,
      purchasing: false,
      purchaseError: null,
      queuePosition: null,
      pollInterval: null
    }
  },
  mounted() {
    this.checkAccess()
    this.fetchProduct()
    this.startPositionPolling()
  },
  
  beforeUnmount() {
    if (this.pollInterval) {
      clearInterval(this.pollInterval)
    }
  },
  methods: {
    async checkAccess() {
      // 檢查使用者是否在搖滾區（允許搖滾區中的人進入購買頁）
      const sessionId = localStorage.getItem('session_id')
      const productId = this.$route.params.productId || localStorage.getItem('product_id')
      
      if (!sessionId || !productId) {
        this.error = '缺少會話資訊，請重新加入佇列'
        return
      }
      
      try {
        const status = await api.getQueueStatus(sessionId, productId)
        
        // 允許搖滾區中的人（position_active >= 0）進入購買頁
        if (status.queue_position_active < 0 && status.queue_position_waiting < 0) {
          this.error = '您不在搖滾區，無法進入購買頁面'
        } else {
          // 記錄當前位置
          this.queuePosition = status.queue_position_active >= 0 
            ? status.queue_position_active 
            : null
        }
      } catch (error) {
        this.error = '無法驗證佇列狀態'
        console.error('檢查佇列狀態失敗:', error)
      }
    },
    
    startPositionPolling() {
      // 每 3 秒輪詢一次位置更新
      this.pollInterval = setInterval(async () => {
        const sessionId = localStorage.getItem('session_id')
        const productId = this.$route.params.productId || localStorage.getItem('product_id')
        
        if (!sessionId || !productId) {
          return
        }
        
        try {
          const status = await api.getQueueStatus(sessionId, productId)
          
          // 更新位置
          if (status.queue_position_active >= 0) {
            this.queuePosition = status.queue_position_active
            
            // 如果變成位置 0，可以購買了
            if (status.queue_position_active === 0) {
              // 可以顯示提示或自動啟用按鈕
            }
          }
        } catch (error) {
          console.error('更新位置失敗:', error)
        }
      }, 3000) // 每 3 秒更新一次
    },
    
    async fetchProduct() {
      const productId = this.$route.params.productId || localStorage.getItem('product_id')
      
      if (!productId) {
        this.error = '缺少商品資訊'
        return
      }
      
      try {
        this.loading = true
        this.product = await api.getProduct(productId)
      } catch (error) {
        this.error = '載入商品失敗'
        console.error('載入商品失敗:', error)
      } finally {
        this.loading = false
      }
    },
    
    async confirmPurchase() {
      const sessionId = localStorage.getItem('session_id')
      const productId = this.$route.params.productId || localStorage.getItem('product_id')
      
      if (!sessionId || !productId) {
        this.purchaseError = '缺少會話資訊，請重新加入佇列'
        return
      }
      
      // 檢查是否在搖滾區（搖滾區中所有人都可以購買）
      try {
        const status = await api.getQueueStatus(sessionId, productId)
        if (status.queue_position_active < 0) {
          this.purchaseError = '您不在搖滾區，無法購買'
          return
        }
      } catch (error) {
        this.purchaseError = '無法驗證佇列狀態'
        return
      }
      
      try {
        this.purchasing = true
        this.purchaseError = null
        
        const response = await api.purchase(productId, 1, sessionId)
        
        if (response.success) {
          // 儲存購買結果
          localStorage.setItem('purchase_result', JSON.stringify(response))
          // 跳轉到結果頁面
          this.$router.push('/result')
        } else {
          this.purchaseError = response.message || '購買失敗'
        }
      } catch (error) {
        this.purchaseError = error.detail?.message || error.message || '購買失敗，請重試'
        console.error('購買失敗:', error)
      } finally {
        this.purchasing = false
      }
    },
    
    goBack() {
      const productId = this.$route.params.productId || localStorage.getItem('product_id')
      this.$router.push(`/queue/${productId}`)
    },
    
    formatPrice(price) {
      return (price / 100).toLocaleString('zh-TW')
    }
  }
}
</script>

<style scoped>
.product-summary {
  display: flex;
  gap: 20px;
  margin: 24px 0;
  padding: 20px;
  background-color: #f8f9fa;
  border-radius: 8px;
}

.product-image {
  width: 150px;
  height: 150px;
  object-fit: cover;
  border-radius: 8px;
}

.product-info h3 {
  font-size: 24px;
  margin-bottom: 12px;
}

.product-info .price {
  font-size: 28px;
  font-weight: bold;
  color: #007bff;
  margin-bottom: 8px;
}

.quantity {
  color: #666;
}

.total-section {
  margin: 24px 0;
  padding: 20px;
  background-color: #e7f3ff;
  border-radius: 8px;
}

.total {
  font-size: 24px;
  text-align: right;
}

.btn-large {
  width: 100%;
  padding: 16px;
  font-size: 18px;
  margin-top: 20px;
}

.position-warning {
  margin: 20px 0;
  padding: 16px;
  border-radius: 8px;
}

.ready-message {
  background-color: #d4edda;
  color: #155724;
  padding: 12px;
  border-radius: 4px;
  font-weight: bold;
}

.wait-message {
  background-color: #fff3cd;
  color: #856404;
  padding: 12px;
  border-radius: 4px;
}
</style>
