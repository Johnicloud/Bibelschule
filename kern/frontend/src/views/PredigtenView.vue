<script setup>
import { inject, onMounted, ref } from 'vue'
import AppIcon from '../components/ui/AppIcon.vue'
import EmptyState from '../components/ui/EmptyState.vue'
import { stellenZuText } from '../application/predigtenService'

const predigten = inject('predigten')
const liste = ref([])
const loadError = ref('')
const blank = () => ({ titel: '', datum: '', prediger: '', notiz: '', stellenText: '' })
const anlegen = ref(false)
const form = ref(blank())
const error = ref('')

const bearbeitetId = ref(null)
const editForm = ref(blank())
const editError = ref('')
const speichert = ref(false)

const dateiFehler = ref({})     // predigt.id -> Fehlertext
const laedtHoch = ref(null)     // predigt.id, während der Upload läuft

async function load() {
  try { liste.value = await predigten.predigten(); loadError.value = '' }
  catch (e) { loadError.value = e.message }
}
async function add() {
  error.value = ''
  try {
    await predigten.add(form.value)
    anlegen.value = false
    form.value = blank()
    await load()
  } catch (e) { error.value = e.message }
}
async function remove(p) {
  if (!confirm(`„${p.titel}“ aus dem Archiv löschen?`)) return
  await predigten.remove(p.id)
  await load()
}
function openEdit(p) {
  editError.value = ''
  editForm.value = { titel: p.titel, datum: p.datum || '', prediger: p.prediger || '', notiz: p.notiz || '',
    stellenText: stellenZuText(p.stellen) }
  bearbeitetId.value = p.id
}
async function saveEdit() {
  editError.value = ''
  speichert.value = true
  try {
    await predigten.update(bearbeitetId.value, editForm.value)
    bearbeitetId.value = null
    await load()
  } catch (e) { editError.value = e.message }
  finally { speichert.value = false }
}

async function dateiGewaehlt(p, e) {
  const datei = e.target.files[0]
  e.target.value = ''
  if (!datei) return
  dateiFehler.value = { ...dateiFehler.value, [p.id]: '' }
  laedtHoch.value = p.id
  try { await predigten.dateiHochladen(p.id, datei); await load() }
  catch (err) { dateiFehler.value = { ...dateiFehler.value, [p.id]: err.message } }
  finally { laedtHoch.value = null }
}

onMounted(load)
</script>

<template>
  <h1 class="text-3xl font-semibold tracking-tight">Predigten</h1>
  <p class="mt-1 text-slate-500 dark:text-slate-400">
    Predigten und eigene Texte archivieren, mit Bibelstellen verknüpfen (der Bibel-Dienst merkt sich dort,
    was auf sie verweist) und optional als Datei hinterlegen.
  </p>

  <div class="mb-3 mt-6 flex items-center justify-between">
    <h2 class="text-lg font-semibold">Archiv</h2>
    <button v-if="!anlegen && liste.length" type="button" class="btn btn-outline !py-1.5" @click="anlegen = true">+ Neue Predigt</button>
  </div>

  <form v-if="anlegen" class="panel mb-4 grid gap-3 p-4 sm:grid-cols-2" @submit.prevent="add">
    <input v-model="form.titel" class="input sm:col-span-2" placeholder="Titel" aria-label="Titel" />
    <input v-model="form.datum" type="date" class="input" aria-label="Datum" />
    <input v-model="form.prediger" class="input" placeholder="Prediger/Autor" aria-label="Prediger/Autor" />
    <textarea v-model="form.stellenText" class="input sm:col-span-2" rows="2"
      placeholder="Bibelstellen, z. B. Joh 3,16, Röm 8,28" aria-label="Bibelstellen"></textarea>
    <textarea v-model="form.notiz" class="input sm:col-span-2" rows="3" placeholder="Notiz" aria-label="Notiz"></textarea>
    <div class="sm:col-span-2">
      <button class="btn btn-primary">Predigt anlegen</button>
      <button type="button" class="btn btn-ghost ml-2" @click="anlegen = false; form = blank()">Abbrechen</button>
      <span v-if="error" class="ml-3 text-sm text-rose-600 dark:text-rose-400">{{ error }}</span>
    </div>
  </form>

  <p v-if="loadError" class="mt-6 text-sm text-rose-600 dark:text-rose-400">{{ loadError }}</p>
  <ul v-else-if="liste.length" class="mt-6 grid items-start gap-3 sm:grid-cols-2">
    <li v-for="p in liste" :key="p.id" class="panel min-w-0 p-4">
      <div v-if="bearbeitetId !== p.id" class="flex items-start justify-between gap-2">
        <div class="min-w-0">
          <div class="flex items-center gap-1.5">
            <p class="truncate font-semibold">{{ p.titel }}</p>
            <button class="btn btn-ghost !p-1.5 shrink-0" :aria-label="`${p.titel} bearbeiten`" @click="openEdit(p)">
              <AppIcon name="stift" class="h-3.5 w-3.5" />
            </button>
          </div>
          <p v-if="p.datum || p.prediger" class="text-sm text-slate-500 dark:text-slate-400">
            {{ [p.datum, p.prediger].filter(Boolean).join(' · ') }}
          </p>
          <p v-if="p.notiz" class="mt-1 whitespace-pre-line text-sm">{{ p.notiz }}</p>
          <p v-if="p.stellen?.length" class="mt-2 flex flex-wrap gap-1">
            <span v-for="s in p.stellen" :key="s" class="rounded-full bg-backdrop px-2 py-0.5 text-xs text-theme-inv">{{ s }}</span>
          </p>
        </div>
        <button class="btn btn-danger !px-2.5 !py-1 shrink-0" :aria-label="`${p.titel} löschen`" @click="remove(p)">Löschen</button>
      </div>

      <form v-else class="grid gap-2" @submit.prevent="saveEdit">
        <input v-model="editForm.titel" class="input" placeholder="Titel" aria-label="Titel" />
        <span class="flex gap-2">
          <input v-model="editForm.datum" type="date" class="input" aria-label="Datum" />
          <input v-model="editForm.prediger" class="input" placeholder="Prediger/Autor" aria-label="Prediger/Autor" />
        </span>
        <textarea v-model="editForm.stellenText" class="input" rows="2" placeholder="Bibelstellen" aria-label="Bibelstellen"></textarea>
        <textarea v-model="editForm.notiz" class="input" rows="3" placeholder="Notiz" aria-label="Notiz"></textarea>
        <div class="flex gap-2">
          <button class="btn btn-primary !py-1.5" :disabled="speichert">{{ speichert ? 'Speichert …' : 'Speichern' }}</button>
          <button type="button" class="btn btn-ghost !py-1.5" @click="bearbeitetId = null">Abbrechen</button>
        </div>
        <p v-if="editError" class="text-sm text-rose-600 dark:text-rose-400">{{ editError }}</p>
      </form>

      <template v-if="bearbeitetId !== p.id">
        <!-- Datei -->
        <div class="mt-3 flex flex-wrap items-center gap-2 border-t border-highlight pt-3">
          <a v-if="p.hat_datei" :href="predigten.dateiUrl(p.id)" target="_blank" class="btn btn-outline !py-1.5">Datei öffnen</a>
          <label class="btn btn-outline inline-flex !py-1.5 cursor-pointer">
            {{ laedtHoch === p.id ? 'Lädt hoch …' : (p.hat_datei ? 'Neu hochladen' : 'PDF hochladen') }}
            <input type="file" accept="application/pdf" class="hidden" :disabled="laedtHoch === p.id" @change="dateiGewaehlt(p, $event)" />
          </label>
        </div>
        <p v-if="dateiFehler[p.id]" class="mt-2 text-sm text-rose-600 dark:text-rose-400">{{ dateiFehler[p.id] }}</p>
      </template>
    </li>
    <li v-if="!anlegen">
      <button class="panel flex min-h-32 w-full flex-col items-center justify-center gap-2 p-5 text-sm font-medium opacity-70 hover:opacity-100"
        @click="anlegen = true">
        <AppIcon name="plus" class="h-6 w-6" />
        Neue Predigt
      </button>
    </li>
  </ul>
  <EmptyState v-else-if="!anlegen" title="Noch keine Predigt" text="Lege die erste Predigt an.">
    <button class="btn btn-primary" @click="anlegen = true">Erste Predigt anlegen</button>
  </EmptyState>
</template>
