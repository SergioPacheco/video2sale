<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import Button from 'primevue/button'
import Tag from 'primevue/tag'
import Select from 'primevue/select'
import api from '../services/api'

const router = useRouter()
const videos = ref<any[]>([])
const products = ref<any[]>([])
const loading = ref(false)
const filterStatus = ref<string | null>(null)

const statusOptions = [
  { label: 'Todos', value: null },
  { label: '✅ Renderizados', value: 'rendered' },
  { label: '📤 Publicados', value: 'published' },
  { label: '⏳ En proceso', value: 'pending' },
  { label: '❌ Error', value: 'error' },
]

const filteredVideos = computed(() => {
  if (!filterStatus.value) return videos.value
  if (filterStatus.value === 'pending') {
    return videos.value.filter(v => !['rendered', 'published', 'error'].includes(v.status))
  }
  return videos.value.filter(v => v.status === filterStatus.value)
})

const statusConfig: Record<string, { label: string; severity: string; icon: string }> = {
  pending_creative: { label: 'Pendiente', severity: 'secondary', icon: '⏳' },
  creative_generated: { label: 'Roteiro', severity: 'info', icon: '✍️' },
  compliance_done: { label: 'Compliance', severity: 'info', icon: '🛡️' },
  human_selected: { label: 'Seleccionado', severity: 'warn', icon: '👤' },
  tts_generated: { label: 'Audio listo', severity: 'warn', icon: '🔊' },
  prompts_ready: { label: 'Prompts', severity: 'warn', icon: '🎬' },
  rendered: { label: 'Listo', severity: 'success', icon: '✅' },
  published: { label: 'Publicado', severity: 'success', icon: '📤' },
  error: { label: 'Error', severity: 'danger', icon: '❌' },
}

function getProductName(productId: number) {
  return products.value.find(p => p.id === productId)?.name || `#${productId}`
}

function getProductImage(productId: number) {
  const product = products.value.find(p => p.id === productId)
  return product?.image_url || null
}

function timeAgo(iso: string) {
  const diff = Date.now() - new Date(iso).getTime()
  const mins = Math.floor(diff / 60000)
  if (mins < 60) return `${mins}m`
  const hours = Math.floor(mins / 60)
  if (hours < 24) return `${hours}h`
  return `${Math.floor(hours / 24)}d`
}

async function loadData() {
  loading.value = true
  const [videosResp, productsResp] = await Promise.all([
    api.get('/videos'),
    api.get('/products/'),
  ])
  videos.value = videosResp.data
  products.value = productsResp.data
  loading.value = false
}

function downloadPack(videoId: number) {
  window.open(`/api/videos/${videoId}/download-pack`, '_blank')
}

async function publishVideo(videoId: number) {
  await api.post(`/videos/${videoId}/publish`, null, { params: { platform: 'tiktok' } })
  await loadData()
}

onMounted(loadData)
</script>

<template>
  <div class="px-6 py-8">
    <!-- Header -->
    <div class="flex justify-between items-center mb-6">
      <div>
        <h2 class="text-2xl font-bold text-gray-900 dark:text-white">Mis Vídeos</h2>
        <p class="text-sm text-gray-500 dark:text-gray-400">{{ videos.length }} vídeos generados</p>
      </div>
      <div class="flex items-center gap-3">
        <Select v-model="filterStatus" :options="statusOptions" optionLabel="label" optionValue="value" placeholder="Filtrar" class="w-44" />
        <Button label="+ Crear" @click="router.push('/')" size="small" />
      </div>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="text-center py-12 text-gray-400">Cargando...</div>

    <!-- Empty state -->
    <div v-else-if="!videos.length" class="text-center py-16">
      <div class="text-5xl mb-4">🎬</div>
      <h3 class="text-lg font-medium text-gray-900 dark:text-white mb-2">Sin vídeos aún</h3>
      <p class="text-gray-500 mb-4">Genera tu primer vídeo con un clic.</p>
      <Button label="Crear Vídeo" @click="router.push('/')" />
    </div>

    <!-- Grid de vídeos -->
    <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      <div v-for="video in filteredVideos" :key="video.id"
           class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 overflow-hidden hover:shadow-md transition-shadow cursor-pointer group"
           @click="router.push(`/videos/${video.id}`)">
        <!-- Thumbnail / Preview -->
        <div class="aspect-[9/16] max-h-48 bg-gray-100 dark:bg-gray-700 relative overflow-hidden">
          <img v-if="getProductImage(video.product_id)"
               :src="getProductImage(video.product_id)"
               class="w-full h-full object-cover group-hover:scale-105 transition-transform" />
          <div v-else class="w-full h-full flex items-center justify-center">
            <span class="text-4xl">{{ statusConfig[video.status]?.icon || '🎬' }}</span>
          </div>

          <!-- Status badge -->
          <div class="absolute top-2 right-2">
            <Tag :value="statusConfig[video.status]?.label || video.status"
                 :severity="statusConfig[video.status]?.severity || 'info'"
                 class="text-xs" />
          </div>

          <!-- Tempo -->
          <div class="absolute bottom-2 left-2 bg-black/60 text-white text-xs px-2 py-0.5 rounded">
            {{ timeAgo(video.created_at) }}
          </div>

          <!-- Renderer badge -->
          <div v-if="video.renderer" class="absolute bottom-2 right-2 bg-black/60 text-white text-xs px-2 py-0.5 rounded">
            {{ video.renderer }}
          </div>
        </div>

        <!-- Info -->
        <div class="p-3">
          <p class="font-medium text-gray-900 dark:text-white text-sm truncate">{{ getProductName(video.product_id) }}</p>
          <div class="flex justify-between items-center mt-1">
            <span class="text-xs text-gray-500">{{ video.week }}</span>
            <div class="flex gap-1">
              <Button v-if="video.status === 'rendered'" icon="pi pi-download" size="small" text
                      @click.stop="downloadPack(video.id)" v-tooltip="'Descargar'" />
              <Button v-if="video.status === 'rendered'" icon="pi pi-send" size="small" text severity="success"
                      @click.stop="publishVideo(video.id)" v-tooltip="'Marcar publicado'" />
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
