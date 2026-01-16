/**
 * API 服務層
 */
import axios from 'axios'

// 在 Docker 環境中，使用 vite proxy，所以 baseURL 保持為 '/api'
// vite proxy 會將請求轉發到後端服務
const api = axios.create({
  baseURL: '/api',
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json'
  }
})

// 請求攔截器
api.interceptors.request.use(
  config => {
    return config
  },
  error => {
    return Promise.reject(error)
  }
)

// 回應攔截器
api.interceptors.response.use(
  response => {
    return response.data
  },
  error => {
    if (error.response) {
      return Promise.reject(error.response.data)
    }
    return Promise.reject(error)
  }
)

export default {
  // 商品 API
  async getProducts() {
    return api.get('/products')
  },
  
  async getProduct(productId) {
    return api.get(`/products/${productId}`)
  },
  
  // 佇列 API
  async joinQueue(productId, turnstileToken) {
    return api.post('/queue/join', {
      product_id: productId,
      turnstile_token: turnstileToken
    })
  },
  
  async getQueueStatus(sessionId, productId) {
    return api.get('/queue/status', {
      params: {
        session_id: sessionId,
        product_id: productId
      }
    })
  },
  
  // 購買 API
  async purchase(productId, quantity, sessionId) {
    return api.post('/purchase', {
      product_id: productId,
      quantity: quantity,
      session_id: sessionId
    })
  },
  
  // 重置庫存 API
  async resetStock() {
    return api.post('/products/reset-stock')
  }
}
