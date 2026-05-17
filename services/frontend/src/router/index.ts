import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', name: 'dashboard', component: () => import('../pages/DashboardPage.vue') },
    { path: '/workflow', name: 'workflow', component: () => import('../pages/WorkflowPage.vue') },
    { path: '/products', name: 'products', component: () => import('../pages/ProductsPage.vue') },
    { path: '/ranking', name: 'ranking', component: () => import('../pages/RankingPage.vue') },
    { path: '/videos', name: 'videos', component: () => import('../pages/VideosPage.vue') },
    { path: '/videos/:id', name: 'video-detail', component: () => import('../pages/VideoDetailPage.vue') },
    { path: '/prompts', name: 'prompts', component: () => import('../pages/PromptsPage.vue') },
    { path: '/metrics', name: 'metrics', component: () => import('../pages/MetricsPage.vue') },
  ],
})

export default router
