<script setup lang="ts">
import { ref } from 'vue'
import Button from 'primevue/button'

const connected = ref(false)
const clientKey = 'sbawagk5dvic56w78s'
const redirectUri = 'https://github.com/SergioPacheco/video2sale'

function loginWithTikTok() {
  const scope = 'user.info.basic,user.info.stats,user.info.profile,video.list'
  const csrfState = Math.random().toString(36).substring(2)
  const url = `https://www.tiktok.com/v2/auth/authorize/?client_key=${clientKey}&scope=${scope}&response_type=code&redirect_uri=${encodeURIComponent(redirectUri)}&state=${csrfState}`
  window.open(url, '_blank', 'width=600,height=700')
}
</script>

<template>
  <div class="max-w-md mx-auto mt-12 text-center">
    <h2 class="text-2xl font-bold text-gray-900 dark:text-white mb-4">Conectar TikTok</h2>
    <p class="text-gray-600 dark:text-gray-300 mb-8">Conecta tu cuenta de TikTok para importar métricas de tus vídeos automáticamente.</p>

    <div v-if="!connected">
      <Button label="Iniciar sesión con TikTok" icon="pi pi-external-link" size="large" @click="loginWithTikTok"
              class="!bg-black !border-black !text-white hover:!bg-gray-800" />
      <p class="text-xs text-gray-400 mt-4">Se abrirá una ventana para autorizar el acceso a tu perfil y vídeos.</p>
    </div>

    <div v-else class="bg-green-50 dark:bg-green-900/30 border border-green-200 dark:border-green-700 rounded-lg p-6">
      <p class="text-green-800 dark:text-green-300 text-lg font-semibold">✅ Cuenta conectada</p>
      <p class="text-sm text-green-600 dark:text-green-400 mt-2">Tus métricas se importarán automáticamente.</p>
    </div>
  </div>
</template>
