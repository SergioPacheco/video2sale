<script setup lang="ts">
import { ref, onMounted } from 'vue'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import Tag from 'primevue/tag'
import Button from 'primevue/button'
import { useRouter } from 'vue-router'
import api from '../services/api'

const router = useRouter()
const videos = ref<any[]>([])
const loading = ref(false)

const statusColors: Record<string, string> = {
  pending_creative: 'warn',
  creative_generated: 'info',
  compliance_done: 'info',
  human_selected: 'info',
  tts_generated: 'info',
  prompts_ready: 'success',
  approved: 'success',
  rejected: 'danger',
  error: 'danger',
}

async function loadVideos() {
  loading.value = true
  const { data } = await api.get('/videos')
  videos.value = data
  loading.value = false
}

onMounted(loadVideos)
</script>

<template>
  <div>
    <h2 class="text-2xl font-bold text-gray-900 mb-6">Vídeos</h2>

    <DataTable :value="videos" :loading="loading" stripedRows paginator :rows="10">
      <Column field="id" header="ID" />
      <Column field="week" header="Semana" sortable />
      <Column field="renderer" header="Renderer" />
      <Column header="Status">
        <template #body="{ data }">
          <Tag :value="data.status" :severity="statusColors[data.status] || 'info'" />
        </template>
      </Column>
      <Column header="Ações">
        <template #body="{ data }">
          <Button label="Ver" size="small" text @click="router.push(`/videos/${data.id}`)" />
        </template>
      </Column>
    </DataTable>
  </div>
</template>
