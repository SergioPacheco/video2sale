<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRoute } from 'vue-router'
import Button from 'primevue/button'
import Card from 'primevue/card'
import Tag from 'primevue/tag'
import Timeline from 'primevue/timeline'
import api from '../services/api'

const route = useRoute()
const video = ref<any>(null)
const loading = ref(false)
const generating = ref(false)

const videoId = computed(() => route.params.id)
const selectedPack = computed(() => video.value?.creative_packs?.find((p: any) => p.selected))

const storyboard = ref<any>(null)
const generatingStoryboard = ref(false)

async function loadVideo() {
  loading.value = true
  const { data } = await api.get(`/videos/${videoId.value}`)
  video.value = data
  loading.value = false
}

async function generateStoryboard() {
  generatingStoryboard.value = true
  const { data } = await api.post(`/storyboard/generate/${videoId.value}`, null, { params: { style: 'product_showcase' } })
  storyboard.value = data
  generatingStoryboard.value = false
}

async function generateCreative() {
  generating.value = true
  await api.post(`/videos/${videoId.value}/generate-creative`)
  await loadVideo()
  generating.value = false
}

async function runCompliance() {
  await api.post(`/videos/${videoId.value}/compliance-check`)
  await loadVideo()
}

async function selectPack(packId: number) {
  await api.post(`/videos/${videoId.value}/select-pack`, null, { params: { pack_id: packId } })
  await loadVideo()
}

async function generateTTS() {
  await api.post(`/videos/${videoId.value}/generate-tts`)
  await loadVideo()
}

async function generatePrompts(renderer: string) {
  await api.post(`/videos/${videoId.value}/generate-prompts`, null, { params: { renderer } })
  await loadVideo()
}

function eventIcon(type: string) {
  const icons: Record<string, string> = {
    product_ranked: 'pi pi-trophy',
    creative_generated: 'pi pi-sparkles',
    compliance_checked: 'pi pi-shield',
    human_selected_pack: 'pi pi-check-circle',
    tts_generated: 'pi pi-volume-up',
    prompts_generated: 'pi pi-video',
    published: 'pi pi-send',
    error: 'pi pi-exclamation-triangle',
  }
  return icons[type] || 'pi pi-circle'
}

function eventColor(type: string) {
  if (type === 'error') return '#ef4444'
  if (type.includes('human')) return '#8b5cf6'
  return '#3b82f6'
}

function formatDate(iso: string) {
  return new Date(iso).toLocaleString('es-ES', { dateStyle: 'short', timeStyle: 'short' })
}

onMounted(loadVideo)
</script>

<template>
  <div v-if="video">
    <div class="flex justify-between items-center mb-6">
      <div>
        <h2 class="text-2xl font-bold text-gray-900">Vídeo #{{ video.id }}</h2>
        <p class="text-sm text-gray-500">Semana {{ video.week }} · Renderer: {{ video.renderer }}</p>
      </div>
      <Tag :value="video.status" size="large" />
    </div>

    <!-- Info de prompts usados -->
    <div v-if="video.script_prompt_id || video.renderer_prompt_id" class="bg-purple-50 border border-purple-200 rounded-lg p-4 mb-6">
      <h4 class="text-sm font-semibold text-purple-800 mb-2">Prompts Utilizados</h4>
      <div class="flex gap-6 text-sm text-purple-700">
        <span v-if="video.script_prompt_id">📝 Script: #{{ video.script_prompt_id }}</span>
        <span v-if="video.renderer_prompt_id">🎬 Renderer: #{{ video.renderer_prompt_id }}</span>
      </div>
    </div>

    <!-- Ações do pipeline -->
    <div class="flex gap-3 mb-8">
      <Button v-if="video.status === 'pending_creative'" label="Gerar Roteiros" icon="pi pi-sparkles" :loading="generating" @click="generateCreative" />
      <Button v-if="video.status === 'creative_generated'" label="Verificar Compliance" icon="pi pi-shield" @click="runCompliance" />
      <Button v-if="video.status === 'human_selected'" label="Gerar Áudio" icon="pi pi-volume-up" @click="generateTTS" />
      <Button v-if="video.status === 'tts_generated'" label="Prompts Seedance" icon="pi pi-video" @click="generatePrompts('seedance')" />
      <Button v-if="video.status === 'tts_generated'" label="Prompts Runway" icon="pi pi-video" severity="secondary" @click="generatePrompts('runway')" />
      <Button v-if="video.status === 'rendered' || video.selected_creative_pack_id" label="📋 Storyboard Seedance" icon="pi pi-file" :loading="generatingStoryboard" @click="generateStoryboard" severity="help" />
      <Button v-if="video.status === 'rendered'" label="⬇️ Download Pack" icon="pi pi-download" @click="window.open(`/api/videos/${video.id}/download-pack`, '_blank')" severity="secondary" />
    </div>

    <!-- Storyboard Result -->
    <div v-if="storyboard" class="mb-8 bg-purple-50 dark:bg-purple-900/20 border border-purple-200 dark:border-purple-700 rounded-xl p-6">
      <h3 class="text-lg font-semibold mb-3 text-purple-800 dark:text-purple-200">📋 Prompt para Seedance/Dreamina</h3>
      <p class="text-xs text-purple-600 dark:text-purple-400 mb-3">Copie e cole no Seedance 2.0 (grátis no app)</p>
      <pre class="bg-white dark:bg-gray-800 rounded-lg p-4 text-sm overflow-x-auto whitespace-pre-wrap border">{{ storyboard.full_prompt }}</pre>
      <div class="mt-3 flex gap-2">
        <Button label="Copiar Prompt" icon="pi pi-copy" size="small" @click="navigator.clipboard.writeText(storyboard.full_prompt)" />
        <span class="text-xs text-purple-500 self-center">{{ storyboard.scenes }} cenas · {{ storyboard.images }} imagens</span>
      </div>
    </div>

    <!-- Preview del Vídeo -->
    <div v-if="selectedPack || video.video_path || video.voiceover_path" class="mb-8 bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-6">
      <h3 class="text-lg font-semibold mb-4 dark:text-white">🎬 Preview del Vídeo</h3>

      <!-- Video final (si existe) -->
      <div v-if="video.video_path" class="mb-4">
        <video controls class="w-full max-w-sm rounded-lg mx-auto bg-black aspect-[9/16]">
          <source :src="video.video_path" type="video/mp4" />
        </video>
      </div>

      <!-- Audio player -->
      <div v-if="video.voiceover_path" class="mb-4">
        <p class="text-sm text-gray-600 dark:text-gray-300 mb-2">🔊 Voiceover</p>
        <audio controls class="w-full">
          <source :src="video.voiceover_path" type="audio/mpeg" />
        </audio>
      </div>

      <!-- Storyboard (cenas do pack selecionado) -->
      <div v-if="selectedPack?.script_json?.length">
        <p class="text-sm text-gray-600 dark:text-gray-300 mb-3">📋 Storyboard ({{ selectedPack.script_json.length }} escenas)</p>
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
          <div v-for="(scene, i) in selectedPack.script_json" :key="i"
               class="border border-gray-200 dark:border-gray-600 rounded-lg p-3 bg-gray-50 dark:bg-gray-700">
            <div class="flex justify-between items-center mb-2">
              <span class="text-xs font-bold text-blue-600 dark:text-blue-400">{{ scene.start }}s – {{ scene.end }}s</span>
              <span class="text-xs text-gray-400">Escena {{ i + 1 }}</span>
            </div>
            <p v-if="scene.text" class="text-sm font-medium dark:text-white mb-1">📝 {{ scene.text }}</p>
            <p v-if="scene.voiceover" class="text-xs text-gray-600 dark:text-gray-300 mb-1">🗣️ {{ scene.voiceover }}</p>
            <p v-if="scene.visual" class="text-xs text-gray-500 dark:text-gray-400 italic">🎥 {{ scene.visual }}</p>
          </div>
        </div>
      </div>

      <!-- Caption + Hashtags -->
      <div v-if="selectedPack" class="mt-4 pt-4 border-t border-gray-200 dark:border-gray-600">
        <p v-if="selectedPack.caption" class="text-sm dark:text-gray-200"><strong>Caption:</strong> {{ selectedPack.caption }}</p>
        <p v-if="selectedPack.hashtags?.length" class="text-sm text-blue-600 dark:text-blue-400 mt-1">{{ selectedPack.hashtags.join(' ') }}</p>
      </div>
    </div>

    <!-- Creative Packs -->
    <div v-if="video.creative_packs?.length" class="mb-8">
      <h3 class="text-lg font-semibold mb-4">Roteiros Gerados</h3>
      <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card v-for="pack in video.creative_packs" :key="pack.id" :class="{ 'ring-2 ring-blue-500': pack.selected }">
          <template #title>
            Versão {{ pack.version }}
            <Tag v-if="pack.selected" value="Selecionado" severity="success" class="ml-2" />
          </template>
          <template #subtitle>{{ pack.hook }}</template>
          <template #content>
            <p class="text-sm text-gray-600 mb-2">{{ pack.caption }}</p>
            <Tag :value="pack.compliance_status" :severity="pack.compliance_status === 'approved' ? 'success' : 'warn'" />
            <p v-if="pack.compliance_notes" class="text-xs text-gray-500 mt-2">{{ pack.compliance_notes }}</p>
          </template>
          <template #footer>
            <Button v-if="video.status === 'compliance_done' && !pack.selected" label="Selecionar" size="small" @click="selectPack(pack.id)" />
          </template>
        </Card>
      </div>
    </div>

    <!-- Timeline de eventos -->
    <div v-if="video.events?.length">
      <h3 class="text-lg font-semibold mb-4">Timeline</h3>
      <Timeline :value="video.events" align="left">
        <template #marker="{ item }">
          <span class="flex items-center justify-center w-8 h-8 rounded-full" :style="{ backgroundColor: eventColor(item.event_type) + '20' }">
            <i :class="eventIcon(item.event_type)" :style="{ color: eventColor(item.event_type) }" />
          </span>
        </template>
        <template #content="{ item }">
          <div class="mb-4">
            <div class="flex items-center gap-2">
              <span class="font-medium text-sm">{{ item.event_type.replace(/_/g, ' ') }}</span>
              <Tag :value="item.actor" :severity="item.actor === 'human' ? 'warn' : 'info'" class="text-xs" />
            </div>
            <p class="text-xs text-gray-400">{{ formatDate(item.created_at) }}</p>
            <div v-if="item.details" class="mt-1 text-xs text-gray-500 bg-gray-50 rounded p-2 font-mono">
              <span v-if="item.details.prompt_id">prompt_id: {{ item.details.prompt_id }} · </span>
              <span v-if="item.details.model">model: {{ item.details.model }} · </span>
              <span v-if="item.details.renderer">renderer: {{ item.details.renderer }} · </span>
              <span v-if="item.details.variations">{{ item.details.variations }} variações · </span>
              <span v-if="item.details.characters">{{ item.details.characters }} chars · </span>
              <span v-if="item.details.score">score: {{ item.details.score }}</span>
            </div>
          </div>
        </template>
      </Timeline>
    </div>
  </div>
</template>
