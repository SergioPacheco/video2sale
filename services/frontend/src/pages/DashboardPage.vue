<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import api from '../services/api'

const router = useRouter()
const stats = ref<any>(null)
const loading = ref(true)

async function loadStats() {
  loading.value = true
  const { data } = await api.get('/stats/')
  stats.value = data
  loading.value = false
}

function eventLabel(type: string) {
  const labels: Record<string, string> = {
    product_ranked: '🏆 Producto rankeado',
    creative_generated: '✨ Roteiro generado',
    compliance_checked: '🛡️ Compliance verificado',
    human_selected_pack: '👤 Pack seleccionado',
    tts_generated: '🔊 Audio generado',
    prompts_generated: '🎬 Prompts generados',
    published: '📤 Publicado',
  }
  return labels[type] || type
}

function timeAgo(iso: string) {
  const diff = Date.now() - new Date(iso).getTime()
  const mins = Math.floor(diff / 60000)
  if (mins < 60) return `hace ${mins}m`
  const hours = Math.floor(mins / 60)
  if (hours < 24) return `hace ${hours}h`
  return `hace ${Math.floor(hours / 24)}d`
}

onMounted(loadStats)
</script>

<template>
  <div>
    <div class="flex justify-between items-center mb-8">
      <h2 class="text-2xl font-bold text-gray-900">Dashboard</h2>
      <button @click="router.push('/workflow')" class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 text-sm font-medium">
        + Nuevo Vídeo
      </button>
    </div>

    <div v-if="loading" class="text-gray-400">Cargando...</div>

    <template v-if="stats">
      <!-- KPI Cards -->
      <div class="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
        <div class="bg-white rounded-xl border border-gray-200 p-5">
          <p class="text-sm text-gray-500">Productos</p>
          <p class="text-3xl font-bold text-gray-900">{{ stats.products }}</p>
        </div>
        <div class="bg-white rounded-xl border border-gray-200 p-5">
          <p class="text-sm text-gray-500">Vídeos</p>
          <p class="text-3xl font-bold text-gray-900">{{ stats.videos }}</p>
        </div>
        <div class="bg-white rounded-xl border border-gray-200 p-5">
          <p class="text-sm text-gray-500">Roteiros</p>
          <p class="text-3xl font-bold text-gray-900">{{ stats.packs }}</p>
        </div>
        <div class="bg-white rounded-xl border border-gray-200 p-5">
          <p class="text-sm text-gray-500">Coste Total</p>
          <p class="text-3xl font-bold text-gray-900">${{ stats.cost.toFixed(4) }}</p>
        </div>
      </div>

      <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
        <!-- Pipeline Status -->
        <div class="bg-white rounded-xl border border-gray-200 p-5">
          <h3 class="font-semibold text-gray-900 mb-4">Pipeline</h3>
          <div v-if="Object.keys(stats.status_counts).length" class="space-y-3">
            <div v-for="(count, status) in stats.status_counts" :key="status" class="flex justify-between items-center">
              <span class="text-sm text-gray-600">{{ (status as string).replace(/_/g, ' ') }}</span>
              <span class="text-sm font-mono font-medium bg-gray-100 px-2 py-0.5 rounded">{{ count }}</span>
            </div>
          </div>
          <p v-else class="text-sm text-gray-400">Sin vídeos aún. <a href="/workflow" class="text-blue-600 underline">Crear primero</a>.</p>
        </div>

        <!-- Actividad Reciente -->
        <div class="bg-white rounded-xl border border-gray-200 p-5">
          <h3 class="font-semibold text-gray-900 mb-4">Actividad Reciente</h3>
          <div v-if="stats.recent_events.length" class="space-y-3">
            <div v-for="event in stats.recent_events" :key="event.id" class="flex justify-between items-center">
              <div>
                <span class="text-sm">{{ eventLabel(event.event_type) }}</span>
                <span class="text-xs text-gray-400 ml-2">vídeo #{{ event.video_id }}</span>
              </div>
              <span class="text-xs text-gray-400">{{ timeAgo(event.created_at) }}</span>
            </div>
          </div>
          <p v-else class="text-sm text-gray-400">Sin actividad aún.</p>
        </div>

        <!-- Producción Semanal -->
        <div class="bg-white rounded-xl border border-gray-200 p-5">
          <h3 class="font-semibold text-gray-900 mb-4">Producción Semanal</h3>
          <div v-if="stats.weekly.length" class="space-y-2">
            <div v-for="w in stats.weekly" :key="w.week" class="flex items-center gap-3">
              <span class="text-sm text-gray-600 w-20">{{ w.week }}</span>
              <div class="flex-1 bg-gray-100 rounded-full h-5 overflow-hidden">
                <div class="bg-blue-500 h-full rounded-full" :style="{ width: Math.min(w.count * 20, 100) + '%' }"></div>
              </div>
              <span class="text-sm font-mono w-6 text-right">{{ w.count }}</span>
            </div>
          </div>
          <p v-else class="text-sm text-gray-400">Sin datos semanales.</p>
        </div>

        <!-- Quick Links -->
        <div class="bg-white rounded-xl border border-gray-200 p-5">
          <h3 class="font-semibold text-gray-900 mb-4">Accesos Rápidos</h3>
          <div class="grid grid-cols-2 gap-3">
            <a href="/workflow" class="flex items-center gap-2 p-3 rounded-lg bg-blue-50 hover:bg-blue-100 text-sm text-blue-700">
              🪄 Workflow
            </a>
            <a href="/products" class="flex items-center gap-2 p-3 rounded-lg bg-green-50 hover:bg-green-100 text-sm text-green-700">
              📦 Productos
            </a>
            <a href="/prompts" class="flex items-center gap-2 p-3 rounded-lg bg-purple-50 hover:bg-purple-100 text-sm text-purple-700">
              📝 Prompts ({{ stats.prompts }})
            </a>
            <a href="/videos" class="flex items-center gap-2 p-3 rounded-lg bg-orange-50 hover:bg-orange-100 text-sm text-orange-700">
              🎬 Vídeos
            </a>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>
