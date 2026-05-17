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
  price: null as number | null, notes: '',
  pain_score: 0, visual_score: 0, trend_score: 0, demo_score: 0, impulse_buy_score: 0,
  assets: [] as { url: string; type: string; label: string }[],
}
const form = ref({ ...emptyForm })

// Asset being added
const newAsset = ref({ url: '', type: 'image', label: '' })

async function loadProducts() {
  loading.value = true
  const { data } = await api.get('/products/')
  products.value = data
  loading.value = false
}

function openNew() {
  form.value = { ...emptyForm, assets: [] }
  editing.value = false
  dialogVisible.value = true
}

function openEdit(product: any) {
  form.value = { ...product, assets: product.assets || [] }
  editing.value = true
  dialogVisible.value = true
}

function addAsset() {
  if (!newAsset.value.url) return
  form.value.assets.push({ ...newAsset.value })
  newAsset.value = { url: '', type: 'image', label: '' }
}

function removeAsset(index: number) {
  form.value.assets.splice(index, 1)
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
    pain_score: form.value.pain_score,
    visual_score: form.value.visual_score,
    trend_score: form.value.trend_score,
    demo_score: form.value.demo_score,
    impulse_buy_score: form.value.impulse_buy_score,
    assets: form.value.assets,
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

    <DataTable :value="products" :loading="loading" stripedRows paginator :rows="10">
      <Column field="name" header="Nombre" sortable />
      <Column field="category" header="Categoría" sortable />
      <Column field="total_score" header="Score" sortable />
      <Column field="price" header="Precio" sortable>
        <template #body="{ data }">{{ data.price ? `€${data.price}` : '—' }}</template>
      </Column>
      <Column header="Assets">
        <template #body="{ data }">
          <Tag v-if="data.assets?.length" :value="`${data.assets.length} archivos`" severity="info" />
          <span v-else class="text-gray-400 text-sm">—</span>
        </template>
      </Column>
      <Column header="Acciones" style="width: 8rem">
        <template #body="{ data }">
          <div class="flex gap-2">
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

        <!-- Assets -->
        <div>
          <label class="block text-sm font-medium mb-2">📎 Materiales (imágenes, vídeos, links)</label>
          <div class="space-y-2 mb-3">
            <div v-for="(asset, i) in form.assets" :key="i" class="flex items-center gap-2 bg-gray-50 dark:bg-gray-700 rounded p-2">
              <Tag :value="asset.type" size="small" />
              <a :href="asset.url" target="_blank" class="text-sm text-blue-600 truncate flex-1">{{ asset.label || asset.url }}</a>
              <Button icon="pi pi-times" size="small" text severity="danger" @click="removeAsset(i)" />
            </div>
          </div>
          <div class="flex gap-2">
            <InputText v-model="newAsset.url" placeholder="URL del material" class="flex-1" />
            <InputText v-model="newAsset.label" placeholder="Etiqueta" class="w-32" />
            <select v-model="newAsset.type" class="border rounded px-2 py-1 text-sm">
              <option value="image">Imagen</option>
              <option value="video">Vídeo</option>
              <option value="reference">Referencia</option>
              <option value="music">Música</option>
            </select>
            <Button icon="pi pi-plus" size="small" @click="addAsset" />
          </div>
        </div>
      </div>

      <template #footer>
        <Button label="Cancelar" text @click="dialogVisible = false" />
        <Button :label="editing ? 'Guardar' : 'Crear'" @click="save" :disabled="!form.name || !form.category" />
      </template>
    </Dialog>
  </div>
</template>
