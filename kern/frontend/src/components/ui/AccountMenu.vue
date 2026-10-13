<script setup>
import { onBeforeUnmount, onMounted, ref } from 'vue'
import { useTheme } from '../../composables/useTheme'

const props = defineProps({ username: String })
const emit = defineEmits(['profile', 'logout'])
const { dark, toggle } = useTheme()

const open = ref(false)

function schliessen(e) {
  if (!e.target.closest('[data-account-menu]')) open.value = false
}
onMounted(() => document.addEventListener('click', schliessen))
onBeforeUnmount(() => document.removeEventListener('click', schliessen))

function go(fn) { open.value = false; fn() }
</script>

<template>
  <div class="relative" data-account-menu>
    <button type="button" class="grid h-9 w-9 place-items-center rounded-full bg-white/15 text-white hover:bg-white/25"
      :aria-expanded="open" aria-haspopup="menu" :aria-label="`Konto: ${username}`" @click="open = !open">
      <svg class="h-5 w-5" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
        <circle cx="12" cy="8" r="4" />
        <path d="M4 20c0-4.4 3.6-7 8-7s8 2.6 8 7v1H4v-1z" />
      </svg>
    </button>

    <div v-if="open" role="menu" class="absolute right-0 mt-2 w-56 rounded-xl border border-highlight bg-theme py-1.5 text-theme-inv shadow-lg">
      <p class="truncate px-3 py-1.5 text-sm font-medium">{{ username }}</p>
      <button type="button" role="menuitem" class="flex w-full items-center justify-between px-3 py-2 text-sm hover:bg-backdrop" @click="toggle">
        {{ dark ? 'Dunkles Design' : 'Helles Design' }}
        <svg v-if="dark" class="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" aria-hidden="true">
          <circle cx="12" cy="12" r="4" /><path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4" />
        </svg>
        <svg v-else class="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
          <path d="M21 12.8A9 9 0 1 1 11.2 3a7 7 0 0 0 9.8 9.8z" />
        </svg>
      </button>
      <button type="button" role="menuitem" class="flex w-full px-3 py-2 text-sm hover:bg-backdrop" @click="go(() => emit('profile'))">Konto</button>
      <hr class="my-1.5 border-highlight" />
      <button type="button" role="menuitem" class="flex w-full px-3 py-2 text-sm text-error hover:bg-backdrop" @click="go(() => emit('logout'))">Abmelden</button>
    </div>
  </div>
</template>
