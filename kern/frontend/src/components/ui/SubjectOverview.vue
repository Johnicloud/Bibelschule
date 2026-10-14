<script setup>
import { computed } from 'vue'
import AppIcon from './AppIcon.vue'
import { BAR_CLASSES, READING_STATUS, TAB_ICONS, TONE_CLASSES } from '../../domain/status'

// Erster Reiter im Fach: Kurzüberblick je Dienst, zum Weiterspringen in den jeweiligen Reiter –
// ersetzt die frühere Zeilen-Liste, die dauerhaft über den Reitern stand (war zu viel auf einmal).
const props = defineProps({ overview: Object, services: { type: Array, default: () => [] }, tabNames: { type: Array, default: () => [] } })
const emit = defineEmits(['go'])

const rows = computed(() => props.overview.parts
  .filter((p) => props.tabNames.includes(p.service))
  .map((p) => {
    const st = props.overview.status[p.service]
    const row = { key: p.service, label: p.label, progress: p.progress, text: '', chip: null }
    if (!p.online || !st) { row.text = 'nicht erreichbar'; return row }
    if (p.service === 'aufgaben') {
      row.text = st.count ? `${st.done} von ${st.count} Aufgaben erledigt` : 'Noch keine Aufgabe'
    } else if (p.service === 'lesenachweis') {
      row.text = st.task_count ? `${st.done_count} von ${st.task_count} Pensen fertig` : 'Noch kein Pensum'
      row.chip = READING_STATUS[st.status] || null
    } else if (p.service === 'karteikarten') {
      row.text = st.card_count
        ? `${st.mastered} von ${st.card_count} Karten sicher gelernt, ${st.due_count} fällig`
        : 'Noch keine Karten'
    } else if (p.service === 'register') {
      row.text = st.entries
        ? `${st.entries} ${st.entries === 1 ? 'Eintrag' : 'Einträge'} in ${st.registers} ${st.registers === 1 ? 'Register' : 'Registern'}`
        : st.registers ? `${st.registers} Register, noch ohne Einträge` : 'Noch kein Register'
    } else {
      const fields = props.services.find((s) => s.name === p.service)?.fields ?? []
      row.text = fields.map((f) => `${st[f.key]} ${f.label}`).join(', ')
    }
    return row
  }))
</script>

<template>
  <ul class="grid gap-4 sm:grid-cols-2">
    <li v-for="r in rows" :key="r.key">
      <button type="button" class="panel w-full p-4 text-left transition hover:-translate-y-0.5 hover:shadow-md" @click="emit('go', r.key)">
        <div class="flex items-center justify-between gap-2">
          <span class="flex items-center gap-2 text-sm font-medium">
            <AppIcon :name="TAB_ICONS[r.key] || 'baustein'" class="h-4 w-4 opacity-70" />
            {{ r.label }}
          </span>
          <span v-if="r.chip" class="rounded-full px-2 py-0.5 text-xs" :class="TONE_CLASSES[r.chip.tone]">{{ r.chip.label }}</span>
          <span v-else-if="r.progress != null" class="text-sm tabular-nums opacity-70">{{ r.progress }} %</span>
        </div>
        <div v-if="r.progress != null" class="mt-2 h-1.5 overflow-hidden rounded-full bg-highlight" aria-hidden="true">
          <div class="h-full rounded-full" :class="BAR_CLASSES[r.chip ? r.chip.tone : 'teal']" :style="{ width: r.progress + '%' }"></div>
        </div>
        <p class="mt-2 text-xs opacity-70">{{ r.text }}</p>
      </button>
    </li>
  </ul>
</template>
