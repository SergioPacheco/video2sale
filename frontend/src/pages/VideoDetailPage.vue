<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRoute } from 'vue-router'
import Button from 'primevue/button'
import Tag from 'primevue/tag'
import Timeline from 'primevue/timeline'
import api from '../services/api'

const route = useRoute()
const video = ref<any>(null)
const loading = ref(false)
const storyboard = ref<any>(null)
const generatingStoryboard = ref(false)

const videoId = computed(() => route.params.id)

async function loadVideo() {
  loading.value = true
  const { data } = await api.get(`/videos/${videoId.value}`)
  video.value = data
  loading.value = false
}

async function generateStoryboard() {
  generatingStoryboard.value = true
  const { data } = await api.post(`/storyboard/generate/${videoId.value}`)
  storyboard.value = data
  generatingStoryboard.value = false
}

function downloadPack() {
  globalThis.window.open(`/api/videos/${videoId.value}/download-pack`, '_blank')
}

function copyStoryboardPrompt() {
  if (storyboard.value?.full_prompt) {
    globalThis.navigator.clipboard.writeText(storyboard.value.full_prompt)
  }
}

function eventIcon(type: string) {
  const icons: Record<string, string> = {
    storyboard_generated: 'pi pi-file',
    prompts_generated: 'pi pi-video',
    video_rendered: 'pi pi-play',
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

function eventMarkerStyle(type: string) {
  return { backgroundColor: `${eventColor(type)}20` }
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

    <div class="flex gap-3 mb-8">
      <Button label="📋 Storyboard" icon="pi pi-file" :loading="generatingStoryboard" @click="generateStoryboard" severity="help" />
      <Button label="⬇️ Download Pack" icon="pi pi-download" @click="downloadPack" severity="secondary" />
    </div>

    <div v-if="storyboard" class="mb-8 bg-purple-50 dark:bg-purple-900/20 border border-purple-200 dark:border-purple-700 rounded-xl p-6">
      <h3 class="text-lg font-semibold mb-3 text-purple-800 dark:text-purple-200">📋 Prompt de vídeo</h3>
      <p class="text-xs text-purple-600 dark:text-purple-400 mb-3">Copie e use no fluxo gratuito local</p>
      <pre class="bg-white dark:bg-gray-800 rounded-lg p-4 text-sm overflow-x-auto whitespace-pre-wrap border">{{ storyboard.full_prompt }}</pre>
      <div class="mt-3 flex gap-2">
        <Button label="Copiar Prompt" icon="pi pi-copy" size="small" @click="copyStoryboardPrompt" />
        <span class="text-xs text-purple-500 self-center">{{ storyboard.scenes }} cenas · {{ storyboard.images }} imagens</span>
      </div>
    </div>

    <div v-if="video.video_path || video.voiceover_path" class="mb-8 bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-6">
      <h3 class="text-lg font-semibold mb-4 dark:text-white">🎬 Preview del Vídeo</h3>

      <div v-if="video.video_path" class="mb-4">
        <video controls class="w-full max-w-sm rounded-lg mx-auto bg-black aspect-[9/16]">
          <source :src="'/api' + video.video_path" type="video/mp4" />
        </video>
      </div>

      <div v-if="video.voiceover_path" class="mb-4">
        <p class="text-sm text-gray-600 dark:text-gray-300 mb-2">🔊 Voiceover</p>
        <audio controls class="w-full">
          <source :src="'/api' + video.voiceover_path" type="audio/mpeg" />
        </audio>
      </div>
    </div>

    <div v-if="video.creative_packs?.length" class="mb-8">
      <h3 class="text-lg font-semibold mb-4">Roteiros Gerados</h3>
      <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div v-for="pack in video.creative_packs" :key="pack.id"
             class="rounded-lg border border-gray-200 dark:border-gray-700 p-4"
             :class="{ 'ring-2 ring-blue-500': pack.selected }">
          <div class="flex items-center justify-between mb-2">
            <span class="font-semibold">Versão {{ pack.version }}</span>
            <Tag v-if="pack.selected" value="Selecionado" severity="success" />
          </div>
          <p v-if="pack.hook" class="text-sm font-medium mb-2">{{ pack.hook }}</p>
          <p v-if="pack.caption" class="text-sm text-gray-600 dark:text-gray-300 mb-2">{{ pack.caption }}</p>
          <p v-if="pack.hashtags?.length" class="text-xs text-blue-600 dark:text-blue-400">{{ pack.hashtags.join(' ') }}</p>
        </div>
      </div>
    </div>

    <div v-if="video.events?.length">
      <h3 class="text-lg font-semibold mb-4">Timeline</h3>
      <Timeline :value="video.events" align="left">
        <template #marker="{ item }">
          <span class="flex items-center justify-center w-8 h-8 rounded-full" :style="eventMarkerStyle(item.event_type)">
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
              <span v-if="item.details.renderer">renderer: {{ item.details.renderer }} · </span>
              <span v-if="item.details.scenes">scenes: {{ item.details.scenes }} · </span>
              <span v-if="item.details.images">images: {{ item.details.images }} · </span>
              <span v-if="item.details.score">score: {{ item.details.score }}</span>
            </div>
          </div>
        </template>
      </Timeline>
    </div>
  </div>
</template>
