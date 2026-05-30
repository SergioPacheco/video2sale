<script setup lang="ts">
import { ref, onMounted } from 'vue'
import Button from 'primevue/button'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import Dialog from 'primevue/dialog'
import InputText from 'primevue/inputtext'
import Textarea from 'primevue/textarea'
import Select from 'primevue/select'
import Tag from 'primevue/tag'
import api from '../services/api'

// === Prompts ===
const prompts = ref<any[]>([])
const dialogVisible = ref(false)
const editing = ref(false)
const form = ref({ id: 0, type: '', name: '', content: '', variables: [] as string[] })
const newVar = ref('')

const promptTypes = [
  { label: 'Script Agent', value: 'script_agent' },
  { label: 'Compliance', value: 'compliance' },
  { label: 'Seedance Prompt', value: 'seedance_prompt' },
  { label: 'Runway Prompt', value: 'runway_prompt' },
  { label: 'TTS Instructions', value: 'tts_instructions' },
]

async function loadPrompts() {
  const { data } = await api.get('/prompts/')
  prompts.value = data
}

function openNew() {
  form.value = { id: 0, type: 'script_agent', name: '', content: '', variables: [] }
  editing.value = false
  dialogVisible.value = true
}

function openEdit(prompt: any) {
  form.value = { ...prompt, variables: prompt.variables || [] }
  editing.value = true
  dialogVisible.value = true
}

function addVariable() {
  if (newVar.value && !form.value.variables.includes(newVar.value)) {
    form.value.variables.push(newVar.value)
    newVar.value = ''
  }
}

function removeVariable(v: string) {
  form.value.variables = form.value.variables.filter(x => x !== v)
}

async function save() {
  const payload = { type: form.value.type, name: form.value.name, content: form.value.content, variables: form.value.variables }
  if (editing.value) {
    await api.put(`/prompts/${form.value.id}`, payload)
  } else {
    await api.post('/prompts/', payload)
  }
  dialogVisible.value = false
  await loadPrompts()
}

async function deletePrompt(id: number) {
  await api.delete(`/prompts/${id}`)
  await loadPrompts()
}

// === Stats ===
const stats = ref<any>(null)
async function loadStats() {
  const { data } = await api.get('/stats/')
  stats.value = data
}

// === Integrations ===
const integrations = ref<any[]>([])
async function loadIntegrations() {
  const { data } = await api.get('/integrations/')
  integrations.value = data
}

function connectTiktok() {
  window.open('/api/tiktok/login', '_self')
}

onMounted(async () => {
  await loadPrompts()
  await loadStats()
  await loadIntegrations()
})
</script>

<template>
  <div class="max-w-5xl mx-auto px-6 py-8">
    <h2 class="text-2xl font-bold text-gray-900 dark:text-white mb-6">Configuración</h2>

    <!-- Stats rápidos -->
    <div v-if="stats" class="grid grid-cols-2 md:grid-cols-5 gap-3 mb-8">
      <div class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-4 text-center">
        <p class="text-2xl font-bold text-gray-900 dark:text-white">{{ stats.products }}</p>
        <p class="text-xs text-gray-500">Productos</p>
      </div>
      <div class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-4 text-center">
        <p class="text-2xl font-bold text-gray-900 dark:text-white">{{ stats.videos }}</p>
        <p class="text-xs text-gray-500">Vídeos</p>
      </div>
      <div class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-4 text-center">
        <p class="text-2xl font-bold text-gray-900 dark:text-white">{{ stats.packs }}</p>
        <p class="text-xs text-gray-500">Roteiros</p>
      </div>
      <div class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-4 text-center">
        <p class="text-2xl font-bold text-gray-900 dark:text-white">{{ stats.prompts }}</p>
        <p class="text-xs text-gray-500">Prompts</p>
      </div>
      <div class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-4 text-center">
        <p class="text-2xl font-bold text-gray-900 dark:text-white">${{ stats.cost?.toFixed(2) }}</p>
        <p class="text-xs text-gray-500">Coste total</p>
      </div>
    </div>

    <!-- Conexões -->
    <div class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-5 mb-6">
      <h3 class="font-semibold text-gray-900 dark:text-white mb-4">🔌 Conexiones</h3>
      <div class="grid grid-cols-1 md:grid-cols-3 gap-3">
        <div v-for="integ in integrations" :key="integ.provider"
             class="flex items-center justify-between p-3 rounded-lg border border-gray-100 dark:border-gray-700">
          <div>
            <p class="font-medium text-sm capitalize">{{ integ.provider }}</p>
            <Tag :value="integ.status" :severity="integ.status === 'connected' ? 'success' : 'secondary'" class="text-xs" />
          </div>
          <Button v-if="integ.provider === 'tiktok' && integ.status !== 'connected'"
                  label="Conectar" size="small" @click="connectTiktok" />
        </div>
      </div>
    </div>

    <!-- Prompts -->
    <div class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-5">
      <div class="flex justify-between items-center mb-4">
        <h3 class="font-semibold text-gray-900 dark:text-white">📝 Prompt Templates</h3>
        <Button label="Nuevo" icon="pi pi-plus" size="small" @click="openNew" />
      </div>

      <DataTable :value="prompts" stripedRows size="small">
        <Column field="type" header="Tipo" style="width: 10rem">
          <template #body="{ data }">
            <Tag :value="data.type" />
          </template>
        </Column>
        <Column field="name" header="Nombre" />
        <Column header="Variables" style="width: 12rem">
          <template #body="{ data }">
            <span class="text-xs text-gray-500">{{ data.variables?.join(', ') || '—' }}</span>
          </template>
        </Column>
        <Column header="" style="width: 6rem">
          <template #body="{ data }">
            <div class="flex gap-1">
              <Button icon="pi pi-pencil" size="small" text @click="openEdit(data)" />
              <Button icon="pi pi-trash" size="small" text severity="danger" @click="deletePrompt(data.id)" />
            </div>
          </template>
        </Column>
      </DataTable>
    </div>

    <!-- Dialog -->
    <Dialog v-model:visible="dialogVisible" :header="editing ? 'Editar Prompt' : 'Nuevo Prompt'" modal style="width: 50rem">
      <div class="flex flex-col gap-4 pt-4">
        <div class="grid grid-cols-2 gap-4">
          <div>
            <label class="block text-sm font-medium mb-1">Tipo</label>
            <Select v-model="form.type" :options="promptTypes" optionLabel="label" optionValue="value" class="w-full" />
          </div>
          <div>
            <label class="block text-sm font-medium mb-1">Nombre</label>
            <InputText v-model="form.name" class="w-full" />
          </div>
        </div>
        <div>
          <label class="block text-sm font-medium mb-1">Contenido</label>
          <Textarea v-model="form.content" rows="12" class="w-full font-mono text-sm" />
        </div>
        <div>
          <label class="block text-sm font-medium mb-1">Variables</label>
          <div class="flex gap-2 flex-wrap mb-2">
            <Tag v-for="v in form.variables" :key="v" :value="v" removable @remove="removeVariable(v)" />
          </div>
          <div class="flex gap-2">
            <InputText v-model="newVar" placeholder="nombre_variable" class="flex-1" @keyup.enter="addVariable" />
            <Button icon="pi pi-plus" size="small" @click="addVariable" />
          </div>
        </div>
      </div>
      <template #footer>
        <Button label="Cancelar" text @click="dialogVisible = false" />
        <Button :label="editing ? 'Guardar' : 'Crear'" @click="save" :disabled="!form.name || !form.content" />
      </template>
    </Dialog>
  </div>
</template>
