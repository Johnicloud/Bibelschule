<script setup>
import { inject, onMounted, ref } from 'vue'
import TaskCard from './TaskCard.vue'
import EmptyState from '../ui/EmptyState.vue'

const props = defineProps({ subjectId: String })
const reading = inject('reading')

const tasks = ref([])
const error = ref('')
const loadError = ref('')
const blank = () => ({ title: '', unit: 'Seiten', total: '', passes: 1, deadline: '' })
const form = ref(blank())

async function load() {
  try { tasks.value = await reading.list(props.subjectId); loadError.value = '' }
  catch (e) { loadError.value = e.message }
}
async function add() {
  error.value = ''
  try { await reading.add(props.subjectId, form.value); form.value = blank(); await load() }
  catch (e) { error.value = e.message }
}
onMounted(load)
</script>

<template>
  <h2 class="mb-3 text-lg font-semibold">Neues Lesepensum</h2>
  <form class="panel grid gap-3 p-4 sm:grid-cols-6" @submit.prevent="add">
    <input v-model="form.title" class="input sm:col-span-6" placeholder="Titel, z. B. Grundriss der Dogmatik" aria-label="Titel" />
    <label class="text-sm sm:col-span-2">
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
      <span class="mb-1 block text-slate-500 dark:text-slate-400">Frist (optional)</span>
      <input v-model="form.deadline" type="date" class="input" />
    </label>
    <div class="sm:col-span-6">
      <button class="btn btn-primary">Pensum anlegen</button>
      <span v-if="error" class="ml-3 text-sm text-rose-600 dark:text-rose-400">{{ error }}</span>
    </div>
  </form>

  <h2 class="mb-3 mt-10 text-lg font-semibold">Pensen in diesem Fach</h2>
  <p v-if="loadError" class="text-sm text-rose-600 dark:text-rose-400">{{ loadError }}</p>
  <ul v-else-if="tasks.length" class="grid gap-4">
    <TaskCard v-for="t in tasks" :key="t.id" :task="t" @changed="load" />
  </ul>
  <EmptyState v-else title="Noch kein Pensum" text="Lege oben ein Buch oder Skript mit Umfang und Frist an." />
</template>
