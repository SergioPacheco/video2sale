<script setup lang="ts">
import { ref } from 'vue'
import Button from 'primevue/button'
import InputText from 'primevue/inputtext'
import Card from 'primevue/card'
import api from '../services/api'

const week = ref('')
const winner = ref<any>(null)
const loading = ref(false)

async function selectWinner() {
  if (!week.value) return
  loading.value = true
  const { data } = await api.post('/weekly-winner', { week: week.value })
  winner.value = data
  loading.value = false
}
</script>

<template>
  <div>
    <h2 class="text-2xl font-bold text-gray-900 mb-6">Ranking Semanal</h2>

    <div class="flex gap-4 mb-8">
      <InputText v-model="week" placeholder="2026-W21" />
      <Button label="Selecionar Vencedor" :loading="loading" @click="selectWinner" />
    </div>

    <Card v-if="winner" class="max-w-md">
      <template #title>🏆 {{ winner.product.name }}</template>
      <template #subtitle>Score: {{ winner.score }}</template>
      <template #content>
        <p class="text-gray-600">{{ winner.reason }}</p>
        <p class="text-sm text-gray-400 mt-2">Semana: {{ winner.week }}</p>
      </template>
    </Card>
  </div>
</template>
