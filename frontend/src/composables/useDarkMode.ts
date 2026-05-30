import { ref, watch } from 'vue'

const isDark = ref(localStorage.getItem('theme') === 'dark')

function apply() {
  document.documentElement.classList.toggle('dark', isDark.value)
}

watch(isDark, (v) => {
  localStorage.setItem('theme', v ? 'dark' : 'light')
  apply()
}, { immediate: true })

export function useDarkMode() {
  function toggle() { isDark.value = !isDark.value }
  return { isDark, toggle }
}
