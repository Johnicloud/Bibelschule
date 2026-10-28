<script setup>
import { inject, onMounted, ref } from 'vue'
import AppIcon from '../components/ui/AppIcon.vue'
import EmptyState from '../components/ui/EmptyState.vue'

const bibliothek = inject('bibliothek')
const liste = ref([])
const loadError = ref('')
const blank = () => ({ titel: '', autor: '', verlag: '', jahr: '', isbn: '', standort: '', notiz: '' })
const anlegen = ref(false)
const form = ref(blank())
const error = ref('')

const bearbeitetId = ref(null)
const editForm = ref(blank())
const editError = ref('')
const speichert = ref(false)

const ausleihenId = ref(null)
const ausleihenAn = ref('')
const ausleihenError = ref('')

const dateiFehler = ref({})     // buch.id -> Fehlertext
const laedtHoch = ref(null)     // buch.id, während der Upload läuft
const erkenntText = ref(null)   // buch.id, während die Text-Erkennung läuft (nur optimistisch, kein Live-Status)

async function load() {
  try { liste.value = await bibliothek.buecher(); loadError.value = '' }
  catch (e) { loadError.value = e.message }
}
async function add() {
  error.value = ''
  try {
    await bibliothek.add(form.value)
    anlegen.value = false
    form.value = blank()
    await load()
  } catch (e) { error.value = e.message }
}
async function remove(b) {
  if (!confirm(`„${b.titel}“ aus der Bibliothek löschen?`)) return
  await bibliothek.remove(b.id)
  await load()
}
function openEdit(b) {
  editError.value = ''
  editForm.value = { titel: b.titel, autor: b.autor || '', verlag: b.verlag || '', jahr: b.jahr ?? '',
    isbn: b.isbn || '', standort: b.standort || '', notiz: b.notiz || '' }
  bearbeitetId.value = b.id
}
async function saveEdit() {
  editError.value = ''
  speichert.value = true
  try {
    await bibliothek.update(bearbeitetId.value, editForm.value)
    bearbeitetId.value = null
    await load()
  } catch (e) { editError.value = e.message }
  finally { speichert.value = false }
}

function openAusleihen(b) { ausleihenError.value = ''; ausleihenAn.value = ''; ausleihenId.value = b.id }
async function saveAusleihen() {
  ausleihenError.value = ''
  try {
    await bibliothek.ausleihen(ausleihenId.value, ausleihenAn.value)
    ausleihenId.value = null
    await load()
  } catch (e) { ausleihenError.value = e.message }
}
async function zurueckgeben(b) {
  await bibliothek.zurueckgeben(b.id)
  await load()
}

async function dateiGewaehlt(b, e) {
  const datei = e.target.files[0]
  e.target.value = ''
  if (!datei) return
  dateiFehler.value = { ...dateiFehler.value, [b.id]: '' }
  laedtHoch.value = b.id
  try { await bibliothek.dateiHochladen(b.id, datei); await load() }
  catch (err) { dateiFehler.value = { ...dateiFehler.value, [b.id]: err.message } }
  finally { laedtHoch.value = null }
}
async function textErkennen(b) {
  dateiFehler.value = { ...dateiFehler.value, [b.id]: '' }
  erkenntText.value = b.id
  try { await bibliothek.textErkennen(b.id) }
  catch (err) { dateiFehler.value = { ...dateiFehler.value, [b.id]: err.message } }
}

onMounted(load)
</script>

<template>
  <h1 class="text-3xl font-semibold tracking-tight">Bibliothek</h1>
  <p class="mt-1 text-slate-500 dark:text-slate-400">
    Der eigene Bücherbestand, unabhängig vom Fach. Gescannte Bücher lassen sich hochladen und per KI (Ollama)
    in eine durchsuchbare Text-PDF umwandeln – das Original bleibt dabei erhalten.
  </p>

  <div class="mb-3 mt-6 flex items-center justify-between">
    <h2 class="text-lg font-semibold">Bücher</h2>
    <button v-if="!anlegen && liste.length" type="button" class="btn btn-outline !py-1.5" @click="anlegen = true">+ Neues Buch</button>
  </div>

  <form v-if="anlegen" class="panel mb-4 grid gap-3 p-4 sm:grid-cols-2" @submit.prevent="add">
    <input v-model="form.titel" class="input sm:col-span-2" placeholder="Titel" aria-label="Titel" />
    <input v-model="form.autor" class="input" placeholder="Autor" aria-label="Autor" />
    <input v-model="form.verlag" class="input" placeholder="Verlag" aria-label="Verlag" />
    <input v-model="form.jahr" type="number" class="input" placeholder="Erscheinungsjahr" aria-label="Erscheinungsjahr" />
    <input v-model="form.isbn" class="input" placeholder="ISBN" aria-label="ISBN" />
    <input v-model="form.standort" class="input sm:col-span-2" placeholder="Standort, z. B. Regal 3" aria-label="Standort" />
    <div class="sm:col-span-2">
      <button class="btn btn-primary">Buch anlegen</button>
      <button type="button" class="btn btn-ghost ml-2" @click="anlegen = false; form = blank()">Abbrechen</button>
      <span v-if="error" class="ml-3 text-sm text-rose-600 dark:text-rose-400">{{ error }}</span>
    </div>
  </form>

  <p v-if="loadError" class="mt-6 text-sm text-rose-600 dark:text-rose-400">{{ loadError }}</p>
  <ul v-else-if="liste.length" class="mt-6 grid items-start gap-3 sm:grid-cols-2">
    <li v-for="b in liste" :key="b.id" class="panel min-w-0 p-4">
      <div v-if="bearbeitetId !== b.id" class="flex items-start justify-between gap-2">
        <div class="min-w-0">
          <div class="flex items-center gap-1.5">
            <p class="truncate font-semibold">{{ b.titel }}</p>
            <button class="btn btn-ghost !p-1.5 shrink-0" :aria-label="`${b.titel} bearbeiten`" @click="openEdit(b)">
              <AppIcon name="stift" class="h-3.5 w-3.5" />
            </button>
          </div>
          <p v-if="b.autor || b.verlag || b.jahr" class="text-sm text-slate-500 dark:text-slate-400">
            {{ [b.autor, b.verlag, b.jahr].filter(Boolean).join(' · ') }}
          </p>
          <p v-if="b.standort" class="text-sm text-slate-500 dark:text-slate-400">{{ b.standort }}</p>
          <p class="mt-1 text-xs">
            <span v-if="b.ausgeliehen_an" class="text-amber-700 dark:text-amber-300">Ausgeliehen an {{ b.ausgeliehen_an }}</span>
            <span v-else class="text-teal-700 dark:text-teal-300">Verfügbar</span>
          </p>
        </div>
        <button class="btn btn-danger !px-2.5 !py-1 shrink-0" :aria-label="`${b.titel} löschen`" @click="remove(b)">Löschen</button>
      </div>

      <form v-else class="grid gap-2" @submit.prevent="saveEdit">
        <input v-model="editForm.titel" class="input" placeholder="Titel" aria-label="Titel" />
        <input v-model="editForm.autor" class="input" placeholder="Autor" aria-label="Autor" />
        <input v-model="editForm.verlag" class="input" placeholder="Verlag" aria-label="Verlag" />
        <span class="flex gap-2">
          <input v-model="editForm.jahr" type="number" class="input" placeholder="Jahr" aria-label="Erscheinungsjahr" />
          <input v-model="editForm.isbn" class="input" placeholder="ISBN" aria-label="ISBN" />
        </span>
        <input v-model="editForm.standort" class="input" placeholder="Standort" aria-label="Standort" />
        <div class="flex gap-2">
          <button class="btn btn-primary !py-1.5" :disabled="speichert">{{ speichert ? 'Speichert …' : 'Speichern' }}</button>
          <button type="button" class="btn btn-ghost !py-1.5" @click="bearbeitetId = null">Abbrechen</button>
        </div>
        <p v-if="editError" class="text-sm text-rose-600 dark:text-rose-400">{{ editError }}</p>
      </form>

      <template v-if="bearbeitetId !== b.id">
        <!-- Ausleihen -->
        <div v-if="ausleihenId === b.id" class="mt-3 grid gap-2 border-t border-highlight pt-3">
          <input v-model="ausleihenAn" class="input" placeholder="Ausgeliehen an" aria-label="Ausgeliehen an" />
          <div class="flex gap-2">
            <button class="btn btn-primary !py-1.5" @click="saveAusleihen">Ausleihen</button>
            <button type="button" class="btn btn-ghost !py-1.5" @click="ausleihenId = null">Abbrechen</button>
          </div>
          <p v-if="ausleihenError" class="text-sm text-rose-600 dark:text-rose-400">{{ ausleihenError }}</p>
        </div>
        <div v-else class="mt-3 border-t border-highlight pt-3">
          <button v-if="!b.ausgeliehen_an" type="button" class="btn btn-outline !py-1.5" @click="openAusleihen(b)">Ausleihen</button>
          <button v-else type="button" class="btn btn-outline !py-1.5" @click="zurueckgeben(b)">Zurückgeben</button>
        </div>

        <!-- Datei und Text-Erkennung -->
        <div class="mt-3 flex flex-wrap items-center gap-2 border-t border-highlight pt-3">
          <a v-if="b.hat_datei" :href="bibliothek.dateiUrl(b.id)" target="_blank" class="btn btn-outline !py-1.5">Original öffnen</a>
          <label class="btn btn-outline inline-flex !py-1.5 cursor-pointer">
            {{ laedtHoch === b.id ? 'Lädt hoch …' : (b.hat_datei ? 'Neu hochladen' : 'PDF hochladen') }}
            <input type="file" accept="application/pdf" class="hidden" :disabled="laedtHoch === b.id" @change="dateiGewaehlt(b, $event)" />
          </label>
          <a v-if="b.text_erkannt" :href="bibliothek.textDateiUrl(b.id)" target="_blank" class="btn btn-outline !py-1.5">Text-PDF öffnen</a>
          <button v-else-if="b.hat_datei" type="button" class="btn btn-outline !py-1.5" @click="textErkennen(b)">
            {{ erkenntText === b.id ? 'Läuft im Hintergrund …' : 'Text erkennen' }}
          </button>
        </div>
        <p v-if="dateiFehler[b.id]" class="mt-2 text-sm text-rose-600 dark:text-rose-400">{{ dateiFehler[b.id] }}</p>
      </template>
    </li>
    <li v-if="!anlegen">
      <button class="panel flex min-h-32 w-full flex-col items-center justify-center gap-2 p-5 text-sm font-medium opacity-70 hover:opacity-100"
        @click="anlegen = true">
        <AppIcon name="plus" class="h-6 w-6" />
        Neues Buch
      </button>
    </li>
  </ul>
  <EmptyState v-else-if="!anlegen" title="Noch kein Buch" text="Lege das erste Buch an.">
    <button class="btn btn-primary" @click="anlegen = true">Erstes Buch anlegen</button>
  </EmptyState>
</template>
