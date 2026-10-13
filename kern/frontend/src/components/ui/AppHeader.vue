<script setup>
import ThemeToggle from './ThemeToggle.vue'

defineProps({ active: String, username: String })
defineEmits(['nav', 'logout', 'profile'])
const tabs = [
  { id: 'home', label: 'Start' },
  { id: 'subjects', label: 'Fächer' },
  { id: 'cards', label: 'Karten' },
  { id: 'study', label: 'Lernen' },
]
</script>

<template>
  <header class="sticky top-0 z-10 border-b border-slate-200 bg-slate-50/80 backdrop-blur dark:border-slate-800 dark:bg-slate-950/80">
    <div class="mx-auto flex max-w-5xl items-center justify-between gap-4 px-4 py-3">
      <button class="flex items-center gap-2 text-lg font-semibold tracking-tight" @click="$emit('nav', 'home')">
        <span class="grid h-8 w-8 place-items-center rounded-lg bg-teal-600 text-white dark:bg-teal-500 dark:text-slate-950" aria-hidden="true">B</span>
        Bibelschule
      </button>
      <nav class="flex items-center gap-1" aria-label="Hauptnavigation">
        <button v-for="t in tabs" :key="t.id" class="btn !px-3.5 !py-2"
          :class="active === t.id
            ? 'bg-slate-900 text-white dark:bg-slate-100 dark:text-slate-900'
            : 'btn-ghost'"
          :aria-current="active === t.id ? 'page' : undefined" @click="$emit('nav', t.id)">
          {{ t.label }}
        </button>
        <ThemeToggle />
        <button class="ml-2 hidden rounded-full px-3 py-1.5 text-sm text-slate-600 hover:bg-slate-200/60 dark:text-slate-300 dark:hover:bg-slate-800 sm:inline"
          :aria-current="active === 'profile' ? 'page' : undefined" @click="$emit('profile')">{{ username }}</button>
        <button class="btn btn-ghost !px-3" @click="$emit('logout')">Abmelden</button>
      </nav>
    </div>
  </header>
</template>
