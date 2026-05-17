<script setup lang="ts">
import { ref, onMounted } from 'vue'
import Button from 'primevue/button'
import FileUpload from 'primevue/fileupload'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import Tag from 'primevue/tag'
import api from '../services/api'

const videos = ref<any[]>([])
const importResult = ref<any>(null)
const loading = ref(false)

async function loadPublishedVideos() {
  loading.value = true
  const { data } = await api.get('/videos', { params: { status: 'published' } })
  // Para cada vídeo, buscar métricas
  for (const v of data) {
    const { data: m } = await api.get(`/metrics/video/${v.id}`)
    v.metrics = m.metrics
    v.metrics_updated = m.updated_at
  }
  videos.value = data
  loading.value = false
}

async function onUpload(event: any) {
  const file = event.files[0]
  const formData = new FormData()
  formData.append('file', file)
  loading.value = true
  const { data } = await api.post('/metrics/import-sortfeed', formData)
  importResult.value = data
  await loadPublishedVideos()
  loading.value = false
}

onMounted(loadPublishedVideos)
</script>

<template>
  <div>
    <div class="flex justify-between items-center mb-6">
      <div>
        <h2 class="text-2xl font-bold text-gray-900 dark:text-white">Métricas</h2>
        <p class="text-sm text-gray-500 dark:text-gray-400">Importa datos de Sort Feed (Chrome extension) para rastrear performance.</p>
      </div>
      <FileUpload mode="basic" accept=".csv" :auto="true" @select="onUpload" chooseLabel="Importar Sort Feed CSV" />
    </div>

    <!-- Resultado da importação -->
    <div v-if="importResult" class="bg-green-50 dark:bg-green-900/30 border border-green-200 dark:border-green-700 rounded-lg p-4 mb-6">
      <p class="font-medium text-green-800 dark:text-green-300">✅ Importación completada</p>
      <p class="text-sm text-green-700 dark:text-green-400">
        {{ importResult.rows_in_csv }} filas en CSV · {{ importResult.videos_updated }} vídeos actualizados
      </p>
    </div>

    <!-- Como funciona -->
    <div class="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-700 rounded-lg p-4 mb-6">
      <h4 class="font-medium text-blue-800 dark:text-blue-300 mb-2">📋 Cómo importar métricas</h4>
      <ol class="text-sm text-blue-700 dark:text-blue-400 space-y-1 list-decimal list-inside">
        <li>Abre tu perfil de TikTok en Chrome</li>
        <li>Activa la extensión <strong>Sort Feed</strong></li>
        <li>Ordena tus vídeos y haz clic en <strong>Export</strong></li>
        <li>Sube el CSV aquí arriba</li>
      </ol>
      <p class="text-xs text-blue-600 dark:text-blue-500 mt-2">El sistema cruza por URL del vídeo (si la guardaste al publicar) o por caption.</p>
    </div>

    <!-- Tabela de vídeos com métricas -->
    <DataTable :value="videos" :loading="loading" stripedRows paginator :rows="10">
      <Column field="id" header="ID" style="width: 4rem" />
      <Column field="week" header="Semana" sortable />
      <Column header="Views">
        <template #body="{ data }">
          <span v-if="data.metrics?.views" class="font-mono">{{ data.metrics.views.toLocaleString() }}</span>
          <span v-else class="text-gray-400">—</span>
        </template>
      </Column>
      <Column header="Likes">
        <template #body="{ data }">
          <span v-if="data.metrics?.likes" class="font-mono">{{ data.metrics.likes.toLocaleString() }}</span>
          <span v-else class="text-gray-400">—</span>
        </template>
      </Column>
      <Column header="Comments">
        <template #body="{ data }">
          <span v-if="data.metrics?.comments" class="font-mono">{{ data.metrics.comments.toLocaleString() }}</span>
          <span v-else class="text-gray-400">—</span>
        </template>
      </Column>
      <Column header="Shares">
        <template #body="{ data }">
          <span v-if="data.metrics?.shares" class="font-mono">{{ data.metrics.shares.toLocaleString() }}</span>
          <span v-else class="text-gray-400">—</span>
        </template>
      </Column>
      <Column header="Saves">
        <template #body="{ data }">
          <span v-if="data.metrics?.saves" class="font-mono">{{ data.metrics.saves.toLocaleString() }}</span>
          <span v-else class="text-gray-400">—</span>
        </template>
      </Column>
      <Column header="Actualizado">
        <template #body="{ data }">
          <span v-if="data.metrics_updated" class="text-xs text-gray-500">{{ new Date(data.metrics_updated).toLocaleDateString() }}</span>
          <Tag v-else value="Sin datos" severity="warn" />
        </template>
      </Column>
    </DataTable>
  </div>
</template>
