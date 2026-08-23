<script setup lang="ts">
import { ref, onMounted } from 'vue'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import Button from 'primevue/button'
import Dialog from 'primevue/dialog'
import InputText from 'primevue/inputtext'
import InputNumber from 'primevue/inputnumber'
import Textarea from 'primevue/textarea'
import FileUpload from 'primevue/fileupload'
import Tag from 'primevue/tag'
import api from '../services/api'

const products = ref<any[]>([])
const loading = ref(false)
const dialogVisible = ref(false)
const editing = ref(false)

const emptyForm = {
  id: 0, name: '', category: '', source: 'TikTok Shop',
  product_url: '', affiliate_url: '', image_url: '',
  price: null as number | null, notes: '', description: '',
  commission_rate: null as number | null, seller_name: '', seller_url: '',
  accepts_affiliates: false,
  pain_score: 0, visual_score: 0, trend_score: 0, demo_score: 0, impulse_buy_score: 0,
}
const form = ref({ ...emptyForm })

async function loadProducts() {
  loading.value = true
  const { data } = await api.get('/products/')
  products.value = data
  loading.value = false
}

function openNew() {
  form.value = { ...emptyForm }
  editing.value = false
  dialogVisible.value = true
}

function openEdit(product: any) {
  form.value = { ...product }
  editing.value = true
  dialogVisible.value = true
}

async function save() {
  const payload = {
    name: form.value.name,
    category: form.value.category,
    source: form.value.source,
    product_url: form.value.product_url || null,
    affiliate_url: form.value.affiliate_url || null,
    image_url: form.value.image_url || null,
    price: form.value.price,
    notes: form.value.notes || null,
    description: form.value.description || null,
    commission_rate: form.value.commission_rate,
    seller_name: form.value.seller_name || null,
    seller_url: form.value.seller_url || null,
    accepts_affiliates: form.value.accepts_affiliates,
    pain_score: form.value.pain_score,
    visual_score: form.value.visual_score,
    trend_score: form.value.trend_score,
    demo_score: form.value.demo_score,
    impulse_buy_score: form.value.impulse_buy_score,
  }
  if (editing.value) {
    await api.put(`/products/${form.value.id}`, payload)
  } else {
    await api.post('/products/', payload)
  }
  dialogVisible.value = false
  await loadProducts()
}

async function deleteProduct(id: number) {
  await api.delete(`/products/${id}`)
  await loadProducts()
}

async function fetchImages(id: number) {
  await api.post(`/products/${id}/fetch-images`)
  await loadProducts()
}

async function quickGenerate(id: number) {
  await api.post('/pipeline/free', null, { params: { product_id: id } })
  await loadProducts()
}

const importUrl = ref('')
const importingUrl = ref(false)

async function importFromUrl() {
  if (!importUrl.value) return
  importingUrl.value = true
  try {
    await api.post('/products/import-url', null, { params: { url: importUrl.value } })
    importUrl.value = ''
    await loadProducts()
  } catch (e: any) {
    alert(e.response?.data?.detail || 'Error al importar')
  }
  importingUrl.value = false
}

async function onUpload(event: any) {
  const file = event.files[0]
  const formData = new FormData()
  formData.append('file', file)
  await api.post('/products/import-csv', formData)
  await loadProducts()
}

onMounted(loadProducts)
</script>

<template>
  <div>
    <div class="flex justify-between items-center mb-6">
      <h2 class="text-2xl font-bold text-gray-900 dark:text-white">Productos</h2>
      <div class="flex gap-3">
        <FileUpload mode="basic" accept=".csv" :auto="true" @select="onUpload" chooseLabel="Importar CSV" />
        <Button label="Nuevo Producto" icon="pi pi-plus" @click="openNew" />
      </div>
    </div>

    <!-- Import por URL -->
    <div class="flex gap-2 mb-4">
      <InputText v-model="importUrl" placeholder="Pegar URL del producto (Amazon, AliExpress, TikTok Shop...)" class="flex-1" @keyup.enter="importFromUrl" />
      <Button label="Importar URL" icon="pi pi-link" :loading="importingUrl" @click="importFromUrl" :disabled="!importUrl" />
    </div>

    <DataTable :value="products" :loading="loading" stripedRows paginator :rows="10">
      <Column header="" style="width: 4rem">
        <template #body="{ data }">
          <img v-if="data.image_url" :src="data.image_url" class="w-10 h-10 rounded object-cover" />
          <div v-else class="w-10 h-10 rounded bg-gray-100 dark:bg-gray-700 flex items-center justify-center text-gray-400">📦</div>
        </template>
      </Column>
      <Column field="name" header="Nombre" sortable />
      <Column field="category" header="Categoría" sortable />
      <Column field="total_score" header="Score" sortable />
      <Column field="price" header="Precio" sortable>
        <template #body="{ data }">{{ data.price ? `€${data.price}` : '—' }}</template>
      </Column>
      <Column header="Afiliado" style="width: 5rem">
        <template #body="{ data }">
          <Tag v-if="data.accepts_affiliates" value="✓" severity="success" />
          <span v-else class="text-gray-400 text-sm">—</span>
        </template>
      </Column>
      <Column header="Acciones" style="width: 12rem">
        <template #body="{ data }">
          <div class="flex gap-1">
            <Button icon="pi pi-images" size="small" text v-tooltip="'Buscar imágenes'" @click="fetchImages(data.id)" />
            <Button icon="pi pi-video" size="small" text severity="success" v-tooltip="'Generar vídeo'" @click="quickGenerate(data.id)" />
            <Button icon="pi pi-pencil" size="small" text @click="openEdit(data)" />
            <Button icon="pi pi-trash" size="small" text severity="danger" @click="deleteProduct(data.id)" />
          </div>
        </template>
      </Column>
    </DataTable>

    <!-- Dialog CRUD -->
    <Dialog v-model:visible="dialogVisible" :header="editing ? 'Editar Producto' : 'Nuevo Producto'" modal style="width: 50rem">
      <div class="flex flex-col gap-4 pt-4">
        <!-- Básico -->
        <div class="grid grid-cols-2 gap-4">
          <div>
            <label class="block text-sm font-medium mb-1">Nombre *</label>
            <InputText v-model="form.name" class="w-full" />
          </div>
          <div>
            <label class="block text-sm font-medium mb-1">Categoría *</label>
            <InputText v-model="form.category" class="w-full" />
          </div>
        </div>

        <div class="grid grid-cols-3 gap-4">
          <div>
            <label class="block text-sm font-medium mb-1">Precio (€)</label>
            <InputNumber v-model="form.price" class="w-full" :min="0" mode="currency" currency="EUR" locale="es-ES" />
          </div>
          <div>
            <label class="block text-sm font-medium mb-1">URL Producto</label>
            <InputText v-model="form.product_url" class="w-full" placeholder="https://..." />
          </div>
          <div>
            <label class="block text-sm font-medium mb-1">URL Afiliado</label>
            <InputText v-model="form.affiliate_url" class="w-full" placeholder="https://..." />
          </div>
        </div>

        <!-- Afiliado -->
        <div class="grid grid-cols-4 gap-4">
          <div>
            <label class="block text-sm font-medium mb-1">Comisión (%)</label>
            <InputNumber v-model="form.commission_rate" class="w-full" :min="0" :max="80" suffix="%" />
          </div>
          <div>
            <label class="block text-sm font-medium mb-1">Seller / Tienda</label>
            <InputText v-model="form.seller_name" class="w-full" />
          </div>
          <div>
            <label class="block text-sm font-medium mb-1">URL Tienda</label>
            <InputText v-model="form.seller_url" class="w-full" placeholder="https://..." />
          </div>
          <div class="flex items-end pb-1">
            <label class="flex items-center gap-2 cursor-pointer">
              <input type="checkbox" v-model="form.accepts_affiliates" class="w-4 h-4" />
              <span class="text-sm">Acepta afiliados</span>
            </label>
          </div>
        </div>

        <!-- Descrição -->
        <div>
          <label class="block text-sm font-medium mb-1">Descripción del producto</label>
          <Textarea v-model="form.description" rows="3" class="w-full" placeholder="Descripción completa, beneficios, características..." />
        </div>

        <!-- Scores -->
        <div>
          <label class="block text-sm font-medium mb-2">Scores (0-10)</label>
          <div class="grid grid-cols-5 gap-3">
            <div>
              <label class="text-xs text-gray-500">Pain</label>
              <InputNumber v-model="form.pain_score" class="w-full" :min="0" :max="10" />
            </div>
            <div>
              <label class="text-xs text-gray-500">Visual</label>
              <InputNumber v-model="form.visual_score" class="w-full" :min="0" :max="10" />
            </div>
            <div>
              <label class="text-xs text-gray-500">Trend</label>
              <InputNumber v-model="form.trend_score" class="w-full" :min="0" :max="10" />
            </div>
            <div>
              <label class="text-xs text-gray-500">Demo</label>
              <InputNumber v-model="form.demo_score" class="w-full" :min="0" :max="10" />
            </div>
            <div>
              <label class="text-xs text-gray-500">Impulso</label>
              <InputNumber v-model="form.impulse_buy_score" class="w-full" :min="0" :max="10" />
            </div>
          </div>
        </div>

        <!-- Notas -->
        <div>
          <label class="block text-sm font-medium mb-1">Notas</label>
          <Textarea v-model="form.notes" rows="2" class="w-full" />
        </div>

      </div>

      <template #footer>
        <Button label="Cancelar" text @click="dialogVisible = false" />
        <Button :label="editing ? 'Guardar' : 'Crear'" @click="save" :disabled="!form.name || !form.category" />
      </template>
    </Dialog>
  </div>
</template>
