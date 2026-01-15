<template>
  <div class="purchase-result">
    <div class="result-card card">
      <div v-if="result && result.success" class="success-result">
        <div class="success-icon">✓</div>
        <h2>購買成功！</h2>
        <div class="result-details">
          <p><strong>訂單編號:</strong> {{ result.order_id }}</p>
          <p><strong>商品 ID:</strong> {{ result.product_id }}</p>
          <p><strong>購買數量:</strong> {{ result.quantity }} 雙</p>
          <p v-if="result.remaining_stock !== undefined">
            <strong>剩餘庫存:</strong> {{ result.remaining_stock }} 雙
          </p>
        </div>
        <p class="success-message">{{ result.message }}</p>
      </div>
      
      <div v-else-if="result && !result.success" class="error-result">
        <div class="error-icon">✗</div>
        <h2>購買失敗</h2>
        <p class="error-message">{{ result.message }}</p>
        <p v-if="result.error" class="error-code">錯誤代碼: {{ result.error }}</p>
      </div>
      
      <div v-else class="no-result">
        <p>沒有購買記錄</p>
      </div>
      
      <div class="actions">
        <button class="btn btn-primary" @click="goHome">
          返回商品列表
        </button>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'PurchaseResult',
  data() {
    return {
      result: null
    }
  },
  mounted() {
    this.loadResult()
  },
  methods: {
    loadResult() {
      const resultStr = localStorage.getItem('purchase_result')
      if (resultStr) {
        try {
          this.result = JSON.parse(resultStr)
        } catch (e) {
          console.error('解析購買結果失敗:', e)
        }
      }
    },
    
    goHome() {
      // 清除購買結果
      localStorage.removeItem('purchase_result')
      this.$router.push('/')
    }
  }
}
</script>

<style scoped>
.result-card {
  max-width: 600px;
  margin: 40px auto;
  text-align: center;
}

.success-icon {
  font-size: 64px;
  color: #28a745;
  margin-bottom: 20px;
}

.error-icon {
  font-size: 64px;
  color: #dc3545;
  margin-bottom: 20px;
}

.success-result h2 {
  color: #28a745;
  margin-bottom: 24px;
}

.error-result h2 {
  color: #dc3545;
  margin-bottom: 24px;
}

.result-details {
  text-align: left;
  background-color: #f8f9fa;
  padding: 20px;
  border-radius: 8px;
  margin: 24px 0;
}

.result-details p {
  margin: 12px 0;
  font-size: 16px;
}

.success-message {
  font-size: 18px;
  color: #28a745;
  margin-top: 20px;
}

.error-message {
  font-size: 18px;
  color: #dc3545;
  margin: 20px 0;
}

.error-code {
  color: #666;
  font-size: 14px;
}

.actions {
  margin-top: 32px;
}

.btn {
  min-width: 200px;
}
</style>
