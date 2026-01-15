import { createRouter, createWebHistory } from 'vue-router'
import ProductList from './views/ProductList.vue'
import ProductDetail from './views/ProductDetail.vue'
import QueueStatus from './views/QueueStatus.vue'
import Purchase from './views/Purchase.vue'
import PurchaseResult from './views/PurchaseResult.vue'

const routes = [
  {
    path: '/',
    name: 'ProductList',
    component: ProductList
  },
  {
    path: '/products/:id',
    name: 'ProductDetail',
    component: ProductDetail
  },
  {
    path: '/queue/:productId',
    name: 'QueueStatus',
    component: QueueStatus
  },
  {
    path: '/purchase/:productId',
    name: 'Purchase',
    component: Purchase
  },
  {
    path: '/result',
    name: 'PurchaseResult',
    component: PurchaseResult
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router
