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

const statusLabels: Record<string, string> = {
  pending_creative: 'Pendiente',
  creative_generated: 'Roteiro generado',
  compliance_done: 'Compliance OK',
  human_selected: 'Listo',
  published: 'Publicado',
  error: 'Error',
}

const statusColors: Record<string, string> = {
  pending_creative: 'warn',
  creative_generated: 'info',
  compliance_done: 'info',
  human_selected: 'success',
  published: 'success',
  error: 'danger',
}

async function loadVideos() {
  loading.value = true
  const { data } = await api.get('/videos')
  // Enriquecer com dados do produto
  const { data: products } = await api.get('/products/?active=true')
  const productMap = Object.fromEntries(products.map((p: any) => [p.id, p]))
  videos.value = data.map((v: any) => ({
    ...v,
    product_name: productMap[v.product_id]?.name || `Producto #${v.product_id}`,
    product_category: productMap[v.product_id]?.category || '',
  }))
  loading.value = false
}

function downloadPack(videoId: number) {
  window.open(`/api/videos/${videoId}/download-pack`, '_blank')
}

function formatDate(iso: string) {
  return new Date(iso).toLocaleDateString('es-ES', { day: '2-digit', month: 'short' })
}

onMounted(loadVideos)
</script>

<template>
  <div>
    <div class="flex justify-between items-center mb-6">
      <h2 class="text-2xl font-bold text-gray-900 dark:text-white">Mis Roteiros</h2>
      <Button label="Crear nuevo" icon="pi pi-plus" size="small" @click="router.push('/workflow')" />
    </div>

    <DataTable :value="videos" :loading="loading" stripedRows paginator :rows="10" sortField="created_at" :sortOrder="-1">
      <Column field="product_name" header="Producto" sortable />
      <Column field="product_category" header="Categoría" sortable style="width: 8rem" />
      <Column field="week" header="Semana" sortable style="width: 6rem" />
      <Column header="Status" sortable field="status" style="width: 8rem">
        <template #body="{ data }">
          <Tag :value="statusLabels[data.status] || data.status" :severity="statusColors[data.status] || 'info'" />
        </template>
      </Column>
      <Column header="Fecha" sortable field="created_at" style="width: 5rem">
        <template #body="{ data }">
          <span class="text-sm text-gray-500">{{ formatDate(data.created_at) }}</span>
        </template>
      </Column>
      <Column header="Acciones" style="width: 10rem">
        <template #body="{ data }">
          <div class="flex gap-1">
            <Button icon="pi pi-eye" size="small" text @click="router.push(`/videos/${data.id}`)" v-tooltip="'Ver detalle'" />
            <Button v-if="data.status === 'human_selected'" icon="pi pi-download" size="small" text severity="success" @click="downloadPack(data.id)" v-tooltip="'Descargar pack'" />
          </div>
        </template>
      </Column>
    </DataTable>
  </div>
</template>
