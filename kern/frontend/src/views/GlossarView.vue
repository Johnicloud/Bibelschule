<script setup>
import { computed, inject, onMounted, ref } from 'vue'
import AppIcon from '../components/ui/AppIcon.vue'
import EmptyState from '../components/ui/EmptyState.vue'

const glossar = inject('glossar')
const bibel = inject('bibel')

const liste = ref([])
const loadError = ref('')
const suche = ref('')

const blank = () => ({ wort: '', transliteration: '', erklaerung: '', stellenText: '' })
const anlegen = ref(false)
const form = ref(blank())
const error = ref('')

const bearbeitetId = ref(null)
const editForm = ref(blank())
const editError = ref('')
const speichert = ref(false)

const bibelFehler = ref('')

async function load() {
  try { liste.value = await glossar.eintraege(); loadError.value = '' }
  catch (e) { loadError.value = e.message }
}

const gefiltert = computed(() => {
  const s = suche.value.trim().toLowerCase()
  const basis = !s ? liste.value
    : liste.value.filter((e) => [e.wort, e.transliteration, e.erklaerung].some((t) => (t || '').toLowerCase().includes(s)))
  return [...basis].sort((a, b) => a.wort.localeCompare(b.wort, 'de'))
})

function stellenListe(text) {
  return (text || '').split(/[;\n]/).map((s) => s.trim()).filter(Boolean)
}

async function add() {
  error.value = ''
  try {
    await glossar.add({ wort: form.value.wort, transliteration: form.value.transliteration,
      erklaerung: form.value.erklaerung, stellen: stellenListe(form.value.stellenText) })
    anlegen.value = false
    form.value = blank()
    await load()
  } catch (e) { error.value = e.message }
}

async function remove(e) {
  if (!confirm(`„${e.wort}“ aus dem Glossar löschen?`)) return
  await glossar.remove(e.id)
  await load()
}

function openEdit(e) {
  editError.value = ''
  editForm.value = { wort: e.wort, transliteration: e.transliteration || '', erklaerung: e.erklaerung || '',
    stellenText: (e.stellen || []).map(stelleAnzeige).join('; ') }
  bearbeitetId.value = e.id
}

async function saveEdit() {
  editError.value = ''
  speichert.value = true
  try {
    await glossar.update(bearbeitetId.value, { wort: editForm.value.wort, transliteration: editForm.value.transliteration,
      erklaerung: editForm.value.erklaerung, stellen: stellenListe(editForm.value.stellenText) })
    bearbeitetId.value = null
    await load()
  } catch (e) { editError.value = e.message }
  finally { speichert.value = false }
}

// Kanonische Adresse ("Joh.3.16") -> lesbare, kurze Schreibweise ("Joh 3,16") fürs Chip und für /api/bibel/stelle
// (das freien Text wie "Joh 3,16" erwartet, nicht die kanonische Punkt-Schreibweise).
function stelleAnzeige(stelle) {
  const teile = stelle.split('.')
  return teile.length >= 3 ? `${teile[0]} ${teile[1]},${teile[2]}` : stelle
}

async function inBibelOeffnen(stelle) {
  bibelFehler.value = ''
  const text = stelleAnzeige(stelle)
  try {
    const { seite } = await bibel.stelle(text)
    window.open(bibel.dateiUrl(seite), '_blank')
  } catch (e) { bibelFehler.value = `${text}: ${e.message}` }
}

onMounted(load)
</script>

<template>
  <h1 class="text-3xl font-semibold tracking-tight">Glossar</h1>
  <p class="mt-1 text-slate-500 dark:text-slate-400">
    Griechische Wörter mit Transliteration, Erklärung und Bibelstellen – unabhängig vom Fach.
  </p>

  <div class="mt-6 flex flex-wrap items-center justify-between gap-3">
    <input v-model="suche" class="input max-w-xs" placeholder="Suchen …" aria-label="Glossar durchsuchen" />
    <button v-if="!anlegen" type="button" class="btn btn-outline !py-1.5" @click="anlegen = true">+ Neuer Eintrag</button>
  </div>

  <form v-if="anlegen" class="panel mt-4 grid gap-3 p-4" @submit.prevent="add">
    <div class="grid gap-3 sm:grid-cols-2">
      <input v-model="form.wort" class="input" placeholder="Griechisches Wort, z. B. ἀγάπη" aria-label="Griechisches Wort" />
      <input v-model="form.transliteration" class="input" placeholder="Transliteration, z. B. agapē" aria-label="Transliteration" />
    </div>
    <textarea v-model="form.erklaerung" class="input" rows="3" placeholder="Erklärung" aria-label="Erklärung" />
    <input v-model="form.stellenText" class="input" placeholder="Bibelstellen, z. B. Joh 3,16; 1Kor 13,4" aria-label="Bibelstellen" />
    <p class="text-xs text-slate-500 dark:text-slate-400">Mehrere Stellen mit Semikolon trennen, jede braucht einen Vers (z. B. „Joh 3,16“, nicht „Joh 3“).</p>
    <div>
      <button class="btn btn-primary">Eintrag anlegen</button>
      <button type="button" class="btn btn-ghost ml-2" @click="anlegen = false; form = blank()">Abbrechen</button>
      <span v-if="error" class="ml-3 text-sm text-rose-600 dark:text-rose-400">{{ error }}</span>
    </div>
  </form>

  <p v-if="loadError" class="mt-6 text-sm text-rose-600 dark:text-rose-400">{{ loadError }}</p>
  <p v-if="bibelFehler" class="mt-4 text-sm text-rose-600 dark:text-rose-400">{{ bibelFehler }}</p>

  <ul v-if="!loadError && gefiltert.length" class="mt-6 grid items-start gap-3 sm:grid-cols-2">
    <li v-for="e in gefiltert" :key="e.id" class="panel min-w-0 p-4">
      <div v-if="bearbeitetId !== e.id">
        <div class="flex items-start justify-between gap-2">
          <div class="min-w-0">
            <div class="flex items-center gap-1.5">
              <p class="truncate text-lg font-semibold">{{ e.wort }}</p>
              <button class="btn btn-ghost !p-1.5 shrink-0" :aria-label="`${e.wort} bearbeiten`" @click="openEdit(e)">
                <AppIcon name="stift" class="h-3.5 w-3.5" />
              </button>
            </div>
            <p v-if="e.transliteration" class="text-sm italic text-slate-500 dark:text-slate-400">{{ e.transliteration }}</p>
          </div>
          <button class="btn btn-danger !px-2.5 !py-1 shrink-0" :aria-label="`${e.wort} löschen`" @click="remove(e)">Löschen</button>
        </div>
        <p v-if="e.erklaerung" class="mt-2 text-sm">{{ e.erklaerung }}</p>
        <div v-if="e.stellen?.length" class="mt-3 flex flex-wrap gap-1.5">
          <button v-for="s in e.stellen" :key="s" type="button" :title="`${stelleAnzeige(s)} – in der Bibel öffnen`"
            class="rounded-full bg-backdrop px-2.5 py-1 text-xs font-medium text-theme-inv opacity-80 transition hover:opacity-100"
            @click="inBibelOeffnen(s)">{{ stelleAnzeige(s) }}</button>
        </div>
      </div>

      <form v-else class="grid gap-2" @submit.prevent="saveEdit">
        <input v-model="editForm.wort" class="input" placeholder="Griechisches Wort" aria-label="Griechisches Wort" />
        <input v-model="editForm.transliteration" class="input" placeholder="Transliteration" aria-label="Transliteration" />
        <textarea v-model="editForm.erklaerung" class="input" rows="3" placeholder="Erklärung" aria-label="Erklärung" />
        <input v-model="editForm.stellenText" class="input" placeholder="Bibelstellen, z. B. Joh 3,16; 1Kor 13,4" aria-label="Bibelstellen" />
        <div class="flex gap-2">
          <button class="btn btn-primary !py-1.5" :disabled="speichert">{{ speichert ? 'Speichert …' : 'Speichern' }}</button>
          <button type="button" class="btn btn-ghost !py-1.5" @click="bearbeitetId = null">Abbrechen</button>
        </div>
        <p v-if="editError" class="text-sm text-rose-600 dark:text-rose-400">{{ editError }}</p>
      </form>
    </li>
    <li v-if="!anlegen">
      <button class="panel flex min-h-32 w-full flex-col items-center justify-center gap-2 p-5 text-sm font-medium opacity-70 hover:opacity-100"
        @click="anlegen = true">
        <AppIcon name="plus" class="h-6 w-6" />
        Neuer Eintrag
      </button>
    </li>
  </ul>
  <EmptyState v-if="!loadError && !gefiltert.length && !anlegen && !liste.length" title="Noch kein Eintrag"
    text="Lege den ersten griechischen Begriff an.">
    <button class="btn btn-primary" @click="anlegen = true">Ersten Eintrag anlegen</button>
  </EmptyState>
  <p v-else-if="!loadError && !gefiltert.length && liste.length" class="mt-6 text-sm text-slate-500 dark:text-slate-400">
    Kein Eintrag passt zur Suche.
  </p>
</template>
