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
import { FilterMatchMode } from '@primevue/core/api'
import api from '../services/api'

// === State ===
const products = ref<any[]>([])
const selectedRow = ref<any>(null)
const filters = ref({ global: { value: null, matchMode: FilterMatchMode.CONTAINS } })
const video = ref<any>(null)
const creativePacks = ref<any[]>([])
const selectedPackId = ref<number | null>(null)
const selectedPack = computed(() => creativePacks.value.find(p => p.selected))
const loading = ref(false)

// Prompt selection + preview
const scriptPrompts = ref<any[]>([])
const selectedScriptPromptId = ref<number | null>(null)
const showPreview = ref(false)
const previewContent = ref('')

// Logs
const logs = ref<{time: string; msg: string; type: string}[]>([])
function addLog(msg: string, type = 'info') {
  const time = new Date().toLocaleTimeString('es-ES', { hour: '2-digit', minute: '2-digit', second: '2-digit' })
  logs.value.push({ time, msg, type })
}

const activeStep = ref('1')
function advance(step: string) { activeStep.value = step }

const week = computed(() => {
  const now = new Date()
  const start = new Date(now.getFullYear(), 0, 1)
  const weekNum = Math.ceil(((now.getTime() - start.getTime()) / 86400000 + start.getDay() + 1) / 7)
  return `${now.getFullYear()}-W${String(weekNum).padStart(2, '0')}`
})

// === Preview logic ===
watch(selectedScriptPromptId, (id) => {
  if (!id) { showPreview.value = false; return }
  const tpl = scriptPrompts.value.find(p => p.id === id)
  if (!tpl) { showPreview.value = false; return }
  const product = selectedRow.value
  let content = tpl.content
    .replaceAll('{{product_name}}', product?.name || '[producto]')
    .replaceAll('{{category}}', product?.category || '[categoría]')
    .replaceAll('{{audience}}', 'Personas en España que buscan soluciones prácticas')
    .replaceAll('{{pain}}', 'Problema que resuelve este producto')
    .replaceAll('{{allowed_claims}}', 'Solo los que se pueden demostrar visualmente')
    .replaceAll('{{restrictions}}', 'No inventar características')
  previewContent.value = content
  showPreview.value = true
})

// === Step 1: Load Products ===
async function loadProducts() {
  const { data } = await api.get('/products/')
  products.value = data
}

// === Step 1: Create Video ===
async function createVideo() {
  if (!selectedRow.value) return
  loading.value = true
  addLog(`Creando vídeo para: ${selectedRow.value.name}...`)
  try {
    const { data } = await api.post('/videos', null, { params: { product_id: selectedRow.value.id, week: week.value } })
    video.value = data
    addLog(`✓ Vídeo #${data.id} creado (semana ${week.value})`, 'success')
    advance('2')
  } catch (e: any) {
    addLog(`✗ Error: ${e.response?.data?.detail || e.message}`, 'error')
  }
  loading.value = false
}

// === Step 2: Generate Creative ===
async function generateCreative() {
  if (!video.value) return
  loading.value = true
  addLog('Generando roteiros con IA...')
  try {
    const params: any = {}
    if (selectedScriptPromptId.value) params.prompt_id = selectedScriptPromptId.value
    const { data } = await api.post(`/videos/${video.value.id}/generate-creative`, null, { params })
    creativePacks.value = data
    addLog(`✓ ${data.length} roteiros generados`, 'success')
    advance('3')
  } catch (e: any) {
    addLog(`✗ Error generando roteiros: ${e.response?.data?.detail || e.message}`, 'error')
  }
  loading.value = false
  showPreview.value = false
}

// === Step 3: Compliance ===
async function runCompliance() {
  if (!video.value) return
  loading.value = true
  addLog('Verificando compliance...')
  try {
    const { data } = await api.post(`/videos/${video.value.id}/compliance-check`)
    creativePacks.value = data
    addLog(`✓ Compliance verificado`, 'success')
    advance('4')
  } catch (e: any) {
    addLog(`✗ Error en compliance: ${e.response?.data?.detail || e.message}`, 'error')
  }
  loading.value = false
}

// === Step 4: Select Pack ===
async function selectPack(packId: number) {
  if (!video.value) return
  addLog(`Seleccionando roteiro...`)
  try {
    await api.post(`/videos/${video.value.id}/select-pack`, null, { params: { pack_id: packId } })
    selectedPackId.value = packId
    creativePacks.value = creativePacks.value.map(p => ({ ...p, selected: p.id === packId }))
    addLog('✓ Roteiro seleccionado', 'success')
    advance('5')
  } catch (e: any) {
    addLog(`✗ Error: ${e.response?.data?.detail || e.message}`, 'error')
  }
}

// === Step 5: Download Pack ===
function downloadPack() {
  if (!video.value) return
  addLog('Descargando pack...')
  window.open(`/api/videos/${video.value.id}/download-pack`, '_blank')
  addLog('✓ Pack descargado', 'success')
}

// === Load prompts ===
async function loadPromptOptions() {
  const { data: script } = await api.get('/prompts/', { params: { type: 'script_agent' } })
  scriptPrompts.value = script
}

onMounted(async () => {
  await loadProducts()
  await loadPromptOptions()
})
</script>

<template>
  <div>
    <h2 class="text-2xl font-bold text-gray-900 dark:text-white mb-6">Workflow — Crear Vídeo</h2>

    <Stepper :value="activeStep">
      <StepList>
        <Step value="1">Producto</Step>
        <Step value="2">Roteiro</Step>
        <Step value="3">Compliance</Step>
        <Step value="4">Seleccionar</Step>
        <Step value="5">Pack</Step>
      </StepList>

      <StepPanels>
        <!-- Step 1: Seleccionar Producto -->
        <StepPanel v-slot="{ activateCallback }" value="1">
          <div class="p-4">
            <p class="text-gray-600 mb-4">Selecciona el producto para el vídeo.</p>
            <DataTable :value="products" v-model:selection="selectedRow" selectionMode="single" dataKey="id"
                       :globalFilterFields="['name', 'category']" v-model:filters="filters"
                       stripedRows paginator :rows="8" size="small" sortField="total_score" :sortOrder="-1">
              <template #header>
                <InputText v-model="filters['global'].value" placeholder="Buscar producto..." class="w-64" />
              </template>
              <Column selectionMode="single" style="width: 3rem" />
              <Column field="name" header="Nombre" sortable />
              <Column field="category" header="Categoría" sortable />
              <Column field="total_score" header="Score" sortable style="width: 5rem" />
              <Column header="Assets" style="width: 5rem">
                <template #body="{ data }">
                  <Tag v-if="data.assets?.length" :value="data.assets.length" severity="info" />
                </template>
              </Column>
            </DataTable>
            <div class="flex items-center gap-4 mt-4">
              <Button label="Crear Vídeo" icon="pi pi-video" :disabled="!selectedRow" :loading="loading" @click="createVideo(); activateCallback('2')" />
              <span v-if="selectedRow" class="text-sm text-gray-500">Seleccionado: <strong>{{ selectedRow.name }}</strong></span>
            </div>
          </div>
        </StepPanel>

        <!-- Step 2: Generate Creative -->
        <StepPanel v-slot="{ activateCallback }" value="2">
          <div class="p-4">
            <p class="text-gray-600 mb-4">Genera 3 variaciones de roteiro creativo.</p>
            <div v-if="showPreview" class="bg-yellow-50 border border-yellow-200 rounded-lg p-4 mb-4">
              <p class="text-xs font-semibold text-yellow-700 mb-2">👁️ Preview del prompt:</p>
              <pre class="text-xs text-yellow-900 whitespace-pre-wrap font-mono max-h-48 overflow-auto">{{ previewContent }}</pre>
            </div>
            <div class="flex gap-4 items-end mb-4">
              <div>
                <label class="block text-sm font-medium mb-1">Prompt Template</label>
                <Select v-model="selectedScriptPromptId" :options="scriptPrompts" optionLabel="name" optionValue="id" placeholder="Default" showClear class="w-64" />
              </div>
              <Button label="Generar Roteiros" icon="pi pi-sparkles" :loading="loading" @click="generateCreative(); activateCallback('3')" />
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

        <!-- Step 5: Pack (resumo + download) -->
        <StepPanel value="5">
          <div class="p-4">
            <h3 class="text-lg font-semibold mb-4">📦 Pack de Materiales</h3>

            <!-- Resumo do roteiro selecionado -->
            <div v-if="selectedPack" class="space-y-4 mb-6">
              <div class="bg-gray-50 dark:bg-gray-800 rounded-lg p-4">
                <p class="text-sm font-semibold mb-2">🎯 Gancho</p>
                <p class="text-gray-700 dark:text-gray-200">{{ selectedPack.hook }}</p>
              </div>

              <div v-if="selectedPack.script_json?.length" class="bg-gray-50 dark:bg-gray-800 rounded-lg p-4">
                <p class="text-sm font-semibold mb-2">🎬 Escenas ({{ selectedPack.script_json.length }})</p>
                <div class="space-y-2">
                  <div v-for="(scene, i) in selectedPack.script_json" :key="i" class="border-l-2 border-blue-300 pl-3">
                    <p class="text-xs text-gray-400">{{ scene.start || 0 }}s – {{ scene.end || 0 }}s</p>
                    <p v-if="scene.text" class="text-sm">📝 {{ scene.text }}</p>
                    <p v-if="scene.voiceover" class="text-xs text-gray-600">🗣️ {{ scene.voiceover }}</p>
                    <p v-if="scene.visual" class="text-xs text-gray-500 italic">🎥 {{ scene.visual }}</p>
                  </div>
                </div>
              </div>

              <div class="bg-gray-50 dark:bg-gray-800 rounded-lg p-4">
                <p class="text-sm font-semibold mb-2">📱 Caption + Hashtags</p>
                <p class="text-gray-700 dark:text-gray-200">{{ selectedPack.caption }}</p>
                <p class="text-blue-600 mt-1">{{ selectedPack.hashtags?.join(' ') }}</p>
              </div>

              <!-- Assets do produto -->
              <div v-if="selectedRow?.assets?.length" class="bg-gray-50 dark:bg-gray-800 rounded-lg p-4">
                <p class="text-sm font-semibold mb-2">📎 Materiales del producto ({{ selectedRow.assets.length }})</p>
                <div class="space-y-1">
                  <a v-for="(asset, i) in selectedRow.assets" :key="i" :href="asset.url" target="_blank"
                     class="flex items-center gap-2 text-sm text-blue-600 hover:underline">
                    <Tag :value="asset.type" size="small" /> {{ asset.label || asset.url }}
                  </a>
                </div>
              </div>
            </div>

            <!-- Download -->
            <Button label="⬇️ Descargar Pack (ZIP)" icon="pi pi-download" size="large" @click="downloadPack" class="w-full" />
            <p class="text-xs text-gray-400 mt-2 text-center">Incluye: roteiro completo (JSON + TXT), caption, hashtags, y links de materiales.</p>
          </div>
        </StepPanel>
      </StepPanels>
    </Stepper>

    <!-- Log Panel -->
    <div v-if="logs.length" class="mt-6 border border-gray-200 dark:border-gray-700 rounded-lg overflow-hidden">
      <div class="flex justify-between items-center bg-gray-100 dark:bg-gray-800 px-4 py-2">
        <span class="text-xs font-semibold text-gray-600 dark:text-gray-300">📋 Log</span>
        <button @click="logs = []" class="text-xs text-gray-400 hover:text-red-500">Limpiar</button>
      </div>
      <div class="max-h-40 overflow-auto p-3 bg-gray-50 dark:bg-gray-900 font-mono text-xs space-y-1">
        <div v-for="(log, i) in logs" :key="i" :class="log.type === 'error' ? 'text-red-500' : log.type === 'success' ? 'text-green-600' : 'text-gray-500'">
          <span class="text-gray-400">{{ log.time }}</span> {{ log.msg }}
        </div>
      </div>
    </div>
  </div>
</template>
