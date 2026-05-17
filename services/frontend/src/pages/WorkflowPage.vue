<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import Stepper from 'primevue/stepper'
import StepList from 'primevue/steplist'
import StepPanels from 'primevue/steppanels'
import Step from 'primevue/step'
import StepPanel from 'primevue/steppanel'
import Button from 'primevue/button'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import Tag from 'primevue/tag'
import Select from 'primevue/select'
import InputText from 'primevue/inputtext'
import api from '../services/api'

// === State ===
const products = ref<any[]>([])
const selectedProductId = ref<number | null>(null)
const selectedProduct = computed(() => products.value.find(p => p.id === selectedProductId.value))
const winner = ref<any>(null)
const video = ref<any>(null)
const creativePacks = ref<any[]>([])
const selectedPackId = ref<number | null>(null)
const ttsResult = ref<any>(null)
const promptsResult = ref<any>(null)
const published = ref(false)
const loading = ref(false)

// Prompt selection + preview
const scriptPrompts = ref<any[]>([])
const rendererPrompts = ref<any[]>([])
const selectedScriptPromptId = ref<number | null>(null)
const selectedRendererPromptId = ref<number | null>(null)
const renderer = ref('seedance')
const showPreview = ref(false)
const previewContent = ref('')

// Publish
const tiktokUrl = ref('')

const rendererOptions = [
  { label: 'Seedance', value: 'seedance' },
  { label: 'Runway', value: 'runway' },
]

const week = computed(() => {
  const now = new Date()
  const start = new Date(now.getFullYear(), 0, 1)
  const weekNum = Math.ceil(((now.getTime() - start.getTime()) / 86400000 + start.getDay() + 1) / 7)
  return `${now.getFullYear()}-W${String(weekNum).padStart(2, '0')}`
})

// === Auto-advance ref ===
const activeStep = ref('1')

function advance(step: string) {
  activeStep.value = step
}

// === Preview logic ===
function buildPreview(promptId: number | null, prompts: any[], context: Record<string, string>) {
  if (!promptId) { showPreview.value = false; return }
  const tpl = prompts.find(p => p.id === promptId)
  if (!tpl) { showPreview.value = false; return }
  let content = tpl.content
  for (const [key, val] of Object.entries(context)) {
    content = content.replaceAll(`{{${key}}}`, val || `[${key}]`)
  }
  previewContent.value = content
  showPreview.value = true
}

watch(selectedScriptPromptId, (id) => {
  const product = winner.value?.product
  buildPreview(id, scriptPrompts.value, {
    product_name: product?.name || '[producto]',
    category: product?.category || '[categoría]',
    audience: 'Personas en España que buscan soluciones prácticas',
    pain: 'Problema que resuelve este producto',
    allowed_claims: 'Solo los que se pueden demostrar visualmente',
    restrictions: 'No inventar características',
  })
})

watch(selectedRendererPromptId, (id) => {
  const product = winner.value?.product
  buildPreview(id, rendererPrompts.value, {
    visual: '[descripción visual de la escena]',
    product_name: product?.name || '[producto]',
    category: product?.category || '[categoría]',
  })
})

// === Step 1: Load Products ===
async function loadProducts() {
  const { data } = await api.get('/products/')
  products.value = data
}

// === Step 1: Create Video ===
async function createVideo() {
  if (!selectedProductId.value) return
  loading.value = true
  const { data } = await api.post('/videos', null, { params: { product_id: selectedProductId.value, week: week.value } })
  video.value = data
  loading.value = false
  advance('2')
}

// === Step 3: Generate Creative ===
async function generateCreative() {
  if (!video.value) return
  loading.value = true
  const params: any = {}
  if (selectedScriptPromptId.value) params.prompt_id = selectedScriptPromptId.value
  const { data } = await api.post(`/videos/${video.value.id}/generate-creative`, null, { params })
  creativePacks.value = data
  loading.value = false
  showPreview.value = false
  advance('3')
}

// === Step 3: Compliance ===
async function runCompliance() {
  if (!video.value) return
  loading.value = true
  const { data } = await api.post(`/videos/${video.value.id}/compliance-check`)
  creativePacks.value = data
  loading.value = false
  advance('4')
}

// === Step 4: Select Pack ===
async function selectPack(packId: number) {
  if (!video.value) return
  await api.post(`/videos/${video.value.id}/select-pack`, null, { params: { pack_id: packId } })
  selectedPackId.value = packId
  creativePacks.value = creativePacks.value.map(p => ({ ...p, selected: p.id === packId }))
  advance('5')
}

// === Step 5: TTS ===
async function generateTTS() {
  if (!video.value) return
  loading.value = true
  const { data } = await api.post(`/videos/${video.value.id}/generate-tts`)
  ttsResult.value = data
  loading.value = false
  advance('6')
}

// === Step 6: Generate Prompts ===
async function generatePrompts() {
  if (!video.value) return
  loading.value = true
  const params: any = { renderer: renderer.value }
  if (selectedRendererPromptId.value) params.prompt_id = selectedRendererPromptId.value
  const { data } = await api.post(`/videos/${video.value.id}/generate-prompts`, null, { params })
  promptsResult.value = data
  loading.value = false
  showPreview.value = false
  advance('7')
}

// === Step 7: Publish ===
async function publishVideo() {
  if (!video.value) return
  loading.value = true
  const params: any = { platform: 'tiktok' }
  if (tiktokUrl.value) params.tiktok_url = tiktokUrl.value
  await api.post(`/videos/${video.value.id}/publish`, null, { params })
  published.value = true
  loading.value = false
}

// === Load prompts ===
async function loadPromptOptions() {
  const { data: script } = await api.get('/prompts/', { params: { type: 'script_agent' } })
  scriptPrompts.value = script
  const { data: seed } = await api.get('/prompts/', { params: { type: 'seedance_prompt' } })
  const { data: run } = await api.get('/prompts/', { params: { type: 'runway_prompt' } })
  rendererPrompts.value = [...seed, ...run]
}

onMounted(async () => {
  await loadProducts()
  await loadPromptOptions()
})
</script>

<template>
  <div>
    <h2 class="text-2xl font-bold text-gray-900 mb-6">Workflow — Crear Vídeo</h2>

    <Stepper :value="activeStep" linear>
      <StepList>
        <Step value="1">Producto</Step>
        <Step value="2">Roteiro</Step>
        <Step value="3">Compliance</Step>
        <Step value="4">Seleccionar</Step>
        <Step value="5">Audio</Step>
        <Step value="6">Prompts</Step>
        <Step value="7">Publicar</Step>
      </StepList>

      <StepPanels>
        <!-- Step 1: Seleccionar Producto -->
        <StepPanel v-slot="{ activateCallback }" value="1">
          <div class="p-4">
            <p class="text-gray-600 mb-4">Selecciona el producto para el vídeo de esta semana.</p>
            <div class="mb-4">
              <label class="block text-sm font-medium mb-1">Producto</label>
              <Select v-model="selectedProductId" :options="products" optionLabel="name" optionValue="id" placeholder="Elige un producto..." filter class="w-96" />
            </div>
            <div v-if="selectedProduct" class="bg-gray-50 dark:bg-gray-700 border rounded-lg p-4 mb-4">
              <p class="font-medium dark:text-white">{{ selectedProduct.name }}</p>
              <p class="text-sm text-gray-500">{{ selectedProduct.category }} · Score: {{ selectedProduct.total_score }} · €{{ selectedProduct.price || '—' }}</p>
              <div v-if="selectedProduct.assets?.length" class="mt-2">
                <p class="text-xs font-medium text-gray-500 mb-1">📎 Materiales:</p>
                <div class="flex flex-wrap gap-2">
                  <a v-for="(asset, i) in selectedProduct.assets" :key="i" :href="asset.url" target="_blank"
                     class="text-xs bg-blue-50 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300 px-2 py-1 rounded">
                    {{ asset.label || asset.type }}
                  </a>
                </div>
              </div>
            </div>
            <Button label="Crear Vídeo" icon="pi pi-video" :disabled="!selectedProductId" :loading="loading" @click="createVideo(); activateCallback('2')" />
          </div>
        </StepPanel>

        <!-- Step 2: Generate Creative -->
        <StepPanel v-slot="{ activateCallback }" value="2">
          <div class="p-4">
            <p class="text-gray-600 mb-4">Genera 3 variaciones de roteiro creativo.</p>
            <div class="flex gap-4 items-end mb-4">
              <div>
                <label class="block text-sm font-medium mb-1">Prompt Template</label>
                <Select v-model="selectedScriptPromptId" :options="scriptPrompts" optionLabel="name" optionValue="id" placeholder="Default (archivo .md)" showClear class="w-64" />
              </div>
              <Button label="Generar Roteiros" icon="pi pi-sparkles" :loading="loading" @click="generateCreative(); activateCallback('3')" />
            </div>
            <!-- Preview -->
            <div v-if="showPreview" class="bg-yellow-50 border border-yellow-200 rounded-lg p-4 mb-4">
              <p class="text-xs font-semibold text-yellow-700 mb-2">👁️ Preview del prompt (variables sustituidas):</p>
              <pre class="text-xs text-yellow-900 whitespace-pre-wrap font-mono max-h-48 overflow-auto">{{ previewContent }}</pre>
            </div>
            <DataTable v-if="creativePacks.length" :value="creativePacks" size="small">
              <Column field="version" header="V" style="width: 3rem" />
              <Column field="hook" header="Gancho" />
              <Column header="Status">
                <template #body="{ data }">
                  <Tag :value="data.compliance_status" :severity="data.compliance_status === 'approved' ? 'success' : 'warn'" />
                </template>
              </Column>
            </DataTable>
          </div>
        </StepPanel>

        <!-- Step 3: Compliance -->
        <StepPanel v-slot="{ activateCallback }" value="3">
          <div class="p-4">
            <p class="text-gray-600 mb-4">Valida los roteiros contra reglas de compliance.</p>
            <Button label="Verificar Compliance" icon="pi pi-shield" :loading="loading" @click="runCompliance(); activateCallback('4')" class="mb-4" />
            <DataTable v-if="creativePacks.length" :value="creativePacks" size="small">
              <Column field="version" header="V" style="width: 3rem" />
              <Column field="hook" header="Gancho" />
              <Column header="Status">
                <template #body="{ data }">
                  <Tag :value="data.compliance_status" :severity="data.compliance_status === 'approved' ? 'success' : data.compliance_status === 'adjusted' ? 'warn' : 'danger'" />
                </template>
              </Column>
              <Column field="compliance_notes" header="Notas" />
            </DataTable>
          </div>
        </StepPanel>

        <!-- Step 4: Select Pack -->
        <StepPanel v-slot="{ activateCallback }" value="4">
          <div class="p-4">
            <p class="text-gray-600 mb-4">Selecciona el roteiro para el vídeo.</p>
            <div class="space-y-3">
              <div v-for="pack in creativePacks" :key="pack.id"
                   class="border rounded-lg p-4 cursor-pointer transition-colors"
                   :class="pack.selected ? 'border-blue-500 bg-blue-50' : 'border-gray-200 hover:border-blue-300'"
                   @click="selectPack(pack.id); activateCallback('5')">
                <div class="flex justify-between items-center">
                  <span class="font-medium">Variación {{ pack.version }}</span>
                  <Tag v-if="pack.selected" value="✓" severity="success" />
                </div>
                <p class="text-sm text-gray-600 mt-1">{{ pack.hook }}</p>
                <p class="text-xs text-gray-400 mt-1">{{ pack.caption }}</p>
              </div>
            </div>
          </div>
        </StepPanel>

        <!-- Step 5: TTS -->
        <StepPanel v-slot="{ activateCallback }" value="5">
          <div class="p-4">
            <p class="text-gray-600 mb-4">Genera el audio de narración (voiceover).</p>
            <Button label="Generar Audio" icon="pi pi-volume-up" :loading="loading" @click="generateTTS(); activateCallback('6')" class="mb-4" />
            <div v-if="ttsResult" class="bg-blue-50 border border-blue-200 rounded-lg p-4">
              <p class="text-sm text-blue-800">✅ Audio generado: {{ ttsResult.characters }} caracteres</p>
              <p class="text-xs text-blue-600">{{ ttsResult.audio_path }}</p>
            </div>
          </div>
        </StepPanel>

        <!-- Step 6: Generate Prompts -->
        <StepPanel v-slot="{ activateCallback }" value="6">
          <div class="p-4">
            <p class="text-gray-600 mb-4">Genera prompts para el renderer de vídeo.</p>
            <div class="flex gap-4 items-end mb-4">
              <div>
                <label class="block text-sm font-medium mb-1">Renderer</label>
                <Select v-model="renderer" :options="rendererOptions" optionLabel="label" optionValue="value" class="w-40" />
              </div>
              <div>
                <label class="block text-sm font-medium mb-1">Prompt Template</label>
                <Select v-model="selectedRendererPromptId" :options="rendererPrompts" optionLabel="name" optionValue="id" placeholder="Default" showClear class="w-64" />
              </div>
              <Button label="Generar Prompts" icon="pi pi-video" :loading="loading" @click="generatePrompts(); activateCallback('7')" />
            </div>
            <!-- Preview -->
            <div v-if="showPreview" class="bg-yellow-50 border border-yellow-200 rounded-lg p-4 mb-4">
              <p class="text-xs font-semibold text-yellow-700 mb-2">👁️ Preview del prompt (variables sustituidas):</p>
              <pre class="text-xs text-yellow-900 whitespace-pre-wrap font-mono max-h-48 overflow-auto">{{ previewContent }}</pre>
            </div>
            <div v-if="promptsResult" class="space-y-2">
              <div v-for="(p, i) in promptsResult.prompts" :key="i" class="bg-gray-50 border rounded p-3">
                <p class="text-xs text-gray-500">Escena {{ i + 1 }} ({{ p.duration }}s)</p>
                <p class="text-sm font-mono">{{ p.prompt }}</p>
              </div>
            </div>
          </div>
        </StepPanel>

        <!-- Step 7: Publish -->
        <StepPanel value="7">
          <div class="p-4">
            <div v-if="!published">
              <p class="text-gray-600 mb-4">Publica el vídeo en TikTok y pega la URL aquí para rastrear métricas después.</p>
              <div class="mb-4 max-w-lg">
                <label class="block text-sm font-medium mb-1">URL del vídeo en TikTok</label>
                <InputText v-model="tiktokUrl" class="w-full" placeholder="https://www.tiktok.com/@tu_usuario/video/..." />
                <p class="text-xs text-gray-400 mt-1">Pega la URL después de publicar. Se usará para importar métricas de Sort Feed.</p>
              </div>
              <Button label="Marcar como Publicado" icon="pi pi-send" :loading="loading" @click="publishVideo" />
            </div>
            <div v-else class="text-center py-8">
              <p class="text-4xl mb-4">🎉</p>
              <h3 class="text-xl font-bold text-gray-900 mb-2">¡Publicado!</h3>
              <p class="text-gray-600">Vídeo registrado. Importa métricas desde <a href="/metrics" class="text-blue-600 underline">Sort Feed</a> cuando tengas datos.</p>
              <div v-if="promptsResult" class="mt-4 text-left max-w-md mx-auto bg-gray-50 rounded-lg p-4 text-sm">
                <p><strong>Producto:</strong> {{ promptsResult.product }}</p>
                <p><strong>Caption:</strong> {{ promptsResult.caption }}</p>
                <p><strong>Hashtags:</strong> {{ promptsResult.hashtags?.join(' ') }}</p>
              </div>
            </div>
          </div>
        </StepPanel>
      </StepPanels>
    </Stepper>
  </div>
</template>
