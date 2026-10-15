<script setup>
import AppIcon from './AppIcon.vue'

defineProps({ active: String })
defineEmits(['nav'])
const tabs = [
  { id: 'subjects', label: 'Fächer', icon: 'faecher' },
  { id: 'cards', label: 'Karten', icon: 'karten' },
  { id: 'noten', label: 'Noten', icon: 'noten' },
  { id: 'bibel', label: 'Bibel', icon: 'buch' },
  { id: 'bibliothek', label: 'Bibliothek', icon: 'bibliothek' },
  { id: 'schnelllesen', label: 'Schnelllesen', icon: 'stoppuhr' },
  { id: 'adressbuch', label: 'Adressbuch', icon: 'adressbuch' },
]
</script>

<template>
  <!-- Pillen-Leiste wie HaushaltsbuchNavigation der Finanzapp auf dem Desktop: eigene Leiste im Inhalt,
       aktiver Reiter mit farbigem Hintergrund (bg-primary), nicht Weiß – das war vorher kaum zu erkennen. -->
  <nav class="mx-auto flex max-w-5xl flex-wrap gap-1 rounded-xl bg-backdrop p-1" aria-label="Hauptnavigation">
    <button v-for="t in tabs" :key="t.id" :title="t.label" :aria-label="t.label"
      class="flex items-center justify-center rounded-lg p-2.5 text-theme-inv opacity-70 transition hover:opacity-100"
      :class="active === t.id ? 'bg-primary text-white opacity-100 shadow-sm' : ''"
      :aria-current="active === t.id ? 'page' : undefined" @click="$emit('nav', t.id)">
      <AppIcon :name="t.icon" class="h-5 w-5" />
    </button>
  </nav>
</template>
