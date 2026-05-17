<script setup lang="ts">
import { ref, onMounted } from 'vue'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import Button from 'primevue/button'
import FileUpload from 'primevue/fileupload'
import api from '../services/api'
import type { Product } from '../types'

const products = ref<Product[]>([])
const loading = ref(false)

async function loadProducts() {
  loading.value = true
  const { data } = await api.get('/products/')
  products.value = data
  loading.value = false
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
      <h2 class="text-2xl font-bold text-gray-900">Produtos</h2>
      <FileUpload mode="basic" accept=".csv" :auto="true" @select="onUpload" chooseLabel="Importar CSV" />
    </div>

    <DataTable :value="products" :loading="loading" stripedRows paginator :rows="10">
      <Column field="name" header="Nome" sortable />
      <Column field="category" header="Categoria" sortable />
      <Column field="total_score" header="Score" sortable />
      <Column field="price" header="Preço" sortable />
      <Column field="source" header="Fonte" />
    </DataTable>
  </div>
</template>
