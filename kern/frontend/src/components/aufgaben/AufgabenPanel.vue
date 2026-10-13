<script setup>
import { inject, onMounted, ref } from 'vue'
import EmptyState from '../ui/EmptyState.vue'
import { formatDate } from '../../domain/status'

const props = defineProps({ subjectId: String })
const emit = defineEmits(['changed'])
const subjects = inject('subjects')

const aufgaben = ref([])
const loadError = ref('')
const error = ref('')
const titel = ref('')
const frist = ref('')
const gewichtung = ref('')

async function load() {
  try { aufgaben.value = (await subjects.get(props.subjectId)).aufgaben; loadError.value = '' }
  catch (e) { loadError.value = e.message }
}
async function refresh() { await load(); emit('changed') }

async function add() {
  error.value = ''
  try {
    await subjects.addAufgabe(props.subjectId, titel.value, frist.value, gewichtung.value)
    titel.value = ''
    frist.value = ''
    gewichtung.value = ''
    await refresh()
  } catch (e) { error.value = e.message }
}
async function toggle(a) { await subjects.setAufgabeErledigt(props.subjectId, a.id, !a.erledigt); await refresh() }
async function remove(a) {
  if (!confirm(`Aufgabe „${a.titel}“ löschen?`)) return
  await subjects.removeAufgabe(props.subjectId, a.id)
  await refresh()
}
onMounted(load)
</script>

<template>
  <h2 class="mb-3 text-lg font-semibold">Neue Aufgabe</h2>
  <form class="panel grid gap-3 p-4 sm:grid-cols-[1fr_10rem_8rem_auto]" @submit.prevent="add">
    <input v-model="titel" class="input" placeholder="Titel, z. B. Exegese Kapitel 3" aria-label="Titel der Aufgabe" />
    <input v-model="frist" type="date" class="input" aria-label="Frist (optional)" />
    <input v-model="gewichtung" type="number" min="0" max="100" class="input" placeholder="Gewichtung %" aria-label="Anteilige Bewertung in Prozent (optional)" />
    <button class="btn btn-primary">Aufgabe anlegen</button>
    <p v-if="error" class="text-sm text-rose-600 dark:text-rose-400 sm:col-span-4">{{ error }}</p>
    <p class="text-xs text-slate-500 dark:text-slate-400 sm:col-span-4">
      Gewichtung = anteilige Bewertung wie im Aufgabenblatt (z. B. Klausur 50 %). Ohne Gewichtung zählt jede Aufgabe gleich viel.
    </p>
  </form>

  <h2 class="mb-3 mt-10 text-lg font-semibold">Umfang dieses Fachs</h2>
  <p v-if="loadError" class="text-sm text-rose-600 dark:text-rose-400">{{ loadError }}</p>
  <ul v-else-if="aufgaben.length" class="grid gap-3">
    <li v-for="a in aufgaben" :key="a.id" class="panel flex items-center gap-3 p-4">
      <input type="checkbox" class="h-5 w-5 shrink-0 rounded-md" :checked="a.erledigt"
        :aria-label="`${a.titel} erledigt`" @change="toggle(a)" />
      <div class="min-w-0 flex-1">
        <p :class="a.erledigt ? 'text-slate-400 line-through dark:text-slate-500' : ''">{{ a.titel }}</p>
        <p v-if="a.frist || a.gewichtung != null" class="text-sm text-slate-500 dark:text-slate-400">
          <template v-if="a.frist">Frist {{ formatDate(a.frist) }}</template>
          <template v-if="a.frist && a.gewichtung != null"> · </template>
          <template v-if="a.gewichtung != null">{{ a.gewichtung }} % der Bewertung</template>
        </p>
      </div>
      <button class="btn btn-danger !px-2.5 !py-1" :aria-label="`${a.titel} löschen`" @click="remove(a)">Löschen</button>
    </li>
  </ul>
  <EmptyState v-else title="Noch keine Aufgabe" text="Lege oben die erste Aufgabe an, um den Umfang des Fachs festzuhalten." />
</template>
