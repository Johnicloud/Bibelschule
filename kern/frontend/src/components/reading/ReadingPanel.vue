<script setup>
import { inject, onMounted, ref } from 'vue'
import TaskCard from './TaskCard.vue'
import ReadingSummary from './ReadingSummary.vue'
import EmptyState from '../ui/EmptyState.vue'
import AppIcon from '../ui/AppIcon.vue'
import { gemeinde as profilGemeinde, nachname as profilNachname, vorname as profilVorname } from '../../state/auth'

const props = defineProps({ subjectId: String })
const emit = defineEmits(['changed'])
const reading = inject('reading')
const subjects = inject('subjects')
const pdfcreator = inject('pdfcreator')

const tasks = ref([])
const status = ref(null)
const error = ref('')
const loadError = ref('')
const anlegen = ref(false)
const blank = () => ({ title: '', unit: 'Seiten', total: '', passes: 1, start: '', deadline: '' })
const form = ref(blank())
const mehrereBuecher = ref(false)
const buecher = ref([{ title: '', total: '' }])

const subjectName = ref('')
const exportieren = ref(false)
// Vorbelegt aus dem eigenen Profil (Konto-Seite), bleibt aber änderbar – kein Pflichtfeld.
const exportName = ref([profilVorname.value, profilNachname.value].filter(Boolean).join(' '))
const exportGemeinde = ref(profilGemeinde.value)
const exportError = ref('')
const exportLaeuft = ref(false)

async function load() {
  try {
    ;[tasks.value, status.value, { name: subjectName.value }] =
      await Promise.all([reading.list(props.subjectId), reading.status(props.subjectId), subjects.get(props.subjectId)])
    loadError.value = ''
  }
  catch (e) { loadError.value = e.message }
}
async function refresh() { await load(); emit('changed') }
async function exportierenAlsPdf() {
  exportError.value = ''
  exportLaeuft.value = true
  try {
    // Tatsächlich gelesene Seiten/Kapitel (b.done bzw. forecast.done), nicht der geplante Umfang (b.total/t.total).
    const alleBuecher = tasks.value.flatMap((t) => t.buecher.length
      ? t.buecher.map((b) => ({ titel: b.title, seiten: b.done }))
      : [{ titel: t.title, seiten: t.forecast.done }])
    await pdfcreator.lesenachweisExportieren(subjectName.value, exportName.value, exportGemeinde.value, alleBuecher)
    exportieren.value = false
  } catch (e) { exportError.value = e.message }
  finally { exportLaeuft.value = false }
}
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
    <h2 class="text-lg font-semibold">Pensen in diesem Fach</h2>
    <div class="flex gap-2">
      <button v-if="tasks.length" type="button" class="btn btn-outline !py-1.5" @click="exportieren = true">Als PDF exportieren</button>
      <button v-if="!anlegen && tasks.length" type="button" class="btn btn-outline !py-1.5" @click="anlegen = true">+ Neues Pensum</button>
    </div>
  </div>

  <section v-if="exportieren" class="panel mb-4 grid gap-3 p-4 sm:grid-cols-2">
    <input v-model="exportName" class="input" placeholder="Name (optional)" aria-label="Name" />
    <input v-model="exportGemeinde" class="input" placeholder="Gemeinde (optional)" aria-label="Gemeinde" />
    <div class="flex gap-2 sm:col-span-2">
      <button class="btn btn-primary" :disabled="exportLaeuft" @click="exportierenAlsPdf">{{ exportLaeuft ? 'Erzeugt PDF …' : 'PDF erzeugen' }}</button>
      <button type="button" class="btn btn-ghost" @click="exportieren = false">Abbrechen</button>
      <span v-if="exportError" class="ml-1 text-sm text-rose-600 dark:text-rose-400">{{ exportError }}</span>
    </div>
  </section>

  <form v-if="anlegen" class="panel mb-4 grid gap-3 p-4 sm:grid-cols-6" @submit.prevent="add">
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

  <p v-if="loadError" class="text-sm text-rose-600 dark:text-rose-400">{{ loadError }}</p>
  <ul v-else-if="tasks.length" class="grid gap-4 sm:grid-cols-2">
    <TaskCard v-for="t in tasks" :key="t.id" :task="t" :subject-name="subjectName" @changed="refresh" />
    <li v-if="!anlegen">
      <button class="panel flex h-full w-full flex-col items-center justify-center gap-2 p-5 text-sm font-medium opacity-70 hover:opacity-100"
        @click="anlegen = true">
        <AppIcon name="plus" class="h-6 w-6" />
        Neues Pensum
      </button>
    </li>
  </ul>
  <EmptyState v-else-if="!anlegen" title="Noch kein Pensum" text="Lege ein Buch oder Skript mit Umfang und Frist an.">
    <button class="btn btn-primary" @click="anlegen = true">Erstes Pensum anlegen</button>
  </EmptyState>
</template>
