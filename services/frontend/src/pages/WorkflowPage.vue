<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import Stepper from 'primevue/stepper'
import StepList from 'primevue/steplist'
import StepPanels from 'primevue/steppanels'
import Step from 'primevue/step'
import StepPanel from 'primevue/steppanel'
import Button from 'primevue/button'
import FileUpload from 'primevue/fileupload'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import Tag from 'primevue/tag'
import Select from 'primevue/select'
import api from '../services/api'

// === State ===
const products = ref<any[]>([])
const winner = ref<any>(null)
const video = ref<any>(null)
const creativePacks = ref<any[]>([])
const selectedPackId = ref<number | null>(null)
const ttsResult = ref<any>(null)
const promptsResult = ref<any>(null)
const loading = ref(false)

// Prompt selection
const scriptPrompts = ref<any[]>([])
const rendererPrompts = ref<any[]>([])
const selectedScriptPromptId = ref<number | null>(null)
const selectedRendererPromptId = ref<number | null>(null)
const renderer = ref('seedance')

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

// === Step 1: Import ===
async function loadProducts() {
  const { data } = await api.get('/products/')
  products.value = data
}

async function onUpload(event: any) {
  const file = event.files[0]
  const formData = new FormData()
  formData.append('file', file)
  await api.post('/products/import-csv', formData)
  await loadProducts()
}

// === Step 2: Ranking ===
async function runRanking() {
  loading.value = true
  const { data } = await api.post('/weekly-winner', { week: week.value })
  winner.value = data
  // Buscar o vídeo criado
  const { data: videos } = await api.get('/videos', { params: { week: week.value } })
  video.value = videos[0] || null
  loading.value = false
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
}

// === Step 4: Compliance ===
async function runCompliance() {
  if (!video.value) return
  loading.value = true
  const { data } = await api.post(`/videos/${video.value.id}/compliance-check`)
  creativePacks.value = data
  loading.value = false
}

// === Step 5: Select Pack ===
async function selectPack(packId: number) {
  if (!video.value) return
  await api.post(`/videos/${video.value.id}/select-pack`, null, { params: { pack_id: packId } })
  selectedPackId.value = packId
  creativePacks.value = creativePacks.value.map(p => ({ ...p, selected: p.id === packId }))
}

// === Step 6: TTS ===
async function generateTTS() {
  if (!video.value) return
  loading.value = true
  const { data } = await api.post(`/videos/${video.value.id}/generate-tts`)
  ttsResult.value = data
  loading.value = false
}

// === Step 7: Generate Prompts ===
async function generatePrompts() {
  if (!video.value) return
  loading.value = true
  const params: any = { renderer: renderer.value }
  if (selectedRendererPromptId.value) params.prompt_id = selectedRendererPromptId.value
  const { data } = await api.post(`/videos/${video.value.id}/generate-prompts`, null, { params })
  promptsResult.value = data
  loading.value = false
}

// === Load prompts for selection ===
async function loadPromptOptions() {
  const { data: script } = await api.get('/prompts/', { params: { type: 'script_agent' } })
  scriptPrompts.value = script
  const { data: rend } = await api.get('/prompts/', { params: { type: `${renderer.value}_prompt` } })
  rendererPrompts.value = rend
}

onMounted(async () => {
  await loadProducts()
  await loadPromptOptions()
})
</script>

<template>
  <div>
    <h2 class="text-2xl font-bold text-gray-900 mb-6">Workflow — Crear Vídeo</h2>

    <Stepper value="1" linear>
      <StepList>
        <Step value="1">Importar</Step>
        <Step value="2">Ranking</Step>
        <Step value="3">Roteiro</Step>
        <Step value="4">Compliance</Step>
        <Step value="5">Seleccionar</Step>
        <Step value="6">Audio</Step>
        <Step value="7">Prompts</Step>
        <Step value="8">Publicar</Step>
      </StepList>

      <StepPanels>
        <!-- Step 1: Import -->
        <StepPanel v-slot="{ activateCallback }" value="1">
          <div class="p-4">
            <p class="text-gray-600 mb-4">Importa productos desde CSV o Amazon para evaluar.</p>
            <FileUpload mode="basic" accept=".csv" :auto="true" @select="onUpload" chooseLabel="Importar CSV" class="mb-4" />
            <DataTable :value="products" stripedRows :rows="5" paginator size="small">
              <Column field="name" header="Producto" />
              <Column field="category" header="Categoría" />
              <Column field="total_score" header="Score" />
            </DataTable>
            <div class="flex justify-end mt-4">
              <Button label="Siguiente" icon="pi pi-arrow-right" iconPos="right" :disabled="!products.length" @click="activateCallback('2')" />
            </div>
          </div>
        </StepPanel>

        <!-- Step 2: Ranking -->
        <StepPanel v-slot="{ activateCallback }" value="2">
          <div class="p-4">
            <p class="text-gray-600 mb-4">Calcula scores y selecciona el producto ganador de la semana <strong>{{ week }}</strong>.</p>
            <Button label="Calcular Ranking" icon="pi pi-trophy" :loading="loading" @click="runRanking" class="mb-4" />
            <div v-if="winner" class="bg-green-50 border border-green-200 rounded-lg p-4">
              <p class="font-semibold text-green-800">🏆 Ganador: {{ winner.product.name }}</p>
              <p class="text-sm text-green-600">Score: {{ winner.score }} — {{ winner.reason }}</p>
            </div>
            <div class="flex justify-between mt-4">
              <Button label="Atrás" icon="pi pi-arrow-left" text @click="activateCallback('1')" />
              <Button label="Siguiente" icon="pi pi-arrow-right" iconPos="right" :disabled="!winner" @click="activateCallback('3')" />
            </div>
          </div>
        </StepPanel>

        <!-- Step 3: Generate Creative -->
        <StepPanel v-slot="{ activateCallback }" value="3">
          <div class="p-4">
            <p class="text-gray-600 mb-4">Genera 3 variaciones de roteiro creativo con IA.</p>
            <div class="flex gap-4 items-end mb-4">
              <div>
                <label class="block text-sm font-medium mb-1">Prompt Template (opcional)</label>
                <Select v-model="selectedScriptPromptId" :options="scriptPrompts" optionLabel="name" optionValue="id" placeholder="Usar default" showClear class="w-64" />
              </div>
              <Button label="Generar Roteiros" icon="pi pi-sparkles" :loading="loading" @click="generateCreative" />
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
            <div class="flex justify-between mt-4">
              <Button label="Atrás" icon="pi pi-arrow-left" text @click="activateCallback('2')" />
              <Button label="Siguiente" icon="pi pi-arrow-right" iconPos="right" :disabled="!creativePacks.length" @click="activateCallback('4')" />
            </div>
          </div>
        </StepPanel>

        <!-- Step 4: Compliance -->
        <StepPanel v-slot="{ activateCallback }" value="4">
          <div class="p-4">
            <p class="text-gray-600 mb-4">Valida los roteiros contra reglas de compliance.</p>
            <Button label="Verificar Compliance" icon="pi pi-shield" :loading="loading" @click="runCompliance" class="mb-4" />
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
            <div class="flex justify-between mt-4">
              <Button label="Atrás" icon="pi pi-arrow-left" text @click="activateCallback('3')" />
              <Button label="Siguiente" icon="pi pi-arrow-right" iconPos="right" @click="activateCallback('5')" />
            </div>
          </div>
        </StepPanel>

        <!-- Step 5: Select Pack -->
        <StepPanel v-slot="{ activateCallback }" value="5">
          <div class="p-4">
            <p class="text-gray-600 mb-4">Selecciona el roteiro que se usará para el vídeo.</p>
            <div class="space-y-3">
              <div v-for="pack in creativePacks" :key="pack.id"
                   class="border rounded-lg p-4 cursor-pointer transition-colors"
                   :class="pack.selected ? 'border-blue-500 bg-blue-50' : 'border-gray-200 hover:border-blue-300'"
                   @click="selectPack(pack.id)">
                <div class="flex justify-between items-center">
                  <span class="font-medium">Variación {{ pack.version }}</span>
                  <Tag v-if="pack.selected" value="Seleccionado" severity="success" />
                </div>
                <p class="text-sm text-gray-600 mt-1">{{ pack.hook }}</p>
              </div>
            </div>
            <div class="flex justify-between mt-4">
              <Button label="Atrás" icon="pi pi-arrow-left" text @click="activateCallback('4')" />
              <Button label="Siguiente" icon="pi pi-arrow-right" iconPos="right" :disabled="!selectedPackId" @click="activateCallback('6')" />
            </div>
          </div>
        </StepPanel>

        <!-- Step 6: TTS -->
        <StepPanel v-slot="{ activateCallback }" value="6">
          <div class="p-4">
            <p class="text-gray-600 mb-4">Genera el audio de narración (voiceover) con TTS.</p>
            <Button label="Generar Audio" icon="pi pi-volume-up" :loading="loading" @click="generateTTS" class="mb-4" />
            <div v-if="ttsResult" class="bg-blue-50 border border-blue-200 rounded-lg p-4">
              <p class="text-sm text-blue-800">✅ Audio generado: {{ ttsResult.characters }} caracteres</p>
              <p class="text-xs text-blue-600">{{ ttsResult.audio_path }}</p>
            </div>
            <div class="flex justify-between mt-4">
              <Button label="Atrás" icon="pi pi-arrow-left" text @click="activateCallback('5')" />
              <Button label="Siguiente" icon="pi pi-arrow-right" iconPos="right" :disabled="!ttsResult" @click="activateCallback('7')" />
            </div>
          </div>
        </StepPanel>

        <!-- Step 7: Generate Prompts -->
        <StepPanel v-slot="{ activateCallback }" value="7">
          <div class="p-4">
            <p class="text-gray-600 mb-4">Genera prompts optimizados para el renderer de vídeo.</p>
            <div class="flex gap-4 items-end mb-4">
              <div>
                <label class="block text-sm font-medium mb-1">Renderer</label>
                <Select v-model="renderer" :options="rendererOptions" optionLabel="label" optionValue="value" class="w-40" />
              </div>
              <div>
                <label class="block text-sm font-medium mb-1">Prompt Template (opcional)</label>
                <Select v-model="selectedRendererPromptId" :options="rendererPrompts" optionLabel="name" optionValue="id" placeholder="Usar default" showClear class="w-64" />
              </div>
              <Button label="Generar Prompts" icon="pi pi-video" :loading="loading" @click="generatePrompts" />
            </div>
            <div v-if="promptsResult" class="space-y-2">
              <div v-for="(p, i) in promptsResult.prompts" :key="i" class="bg-gray-50 border rounded p-3">
                <p class="text-xs text-gray-500">Escena {{ i + 1 }} ({{ p.duration }}s)</p>
                <p class="text-sm font-mono">{{ p.prompt }}</p>
                <p v-if="p.text_overlay" class="text-xs text-blue-600 mt-1">📝 {{ p.text_overlay }}</p>
              </div>
            </div>
            <div class="flex justify-between mt-4">
              <Button label="Atrás" icon="pi pi-arrow-left" text @click="activateCallback('6')" />
              <Button label="Siguiente" icon="pi pi-arrow-right" iconPos="right" :disabled="!promptsResult" @click="activateCallback('8')" />
            </div>
          </div>
        </StepPanel>

        <!-- Step 8: Publish -->
        <StepPanel v-slot="{ activateCallback }" value="8">
          <div class="p-4">
            <div class="text-center py-8">
              <p class="text-4xl mb-4">🎉</p>
              <h3 class="text-xl font-bold text-gray-900 mb-2">¡Vídeo listo para publicar!</h3>
              <p class="text-gray-600">Todos los assets están generados. Publica manualmente en TikTok Shop.</p>
              <div v-if="promptsResult" class="mt-4 text-left max-w-md mx-auto bg-gray-50 rounded-lg p-4 text-sm">
                <p><strong>Producto:</strong> {{ promptsResult.product }}</p>
                <p><strong>Gancho:</strong> {{ promptsResult.hook }}</p>
                <p><strong>Caption:</strong> {{ promptsResult.caption }}</p>
                <p><strong>Hashtags:</strong> {{ promptsResult.hashtags?.join(' ') }}</p>
              </div>
            </div>
            <div class="flex justify-start mt-4">
              <Button label="Atrás" icon="pi pi-arrow-left" text @click="activateCallback('7')" />
            </div>
          </div>
        </StepPanel>
      </StepPanels>
    </Stepper>
  </div>
</template>
