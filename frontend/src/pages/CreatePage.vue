<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import Button from 'primevue/button'
import Select from 'primevue/select'
import InputNumber from 'primevue/inputnumber'
import api from '../services/api'

const router = useRouter()

// State
const products = ref<any[]>([])
const selectedProductId = ref<number | null>(null)
const batchCount = ref(1)
const selectedLanguage = ref('es-ES')
const selectedEngine = ref('ffmpeg')
const generating = ref(false)
const result = ref<any>(null)
const error = ref<string | null>(null)
const progress = ref<string[]>([])

const languages = [
  { label: '🇬🇧 English', value: 'en-US' },
  { label: '🇪🇸 Español', value: 'es-ES' },
  { label: '🇧🇷 Português', value: 'pt-BR' },
  { label: '🇫🇷 Français', value: 'fr-FR' },
  { label: '🇩🇪 Deutsch', value: 'de-DE' },
]

const engines = [
  { label: '🎬 FFmpeg (grátis)', value: 'ffmpeg' },
  { label: '🤖 Seedance AI (~$1/vídeo)', value: 'seedance' },
]

// Actions
async function generate() {
  generating.value = true
  result.value = null
  error.value = null
  progress.value = ['Iniciando pipeline...']

  try {
    const params: any = { language: selectedLanguage.value, engine: selectedEngine.value }
    if (selectedProductId.value) params.product_id = selectedProductId.value

    if (batchCount.value > 1) {
      params.count = batchCount.value
      progress.value.push(`Generando ${batchCount.value} vídeos...`)
      const { data } = await api.post('/pipeline/batch', null, { params })
      result.value = data
      progress.value.push(`✅ ${data.completed}/${data.requested} vídeos generados`)
    } else {
      const { data } = await api.post('/pipeline/full', null, { params })
      result.value = data

      for (const step of data.steps || []) {
        if (step.step === 'product') progress.value.push(`📦 ${step.name}`)
        if (step.step === 'roteiro') progress.value.push(`✍️ ${step.packs} roteiros`)
        if (step.step === 'compliance') progress.value.push('🛡️ Compliance OK')
        if (step.step === 'pack_selected') progress.value.push(`🎯 "${step.hook}"`)
        if (step.step === 'tts') progress.value.push(`🔊 ${step.characters} chars`)
        if (step.step === 'rendered') progress.value.push(`🎬 ${step.duration?.toFixed(1)}s — listo!`)
      }

      if (data.status === 'ok') progress.value.push('✅ ¡Vídeo generado!')
    }
  } catch (e: any) {
    const detail = e.response?.data?.detail
    if (typeof detail === 'object') {
      error.value = detail.message
      for (const step of detail.steps || []) {
        progress.value.push(`${step.step === 'error' ? '❌' : '→'} ${step.step}`)
      }
    } else {
      error.value = detail || e.message
    }
  }

  generating.value = false
}

async function loadProducts() {
  const { data } = await api.get('/products/')
  products.value = data
}

onMounted(loadProducts)
</script>

<template>
  <div class="max-w-2xl mx-auto px-6 py-12">
    <!-- Header -->
    <div class="text-center mb-10">
      <h1 class="text-3xl font-bold text-gray-900 dark:text-white mb-2">Crear Vídeo</h1>
      <p class="text-gray-500 dark:text-gray-400">Producto → Roteiro → Audio → Vídeo MP4. Un clic.</p>
    </div>

    <!-- Card principal -->
    <div class="bg-white dark:bg-gray-800 rounded-2xl border border-gray-200 dark:border-gray-700 shadow-sm overflow-hidden">
      <!-- Producto -->
      <div class="p-6 border-b border-gray-100 dark:border-gray-700">
        <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Producto</label>
        <Select
          v-model="selectedProductId"
          :options="products"
          optionLabel="name"
          optionValue="id"
          placeholder="🤖 Automático (mejor score)"
          showClear
          filter
          class="w-full"
        >
          <template #option="{ option }">
            <div class="flex justify-between items-center w-full">
              <span class="font-medium">{{ option.name }}</span>
              <span class="text-xs font-mono text-blue-600">{{ option.total_score }}</span>
            </div>
          </template>
        </Select>
        <p class="text-xs text-gray-400 mt-1">Vacío = sistema elige el mejor producto.</p>
      </div>

      <!-- Cantidad -->
      <div class="p-6 border-b border-gray-100 dark:border-gray-700">
        <div class="flex items-center justify-between">
          <div>
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300">Idioma</label>
            <p class="text-xs text-gray-400">Idioma del roteiro y narración</p>
          </div>
          <Select
            v-model="selectedLanguage"
            :options="languages"
            optionLabel="label"
            optionValue="value"
            class="w-48"
          />
        </div>
      </div>

      <!-- Cantidad -->
      <div class="p-6 border-b border-gray-100 dark:border-gray-700">
        <div class="flex items-center justify-between">
          <div>
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300">Engine</label>
            <p class="text-xs text-gray-400">Motor de renderização</p>
          </div>
          <Select
            v-model="selectedEngine"
            :options="engines"
            optionLabel="label"
            optionValue="value"
            class="w-56"
          />
        </div>
      </div>

      <!-- Cantidad -->
      <div class="p-6 border-b border-gray-100 dark:border-gray-700">
        <div class="flex items-center justify-between">
          <div>
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300">Cantidad</label>
            <p class="text-xs text-gray-400">Top N productos por score</p>
          </div>
          <InputNumber v-model="batchCount" :min="1" :max="10" showButtons class="w-28" />
        </div>
      </div>

      <!-- Botão -->
      <div class="p-6 bg-gray-50 dark:bg-gray-800/50">
        <Button
          :label="generating ? 'Generando...' : batchCount > 1 ? `🚀 Generar ${batchCount} Vídeos` : '🚀 Generar Vídeo'"
          :loading="generating"
          @click="generate"
          class="w-full !text-lg !py-3"
          size="large"
        />
      </div>
    </div>

    <!-- Progress -->
    <div v-if="progress.length" class="mt-6 bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-5">
      <div class="space-y-2">
        <div v-for="(msg, i) in progress" :key="i" class="flex items-start gap-2">
          <div v-if="i === progress.length - 1 && generating" class="w-4 h-4 mt-0.5 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
          <div v-else class="w-4 h-4 mt-0.5 rounded-full bg-green-500 flex items-center justify-center">
            <svg class="w-2.5 h-2.5 text-white" fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clip-rule="evenodd"/></svg>
          </div>
          <span class="text-sm text-gray-600 dark:text-gray-300">{{ msg }}</span>
        </div>
      </div>
    </div>

    <!-- Error -->
    <div v-if="error" class="mt-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-700 rounded-xl p-4">
      <p class="text-sm text-red-700 dark:text-red-300">❌ {{ error }}</p>
    </div>

    <!-- Resultado -->
    <div v-if="result && !generating" class="mt-6 bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-700 rounded-xl p-6">
      <template v-if="result.video_id">
        <div class="flex items-center justify-between mb-3">
          <h3 class="text-lg font-semibold text-green-800 dark:text-green-200">✅ Vídeo Listo</h3>
          <Button label="Ver" icon="pi pi-eye" size="small" @click="router.push(`/videos/${result.video_id}`)" />
        </div>
        <div class="grid grid-cols-3 gap-3 text-sm">
          <div class="bg-white dark:bg-gray-800 rounded-lg p-3">
            <p class="text-xs text-gray-500">Producto</p>
            <p class="font-medium truncate">{{ result.product?.name }}</p>
          </div>
          <div class="bg-white dark:bg-gray-800 rounded-lg p-3">
            <p class="text-xs text-gray-500">Duración</p>
            <p class="font-medium">{{ result.duration?.toFixed(1) }}s</p>
          </div>
          <div class="bg-white dark:bg-gray-800 rounded-lg p-3">
            <p class="text-xs text-gray-500">Coste</p>
            <p class="font-medium">${{ result.total_cost?.toFixed(4) }}</p>
          </div>
        </div>
      </template>

      <template v-else-if="result.results">
        <h3 class="text-lg font-semibold text-green-800 dark:text-green-200 mb-2">
          ✅ {{ result.completed }}/{{ result.requested }} Vídeos
        </h3>
        <p class="text-sm text-green-700 dark:text-green-300">Coste: ${{ result.total_cost?.toFixed(4) }}</p>
      </template>
    </div>

    <!-- Stats -->
    <div class="mt-8 text-center text-xs text-gray-400">
      {{ products.length }} productos disponibles · ffmpeg render · ~30s por vídeo
    </div>
  </div>
</template>
