<script setup>
import AccountMenu from './AccountMenu.vue'

defineProps({ active: String, username: String })
defineEmits(['nav', 'logout', 'profile'])
const tabs = [
  { id: 'subjects', label: 'Fächer' },
  { id: 'cards', label: 'Karten' },
  { id: 'study', label: 'Lernen' },
  { id: 'adressbuch', label: 'Adressbuch' },
]
</script>

<template>
  <!-- Kopfleiste in Primärfarbe wie bei der Finanzapp (AppRoot .app-header): eigene Markenfarbe statt neutralem Grau. -->
  <header class="sticky top-0 z-10 flex h-14 items-center gap-2 bg-primary px-3 text-white sm:gap-4 sm:px-4">
    <button class="flex shrink-0 items-center gap-2 text-lg font-semibold tracking-tight" @click="$emit('nav', 'home')">
      <span class="grid h-8 w-8 place-items-center rounded-lg bg-white/15 text-white" aria-hidden="true">B</span>
      <span class="hidden sm:inline">Bibelschule</span>
    </button>

    <!-- Pillen-Leiste wie HaushaltsbuchNavigation der Finanzapp (dort unten am Handy fest, hier im Kopf) -->
    <nav class="mx-auto flex max-w-full flex-1 flex-wrap gap-1 overflow-x-auto rounded-xl bg-black/10 p-1 sm:flex-none"
      aria-label="Hauptnavigation">
      <button v-for="t in tabs" :key="t.id"
        class="min-w-0 shrink-0 rounded-lg px-3 py-2 text-sm font-medium text-white/80 transition hover:bg-white/10 hover:text-white"
        :class="active === t.id ? 'bg-white text-primary shadow-sm hover:bg-white hover:text-primary' : ''"
        :aria-current="active === t.id ? 'page' : undefined" @click="$emit('nav', t.id)">
        {{ t.label }}
      </button>
    </nav>

    <AccountMenu :username="username" class="ml-auto shrink-0 sm:ml-0" @profile="$emit('profile')" @logout="$emit('logout')" />
  </header>
</template>
