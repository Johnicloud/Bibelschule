<script setup>
import { computed } from 'vue'
import { BAR_CLASSES, READING_STATUS, TONE_CLASSES } from '../../domain/status'

// Gesamtfortschritt eines Fachs: Mittel aller Dienste, die einen Fortschritt melden (Antwort des Kerns).
const props = defineProps({ overview: Object, services: { type: Array, default: () => [] } })

const measured = computed(() => props.overview.parts.filter((p) => p.progress != null).map((p) => p.label))

const rows = computed(() => props.overview.parts.map((p) => {
  const st = props.overview.status[p.service]
  const row = { key: p.service, label: p.label, progress: p.progress, text: '', chip: null }
  if (!p.online || !st) { row.text = 'nicht erreichbar'; return row }
  if (p.service === 'lesenachweis') {
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
  <section class="panel p-5" aria-label="Gesamtfortschritt">
    <div class="flex flex-wrap items-end justify-between gap-3">
      <div>
        <div class="text-xs font-medium uppercase tracking-wide text-slate-500 dark:text-slate-400">Gesamtfortschritt</div>
        <div class="mt-1 text-4xl font-semibold tabular-nums">{{ overview.progress != null ? overview.progress + ' %' : '–' }}</div>
      </div>
      <p class="max-w-sm text-right text-sm text-slate-500 dark:text-slate-400">
        <template v-if="measured.length">Mittel aus {{ measured.join(' und ') }}.</template>
        <template v-else>Noch nichts, was sich messen lässt. Lege Lesepensen oder Karteikarten an.</template>
      </p>
    </div>
    <div v-if="overview.progress != null" class="mt-3 h-2.5 overflow-hidden rounded-full bg-slate-200 dark:bg-slate-800"
      role="progressbar" :aria-valuenow="overview.progress" aria-valuemin="0" aria-valuemax="100">
      <div class="h-full rounded-full bg-teal-500 transition-all" :style="{ width: overview.progress + '%' }"></div>
    </div>

    <ul class="mt-5 grid gap-4 sm:grid-cols-3">
      <li v-for="r in rows" :key="r.key">
        <div class="flex items-center justify-between gap-2">
          <span class="text-sm font-medium">{{ r.label }}</span>
          <span v-if="r.chip" class="rounded-full px-2 py-0.5 text-xs" :class="TONE_CLASSES[r.chip.tone]">{{ r.chip.label }}</span>
          <span v-else-if="r.progress != null" class="text-sm tabular-nums text-slate-500 dark:text-slate-400">{{ r.progress }} %</span>
        </div>
        <div v-if="r.progress != null" class="mt-1.5 h-1.5 overflow-hidden rounded-full bg-slate-200 dark:bg-slate-800" aria-hidden="true">
          <div class="h-full rounded-full" :class="BAR_CLASSES[r.chip ? r.chip.tone : 'teal']" :style="{ width: r.progress + '%' }"></div>
        </div>
        <p class="mt-1.5 text-xs text-slate-500 dark:text-slate-400">{{ r.text }}</p>
      </li>
    </ul>
  </section>
</template>
