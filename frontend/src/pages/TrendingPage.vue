<script setup lang="ts">
import { ref, onMounted } from 'vue'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import Button from 'primevue/button'
import Select from 'primevue/select'
import Tag from 'primevue/tag'
import api from '../services/api'

const products = ref<any[]>([])
const selected = ref<any[]>([])
const loading = ref(false)
const importing = ref(false)
const country = ref('ES')
const period = ref(7)
const importResult = ref<any>(null)
const source = ref('')

const countryOptions = [
  { label: '🇪🇸 España', value: 'ES' },
  { label: '🇺🇸 USA', value: 'US' },
  { label: '🇬🇧 UK', value: 'GB' },
  { label: '🇫🇷 France', value: 'FR' },
  { label: '🇩🇪 Germany', value: 'DE' },
  { label: '🇧🇷 Brasil', value: 'BR' },
]

const periodOptions = [
  { label: '7 días', value: 7 },
  { label: '30 días', value: 30 },
]

async function loadTrending() {
  loading.value = true
  importResult.value = null
  const { data } = await api.get('/tiktok-trending/', { params: { country: country.value, period: period.value } })
  products.value = data.map((p: any, i: number) => ({ ...p, _index: i }))
  source.value = data.length > 0 ? data[0].source || '' : ''
  selected.value = []
  loading.value = false
}

async function importSelected() {
  if (!selected.value.length) return
  importing.value = true
  const indices = selected.value.map(p => p._index)
  try {
    const { data } = await api.post('/tiktok-trending/import', indices, {
      params: { country: country.value, period: period.value },
    })
    importResult.value = data
  } catch (e: any) {
    importResult.value = { error: e.response?.data?.detail || 'Error al importar' }
  }
  importing.value = false
}

onMounted(loadTrending)
</script>

<template>
  <div>
    <div class="flex justify-between items-center mb-6">
      <div>
        <h2 class="text-2xl font-bold text-gray-900 dark:text-white">🔥 Trending</h2>
        <p class="text-sm text-gray-500 dark:text-gray-400">
          <template v-if="source === 'tiktok_creative_center'">Datos del TikTok Creative Center</template>
          <template v-else>Top productos del catálogo local por score</template>
        </p>
      </div>
    </div>

    <!-- Filtros -->
    <div class="flex gap-4 items-end mb-4">
      <div>
        <label class="block text-sm font-medium mb-1">País</label>
        <Select v-model="country" :options="countryOptions" optionLabel="label" optionValue="value" class="w-44" />
      </div>
      <div>
        <label class="block text-sm font-medium mb-1">Período</label>
        <Select v-model="period" :options="periodOptions" optionLabel="label" optionValue="value" class="w-32" />
      </div>
      <Button label="Buscar" icon="pi pi-search" :loading="loading" @click="loadTrending" />
      <Button v-if="selected.length && source === 'tiktok_creative_center'" :label="`Importar ${selected.length}`" icon="pi pi-download" severity="success" :loading="importing" @click="importSelected" />
    </div>

    <!-- Resultado importação -->
    <div v-if="importResult?.imported" class="bg-green-50 dark:bg-green-900/30 border border-green-200 dark:border-green-700 rounded-lg p-3 mb-4">
      <p class="text-sm text-green-800 dark:text-green-300">✅ {{ importResult.imported }} producto(s) importado(s)</p>
    </div>
    <div v-if="importResult?.error" class="bg-yellow-50 dark:bg-yellow-900/30 border border-yellow-200 dark:border-yellow-700 rounded-lg p-3 mb-4">
      <p class="text-sm text-yellow-800 dark:text-yellow-300">⚠️ {{ importResult.error }}</p>
    </div>

    <!-- Info quando é catálogo local -->
    <div v-if="source === 'local_catalog' && products.length" class="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-700 rounded-lg p-3 mb-4">
      <p class="text-sm text-blue-800 dark:text-blue-300">ℹ️ TikTok Creative Center indisponível. Mostrando top productos del catálogo local.</p>
    </div>

    <!-- Tabela -->
    <DataTable :value="products" v-model:selection="selected" :loading="loading" dataKey="_index"
               stripedRows paginator :rows="20" size="small" sortField="total_score" :sortOrder="-1">
      <Column v-if="source === 'tiktok_creative_center'" selectionMode="multiple" style="width: 3rem" />
      <Column field="name" header="Producto" sortable />
      <Column field="category" header="Categoría" sortable />
      <Column v-if="source === 'local_catalog'" field="total_score" header="Score" sortable style="width: 5rem">
        <template #body="{ data }">
          <Tag :value="data.total_score?.toFixed(1)" severity="info" />
        </template>
      </Column>
      <Column v-if="source === 'tiktok_creative_center'" field="popularity" header="Posts" sortable style="width: 5rem">
        <template #body="{ data }">{{ (data.popularity / 1000).toFixed(0) }}K</template>
      </Column>
      <Column v-if="source === 'tiktok_creative_center'" field="ctr" header="CTR" sortable style="width: 4rem">
        <template #body="{ data }">{{ data.ctr }}%</template>
      </Column>
      <Column v-if="source === 'tiktok_creative_center'" field="cvr" header="CVR" sortable style="width: 4rem">
        <template #body="{ data }">{{ data.cvr }}%</template>
      </Column>
      <Column field="product_type" header="Fuente" style="width: 8rem">
        <template #body="{ data }">
          <Tag :value="data.product_type || data.source" :severity="data.source === 'local_catalog' ? 'secondary' : 'success'" />
        </template>
      </Column>
    </DataTable>

    <!-- Empty state -->
    <div v-if="!loading && !products.length" class="text-center py-12 text-gray-400">
      <p class="text-4xl mb-3">📦</p>
      <p>No hay productos. Importa via CSV en la página de Productos.</p>
    </div>
  </div>
</template>
