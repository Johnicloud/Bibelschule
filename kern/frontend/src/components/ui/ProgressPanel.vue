<script setup>
import { computed } from 'vue'

// Gesamtfortschritt eines Fachs: Mittel aller Dienste, die einen Fortschritt melden (Antwort des Kerns).
// Zeigt nur noch die Zahl – die Aufschlüsselung je Dienst steht im Reiter „Übersicht“ (SubjectOverview.vue),
// war hier dauerhaft sichtbar zu viel auf einmal.
const props = defineProps({ overview: Object })

const measured = computed(() => props.overview.parts.filter((p) => p.progress != null).map((p) => p.label))
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
  </section>
</template>
