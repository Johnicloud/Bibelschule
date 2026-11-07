<script setup>
import { inject, onMounted, ref } from 'vue'
import AppIcon from '../components/ui/AppIcon.vue'
import EmptyState from '../components/ui/EmptyState.vue'

const subjects = inject('subjects')
const liste = ref([])
const auswertung = ref(null)
const loadError = ref('')

const bearbeitetId = ref(null)
const editNote = ref('')
const editError = ref('')
const speichert = ref(false)

async function load() {
  try {
    ;[liste.value, auswertung.value] = await Promise.all([subjects.list(), subjects.noten()])
    loadError.value = ''
  } catch (e) { loadError.value = e.message }
}
function openEdit(s) {
  editError.value = ''
  editNote.value = s.note ?? ''
  bearbeitetId.value = s.id
}
async function saveEdit(s) {
  editError.value = ''
  speichert.value = true
  try {
    await subjects.setNote(s.id, editNote.value)
    bearbeitetId.value = null
    await load()
  } catch (e) { editError.value = e.message }
  finally { speichert.value = false }
}
onMounted(load)
</script>

<template>
  <h1 class="text-3xl font-semibold tracking-tight">Noten</h1>
  <p class="mt-1 text-slate-500 dark:text-slate-400">Deine Note je Fach und der Durchschnitt über alle benoteten Fächer (gewichtet nach SE).</p>

  <p v-if="loadError" class="mt-6 text-sm text-rose-600 dark:text-rose-400">{{ loadError }}</p>

  <div v-if="auswertung" class="panel mt-6 p-5">
    <p class="text-sm text-slate-500 dark:text-slate-400">Durchschnitt</p>
    <p v-if="auswertung.durchschnitt != null" class="text-4xl font-semibold tabular-nums">{{ auswertung.durchschnitt.toFixed(2).replace('.', ',') }}</p>
    <p v-else class="text-lg opacity-70">Noch keine Note eingetragen</p>
    <p v-if="auswertung.anzahl" class="mt-1 text-sm opacity-70">aus {{ auswertung.anzahl }} {{ auswertung.anzahl === 1 ? 'Fach' : 'Fächern' }}</p>
  </div>

  <ul v-if="liste.length" class="mt-6 grid items-start gap-3 sm:grid-cols-2">
    <li v-for="s in liste" :key="s.id" class="panel min-w-0 p-4">
      <div v-if="bearbeitetId !== s.id" class="flex items-center justify-between gap-2">
        <div>
          <p class="font-semibold">{{ s.name }}</p>
          <p class="text-sm text-slate-500 dark:text-slate-400">
            <span v-if="s.note != null">Note {{ s.note.toFixed(1).replace('.', ',') }}</span>
            <span v-else class="opacity-60">Keine Note</span>
            <template v-if="s.se != null"> · {{ s.se }} SE</template>
          </p>
        </div>
        <button class="btn btn-ghost !p-1.5" :aria-label="`Note für ${s.name} eintragen`" @click="openEdit(s)">
          <AppIcon name="stift" class="h-3.5 w-3.5" />
        </button>
      </div>
      <form v-else class="grid gap-2" @submit.prevent="saveEdit(s)">
        <input v-model="editNote" type="number" min="1" max="5" step="0.1" class="input" placeholder="Note (1,0 bis 5,0)" :aria-label="`Note für ${s.name}`" />
        <div class="flex gap-2">
          <button class="btn btn-primary !py-1.5" :disabled="speichert">{{ speichert ? 'Speichert …' : 'Speichern' }}</button>
          <button type="button" class="btn btn-ghost !py-1.5" @click="bearbeitetId = null">Abbrechen</button>
        </div>
        <p v-if="editError" class="text-sm text-rose-600 dark:text-rose-400">{{ editError }}</p>
      </form>
    </li>
  </ul>
  <EmptyState v-else-if="!loadError" title="Noch kein Fach" text="Lege zuerst ein Fach an, um Noten eintragen zu können." />
</template>
