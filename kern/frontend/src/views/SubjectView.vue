<script setup>
import { computed, inject, onMounted, ref, watch } from 'vue'
import DeckPanel from './DeckPanel.vue'
import AufgabenPanel from '../components/aufgaben/AufgabenPanel.vue'
import ReadingPanel from '../components/reading/ReadingPanel.vue'
import RegisterPanel from '../components/register/RegisterPanel.vue'
import ExternalPanel from '../components/ui/ExternalPanel.vue'
import ProgressPanel from '../components/ui/ProgressPanel.vue'
import { NATIVE_SERVICES } from '../domain/status'

const props = defineProps({ subjectId: String, tab: { type: String, default: 'aufgaben' } })
defineEmits(['back', 'study', 'update:tab'])
const subjects = inject('subjects')
const adressbuch = inject('adressbuch')
const subject = ref(null)
const services = ref([])
const overview = ref(null)
const error = ref('')

const bearbeiten = ref(false)
const editName = ref('')
const editSe = ref('')
const editCredits = ref('')
const alleDozenten = ref([])
const ausgewaehlteDozenten = ref([])
const editError = ref('')
const speichert = ref(false)

let syncCredits = false
watch(editSe, (v) => { if (syncCredits) return; syncCredits = true; editCredits.value = v === '' ? '' : (Number(v) * 1.5).toFixed(1); syncCredits = false })
watch(editCredits, (v) => { if (syncCredits) return; syncCredits = true; editSe.value = v === '' ? '' : (Number(v) / 1.5).toFixed(1); syncCredits = false })

// Reiter = Aufgaben (gehört zum Fach im Kern), die eingebauten Dienste und jeder Dienst mit eigener Seite (panel).
const tabs = computed(() => [
  { name: 'aufgaben', label: 'Aufgaben' },
  ...services.value.filter((s) => NATIVE_SERVICES.includes(s.name) || s.panel),
])
const current = computed(() => tabs.value.find((t) => t.name === props.tab) || tabs.value[0])

// Der Gesamtfortschritt wird neu geholt, wenn ein Reiter etwas geändert hat (Karte, Lesen, Register).
async function loadOverview() {
  try { overview.value = await subjects.overviewOf(props.subjectId) } catch { /* Anzeige bleibt wie sie war */ }
}

async function openEdit() {
  editError.value = ''
  editName.value = subject.value.name
  editSe.value = subject.value.se ?? ''
  editCredits.value = subject.value.credits ?? ''
  try { alleDozenten.value = await adressbuch.dozenten() } catch { alleDozenten.value = [] }
  ausgewaehlteDozenten.value = alleDozenten.value.filter((d) => d.faecher.includes(props.subjectId)).map((d) => d.id)
  bearbeiten.value = true
}
async function saveEdit() {
  editError.value = ''
  speichert.value = true
  try {
    if (editName.value.trim() !== subject.value.name) await subjects.rename(props.subjectId, editName.value)
    subject.value = await subjects.setSe(props.subjectId, editSe.value)
    const vorher = new Set(alleDozenten.value.filter((d) => d.faecher.includes(props.subjectId)).map((d) => d.id))
    const nachher = new Set(ausgewaehlteDozenten.value)
    await Promise.all([
      ...[...nachher].filter((id) => !vorher.has(id)).map((id) => adressbuch.assign(id, props.subjectId)),
      ...[...vorher].filter((id) => !nachher.has(id)).map((id) => adressbuch.unassign(id, props.subjectId)),
    ])
    bearbeiten.value = false
    await loadOverview()
  } catch (e) { editError.value = e.message }
  finally { speichert.value = false }
}

onMounted(async () => {
  try {
    ;[subject.value, services.value] = await Promise.all([subjects.get(props.subjectId), subjects.services()])
    loadOverview()
  } catch (e) { error.value = e.message }
})
</script>

<template>
  <button class="btn btn-ghost !px-2" @click="$emit('back')">Zurück zu den Fächern</button>
  <p v-if="error" class="mt-4 text-sm text-rose-600 dark:text-rose-400">{{ error }}</p>
  <template v-if="subject && current">
    <div v-if="!bearbeiten" class="mt-2 flex flex-wrap items-baseline gap-x-3 gap-y-1">
      <h1 class="text-3xl font-semibold tracking-tight">{{ subject.name }}</h1>
      <span v-if="subject.se != null" class="text-sm text-slate-500 dark:text-slate-400">{{ subject.se }} SE · {{ subject.credits }} Credits</span>
      <button class="btn btn-ghost !px-2.5 !py-1 text-sm" @click="openEdit">Bearbeiten</button>
    </div>

    <form v-else class="panel mt-2 grid gap-3 p-4" @submit.prevent="saveEdit">
      <input v-model="editName" class="input" placeholder="Name des Fachs" aria-label="Name des Fachs" />
      <div class="flex flex-wrap items-start gap-4">
        <div class="flex gap-2">
          <input v-model="editSe" type="number" min="0" step="0.5" class="input !w-24" placeholder="SE" aria-label="Studieneinheiten" />
          <input v-model="editCredits" type="number" min="0" step="0.1" class="input !w-28" placeholder="Credits" aria-label="Credits" />
        </div>
        <div v-if="alleDozenten.length" class="flex-1">
          <span class="mb-1.5 block text-sm text-slate-500 dark:text-slate-400">Dozenten</span>
          <div class="flex flex-wrap gap-x-4 gap-y-1.5">
            <label v-for="d in alleDozenten" :key="d.id" class="flex items-center gap-1.5 text-sm">
              <input type="checkbox" :value="d.id" v-model="ausgewaehlteDozenten" class="h-4 w-4 rounded" />
              {{ d.name }}
            </label>
          </div>
        </div>
      </div>
      <div class="flex gap-2">
        <button class="btn btn-primary" :disabled="speichert">{{ speichert ? 'Speichert …' : 'Speichern' }}</button>
        <button type="button" class="btn btn-ghost" @click="bearbeiten = false">Abbrechen</button>
      </div>
      <p v-if="editError" class="text-sm text-rose-600 dark:text-rose-400">{{ editError }}</p>
    </form>

    <ProgressPanel v-if="overview" :overview="overview" :services="services" class="mt-4" />

    <div class="mt-6 flex gap-1 overflow-x-auto border-b border-slate-200 dark:border-slate-800" role="tablist">
      <button v-for="t in tabs" :key="t.name" role="tab" :aria-selected="current.name === t.name"
        class="-mb-px shrink-0 border-b-2 px-4 py-2.5 text-sm font-medium transition"
        :class="current.name === t.name
          ? 'border-teal-600 text-teal-700 dark:border-teal-400 dark:text-teal-300'
          : 'border-transparent text-slate-500 hover:text-slate-900 dark:text-slate-400 dark:hover:text-slate-100'"
        @click="$emit('update:tab', t.name)">
        {{ t.label }}
      </button>
    </div>

    <div class="mt-6" role="tabpanel">
      <AufgabenPanel v-if="current.name === 'aufgaben'" :subject-id="subjectId" @changed="loadOverview" />
      <DeckPanel v-else-if="current.name === 'karteikarten'" :subject-id="subjectId" @study="$emit('study')" @changed="loadOverview" />
      <ReadingPanel v-else-if="current.name === 'lesenachweis'" :subject-id="subjectId" @changed="loadOverview" />
      <RegisterPanel v-else-if="current.name === 'register'" :subject-id="subjectId" @changed="loadOverview" />
      <ExternalPanel v-else :src="`/api/${current.name}/${current.panel}?subject=${encodeURIComponent(subjectId)}`" :title="current.label" />
    </div>
  </template>
</template>
