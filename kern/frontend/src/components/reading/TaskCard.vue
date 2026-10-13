<script setup>
import { computed, inject, ref } from 'vue'
import { BAR_CLASSES, READING_STATUS, TONE_CLASSES, forecastText, formatDate, num } from '../../domain/status'

const props = defineProps({ task: Object })
const emit = defineEmits(['changed'])
const reading = inject('reading')

const amount = ref('')
const day = ref('')
const note = ref('')
const error = ref('')
const today = new Date().toLocaleDateString('sv-SE') // YYYY-MM-DD in der Zeit des Geräts

const f = computed(() => props.task.forecast)
const status = computed(() => READING_STATUS[f.value.status])

async function log() {
  error.value = ''
  try {
    await reading.log(props.task.id, { amount: amount.value, day: day.value, note: note.value })
    amount.value = ''
    note.value = ''
    emit('changed')
  } catch (e) { error.value = e.message }
}
async function removeEntry(entry) {
  await reading.deleteEntry(props.task.id, entry.id)
  emit('changed')
}
async function removeTask() {
  if (!confirm(`Pensum „${props.task.title}“ mit dem ganzen Leseprotokoll löschen?`)) return
  await reading.remove(props.task.id)
  emit('changed')
}
</script>

<template>
  <li class="panel p-5">
    <div class="flex flex-wrap items-start justify-between gap-3">
      <div>
        <h3 class="text-lg font-semibold">{{ task.title }}</h3>
        <p class="text-sm text-slate-500 dark:text-slate-400">
          {{ num(task.total) }} {{ task.unit }}<template v-if="task.passes > 1">, {{ task.passes }} Durchgänge</template>
          <template v-if="task.start"> · Start {{ formatDate(task.start) }}</template>
          <template v-if="task.deadline"> · Frist {{ formatDate(task.deadline) }}</template>
          <template v-if="f.plan_per_day"> · Plan {{ num(f.plan_per_day) }} {{ task.unit }}/Tag</template>
        </p>
      </div>
      <span class="rounded-full px-2.5 py-0.5 text-xs font-medium" :class="TONE_CLASSES[status.tone]">{{ status.label }}</span>
    </div>

    <div class="mt-4">
      <div class="flex justify-between text-sm">
        <span class="tabular-nums">{{ num(f.done) }} von {{ num(f.target) }} {{ task.unit }}</span>
        <span class="font-medium tabular-nums">{{ num(f.percent) }} %</span>
      </div>
      <div class="mt-1.5 h-2 overflow-hidden rounded-full bg-slate-200 dark:bg-slate-800" role="progressbar"
        :aria-valuenow="f.percent" aria-valuemin="0" aria-valuemax="100">
        <div class="h-full rounded-full" :class="BAR_CLASSES[status.tone]" :style="{ width: f.percent + '%' }"></div>
      </div>
      <p class="mt-3 text-sm text-slate-600 dark:text-slate-300">{{ forecastText(task) }}</p>
    </div>

    <form class="mt-4 grid gap-2 sm:grid-cols-[7rem_9rem_1fr_auto]" @submit.prevent="log">
      <input v-model="amount" type="number" min="1" class="input" :placeholder="task.unit" :aria-label="`Gelesene ${task.unit}`" />
      <input v-model="day" type="date" :max="today" class="input" aria-label="Datum (leer = heute)" />
      <input v-model="note" class="input" placeholder="Notiz (optional)" aria-label="Notiz" />
      <button class="btn btn-primary">Eintragen</button>
    </form>
    <p v-if="error" class="mt-2 text-sm text-rose-600 dark:text-rose-400">{{ error }}</p>

    <details v-if="task.entries.length" class="mt-4">
      <summary class="cursor-pointer text-sm text-slate-500 dark:text-slate-400">
        Leseprotokoll ({{ task.entries.length }} {{ task.entries.length === 1 ? 'Eintrag' : 'Einträge' }})
      </summary>
      <ul class="mt-2 divide-y divide-slate-200 text-sm dark:divide-slate-800">
        <li v-for="e in task.entries" :key="e.id" class="flex items-center gap-3 py-2">
          <span class="w-24 shrink-0 tabular-nums text-slate-500 dark:text-slate-400">{{ formatDate(e.day) }}</span>
          <span class="w-28 shrink-0 tabular-nums">{{ num(e.amount) }} {{ task.unit }}</span>
          <span class="min-w-0 flex-1 truncate text-slate-500 dark:text-slate-400">{{ e.note }}</span>
          <button class="btn btn-danger !px-2.5 !py-1" :aria-label="`Eintrag vom ${formatDate(e.day)} löschen`" @click="removeEntry(e)">Löschen</button>
        </li>
      </ul>
    </details>

    <div class="mt-4 flex justify-end">
      <button class="btn btn-danger !py-1.5" @click="removeTask">Pensum löschen</button>
    </div>
  </li>
</template>
