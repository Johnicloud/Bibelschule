<script setup>
import { computed, inject, ref } from 'vue'
import AppIcon from '../ui/AppIcon.vue'
import { BAR_CLASSES, READING_STATUS, TONE_CLASSES, forecastText, formatDate, num } from '../../domain/status'

const props = defineProps({ task: Object })
const emit = defineEmits(['changed'])
const reading = inject('reading')

const amount = ref('')
const day = ref('')
const error = ref('')
const today = new Date().toLocaleDateString('sv-SE') // YYYY-MM-DD in der Zeit des Geräts

const bearbeiten = ref(false)
const editForm = ref(null)
const editMehrereBuecher = ref(false)
const editBuecher = ref([])
const editError = ref('')
const speichert = ref(false)

const f = computed(() => props.task.forecast)
const status = computed(() => READING_STATUS[f.value.status])
const heutigesZiel = computed(() => f.value.needed_per_day ?? f.value.plan_per_day)
const heuteSchonGelesen = computed(() => props.task.entries.some((e) => e.day === today))
const zeigeTagesziel = computed(() => f.value.status !== 'done' && !heuteSchonGelesen.value && heutigesZiel.value)

async function log() {
  error.value = ''
  try {
    await reading.log(props.task.id, { amount: amount.value, day: day.value })
    amount.value = ''
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

function openEdit() {
  editError.value = ''
  const t = props.task
  editForm.value = { title: t.title, unit: t.unit, total: t.total, passes: t.passes, start: t.start || '', deadline: t.deadline || '' }
  editMehrereBuecher.value = t.buecher.length > 0
  editBuecher.value = t.buecher.length ? t.buecher.map((b) => ({ title: b.title, total: b.total })) : [{ title: '', total: '' }]
  bearbeiten.value = true
}
function addEditBuchFeld() { editBuecher.value.push({ title: '', total: '' }) }
function removeEditBuchFeld(i) { editBuecher.value.splice(i, 1) }
async function saveEdit() {
  editError.value = ''
  speichert.value = true
  try {
    await reading.update(props.task.id, editForm.value, editMehrereBuecher.value ? editBuecher.value : null)
    bearbeiten.value = false
    emit('changed')
  } catch (e) { editError.value = e.message }
  finally { speichert.value = false }
}
</script>

<template>
  <li class="panel p-5">
    <div v-if="!bearbeiten" class="flex flex-wrap items-start justify-between gap-3">
      <div>
        <div class="flex items-center gap-1.5">
          <h3 class="text-lg font-semibold">{{ task.title }}</h3>
          <button class="btn btn-ghost !p-1.5" aria-label="Pensum bearbeiten" @click="openEdit">
            <AppIcon name="stift" class="h-3.5 w-3.5" />
          </button>
        </div>
        <p class="text-sm text-slate-500 dark:text-slate-400">
          {{ num(task.total) }} {{ task.unit }}<template v-if="task.passes > 1">, {{ task.passes }} Durchgänge</template>
          <template v-if="task.start"> · Start {{ formatDate(task.start) }}</template>
          <template v-if="task.deadline"> · Frist {{ formatDate(task.deadline) }}</template>
          <template v-if="f.plan_per_day"> · Plan {{ num(f.plan_per_day) }} {{ task.unit }}/Tag</template>
        </p>
        <p v-if="task.buecher.length" class="mt-1 text-sm text-slate-500 dark:text-slate-400">
          aus: {{ task.buecher.map((b) => `${b.title} (${num(b.total)})`).join(', ') }}
        </p>
      </div>
      <span class="rounded-full px-2.5 py-0.5 text-xs font-medium" :class="TONE_CLASSES[status.tone]">{{ status.label }}</span>
    </div>

    <form v-else class="grid gap-3 sm:grid-cols-6" @submit.prevent="saveEdit">
      <input v-model="editForm.title" class="input sm:col-span-6" placeholder="Titel" aria-label="Titel" />

      <label class="flex items-center gap-1.5 text-sm sm:col-span-6">
        <input type="checkbox" v-model="editMehrereBuecher" class="h-4 w-4 rounded" />
        Aus mehreren Büchern zusammensetzen
      </label>

      <template v-if="editMehrereBuecher">
        <div class="sm:col-span-6">
          <div v-for="(b, i) in editBuecher" :key="i" class="mb-2 flex gap-2">
            <input v-model="b.title" class="input" placeholder="Buchtitel" :aria-label="`Titel Buch ${i + 1}`" />
            <input v-model="b.total" type="number" min="1" class="input !w-32" placeholder="Seiten/Kapitel" :aria-label="`Umfang Buch ${i + 1}`" />
            <button v-if="editBuecher.length > 1" type="button" class="btn btn-ghost !px-2.5" aria-label="Buch entfernen" @click="removeEditBuchFeld(i)">✕</button>
          </div>
          <button type="button" class="btn btn-outline !py-1.5" @click="addEditBuchFeld">+ Weiteres Buch</button>
        </div>
        <label class="text-sm sm:col-span-2">
          <span class="mb-1 block text-slate-500 dark:text-slate-400">Einheit</span>
          <select v-model="editForm.unit" class="input" aria-label="Einheit">
            <option>Seiten</option>
            <option>Kapitel</option>
          </select>
        </label>
      </template>
      <label v-else class="text-sm sm:col-span-2">
        <span class="mb-1 block text-slate-500 dark:text-slate-400">Umfang</span>
        <span class="flex gap-2">
          <input v-model="editForm.total" type="number" min="1" class="input" aria-label="Umfang" />
          <select v-model="editForm.unit" class="input !w-auto" aria-label="Einheit">
            <option>Seiten</option>
            <option>Kapitel</option>
          </select>
        </span>
      </label>
      <label class="text-sm sm:col-span-2">
        <span class="mb-1 block text-slate-500 dark:text-slate-400">Durchgänge</span>
        <input v-model="editForm.passes" type="number" min="1" max="20" class="input" />
      </label>
      <label class="text-sm sm:col-span-2">
        <span class="mb-1 block text-slate-500 dark:text-slate-400">Start (optional)</span>
        <input v-model="editForm.start" type="date" class="input" />
      </label>
      <label class="text-sm sm:col-span-2">
        <span class="mb-1 block text-slate-500 dark:text-slate-400">Frist (optional)</span>
        <input v-model="editForm.deadline" type="date" class="input" />
      </label>
      <div class="flex gap-2 sm:col-span-6">
        <button class="btn btn-primary" :disabled="speichert">{{ speichert ? 'Speichert …' : 'Speichern' }}</button>
        <button type="button" class="btn btn-ghost" @click="bearbeiten = false">Abbrechen</button>
      </div>
      <p v-if="editError" class="text-sm text-rose-600 dark:text-rose-400 sm:col-span-6">{{ editError }}</p>
    </form>

    <div v-if="!bearbeiten" class="mt-4">
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

    <p v-if="!bearbeiten && zeigeTagesziel" class="mt-4 rounded-xl bg-amber-50 px-3 py-2 text-sm text-amber-800 dark:bg-amber-500/10 dark:text-amber-300">
      Heute noch nicht gelesen — Ziel: {{ num(heutigesZiel) }} {{ task.unit }}
    </p>

    <form v-if="!bearbeiten" class="mt-4 grid gap-2 sm:grid-cols-[7rem_9rem_auto]" @submit.prevent="log">
      <input v-model="amount" type="number" min="1" class="input" :placeholder="task.unit" :aria-label="`Gelesene ${task.unit}`" />
      <input v-model="day" type="date" :max="today" class="input" aria-label="Datum (leer = heute)" />
      <button class="btn btn-primary">Eintragen</button>
    </form>
    <p v-if="!bearbeiten && error" class="mt-2 text-sm text-rose-600 dark:text-rose-400">{{ error }}</p>

    <details v-if="!bearbeiten && task.entries.length" class="mt-4">
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

    <div v-if="!bearbeiten" class="mt-4 flex justify-end">
      <button class="btn btn-danger !py-1.5" @click="removeTask">Pensum löschen</button>
    </div>
  </li>
</template>
