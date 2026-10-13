<script setup>
import { computed, inject, onMounted, ref } from 'vue'
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
const subject = ref(null)
const services = ref([])
const overview = ref(null)
const error = ref('')

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
async function editSe() {
  const next = prompt('Studieneinheiten (SE) dieses Fachs', subject.value.se ?? '')
  if (next === null) return
  subject.value = await subjects.setSe(props.subjectId, next.trim())
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
    <div class="mt-2 flex flex-wrap items-baseline gap-x-3 gap-y-1">
      <h1 class="text-3xl font-semibold tracking-tight">{{ subject.name }}</h1>
      <button class="text-sm text-slate-500 hover:underline dark:text-slate-400" @click="editSe">
        <template v-if="subject.se != null">{{ subject.se }} SE · {{ subject.credits }} Credits</template>
        <template v-else>SE eintragen</template>
      </button>
    </div>

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
