import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    // === Core ===
    { path: '/', redirect: '/create' },
    { path: '/create', name: 'create', component: () => import('../pages/CreatePage.vue') },
    { path: '/videos', name: 'videos', component: () => import('../pages/VideosPage.vue') },
    { path: '/videos/:id', name: 'video-detail', component: () => import('../pages/VideoDetailPage.vue') },

    { path: '/products', name: 'products', component: () => import('../pages/ProductsPage.vue') },
  ],
})

export default router
