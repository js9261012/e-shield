<template>
  <div class="product-list">
    <h2>商品列表</h2>
    
    <div v-if="loading" class="loading">載入中...</div>
    
    <div v-else-if="error" class="error">{{ error }}</div>
    
    <div v-else class="products-grid">
      <div
        v-for="product in products"
        :key="product.id"
        class="product-card card"
        @click="goToDetail(product.id)"
      >
        <img :src="product.image_url" :alt="product.name" class="product-image" />
        <h3>{{ product.name }}</h3>
        <p class="price">NT$ {{ formatPrice(product.price) }}</p>
        <p class="stock">剩餘庫存: {{ product.remaining_stock }} / {{ product.total_stock }}</p>
        <button class="btn btn-success" @click.stop="goToDetail(product.id)">
          購買
        </button>
      </div>
    </div>
  </div>
</template>

<script>
import api from '../services/api'

export default {
  name: 'ProductList',
  data() {
    return {
      products: [],
      loading: true,
      error: null
    }
  },
  mounted() {
    this.fetchProducts()
  },
  methods: {
    async fetchProducts() {
      try {
        this.loading = true
        const response = await api.getProducts()
        this.products = response.products
      } catch (error) {
        this.error = '載入商品失敗，請重新整理頁面'
        console.error('載入商品失敗:', error)
      } finally {
        this.loading = false
      }
    },
    
    goToDetail(productId) {
      this.$router.push(`/products/${productId}`)
    },
    
    formatPrice(price) {
      return (price / 100).toLocaleString('zh-TW')
    }
  }
}
</script>

<style scoped>
.products-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 20px;
  margin-top: 20px;
}

.product-card {
  cursor: pointer;
  transition: transform 0.2s, box-shadow 0.2s;
}

.product-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.product-image {
  width: 100%;
  height: 200px;
  object-fit: cover;
  border-radius: 4px;
  margin-bottom: 12px;
}

.product-card h3 {
  font-size: 20px;
  margin-bottom: 8px;
  color: #333;
}

.price {
  font-size: 24px;
  font-weight: bold;
  color: #007bff;
  margin-bottom: 8px;
}

.stock {
  color: #666;
  margin-bottom: 16px;
}
</style>
