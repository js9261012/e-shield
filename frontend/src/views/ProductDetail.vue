<template>
  <div class="product-detail">
    <div v-if="loading" class="loading">載入中...</div>
    
    <div v-else-if="error" class="error">{{ error }}</div>
    
    <div v-else-if="product" class="product-info card">
      <div class="product-header">
        <img :src="product.image_url" :alt="product.name" class="product-image-large" />
        <div class="product-details">
          <h2>{{ product.name }}</h2>
          <p class="price-large">NT$ {{ formatPrice(product.price) }}</p>
          <p class="stock-info">
            <span :class="{'low-stock': product.remaining_stock <= 2}">
              剩餘庫存: {{ product.remaining_stock }} / {{ product.total_stock }}
            </span>
          </p>
          
          <div v-if="product.remaining_stock > 0" class="join-queue-section">
            <h3>加入排隊</h3>
            <p class="description">通過驗證後即可加入購買佇列</p>
            
            <TurnstileWidget
              :site-key="turnstileSiteKey"
              @verified="onTurnstileVerified"
              @error="onTurnstileError"
            />
            
            <div v-if="turnstileToken" class="verified-message success">
              ✓ 驗證成功，可以加入佇列
            </div>
            
            <div v-if="turnstileError" class="error">{{ turnstileError }}</div>
            
            <button
              class="btn btn-primary btn-large"
              :disabled="!turnstileToken || joining"
              @click="joinQueue"
            >
              {{ joining ? '加入中...' : '加入排隊' }}
            </button>
            
            <div v-if="joinError" class="error">{{ joinError }}</div>
          </div>
          
          <div v-else class="out-of-stock">
            <p>商品已售完</p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import api from '../services/api'
import TurnstileWidget from '../components/TurnstileWidget.vue'

export default {
  name: 'ProductDetail',
  components: {
    TurnstileWidget
  },
  data() {
    return {
      product: null,
      loading: true,
      error: null,
      turnstileToken: null,
      turnstileError: null,
      joining: false,
      joinError: null,
      turnstileSiteKey: '1x00000000000000000000AA' // 測試模式金鑰
    }
  },
  mounted() {
    this.fetchProduct()
  },
  methods: {
    async fetchProduct() {
      try {
        this.loading = true
        this.product = await api.getProduct(this.$route.params.id)
      } catch (error) {
        this.error = '載入商品失敗'
        console.error('載入商品失敗:', error)
      } finally {
        this.loading = false
      }
    },
    
    onTurnstileVerified(token) {
      this.turnstileToken = token
      this.turnstileError = null
    },
    
    onTurnstileError(error) {
      this.turnstileToken = null
      this.turnstileError = 'Turnstile 驗證失敗，請重試'
    },
    
    async joinQueue() {
      if (!this.turnstileToken) {
        this.joinError = '請先完成 Turnstile 驗證'
        return
      }
      
      try {
        this.joining = true
        this.joinError = null
        
        const response = await api.joinQueue(this.product.id, this.turnstileToken)
        
        if (response.success) {
          // 儲存 session_id 到 LocalStorage
          localStorage.setItem('session_id', response.session_id)
          localStorage.setItem('product_id', this.product.id)
          
          // 跳轉到佇列狀態頁面
          this.$router.push(`/queue/${this.product.id}`)
        } else {
          this.joinError = response.message || '加入佇列失敗'
        }
      } catch (error) {
        this.joinError = error.detail?.message || error.message || '加入佇列失敗，請重試'
        console.error('加入佇列失敗:', error)
      } finally {
        this.joining = false
      }
    },
    
    formatPrice(price) {
      return (price / 100).toLocaleString('zh-TW')
    }
  }
}
</script>

<style scoped>
.product-header {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 40px;
}

.product-image-large {
  width: 100%;
  border-radius: 8px;
}

.product-details h2 {
  font-size: 32px;
  margin-bottom: 16px;
}

.price-large {
  font-size: 36px;
  font-weight: bold;
  color: #007bff;
  margin-bottom: 16px;
}

.stock-info {
  font-size: 18px;
  margin-bottom: 24px;
}

.low-stock {
  color: #dc3545;
  font-weight: bold;
}

.join-queue-section {
  margin-top: 32px;
  padding-top: 32px;
  border-top: 1px solid #eee;
}

.join-queue-section h3 {
  font-size: 24px;
  margin-bottom: 8px;
}

.description {
  color: #666;
  margin-bottom: 20px;
}

.btn-large {
  width: 100%;
  margin-top: 20px;
  font-size: 18px;
  padding: 16px;
}

.verified-message {
  margin-top: 12px;
  padding: 12px;
  background-color: #d4edda;
  border-radius: 4px;
}

.out-of-stock {
  text-align: center;
  padding: 40px;
  color: #dc3545;
  font-size: 20px;
}

@media (max-width: 768px) {
  .product-header {
    grid-template-columns: 1fr;
  }
}
</style>
