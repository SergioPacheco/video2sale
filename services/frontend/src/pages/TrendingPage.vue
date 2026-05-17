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
        <p class="text-sm text-gray-500 dark:text-gray-400">Produtos trending do TikTok Creative Center (dados públicos e gratuitos)</p>
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
      <Column field="likes" header="Likes" sortable style="width: 5rem">
        <template #body="{ data }">{{ (data.likes / 1000).toFixed(0) }}K</template>
      </Column>
      <Column field="impressions" header="Impressões" sortable style="width: 6rem">
        <template #body="{ data }">{{ (data.impressions / 1000000).toFixed(0) }}M</template>
      </Column>
      <Column field="view_rate_6s" header="6s View" sortable style="width: 5rem">
        <template #body="{ data }">{{ data.view_rate_6s }}%</template>
      </Column>
    </DataTable>
  </div>
</template>
