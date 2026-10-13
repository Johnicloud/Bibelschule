<script setup>
import { inject, onMounted, ref } from 'vue'
import TaskCard from './TaskCard.vue'
import ReadingSummary from './ReadingSummary.vue'
import EmptyState from '../ui/EmptyState.vue'

const props = defineProps({ subjectId: String })
const emit = defineEmits(['changed'])
const reading = inject('reading')

const tasks = ref([])
const status = ref(null)
const error = ref('')
const loadError = ref('')
const anlegen = ref(false)
const blank = () => ({ title: '', unit: 'Seiten', total: '', passes: 1, start: '', deadline: '' })
const form = ref(blank())
const mehrereBuecher = ref(false)
const buecher = ref([{ title: '', total: '' }])

async function load() {
  try {
    ;[tasks.value, status.value] = await Promise.all([reading.list(props.subjectId), reading.status(props.subjectId)])
    loadError.value = ''
  }
  catch (e) { loadError.value = e.message }
}
async function refresh() { await load(); emit('changed') }
function addBuchFeld() { buecher.value.push({ title: '', total: '' }) }
function removeBuchFeld(i) { buecher.value.splice(i, 1) }
function abbrechen() {
  anlegen.value = false
  error.value = ''
  form.value = blank()
  mehrereBuecher.value = false
  buecher.value = [{ title: '', total: '' }]
}
async function add() {
  error.value = ''
  try {
    await reading.add(props.subjectId, form.value, mehrereBuecher.value ? buecher.value : null)
    abbrechen()
    await refresh()
  } catch (e) { error.value = e.message }
}
onMounted(load)
</script>

<template>
  <ReadingSummary v-if="status && status.task_count" :status="status" class="mb-8" />

  <div class="mb-3 flex items-center justify-between">
    <h2 class="text-lg font-semibold">Neues Lesepensum</h2>
    <button v-if="!anlegen" type="button" class="btn btn-primary" @click="anlegen = true">+ Neues Pensum</button>
  </div>
  <form v-if="anlegen" class="panel grid gap-3 p-4 sm:grid-cols-6" @submit.prevent="add">
    <input v-model="form.title" class="input sm:col-span-6" placeholder="Titel, z. B. Grundriss der Dogmatik / Pflicht-Lektüre" aria-label="Titel" />

    <label class="flex items-center gap-1.5 text-sm sm:col-span-6">
      <input type="checkbox" v-model="mehrereBuecher" class="h-4 w-4 rounded" />
      Aus mehreren Büchern zusammensetzen (z. B. 600 Seiten aus drei Büchern mit je eigenem Umfang)
    </label>

    <template v-if="mehrereBuecher">
      <div class="sm:col-span-6">
        <div v-for="(b, i) in buecher" :key="i" class="mb-2 flex gap-2">
          <input v-model="b.title" class="input" placeholder="Buchtitel" :aria-label="`Titel Buch ${i + 1}`" />
          <input v-model="b.total" type="number" min="1" class="input !w-32" placeholder="Seiten/Kapitel" :aria-label="`Umfang Buch ${i + 1}`" />
          <button v-if="buecher.length > 1" type="button" class="btn btn-ghost !px-2.5" aria-label="Buch entfernen" @click="removeBuchFeld(i)">✕</button>
        </div>
        <button type="button" class="btn btn-outline !py-1.5" @click="addBuchFeld">+ Weiteres Buch</button>
      </div>
      <label class="text-sm sm:col-span-2">
        <span class="mb-1 block text-slate-500 dark:text-slate-400">Einheit</span>
        <select v-model="form.unit" class="input" aria-label="Einheit">
          <option>Seiten</option>
          <option>Kapitel</option>
        </select>
      </label>
    </template>
    <label v-else class="text-sm sm:col-span-2">
      <span class="mb-1 block text-slate-500 dark:text-slate-400">Umfang</span>
      <span class="flex gap-2">
        <input v-model="form.total" type="number" min="1" class="input" aria-label="Umfang" />
        <select v-model="form.unit" class="input !w-auto" aria-label="Einheit">
          <option>Seiten</option>
          <option>Kapitel</option>
        </select>
      </span>
    </label>
    <label class="text-sm sm:col-span-2">
      <span class="mb-1 block text-slate-500 dark:text-slate-400">Durchgänge</span>
      <input v-model="form.passes" type="number" min="1" max="20" class="input" />
    </label>
    <label class="text-sm sm:col-span-2">
      <span class="mb-1 block text-slate-500 dark:text-slate-400">Start (optional)</span>
      <input v-model="form.start" type="date" class="input" />
    </label>
    <label class="text-sm sm:col-span-2">
      <span class="mb-1 block text-slate-500 dark:text-slate-400">Frist (optional)</span>
      <input v-model="form.deadline" type="date" class="input" />
    </label>
    <div class="flex gap-2 sm:col-span-6">
      <button class="btn btn-primary">Pensum anlegen</button>
      <button type="button" class="btn btn-ghost" @click="abbrechen">Abbrechen</button>
      <span v-if="error" class="ml-1 text-sm text-rose-600 dark:text-rose-400">{{ error }}</span>
    </div>
  </form>

  <h2 class="mb-3 mt-10 text-lg font-semibold">Pensen in diesem Fach</h2>
  <p v-if="loadError" class="text-sm text-rose-600 dark:text-rose-400">{{ loadError }}</p>
  <ul v-else-if="tasks.length" class="grid gap-4">
    <TaskCard v-for="t in tasks" :key="t.id" :task="t" @changed="refresh" />
  </ul>
  <EmptyState v-else title="Noch kein Pensum" text="Lege oben ein Buch oder Skript mit Umfang und Frist an." />
</template>
