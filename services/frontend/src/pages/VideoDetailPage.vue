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

async function loadVideo() {
  loading.value = true
  const { data } = await api.get(`/videos/${videoId.value}`)
  video.value = data
  loading.value = false
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

onMounted(loadVideo)
</script>

<template>
  <div v-if="video">
    <div class="flex justify-between items-center mb-6">
      <h2 class="text-2xl font-bold text-gray-900">Vídeo #{{ video.id }}</h2>
      <Tag :value="video.status" size="large" />
    </div>

    <!-- Ações do pipeline -->
    <div class="flex gap-3 mb-8">
      <Button v-if="video.status === 'pending_creative'" label="Gerar Roteiros" :loading="generating" @click="generateCreative" />
      <Button v-if="video.status === 'creative_generated'" label="Verificar Compliance" @click="runCompliance" />
      <Button v-if="video.status === 'human_selected'" label="Gerar Áudio" @click="generateTTS" />
      <Button v-if="video.status === 'tts_generated'" label="Gerar Prompts (Seedance)" @click="generatePrompts('seedance')" />
      <Button v-if="video.status === 'tts_generated'" label="Gerar Prompts (Runway)" severity="secondary" @click="generatePrompts('runway')" />
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
          </template>
          <template #footer>
            <Button v-if="video.status === 'compliance_done' && !pack.selected" label="Selecionar" size="small" @click="selectPack(pack.id)" />
          </template>
        </Card>
      </div>
    </div>

    <!-- Timeline de eventos -->
    <div v-if="video.events?.length">
      <h3 class="text-lg font-semibold mb-4">Histórico</h3>
      <Timeline :value="video.events">
        <template #content="{ item }">
          <div class="text-sm">
            <span class="font-medium">{{ item.event_type }}</span>
            <span class="text-gray-400 ml-2">{{ item.actor }}</span>
          </div>
        </template>
      </Timeline>
    </div>
  </div>
</template>
