<script setup>
import { inject, onMounted, ref } from 'vue'
import AppIcon from '../components/ui/AppIcon.vue'
import EmptyState from '../components/ui/EmptyState.vue'

const adressbuch = inject('adressbuch')
const liste = ref([])
const loadError = ref('')
const blank = () => ({ name: '', email: '', telefon: '', strasse: '', plz: '', ort: '', notiz: '' })
const anlegen = ref(false)
const form = ref(blank())
const error = ref('')

const bearbeitetId = ref(null)
const editForm = ref(blank())
const editError = ref('')
const speichert = ref(false)

// Anschrift zur Anzeige: neue, getrennte Felder bevorzugt; ältere Dozenten mit dem alten Freitext-Feld
// `adresse` zeigen weiterhin dieses, bis jemand ihre Anschrift einmal neu einträgt.
function anschrift(d) {
  const zeile2 = [d.plz, d.ort].filter(Boolean).join(' ')
  const neu = [d.strasse, zeile2].filter(Boolean).join(', ')
  return neu || d.adresse || ''
}

async function load() {
  try { liste.value = await adressbuch.dozenten(); loadError.value = '' }
  catch (e) { loadError.value = e.message }
}
async function add() {
  error.value = ''
  try {
    await adressbuch.add(form.value)
    anlegen.value = false
    form.value = blank()
    await load()
  }
  catch (e) { error.value = e.message }
}
async function remove(d) {
  if (!confirm(`„${d.name}“ aus dem Adressbuch löschen?`)) return
  await adressbuch.remove(d.id)
  await load()
}
function openEdit(d) {
  editError.value = ''
  editForm.value = { name: d.name, email: d.email || '', telefon: d.telefon || '',
    strasse: d.strasse || '', plz: d.plz || '', ort: d.ort || '', notiz: d.notiz || '' }
  bearbeitetId.value = d.id
}
async function saveEdit() {
  editError.value = ''
  speichert.value = true
  try {
    await adressbuch.update(bearbeitetId.value, editForm.value)
    bearbeitetId.value = null
    await load()
  } catch (e) { editError.value = e.message }
  finally { speichert.value = false }
}
onMounted(load)
</script>

<template>
  <h1 class="text-3xl font-semibold tracking-tight">Adressbuch</h1>
  <p class="mt-1 text-slate-500 dark:text-slate-400">Dozenten, unabhängig vom Fach. Zuordnung zu Fächern passiert im jeweiligen Fach.</p>

  <div class="mb-3 mt-6 flex items-center justify-between">
    <h2 class="text-lg font-semibold">Dozenten</h2>
    <button v-if="!anlegen && liste.length" type="button" class="btn btn-outline !py-1.5" @click="anlegen = true">+ Neuer Dozent</button>
  </div>

  <form v-if="anlegen" class="panel mb-4 grid gap-3 p-4 sm:grid-cols-2" @submit.prevent="add">
    <input v-model="form.name" class="input sm:col-span-2" placeholder="Name" aria-label="Name" />
    <input v-model="form.email" type="email" class="input" placeholder="E-Mail" aria-label="E-Mail" />
    <input v-model="form.telefon" class="input" placeholder="Telefon" aria-label="Telefon" />
    <input v-model="form.strasse" class="input sm:col-span-2" placeholder="Straße und Hausnummer" aria-label="Straße und Hausnummer" />
    <input v-model="form.plz" class="input" placeholder="PLZ" aria-label="Postleitzahl" />
    <input v-model="form.ort" class="input" placeholder="Ort" aria-label="Ort" />
    <div class="sm:col-span-2">
      <button class="btn btn-primary">Dozent anlegen</button>
      <button type="button" class="btn btn-ghost ml-2" @click="anlegen = false; form = blank()">Abbrechen</button>
      <span v-if="error" class="ml-3 text-sm text-rose-600 dark:text-rose-400">{{ error }}</span>
    </div>
  </form>

  <p v-if="loadError" class="mt-6 text-sm text-rose-600 dark:text-rose-400">{{ loadError }}</p>
  <ul v-else-if="liste.length" class="mt-6 grid gap-3 sm:grid-cols-2">
    <li v-for="d in liste" :key="d.id" class="panel p-4">
      <div v-if="bearbeitetId !== d.id" class="flex items-start justify-between gap-2">
        <div>
          <div class="flex items-center gap-1.5">
            <p class="font-semibold">{{ d.name }}</p>
            <button class="btn btn-ghost !p-1.5" :aria-label="`${d.name} bearbeiten`" @click="openEdit(d)">
              <AppIcon name="stift" class="h-3.5 w-3.5" />
            </button>
          </div>
          <p v-if="d.email" class="text-sm text-slate-500 dark:text-slate-400">{{ d.email }}</p>
          <p v-if="d.telefon" class="text-sm text-slate-500 dark:text-slate-400">{{ d.telefon }}</p>
          <p v-if="anschrift(d)" class="text-sm text-slate-500 dark:text-slate-400">{{ anschrift(d) }}</p>
          <p class="mt-1 text-xs text-slate-400 dark:text-slate-500">
            {{ d.faecher.length }} {{ d.faecher.length === 1 ? 'Fach' : 'Fächer' }} zugeordnet
          </p>
        </div>
        <button class="btn btn-danger !px-2.5 !py-1" :aria-label="`${d.name} löschen`" @click="remove(d)">Löschen</button>
      </div>

      <form v-else class="grid gap-2" @submit.prevent="saveEdit">
        <input v-model="editForm.name" class="input" placeholder="Name" aria-label="Name" />
        <input v-model="editForm.email" type="email" class="input" placeholder="E-Mail" aria-label="E-Mail" />
        <input v-model="editForm.telefon" class="input" placeholder="Telefon" aria-label="Telefon" />
        <input v-model="editForm.strasse" class="input" placeholder="Straße und Hausnummer" aria-label="Straße und Hausnummer" />
        <span class="flex gap-2">
          <input v-model="editForm.plz" class="input !w-24" placeholder="PLZ" aria-label="Postleitzahl" />
          <input v-model="editForm.ort" class="input" placeholder="Ort" aria-label="Ort" />
        </span>
        <div class="flex gap-2">
          <button class="btn btn-primary !py-1.5" :disabled="speichert">{{ speichert ? 'Speichert …' : 'Speichern' }}</button>
          <button type="button" class="btn btn-ghost !py-1.5" @click="bearbeitetId = null">Abbrechen</button>
        </div>
        <p v-if="editError" class="text-sm text-rose-600 dark:text-rose-400">{{ editError }}</p>
      </form>
    </li>
    <li v-if="!anlegen">
      <button class="panel flex h-full w-full flex-col items-center justify-center gap-2 p-5 text-sm font-medium opacity-70 hover:opacity-100"
        @click="anlegen = true">
        <AppIcon name="plus" class="h-6 w-6" />
        Neuer Dozent
      </button>
    </li>
  </ul>
  <EmptyState v-else-if="!anlegen" title="Noch kein Dozent" text="Lege den ersten Dozenten an.">
    <button class="btn btn-primary" @click="anlegen = true">Ersten Dozenten anlegen</button>
  </EmptyState>
</template>
