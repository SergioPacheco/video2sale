<script setup lang="ts">
import { Package, Video, Trophy, BarChart3, Wand2, Settings } from 'lucide-vue-next'
</script>

<template>
  <div class="flex h-screen bg-gray-50">
    <!-- Sidebar -->
    <aside class="w-64 bg-white border-r border-gray-200 flex flex-col">
      <div class="p-6 border-b border-gray-200">
        <h1 class="text-xl font-bold text-gray-900">Video2Sale</h1>
        <p class="text-sm text-gray-500">Fábrica de conteúdo</p>
      </div>
      <nav class="flex-1 p-4 space-y-1">
        <RouterLink to="/" class="flex items-center gap-3 px-3 py-2 rounded-lg text-gray-700 hover:bg-gray-100">
          <BarChart3 :size="20" />
          <span>Dashboard</span>
        </RouterLink>
        <RouterLink to="/workflow" class="flex items-center gap-3 px-3 py-2 rounded-lg text-gray-700 hover:bg-gray-100">
          <Wand2 :size="20" />
          <span>Workflow</span>
        </RouterLink>
        <RouterLink to="/products" class="flex items-center gap-3 px-3 py-2 rounded-lg text-gray-700 hover:bg-gray-100">
          <Package :size="20" />
          <span>Productos</span>
        </RouterLink>
        <RouterLink to="/ranking" class="flex items-center gap-3 px-3 py-2 rounded-lg text-gray-700 hover:bg-gray-100">
          <Trophy :size="20" />
          <span>Ranking</span>
        </RouterLink>
        <RouterLink to="/videos" class="flex items-center gap-3 px-3 py-2 rounded-lg text-gray-700 hover:bg-gray-100">
          <Video :size="20" />
          <span>Vídeos</span>
        </RouterLink>
      </nav>
      <div class="p-4 border-t border-gray-200">
        <RouterLink to="/prompts" class="flex items-center gap-3 px-3 py-2 rounded-lg text-gray-700 hover:bg-gray-100">
          <Settings :size="20" />
          <span>Configuración</span>
        </RouterLink>
      </div>
    </aside>

    <!-- Main content -->
    <main class="flex-1 overflow-auto p-8">
      <slot />
    </main>
  </div>
</template>
