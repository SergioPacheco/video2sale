<template>
  <div class="max-w-3xl">
    <h2 class="text-2xl font-bold text-gray-900 dark:text-white mb-6">📖 Guía del Workflow</h2>

    <div class="space-y-6">
      <section v-for="step in steps" :key="step.num" class="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl p-5">
        <div class="flex items-start gap-4">
          <span class="flex items-center justify-center w-8 h-8 rounded-full bg-blue-100 dark:bg-blue-900 text-blue-700 dark:text-blue-300 font-bold text-sm shrink-0">{{ step.num }}</span>
          <div>
            <h3 class="font-semibold text-gray-900 dark:text-white">{{ step.title }}</h3>
            <p class="text-sm text-gray-600 dark:text-gray-300 mt-1">{{ step.desc }}</p>
            <p v-if="step.tip" class="text-xs text-gray-400 dark:text-gray-500 mt-2 italic">💡 {{ step.tip }}</p>
          </div>
        </div>
      </section>

      <section class="bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-700 rounded-xl p-5">
        <h3 class="font-semibold text-yellow-800 dark:text-yellow-300 mb-2">📊 Después de publicar</h3>
        <ol class="text-sm text-yellow-700 dark:text-yellow-400 space-y-1 list-decimal list-inside">
          <li>Espera unos días para acumular métricas en TikTok</li>
          <li>Abre tu perfil TikTok en Chrome con <strong>Sort Feed</strong> activo</li>
          <li>Exporta el CSV desde la extensión</li>
          <li>Ve a <a href="/metrics" class="underline font-medium">Métricas</a> y sube el CSV</li>
          <li>El sistema cruza automáticamente por URL o caption</li>
        </ol>
      </section>
    </div>
  </div>
</template>

<script setup lang="ts">
const steps = [
  { num: 1, title: 'Importar Productos', desc: 'Sube un CSV con productos candidatos (nombre, categoría, scores) o búscalos en Amazon.', tip: 'El CSV debe tener columnas: name, category, pain_score, visual_score, etc.' },
  { num: 2, title: 'Ranking', desc: 'El sistema calcula un score ponderado y selecciona el producto ganador de la semana. Se crea automáticamente un registro de vídeo.', tip: 'Puedes repetir el ranking si agregas nuevos productos.' },
  { num: 3, title: 'Generar Roteiros', desc: 'La IA genera 3 variaciones de guión creativo (hook, escenas, caption, hashtags). Puedes elegir un prompt template personalizado.', tip: 'Selecciona un template para ver el preview con variables sustituidas antes de generar.' },
  { num: 4, title: 'Compliance', desc: 'Cada roteiro es validado contra reglas de contenido: sin promesas exageradas, sin alegaciones médicas, con aviso de afiliado.', tip: 'Si un roteiro es "AJUSTAR", la IA lo corrige automáticamente.' },
  { num: 5, title: 'Seleccionar Roteiro', desc: 'Tú eliges cuál de las 3 variaciones usar para el vídeo final. Lee el hook y caption de cada una.', tip: 'Elige la que tenga el gancho más fuerte para los primeros 2 segundos.' },
  { num: 6, title: 'Generar Audio', desc: 'Se genera el voiceover (narración) concatenando el texto de todas las escenas y enviando al servicio TTS.', tip: 'El audio se guarda en /output/{semana}/{producto}/' },
  { num: 7, title: 'Generar Prompts de Vídeo', desc: 'Se generan prompts optimizados para el renderer elegido (Seedance o Runway). Cada escena recibe un prompt visual.', tip: 'Usa estos prompts en Seedance/Runway para generar los clips de cada escena.' },
  { num: 8, title: 'Publicar', desc: 'Marca el vídeo como publicado y pega la URL de TikTok. Esta URL se usa después para importar métricas de Sort Feed.', tip: 'Sin la URL, el cruce de métricas se hace por caption (menos preciso).' },
]
</script>
