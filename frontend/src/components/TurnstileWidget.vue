<template>
  <div class="turnstile-widget">
    <div ref="turnstileContainer" id="turnstile-container"></div>
    <div v-if="error" class="error">{{ error }}</div>
  </div>
</template>

<script>
export default {
  name: 'TurnstileWidget',
  props: {
    siteKey: {
      type: String,
      default: '1x00000000000000000000AA' // 測試模式金鑰
    }
  },
  emits: ['verified', 'error'],
  data() {
    return {
      widgetId: null,
      error: null
    }
  },
  mounted() {
    this.loadTurnstile()
  },
  beforeUnmount() {
    if (this.widgetId && window.turnstile) {
      window.turnstile.remove(this.widgetId)
    }
  },
  methods: {
    loadTurnstile() {
      // 檢查 Turnstile 是否已載入
      if (window.turnstile) {
        this.initWidget()
      } else {
        // 等待 Turnstile 載入
        const checkInterval = setInterval(() => {
          if (window.turnstile) {
            clearInterval(checkInterval)
            this.initWidget()
          }
        }, 100)
        
        // 10 秒超時
        setTimeout(() => {
          clearInterval(checkInterval)
          if (!window.turnstile) {
            this.error = 'Turnstile 載入失敗，請重新整理頁面'
            this.$emit('error', 'LOAD_FAILED')
          }
        }, 10000)
      }
    },
    
    initWidget() {
      try {
        this.widgetId = window.turnstile.render(this.$refs.turnstileContainer, {
          sitekey: this.siteKey,
          callback: (token) => {
            this.error = null
            this.$emit('verified', token)
          },
          'error-callback': () => {
            this.error = 'Turnstile 驗證失敗，請重試'
            this.$emit('error', 'VERIFICATION_FAILED')
          },
          'expired-callback': () => {
            this.error = 'Turnstile 驗證已過期，請重新驗證'
            this.$emit('error', 'EXPIRED')
          }
        })
      } catch (error) {
        this.error = 'Turnstile 初始化失敗'
        this.$emit('error', 'INIT_FAILED')
      }
    },
    
    reset() {
      if (this.widgetId && window.turnstile) {
        window.turnstile.reset(this.widgetId)
      }
    }
  }
}
</script>

<style scoped>
.turnstile-widget {
  margin: 20px 0;
}

.error {
  color: #dc3545;
  margin-top: 10px;
  font-size: 14px;
}
</style>
