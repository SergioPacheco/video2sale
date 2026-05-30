<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import Button from 'primevue/button'
import api from '../services/api'

const router = useRouter()
const stats = ref<any>(null)
const recentVideos = ref<any[]>([])
const products = ref<any[]>([])

async function loadData() {
  const [s, v, p] = await Promise.all([
    api.get('/stats/'),
    api.get('/videos'),
    api.get('/products/'),
  ])
  stats.value = s.data
  recentVideos.value = v.data.slice(0, 5)
  products.value = p.data.slice(0, 5)
}

onMounted(loadData)
</script>

<template>
  <div class="px-6 py-8 max-w-6xl mx-auto">
    <div class="flex justify-between items-center mb-8">
      <div>
        <h1 class="text-3xl font-bold text-gray-900 dark:text-white">Video2Sale</h1>
        <p class="text-gray-500 dark:text-gray-400">Producto → Vídeo TikTok en 1 clic</p>
      </div>
      <Button label="🚀 Crear Vídeo" @click="router.push('/create')" size="large" />
    </div>

    <!-- KPIs -->
    <div v-if="stats" class="grid grid-cols-2 md:grid-cols-5 gap-4 mb-8">
      <div class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-5 text-center">
        <p class="text-3xl font-bold text-blue-600">{{ stats.products }}</p>
        <p class="text-sm text-gray-500 mt-1">Productos</p>
      </div>
      <div class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-5 text-center">
        <p class="text-3xl font-bold text-green-600">{{ stats.videos }}</p>
        <p class="text-sm text-gray-500 mt-1">Vídeos</p>
      </div>
      <div class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-5 text-center">
        <p class="text-3xl font-bold text-purple-600">{{ stats.packs }}</p>
        <p class="text-sm text-gray-500 mt-1">Roteiros</p>
      </div>
      <div class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-5 text-center">
        <p class="text-3xl font-bold text-orange-600">{{ stats.prompts }}</p>
        <p class="text-sm text-gray-500 mt-1">Prompts</p>
      </div>
      <div class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-5 text-center">
        <p class="text-3xl font-bold text-gray-900 dark:text-white">${{ stats.cost?.toFixed(3) }}</p>
        <p class="text-sm text-gray-500 mt-1">Coste total</p>
      </div>
    </div>

    <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
      <!-- Últimos vídeos -->
      <div class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-5">
        <div class="flex justify-between items-center mb-4">
          <h3 class="font-semibold text-gray-900 dark:text-white">🎬 Últimos Vídeos</h3>
          <Button label="Ver todos" size="small" text @click="router.push('/videos')" />
        </div>
        <div v-if="recentVideos.length" class="space-y-3">
          <div v-for="v in recentVideos" :key="v.id"
               class="flex items-center justify-between p-3 rounded-lg bg-gray-50 dark:bg-gray-700 cursor-pointer hover:bg-gray-100 dark:hover:bg-gray-600"
               @click="router.push(`/videos/${v.id}`)">
            <div>
              <p class="text-sm font-medium dark:text-white">Vídeo #{{ v.id }}</p>
              <p class="text-xs text-gray-500">{{ v.week }} · {{ v.renderer }}</p>
            </div>
            <span class="text-xs px-2 py-1 rounded-full"
                  :class="v.status === 'rendered' ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-600'">
              {{ v.status }}
            </span>
          </div>
        </div>
        <p v-else class="text-gray-400 text-center py-6">Sin vídeos aún</p>
      </div>

      <!-- Top productos -->
      <div class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-5">
        <div class="flex justify-between items-center mb-4">
          <h3 class="font-semibold text-gray-900 dark:text-white">📦 Top Productos</h3>
          <Button label="Ver todos" size="small" text @click="router.push('/products')" />
        </div>
        <div v-if="products.length" class="space-y-3">
          <div v-for="p in products" :key="p.id"
               class="flex items-center gap-3 p-3 rounded-lg bg-gray-50 dark:bg-gray-700">
            <img v-if="p.image_url" :src="p.image_url" class="w-10 h-10 rounded object-cover" />
            <div v-else class="w-10 h-10 rounded bg-gray-200 dark:bg-gray-600 flex items-center justify-center">📦</div>
            <div class="flex-1 min-w-0">
              <p class="text-sm font-medium dark:text-white truncate">{{ p.name }}</p>
              <p class="text-xs text-gray-500">{{ p.category }}</p>
            </div>
            <span class="text-sm font-bold text-blue-600">{{ p.total_score }}</span>
          </div>
        </div>
        <p v-else class="text-gray-400 text-center py-6">Sin productos. <a href="/products" class="text-blue-500">Importar</a></p>
      </div>
    </div>

    <!-- Ações rápidas -->
    <div class="mt-8 grid grid-cols-1 md:grid-cols-3 gap-4">
      <div class="bg-gradient-to-br from-blue-50 to-blue-100 dark:from-blue-900/20 dark:to-blue-800/20 rounded-xl p-5 border border-blue-200 dark:border-blue-700 cursor-pointer hover:shadow-md transition-shadow"
           @click="router.push('/create')">
        <p class="text-2xl mb-2">🚀</p>
        <h4 class="font-semibold text-blue-900 dark:text-blue-200">Crear Vídeo</h4>
        <p class="text-sm text-blue-700 dark:text-blue-300">Pipeline completo: roteiro + audio + vídeo</p>
      </div>
      <div class="bg-gradient-to-br from-green-50 to-green-100 dark:from-green-900/20 dark:to-green-800/20 rounded-xl p-5 border border-green-200 dark:border-green-700 cursor-pointer hover:shadow-md transition-shadow"
           @click="router.push('/products')">
        <p class="text-2xl mb-2">📦</p>
        <h4 class="font-semibold text-green-900 dark:text-green-200">Importar Productos</h4>
        <p class="text-sm text-green-700 dark:text-green-300">CSV, manual o desde TikTok Shop</p>
      </div>
      <div class="bg-gradient-to-br from-purple-50 to-purple-100 dark:from-purple-900/20 dark:to-purple-800/20 rounded-xl p-5 border border-purple-200 dark:border-purple-700 cursor-pointer hover:shadow-md transition-shadow"
           @click="router.push('/trending')">
        <p class="text-2xl mb-2">🔥</p>
        <h4 class="font-semibold text-purple-900 dark:text-purple-200">Trending</h4>
        <p class="text-sm text-purple-700 dark:text-purple-300">Descubrir productos virales</p>
      </div>
    </div>
  </div>
</template>
