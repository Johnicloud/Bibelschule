<script setup>
import { onBeforeUnmount, onMounted, ref } from 'vue'
import ThemeSwitch from './ThemeSwitch.vue'
import AppIcon from './AppIcon.vue'

const props = defineProps({ username: String })
const emit = defineEmits(['profile', 'logout'])

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
      <div class="flex w-full items-center justify-between px-3 py-2 text-sm">
        Dunkles Design
        <ThemeSwitch />
      </div>
      <button type="button" role="menuitem" class="flex w-full items-center gap-2 px-3 py-2 text-sm hover:bg-backdrop" @click="go(() => emit('profile'))">
        <AppIcon name="adressbuch" class="h-4 w-4 opacity-70" />
        Konto
      </button>
      <hr class="my-1.5 border-highlight" />
      <button type="button" role="menuitem" class="flex w-full items-center gap-2 px-3 py-2 text-sm text-error hover:bg-backdrop" @click="go(() => emit('logout'))">
        <AppIcon name="x" class="h-4 w-4" />
        Abmelden
      </button>
    </div>
  </div>
</template>
