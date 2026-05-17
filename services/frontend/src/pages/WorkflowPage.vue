<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import Button from 'primevue/button'
import Select from 'primevue/select'
import Textarea from 'primevue/textarea'
import InputText from 'primevue/inputtext'
import Tag from 'primevue/tag'
import api from '../services/api'

const products = ref<any[]>([])
const prompts = ref<any[]>([])
const selectedProductId = ref<number | null>(null)
const selectedPromptId = ref<number | null>(null)
const loading = ref(false)
const error = ref('')

// Resultado
const result = ref<any>(null)
const videoId = ref<number | null>(null)

// Asset inline add
const newAssetUrl = ref('')
const newAssetLabel = ref('')

const selectedProduct = computed(() => products.value.find(p => p.id === selectedProductId.value))

async function loadData() {
  const [{ data: prods }, { data: prms }] = await Promise.all([
    api.get('/products/'),
    api.get('/prompts/', { params: { type: 'script_agent' } }),
  ])
  products.value = prods
  prompts.value = prms
}

function addAsset() {
  if (!newAssetUrl.value || !selectedProduct.value) return
  selectedProduct.value.assets = selectedProduct.value.assets || []
  selectedProduct.value.assets.push({ url: newAssetUrl.value, type: 'image', label: newAssetLabel.value || 'Material' })
  // Salvar no backend
  api.put(`/products/${selectedProduct.value.id}`, { ...selectedProduct.value })
  newAssetUrl.value = ''
  newAssetLabel.value = ''
}

function removeAsset(index: number) {
  if (!selectedProduct.value) return
  selectedProduct.value.assets.splice(index, 1)
  api.put(`/products/${selectedProduct.value.id}`, { ...selectedProduct.value })
}

async function generate() {
  if (!selectedProductId.value) return
  loading.value = true
  error.value = ''
  result.value = null

  try {
    // 1. Criar vídeo
    const now = new Date()
    const weekNum = Math.ceil(((now.getTime() - new Date(now.getFullYear(), 0, 1).getTime()) / 86400000 + 1) / 7)
    const week = `${now.getFullYear()}-W${String(weekNum).padStart(2, '0')}`

    const { data: video } = await api.post('/videos', null, { params: { product_id: selectedProductId.value, week } })
    videoId.value = video.id

    // 2. Gerar roteiro
    const params: any = {}
    if (selectedPromptId.value) params.prompt_id = selectedPromptId.value
    const { data: packs } = await api.post(`/videos/${video.id}/generate-creative`, null, { params })

    // 3. Compliance automático
    const { data: checked } = await api.post(`/videos/${video.id}/compliance-check`)

    // 4. Selecionar o melhor (primeiro aprovado ou primeiro)
    const best = checked.find((p: any) => p.compliance_status === 'approved') || checked[0]
    if (best) {
      await api.post(`/videos/${video.id}/select-pack`, null, { params: { pack_id: best.id } })
    }

    result.value = {
      pack: best,
      allPacks: checked,
      videoId: video.id,
    }
  } catch (e: any) {
    error.value = e.response?.data?.detail || e.message || 'Error desconocido'
  }
  loading.value = false
}

function downloadPack() {
  if (videoId.value) {
    window.open(`/api/videos/${videoId.value}/download-pack`, '_blank')
  }
}

onMounted(loadData)
</script>

<template>
  <div>
    <h2 class="text-2xl font-bold text-gray-900 dark:text-white mb-6">🚀 Crear Roteiro</h2>

    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <!-- ESQUERDA: Input -->
      <div class="space-y-4">
        <!-- Produto -->
        <div class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-5">
          <h3 class="font-semibold mb-3 dark:text-white">📦 Producto</h3>
          <Select v-model="selectedProductId" :options="products" optionLabel="name" optionValue="id"
                  placeholder="Seleccionar producto..." filter class="w-full mb-3" />

          <div v-if="selectedProduct" class="text-sm space-y-2">
            <p class="text-gray-600 dark:text-gray-300"><strong>Categoría:</strong> {{ selectedProduct.category }}</p>
            <p v-if="selectedProduct.description" class="text-gray-600 dark:text-gray-300">{{ selectedProduct.description }}</p>
            <p v-if="selectedProduct.seller_name" class="text-gray-500"><strong>Tienda:</strong> {{ selectedProduct.seller_name }}</p>
            <p v-if="selectedProduct.commission_rate" class="text-gray-500"><strong>Comisión:</strong> {{ selectedProduct.commission_rate }}%</p>
          </div>
        </div>

        <!-- Assets -->
        <div v-if="selectedProduct" class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-5">
          <h3 class="font-semibold mb-3 dark:text-white">📎 Materiales</h3>
          <div v-if="selectedProduct.assets?.length" class="space-y-2 mb-3">
            <div v-for="(asset, i) in selectedProduct.assets" :key="i" class="flex items-center gap-2 text-sm">
              <Tag :value="asset.type" size="small" />
              <a :href="asset.url" target="_blank" class="text-blue-600 truncate flex-1 hover:underline">{{ asset.label || asset.url }}</a>
              <button @click="removeAsset(i)" class="text-red-400 hover:text-red-600 text-xs">✕</button>
            </div>
          </div>
          <div class="flex gap-2">
            <InputText v-model="newAssetUrl" placeholder="URL (imagen, video...)" class="flex-1" size="small" />
            <InputText v-model="newAssetLabel" placeholder="Nombre" class="w-28" size="small" />
            <Button icon="pi pi-plus" size="small" @click="addAsset" />
          </div>
        </div>

        <!-- Config -->
        <div class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-5">
          <h3 class="font-semibold mb-3 dark:text-white">⚙️ Configuración</h3>
          <div class="space-y-3">
            <div>
              <label class="text-sm text-gray-600 dark:text-gray-300">Prompt Template</label>
              <Select v-model="selectedPromptId" :options="prompts" optionLabel="name" optionValue="id"
                      placeholder="Default (TikTok Shop Estándar)" showClear class="w-full" />
            </div>
          </div>
        </div>

        <!-- Botão -->
        <Button label="🚀 Generar Roteiro" :loading="loading" @click="generate"
                :disabled="!selectedProductId" class="w-full !text-lg !py-3" />

        <p v-if="loading" class="text-sm text-gray-400 text-center">Generando 3 variaciones + compliance... (~30s)</p>
        <p v-if="error" class="text-sm text-red-500 text-center">❌ {{ error }}</p>
      </div>

      <!-- DIREITA: Resultado -->
      <div>
        <div v-if="!result && !loading" class="bg-gray-50 dark:bg-gray-800 rounded-xl border border-dashed border-gray-300 dark:border-gray-600 p-8 text-center">
          <p class="text-gray-400 text-lg">Selecciona un producto y haz clic en Generar</p>
          <p class="text-gray-300 text-sm mt-2">El roteiro aparecerá aquí</p>
        </div>

        <div v-if="result" class="space-y-4">
          <!-- Gancho -->
          <div class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-5">
            <div class="flex justify-between items-center mb-2">
              <h3 class="font-semibold dark:text-white">🎯 Gancho</h3>
              <Tag :value="result.pack.compliance_status" :severity="result.pack.compliance_status === 'approved' ? 'success' : 'warn'" />
            </div>
            <p class="text-lg text-gray-800 dark:text-gray-100">{{ result.pack.hook }}</p>
          </div>

          <!-- Escenas -->
          <div class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-5">
            <h3 class="font-semibold mb-3 dark:text-white">🎬 Escenas</h3>
            <div class="space-y-3">
              <div v-for="(scene, i) in result.pack.script_json || []" :key="i" class="border-l-3 border-blue-400 pl-3">
                <p class="text-xs text-gray-400 font-mono">{{ scene.start || 0 }}s – {{ scene.end || 0 }}s</p>
                <p v-if="scene.text" class="text-sm font-medium dark:text-white">📝 {{ scene.text }}</p>
                <p v-if="scene.voiceover" class="text-xs text-gray-600 dark:text-gray-300">🗣️ {{ scene.voiceover }}</p>
                <p v-if="scene.visual" class="text-xs text-gray-500 italic">🎥 {{ scene.visual }}</p>
              </div>
            </div>
          </div>

          <!-- Caption -->
          <div class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-5">
            <h3 class="font-semibold mb-2 dark:text-white">📱 Caption</h3>
            <p class="text-gray-700 dark:text-gray-200">{{ result.pack.caption }}</p>
            <p class="text-blue-600 mt-2">{{ result.pack.hashtags?.join(' ') }}</p>
          </div>

          <!-- Outras variações -->
          <div v-if="result.allPacks.length > 1" class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-5">
            <h3 class="font-semibold mb-2 dark:text-white">🔄 Otras variaciones ({{ result.allPacks.length - 1 }})</h3>
            <div v-for="pack in result.allPacks.filter(p => p.id !== result.pack.id)" :key="pack.id" class="border-b last:border-0 py-2">
              <p class="text-sm"><strong>Gancho:</strong> {{ pack.hook }}</p>
              <p class="text-xs text-gray-500">{{ pack.caption }}</p>
            </div>
          </div>

          <!-- Download -->
          <Button label="⬇️ Descargar Pack (ZIP)" icon="pi pi-download" @click="downloadPack" class="w-full" severity="success" />
        </div>
      </div>
    </div>
  </div>
</template>
