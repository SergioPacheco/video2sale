<script setup lang="ts">
import { ref, onMounted } from 'vue'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import Button from 'primevue/button'
import Select from 'primevue/select'
import Dialog from 'primevue/dialog'
import Tag from 'primevue/tag'
import api from '../services/api'

const products = ref<any[]>([])
const selected = ref<any[]>([])
const loading = ref(false)
const importing = ref(false)
const country = ref('ES')
const period = ref(7)
const importResult = ref<any>(null)

// Detail modal
const detailVisible = ref(false)
const detail = ref<any>(null)
const detailLoading = ref(false)

const countryOptions = [
  { label: '🇪🇸 España', value: 'ES' },
  { label: '🇺🇸 USA', value: 'US' },
  { label: '🇬🇧 UK', value: 'GB' },
  { label: '🇫🇷 France', value: 'FR' },
  { label: '🇩🇪 Germany', value: 'DE' },
  { label: '🇧🇷 Brasil', value: 'BR' },
  { label: '🇲🇽 México', value: 'MX' },
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
  selected.value = []
  loading.value = false
}

async function openDetail(product: any) {
  detailLoading.value = true
  detailVisible.value = true
  detail.value = null
  const { data } = await api.get(`/tiktok-trending/detail/${product.category_id}`, {
    params: { name: product.name, country: country.value, period: period.value }
  })
  detail.value = data
  detailLoading.value = false

  // Carregar thumbnails em background
  for (const v of data.videos) {
    api.get(`/tiktok-trending/oembed/${v.id}`)
      .then(({ data: d }) => {
        v.thumbnail = d.thumbnail || ''
        v.title = d.title || ''
        v.author = d.author || ''
        detail.value = { ...detail.value }
      })
      .catch(() => {})
  }
}

async function importSelected() {
  if (!selected.value.length) return
  importing.value = true
  const indices = selected.value.map(p => p._index)
  const { data } = await api.post('/tiktok-trending/import', indices, {
    params: { country: country.value, period: period.value },
  })
  importResult.value = data
  importing.value = false
}

onMounted(loadTrending)
</script>

<template>
  <div>
    <div class="flex justify-between items-center mb-6">
      <div>
        <h2 class="text-2xl font-bold text-gray-900 dark:text-white">🔥 TikTok Trending</h2>
        <p class="text-sm text-gray-500 dark:text-gray-400">Produtos trending do TikTok Creative Center — dados públicos e gratuitos</p>
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
      <Button v-if="selected.length" :label="`Importar ${selected.length} producto(s)`" icon="pi pi-download" severity="success" :loading="importing" @click="importSelected" />
    </div>

    <!-- Resultado importação -->
    <div v-if="importResult" class="bg-green-50 dark:bg-green-900/30 border border-green-200 dark:border-green-700 rounded-lg p-3 mb-4">
      <p class="text-sm text-green-800 dark:text-green-300">✅ {{ importResult.imported }} producto(s) importado(s) al catálogo</p>
    </div>

    <!-- Tabela -->
    <DataTable :value="products" v-model:selection="selected" :loading="loading" dataKey="_index"
               stripedRows paginator :rows="20" size="small" sortField="popularity" :sortOrder="-1">
      <Column selectionMode="multiple" style="width: 3rem" />
      <Column field="name" header="Producto" sortable />
      <Column field="category" header="Categoría" sortable />
      <Column field="popularity" header="Posts" sortable style="width: 5rem">
        <template #body="{ data }">{{ (data.popularity / 1000).toFixed(0) }}K</template>
      </Column>
      <Column field="popularity_change" header="Δ" sortable style="width: 4rem">
        <template #body="{ data }">
          <span :class="data.popularity_change >= 0 ? 'text-green-600' : 'text-red-600'">
            {{ data.popularity_change >= 0 ? '+' : '' }}{{ data.popularity_change.toFixed(0) }}%
          </span>
        </template>
      </Column>
      <Column field="ctr" header="CTR" sortable style="width: 4rem">
        <template #body="{ data }">{{ data.ctr }}%</template>
      </Column>
      <Column field="cvr" header="CVR" sortable style="width: 4rem">
        <template #body="{ data }">{{ data.cvr }}%</template>
      </Column>
      <Column field="impressions" header="Impressões" sortable style="width: 6rem">
        <template #body="{ data }">{{ (data.impressions / 1000000).toFixed(0) }}M</template>
      </Column>
      <Column header="" style="width: 5rem">
        <template #body="{ data }">
          <Button icon="pi pi-info-circle" size="small" text @click="openDetail(data)" />
        </template>
      </Column>
    </DataTable>

    <!-- Modal de Detalhe -->
    <Dialog v-model:visible="detailVisible" :header="detail?.name || 'Cargando...'" modal style="width: 55rem">
      <div v-if="detailLoading" class="text-center py-8 text-gray-400">Cargando detalles...</div>
      <div v-else-if="detail" class="space-y-5">
        <!-- Métricas -->
        <div class="grid grid-cols-3 gap-4">
          <div class="bg-gray-50 dark:bg-gray-700 rounded-lg p-3 text-center">
            <p class="text-xs text-gray-500">CTR</p>
            <p class="text-xl font-bold">{{ detail.metrics.ctr }}%</p>
          </div>
          <div class="bg-gray-50 dark:bg-gray-700 rounded-lg p-3 text-center">
            <p class="text-xs text-gray-500">CVR</p>
            <p class="text-xl font-bold">{{ detail.metrics.cvr }}%</p>
          </div>
          <div class="bg-gray-50 dark:bg-gray-700 rounded-lg p-3 text-center">
            <p class="text-xs text-gray-500">CPA</p>
            <p class="text-xl font-bold">${{ detail.metrics.cpa }}</p>
          </div>
        </div>

        <!-- Hashtags -->
        <div v-if="detail.hashtags.length">
          <h4 class="text-sm font-semibold mb-2">🏷️ Hashtags populares</h4>
          <div class="flex flex-wrap gap-2">
            <Tag v-for="h in detail.hashtags" :key="h" :value="'#' + h" />
          </div>
        </div>

        <!-- Audience -->
        <div v-if="detail.audience_ages.length">
          <h4 class="text-sm font-semibold mb-2">👥 Audiencia por edad</h4>
          <div class="flex gap-3">
            <div v-for="age in detail.audience_ages" :key="age.ageLevel" class="text-center">
              <div class="bg-blue-100 dark:bg-blue-900 rounded h-16 w-10 flex items-end justify-center overflow-hidden">
                <div class="bg-blue-500 w-full" :style="{ height: age.score + '%' }"></div>
              </div>
              <p class="text-xs mt-1">{{ age.ageLevel }}+</p>
              <p class="text-xs text-gray-500">{{ age.score }}%</p>
            </div>
          </div>
        </div>

        <!-- Vídeos -->
        <div v-if="detail.videos.length">
          <h4 class="text-sm font-semibold mb-2">🎬 Vídeos de ejemplo ({{ detail.videos.length }})</h4>
          <div class="flex gap-3 overflow-x-auto pb-2">
            <a v-for="v in detail.videos" :key="v.id" :href="v.url" target="_blank"
               class="shrink-0 w-36 rounded-lg overflow-hidden border border-gray-200 dark:border-gray-600 hover:ring-2 hover:ring-blue-400 transition-all">
              <img v-if="v.thumbnail" :src="v.thumbnail" class="w-full h-48 object-cover" />
              <div v-else class="w-full h-48 bg-gray-200 dark:bg-gray-700 flex items-center justify-center">
                <span class="pi pi-video text-2xl text-gray-400"></span>
              </div>
              <div class="p-2">
                <p class="text-xs text-gray-600 dark:text-gray-300 line-clamp-2">{{ v.title || 'Ver vídeo' }}</p>
                <p v-if="v.author" class="text-xs text-gray-400 mt-1">@{{ v.author }}</p>
              </div>
            </a>
          </div>
        </div>
      </div>
    </Dialog>
  </div>
</template>
