<script setup>
import { inject, onMounted, ref } from 'vue'
import EmptyState from '../components/ui/EmptyState.vue'
import { SERVICE_LABELS } from '../domain/status'

defineEmits(['open-subject'])
const subjects = inject('subjects')
const list = ref([])
const name = ref('')
const error = ref('')
const warning = ref('')

async function load() { list.value = await subjects.list() }

function warn(synced) {
  const missed = Object.entries(synced || {}).filter(([, ok]) => !ok).map(([n]) => SERVICE_LABELS[n] || n)
  warning.value = missed.length
    ? `${missed.join(', ')} nicht erreichbar. Das Fach ist gespeichert; „Dienste abgleichen“ auf der Startseite holt es nach.`
    : ''
}
async function create() {
  error.value = ''
  warning.value = ''
  try {
    const subject = await subjects.create(name.value)
    name.value = ''
    warn(subject.synced)
    await load()
  } catch (e) { error.value = e.message }
}
async function rename(subject) {
  const next = prompt('Neuer Name des Fachs', subject.name)
  if (next === null || !next.trim() || next.trim() === subject.name) return
  error.value = ''
  try { warn((await subjects.rename(subject.id, next)).synced); await load() }
  catch (e) { error.value = e.message }
}
async function remove(subject) {
  if (!confirm(`Fach „${subject.name}“ mit Karteikarten, Lesenachweis und Register löschen?`)) return
  await subjects.remove(subject.id)
  await load()
}
onMounted(load)
</script>

<template>
  <h1 class="text-3xl font-semibold tracking-tight">Fächer</h1>
  <p class="mt-1 text-slate-500 dark:text-slate-400">Jedes Fach hat Karteikarten, Lesenachweis und Register.</p>

  <form class="mt-6 flex gap-2" @submit.prevent="create">
    <input v-model="name" class="input" placeholder="Neues Fach, z. B. Bibelkunde" aria-label="Name des Fachs" />
    <button class="btn btn-primary shrink-0">Fach anlegen</button>
  </form>
  <p v-if="error" class="mt-2 text-sm text-rose-600 dark:text-rose-400">{{ error }}</p>
  <p v-if="warning" class="mt-2 text-sm text-amber-700 dark:text-amber-300">{{ warning }}</p>

  <ul v-if="list.length" class="mt-6 grid gap-4 sm:grid-cols-2">
    <li v-for="s in list" :key="s.id" class="panel flex flex-col p-5">
      <button class="text-left text-xl font-semibold hover:text-teal-600 dark:hover:text-teal-400" @click="$emit('open-subject', s.id)">
        {{ s.name }}
      </button>
      <div class="mt-5 flex gap-2">
        <button class="btn btn-outline" @click="$emit('open-subject', s.id)">Öffnen</button>
        <button class="btn btn-ghost" @click="rename(s)">Umbenennen</button>
        <button class="btn btn-danger ml-auto" @click="remove(s)">Löschen</button>
      </div>
    </li>
  </ul>
  <EmptyState v-else class="mt-6" title="Noch kein Fach" text="Gib oben einen Namen ein und lege dein erstes Fach an." />
</template>
