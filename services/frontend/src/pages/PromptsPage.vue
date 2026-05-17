<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import Button from 'primevue/button'
import Dialog from 'primevue/dialog'
import InputText from 'primevue/inputtext'
import Textarea from 'primevue/textarea'
import Select from 'primevue/select'
import Tag from 'primevue/tag'
import api from '../services/api'

interface PromptTemplate {
  id: number
  type: string
  name: string
  content: string
  variables: string[]
  active: boolean
  created_at: string
  updated_at: string
}

const prompts = ref<PromptTemplate[]>([])
const loading = ref(false)
const dialogVisible = ref(false)
const editing = ref(false)

const form = ref({ id: 0, type: 'script_agent', name: '', content: '', variables: '' })

const typeOptions = [
  { label: 'Script Agent', value: 'script_agent' },
  { label: 'Compliance', value: 'compliance' },
  { label: 'Seedance Prompt', value: 'seedance_prompt' },
  { label: 'Runway Prompt', value: 'runway_prompt' },
  { label: 'TTS Instructions', value: 'tts_instructions' },
]

const typeLabels: Record<string, string> = {
  script_agent: 'Script Agent',
  compliance: 'Compliance',
  seedance_prompt: 'Seedance',
  runway_prompt: 'Runway',
  tts_instructions: 'TTS',
}

async function loadPrompts() {
  loading.value = true
  const { data } = await api.get('/prompts/')
  prompts.value = data
  loading.value = false
}

function openNew() {
  form.value = { id: 0, type: 'script_agent', name: '', content: '', variables: '' }
  editing.value = false
  dialogVisible.value = true
}

function openEdit(prompt: PromptTemplate) {
  form.value = {
    id: prompt.id,
    type: prompt.type,
    name: prompt.name,
    content: prompt.content,
    variables: prompt.variables.join(', '),
  }
  editing.value = true
  dialogVisible.value = true
}

async function save() {
  const payload = {
    type: form.value.type,
    name: form.value.name,
    content: form.value.content,
    variables: form.value.variables.split(',').map(v => v.trim()).filter(Boolean),
  }

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

onMounted(loadPrompts)
</script>

<template>
  <div>
    <div class="flex justify-between items-center mb-6">
      <h2 class="text-2xl font-bold text-gray-900">Prompt Templates</h2>
      <Button label="Nuevo Prompt" icon="pi pi-plus" @click="openNew" />
    </div>

    <DataTable :value="prompts" :loading="loading" stripedRows paginator :rows="10">
      <Column field="name" header="Nombre" sortable />
      <Column header="Tipo" sortable field="type">
        <template #body="{ data }">
          <Tag :value="typeLabels[data.type] || data.type" />
        </template>
      </Column>
      <Column header="Variables">
        <template #body="{ data }">
          <span class="text-sm text-gray-500">{{ data.variables.join(', ') || '—' }}</span>
        </template>
      </Column>
      <Column header="Acciones" style="width: 10rem">
        <template #body="{ data }">
          <div class="flex gap-2">
            <Button icon="pi pi-pencil" size="small" text @click="openEdit(data)" />
            <Button icon="pi pi-trash" size="small" text severity="danger" @click="deletePrompt(data.id)" />
          </div>
        </template>
      </Column>
    </DataTable>

    <!-- Dialog de criação/edição -->
    <Dialog v-model:visible="dialogVisible" :header="editing ? 'Editar Prompt' : 'Nuevo Prompt'" modal style="width: 50rem">
      <div class="flex flex-col gap-4 pt-4">
        <div class="flex gap-4">
          <div class="flex-1">
            <label class="block text-sm font-medium mb-1">Nombre</label>
            <InputText v-model="form.name" class="w-full" />
          </div>
          <div>
            <label class="block text-sm font-medium mb-1">Tipo</label>
            <Select v-model="form.type" :options="typeOptions" optionLabel="label" optionValue="value" class="w-48" />
          </div>
        </div>

        <div>
          <label class="block text-sm font-medium mb-1">Variables (separadas por coma)</label>
          <InputText v-model="form.variables" class="w-full" placeholder="product_name, category, visual" />
        </div>

        <div>
          <label class="block text-sm font-medium mb-1">Contenido del Prompt</label>
          <Textarea v-model="form.content" rows="12" class="w-full font-mono text-sm" />
        </div>
      </div>

      <template #footer>
        <Button label="Cancelar" text @click="dialogVisible = false" />
        <Button :label="editing ? 'Guardar' : 'Crear'" @click="save" />
      </template>
    </Dialog>
  </div>
</template>
