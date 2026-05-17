<script setup lang="ts">
import { Package, Video, Trophy, BarChart3, Wand2, Settings, Moon, Sun, TrendingUp, BookOpen, Flame } from 'lucide-vue-next'
import { useDarkMode } from '../composables/useDarkMode'

const { isDark, toggle } = useDarkMode()
</script>

<template>
  <div class="flex h-screen bg-gray-50 dark:bg-gray-900">
    <!-- Sidebar -->
    <aside class="w-64 bg-white dark:bg-gray-800 border-r border-gray-200 dark:border-gray-700 flex flex-col">
      <div class="p-6 border-b border-gray-200 dark:border-gray-700">
        <h1 class="text-xl font-bold text-gray-900 dark:text-white">Video2Sale</h1>
        <p class="text-sm text-gray-500 dark:text-gray-400">Fábrica de conteúdo</p>
      </div>
      <nav class="flex-1 p-4 space-y-1">
        <RouterLink to="/" class="flex items-center gap-3 px-3 py-2 rounded-lg text-gray-700 dark:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-700">
          <BarChart3 :size="20" />
          <span>Dashboard</span>
        </RouterLink>
        <RouterLink to="/trending" class="flex items-center gap-3 px-3 py-2 rounded-lg text-gray-700 dark:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-700">
          <Flame :size="20" />
          <span>Trending</span>
        </RouterLink>
        <RouterLink to="/workflow" class="flex items-center gap-3 px-3 py-2 rounded-lg text-gray-700 dark:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-700">
          <Wand2 :size="20" />
          <span>Workflow</span>
        </RouterLink>
        <RouterLink to="/products" class="flex items-center gap-3 px-3 py-2 rounded-lg text-gray-700 dark:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-700">
          <Package :size="20" />
          <span>Productos</span>
        </RouterLink>
        <RouterLink to="/prompts" class="flex items-center gap-3 px-3 py-2 rounded-lg text-gray-700 dark:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-700">
          <Settings :size="20" />
          <span>Prompts</span>
        </RouterLink>
        <RouterLink to="/ranking" class="flex items-center gap-3 px-3 py-2 rounded-lg text-gray-700 dark:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-700">
          <Trophy :size="20" />
          <span>Ranking</span>
        </RouterLink>
        <RouterLink to="/videos" class="flex items-center gap-3 px-3 py-2 rounded-lg text-gray-700 dark:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-700">
          <Video :size="20" />
          <span>Vídeos</span>
        </RouterLink>
        <RouterLink to="/metrics" class="flex items-center gap-3 px-3 py-2 rounded-lg text-gray-700 dark:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-700">
          <TrendingUp :size="20" />
          <span>Métricas</span>
        </RouterLink>
      </nav>
      <div class="p-4 border-t border-gray-200 dark:border-gray-700 space-y-1">
        <RouterLink to="/guide" class="flex items-center gap-3 px-3 py-2 rounded-lg text-gray-700 dark:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-700">
          <BookOpen :size="20" />
          <span>Guía</span>
        </RouterLink>
        <button @click="toggle" class="flex items-center gap-3 px-3 py-2 rounded-lg text-gray-700 dark:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-700 w-full">
          <Sun v-if="isDark" :size="20" />
          <Moon v-else :size="20" />
          <span>{{ isDark ? 'Modo Claro' : 'Modo Oscuro' }}</span>
        </button>
      </div>
    </aside>

    <!-- Main content -->
    <main class="flex-1 overflow-auto p-8">
      <slot />
    </main>
  </div>
</template>
