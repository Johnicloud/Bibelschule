<script setup>
import { computed, inject, onMounted, ref, watch } from 'vue'
import DeckPanel from './DeckPanel.vue'
import AufgabenPanel from '../components/aufgaben/AufgabenPanel.vue'
import ReadingPanel from '../components/reading/ReadingPanel.vue'
import RegisterPanel from '../components/register/RegisterPanel.vue'
import ExternalPanel from '../components/ui/ExternalPanel.vue'
import SubjectOverview from '../components/ui/SubjectOverview.vue'
import AppIcon from '../components/ui/AppIcon.vue'
import DozentenAuswahl from '../components/ui/DozentenAuswahl.vue'
import { BAR_CLASSES, FACH_STATUS, OPTIONAL_SERVICES, TAB_ICONS } from '../domain/status'

const props = defineProps({ subjectId: String, tab: { type: String, default: 'uebersicht' } })
defineEmits(['study', 'update:tab'])
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

// Reiter = Übersicht (Kurzüberblick, erster Reiter), Aufgaben und Lesenachweis sind fest; Register/Karteikarten/
// Bibelverse/Skripte sind optional und erscheinen erst, wenn im Fach aktiviert (subject.aktive_dienste) –
// siehe SubjectOverview.vue, wo man sie hinzufügen kann. Adressbuch erscheint hier nie (siehe status.js).
const tabs = computed(() => [
  { name: 'uebersicht', label: 'Übersicht' },
  { name: 'aufgaben', label: 'Aufgaben' },
  ...services.value.filter((s) => s.name === 'lesenachweis'),
  ...services.value.filter((s) => OPTIONAL_SERVICES.includes(s.name) && (subject.value?.aktive_dienste || []).includes(s.name)),
])
const current = computed(() => tabs.value.find((t) => t.name === props.tab) || tabs.value[0])

async function dienstAktivieren(name) {
  subject.value = await subjects.setAktiveDienste(props.subjectId, [...(subject.value.aktive_dienste || []), name])
}

// Der Gesamtfortschritt wird neu geholt, wenn ein Reiter etwas geändert hat (Karte, Lesen, Register).
// Auch das Fach selbst (subject.aufgaben kann sich geändert haben, z. B. Pensum-Verknüpfung), damit die
// Übersicht nicht die veraltete Aufgabenliste vom ersten Laden zeigt.
async function loadOverview() {
  try {
    ;[subject.value, overview.value] = await Promise.all([subjects.get(props.subjectId), subjects.overviewOf(props.subjectId)])
  } catch { /* Anzeige bleibt wie sie war */ }
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
  <p v-if="error" class="text-sm text-rose-600 dark:text-rose-400">{{ error }}</p>
  <template v-if="subject && current">
    <div class="panel p-5">
      <template v-if="!bearbeiten">
        <div class="flex flex-wrap items-center gap-x-3 gap-y-1">
          <h1 class="text-3xl font-semibold tracking-tight">{{ subject.name }}</h1>
          <button class="btn btn-ghost !p-2 ml-auto" aria-label="Fach bearbeiten" @click="openEdit">
            <AppIcon name="stift" class="h-4 w-4" />
          </button>
        </div>
        <!-- Nur ein Farbbalken: Farbe nach Fach-Status, Breite nach Gesamtfortschritt – keine Zahl, kein
             Satz, kein eigener Status-Chip mehr (auf Wunsch so minimal). -->
        <div v-if="overview && overview.progress != null" class="mt-3 h-2 overflow-hidden rounded-full bg-highlight"
          role="progressbar" :aria-valuenow="overview.progress" aria-valuemin="0" aria-valuemax="100"
          :aria-label="FACH_STATUS[overview.stufe]?.label">
          <div class="h-full rounded-full" :class="BAR_CLASSES[FACH_STATUS[overview.stufe]?.tone || 'teal']" :style="{ width: overview.progress + '%' }"></div>
        </div>
      </template>

      <form v-else class="grid gap-3" @submit.prevent="saveEdit">
        <input v-model="editName" class="input" placeholder="Name des Fachs" aria-label="Name des Fachs" />
        <div class="flex flex-wrap items-start gap-4">
          <div class="flex gap-2">
            <input v-model="editSe" type="number" min="0" step="0.5" class="input !w-24" placeholder="SE" aria-label="Studieneinheiten" />
            <input v-model="editCredits" type="number" min="0" step="0.1" class="input !w-28" placeholder="Credits" aria-label="Credits" />
          </div>
          <DozentenAuswahl v-model="ausgewaehlteDozenten" :dozenten="alleDozenten" class="flex-1" />
        </div>
        <div class="flex gap-2">
          <button class="btn btn-primary" :disabled="speichert">{{ speichert ? 'Speichert …' : 'Speichern' }}</button>
          <button type="button" class="btn btn-ghost" @click="bearbeiten = false">Abbrechen</button>
        </div>
        <p v-if="editError" class="text-sm text-rose-600 dark:text-rose-400">{{ editError }}</p>
      </form>
    </div>

    <!-- So breit wie die Kachel darüber: Pillen-Leiste wie AppNav.vue statt schmalem Unterstrich-Streifen,
         die Reiter teilen sich die volle Breite gleichmäßig auf, Symbole entsprechend größer. -->
    <div class="mt-6 flex gap-1 rounded-xl bg-backdrop p-1" role="tablist">
      <button v-for="t in tabs" :key="t.name" role="tab" :aria-selected="current.name === t.name"
        :title="t.label" :aria-label="t.label"
        class="flex flex-1 items-center justify-center rounded-lg py-3 text-theme-inv opacity-70 transition hover:opacity-100"
        :class="current.name === t.name ? 'bg-primary text-white opacity-100 shadow-sm' : ''"
        @click="$emit('update:tab', t.name)">
        <AppIcon :name="TAB_ICONS[t.name] || 'baustein'" class="h-6 w-6" />
      </button>
    </div>

    <div class="mt-6" role="tabpanel">
      <SubjectOverview v-if="current.name === 'uebersicht' && overview" :subject="subject" :overview="overview" :services="services"
        @go="(name) => $emit('update:tab', name)" @aktivieren="(name) => dienstAktivieren(name).then(() => $emit('update:tab', name))" />
      <AufgabenPanel v-else-if="current.name === 'aufgaben'" :subject-id="subjectId" @changed="loadOverview" />
      <DeckPanel v-else-if="current.name === 'karteikarten'" :subject-id="subjectId" @study="$emit('study')" @changed="loadOverview" />
      <ReadingPanel v-else-if="current.name === 'lesenachweis'" :subject-id="subjectId" @changed="loadOverview" />
      <RegisterPanel v-else-if="current.name === 'register'" :subject-id="subjectId" @changed="loadOverview" />
      <ExternalPanel v-else :src="`/api/${current.name}/${current.panel}?subject=${encodeURIComponent(subjectId)}`" :title="current.label" />
    </div>
  </template>
</template>
