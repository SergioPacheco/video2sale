<script setup lang="ts">
import { Video, Package, Flame, Settings, Moon, Sun, Clapperboard, LayoutDashboard } from 'lucide-vue-next'
import { useDarkMode } from '../composables/useDarkMode'
import { useRoute } from 'vue-router'

const { isDark, toggle } = useDarkMode()
const route = useRoute()
</script>

<template>
  <div class="flex h-screen bg-gray-50 dark:bg-gray-900">
    <!-- Sidebar compacta -->
    <aside class="w-16 lg:w-56 bg-white dark:bg-gray-800 border-r border-gray-200 dark:border-gray-700 flex flex-col transition-all">
      <!-- Logo -->
      <div class="p-3 lg:p-5 border-b border-gray-200 dark:border-gray-700">
        <div class="flex items-center gap-3">
          <img src="/logo.png" alt="V2S" class="w-8 h-8 rounded-lg" />
          <div class="hidden lg:block">
            <h1 class="text-base font-bold text-gray-900 dark:text-white">Video2Sale</h1>
          </div>
        </div>
      </div>

      <!-- Nav -->
      <nav class="flex-1 p-2 lg:p-3 space-y-1">
        <RouterLink to="/"
          :class="['flex items-center gap-3 px-3 py-2.5 rounded-lg transition-colors', route.path === '/' ? 'bg-blue-50 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300 font-medium' : 'text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700']">
          <Clapperboard :size="20" />
          <span class="hidden lg:inline">Dashboard</span>
        </RouterLink>

        <RouterLink to="/create"
          :class="['flex items-center gap-3 px-3 py-2.5 rounded-lg transition-colors', route.path === '/create' ? 'bg-blue-50 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300 font-medium' : 'text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700']">
          <Clapperboard :size="20" />
          <span class="hidden lg:inline">Crear Vídeo</span>
        </RouterLink>

        <RouterLink to="/videos"
          :class="['flex items-center gap-3 px-3 py-2.5 rounded-lg transition-colors', route.path.startsWith('/videos') ? 'bg-blue-50 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300 font-medium' : 'text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700']">
          <Video :size="20" />
          <span class="hidden lg:inline">Mis Vídeos</span>
        </RouterLink>

        <RouterLink to="/trending"
          :class="['flex items-center gap-3 px-3 py-2.5 rounded-lg transition-colors', route.path === '/trending' ? 'bg-blue-50 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300 font-medium' : 'text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700']">
          <Flame :size="20" />
          <span class="hidden lg:inline">Trending</span>
        </RouterLink>

        <RouterLink to="/products"
          :class="['flex items-center gap-3 px-3 py-2.5 rounded-lg transition-colors', route.path === '/products' ? 'bg-blue-50 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300 font-medium' : 'text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700']">
          <Package :size="20" />
          <span class="hidden lg:inline">Productos</span>
        </RouterLink>

        <RouterLink to="/settings"
          :class="['flex items-center gap-3 px-3 py-2.5 rounded-lg transition-colors', route.path === '/settings' ? 'bg-blue-50 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300 font-medium' : 'text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700']">
          <Settings :size="20" />
          <span class="hidden lg:inline">Configuración</span>
        </RouterLink>
      </nav>

      <!-- Footer -->
      <div class="p-2 lg:p-3 border-t border-gray-200 dark:border-gray-700">
        <button @click="toggle" class="flex items-center gap-3 px-3 py-2 rounded-lg text-gray-500 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700 w-full">
          <Sun v-if="isDark" :size="18" />
          <Moon v-else :size="18" />
          <span class="hidden lg:inline text-sm">{{ isDark ? 'Claro' : 'Oscuro' }}</span>
        </button>
      </div>
    </aside>

    <!-- Main content -->
    <main class="flex-1 overflow-auto">
      <slot />
    </main>
  </div>
</template>
