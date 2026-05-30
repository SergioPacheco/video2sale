import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    // === Core ===
    { path: '/', name: 'dashboard', component: () => import('../pages/DashboardPage.vue') },
    { path: '/create', name: 'create', component: () => import('../pages/CreatePage.vue') },
    { path: '/videos', name: 'videos', component: () => import('../pages/VideosPage.vue') },
    { path: '/videos/:id', name: 'video-detail', component: () => import('../pages/VideoDetailPage.vue') },

    // === Discovery ===
    { path: '/trending', name: 'trending', component: () => import('../pages/TrendingPage.vue') },
    { path: '/products', name: 'products', component: () => import('../pages/ProductsPage.vue') },

    // === Config ===
    { path: '/settings', name: 'settings', component: () => import('../pages/SettingsPage.vue') },

    // === Legacy (redirect) ===
    { path: '/dashboard', redirect: '/' },
  ],
})

export default router
