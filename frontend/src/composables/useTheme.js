import { ref } from 'vue'

const dark = ref(document.documentElement.classList.contains('dark'))

export function useTheme() {
  function toggle() {
    dark.value = !dark.value
    document.documentElement.classList.toggle('dark', dark.value)
    localStorage.setItem('theme', dark.value ? 'dark' : 'light')
  }
  return { dark, toggle }
}
