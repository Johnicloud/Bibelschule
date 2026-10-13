<script setup>
import { inject, onMounted, ref, watch } from 'vue'
import EmptyState from '../components/ui/EmptyState.vue'
import { SERVICE_LABELS } from '../domain/status'

defineEmits(['open-subject'])
const subjects = inject('subjects')
const adressbuch = inject('adressbuch')
const list = ref([])
const name = ref('')
const se = ref('')
const credits = ref('')
const aufgaben = ref([''])
const dozenten = ref([])
const ausgewaehlteDozenten = ref([])
const error = ref('')
const warning = ref('')

// SE und Credits bleiben im Eingabeformular synchron (Credits = SE * 1,5); gespeichert wird nur SE.
let sync = false
watch(se, (v) => { if (sync) return; sync = true; credits.value = v === '' ? '' : (Number(v) * 1.5).toFixed(1); sync = false })
watch(credits, (v) => { if (sync) return; sync = true; se.value = v === '' ? '' : (Number(v) / 1.5).toFixed(1); sync = false })

async function load() { list.value = await subjects.list() }
async function loadDozenten() { try { dozenten.value = await adressbuch.dozenten() } catch { /* Adressbuch gerade nicht erreichbar */ } }

function warn(synced) {
  const missed = Object.entries(synced || {}).filter(([, ok]) => !ok).map(([n]) => SERVICE_LABELS[n] || n)
  warning.value = missed.length
    ? `${missed.join(', ')} nicht erreichbar. Das Fach ist gespeichert; „Dienste abgleichen“ auf der Startseite holt es nach.`
    : ''
}
function addAufgabenFeld() { aufgaben.value.push('') }
function removeAufgabenFeld(i) { aufgaben.value.splice(i, 1) }
async function create() {
  error.value = ''
  warning.value = ''
  try {
    const subject = await subjects.create(name.value, aufgaben.value, se.value)
    await Promise.all(ausgewaehlteDozenten.value.map((id) => adressbuch.assign(id, subject.id).catch(() => {})))
    name.value = ''
    se.value = ''
    credits.value = ''
    aufgaben.value = ['']
    ausgewaehlteDozenten.value = []
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
onMounted(() => { load(); loadDozenten() })
</script>

<template>
  <h1 class="text-3xl font-semibold tracking-tight">Fächer</h1>
  <p class="mt-1 text-slate-500 dark:text-slate-400">Jedes Fach hat Karteikarten, Lesenachweis und Register.</p>

  <form class="panel mt-6 grid gap-3 p-4" @submit.prevent="create">
    <input v-model="name" class="input" placeholder="Neues Fach, z. B. Bibelkunde" aria-label="Name des Fachs" />

    <div class="flex flex-wrap items-start gap-4">
      <div class="flex gap-2">
        <input v-model="se" type="number" min="0" step="0.5" class="input !w-24" placeholder="SE" aria-label="Studieneinheiten (optional)" />
        <input v-model="credits" type="number" min="0" step="0.1" class="input !w-28" placeholder="Credits" aria-label="Credits (optional)" />
      </div>
      <div v-if="dozenten.length" class="flex-1">
        <span class="mb-1.5 block text-sm text-slate-500 dark:text-slate-400">Dozenten (optional)</span>
        <div class="flex flex-wrap gap-x-4 gap-y-1.5">
          <label v-for="d in dozenten" :key="d.id" class="flex items-center gap-1.5 text-sm">
            <input type="checkbox" :value="d.id" v-model="ausgewaehlteDozenten" class="h-4 w-4 rounded" />
            {{ d.name }}
          </label>
        </div>
      </div>
    </div>

    <div>
      <span class="mb-1.5 block text-sm text-slate-500 dark:text-slate-400">
        Umfang (optional): die Aufgaben, die in diesem Fach anstehen
      </span>
      <div v-for="(a, i) in aufgaben" :key="i" class="mb-2 flex gap-2">
        <input v-model="aufgaben[i]" class="input" placeholder="Aufgabe, z. B. Exegese Kapitel 3" :aria-label="`Aufgabe ${i + 1}`" />
        <button v-if="aufgaben.length > 1" type="button" class="btn btn-ghost !px-2.5" aria-label="Aufgabe entfernen" @click="removeAufgabenFeld(i)">✕</button>
      </div>
      <button type="button" class="btn btn-outline !py-1.5" @click="addAufgabenFeld">+ Weitere Aufgabe</button>
    </div>

    <button class="btn btn-primary justify-self-start">Fach anlegen</button>
  </form>
  <p v-if="error" class="mt-2 text-sm text-rose-600 dark:text-rose-400">{{ error }}</p>
  <p v-if="warning" class="mt-2 text-sm text-amber-700 dark:text-amber-300">{{ warning }}</p>

  <ul v-if="list.length" class="mt-6 grid gap-4 sm:grid-cols-2">
    <li v-for="s in list" :key="s.id" class="panel flex flex-col p-5">
      <button class="text-left text-xl font-semibold hover:text-teal-600 dark:hover:text-teal-400" @click="$emit('open-subject', s.id)">
        {{ s.name }}
      </button>
      <p v-if="s.se != null" class="mt-1 text-sm text-slate-500 dark:text-slate-400">{{ s.se }} SE · {{ (s.se * 1.5).toFixed(1) }} Credits</p>
      <div class="mt-5 flex gap-2">
        <button class="btn btn-outline" @click="$emit('open-subject', s.id)">Öffnen</button>
        <button class="btn btn-ghost" @click="rename(s)">Umbenennen</button>
        <button class="btn btn-danger ml-auto" @click="remove(s)">Löschen</button>
      </div>
    </li>
  </ul>
  <EmptyState v-else class="mt-6" title="Noch kein Fach" text="Gib oben einen Namen ein und lege dein erstes Fach an." />
</template>
