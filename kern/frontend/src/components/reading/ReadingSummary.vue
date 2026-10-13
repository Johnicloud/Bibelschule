<script setup>
import { computed } from 'vue'
import { BAR_CLASSES, READING_STATUS, TONE_CLASSES, formatDate, num } from '../../domain/status'

// Lesestatus des ganzen Fachs (Antwort des Lesenachweis-Dienstes: /subjects/{id}/status)
const props = defineProps({ status: Object })
const st = computed(() => READING_STATUS[props.status.status] || READING_STATUS.open)
</script>

<template>
  <section class="panel p-5" aria-label="Lesestatus des Fachs">
    <div class="flex flex-wrap items-center justify-between gap-3">
      <h2 class="text-lg font-semibold">Lesestatus des Fachs</h2>
      <span class="rounded-full px-2.5 py-0.5 text-xs font-medium" :class="TONE_CLASSES[st.tone]">{{ st.label }}</span>
    </div>

    <div class="mt-3 flex items-baseline gap-2">
      <span class="text-3xl font-semibold tabular-nums">{{ num(status.percent) }} %</span>
      <span class="text-sm text-slate-500 dark:text-slate-400">gelesen, alle Pensen gleich gewichtet</span>
    </div>
    <div class="mt-2 h-2 overflow-hidden rounded-full bg-slate-200 dark:bg-slate-800" role="progressbar"
      :aria-valuenow="Math.round(status.percent)" aria-valuemin="0" aria-valuemax="100">
      <div class="h-full rounded-full transition-all" :class="BAR_CLASSES[st.tone]" :style="{ width: status.percent + '%' }"></div>
    </div>

    <ul class="mt-3 space-y-1 text-sm text-slate-600 dark:text-slate-300">
      <li>{{ status.done_count }} von {{ status.task_count }} {{ status.task_count === 1 ? 'Pensum' : 'Pensen' }} fertig.</li>
      <li v-if="status.urgent_title">Am dringendsten: <span class="font-medium">{{ status.urgent_title }}</span></li>
      <li v-if="status.next_deadline">Nächste Frist: {{ formatDate(status.next_deadline) }}</li>
    </ul>
  </section>
</template>
