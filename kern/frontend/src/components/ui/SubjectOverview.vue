<script setup>
import { computed, inject, onMounted, ref } from 'vue'
import AppIcon from './AppIcon.vue'
import { BAR_CLASSES, OPTIONAL_SERVICES, READING_STATUS, TAB_ICONS, TONE_CLASSES, artInfo, formatDate, tageBisText } from '../../domain/status'

// Erster Reiter im Fach: besteht aus den Aufgaben (der Umfang des Fachs) – jede mit einem erledigt/offen-Feld,
// oder, ist sie mit einem Lesenachweis-Pensum verknüpft (Aufgabe bearbeiten -> „Lesepensum“), mit dessen
// echtem Lesestatus. Darunter die optionalen Dienste: aktive als Kachel zum Weiterspringen, inaktive als
// „+ hinzufügen“-Kachel (schaltet den Reiter dafür frei, siehe SubjectView.vue `dienstAktivieren`).
const props = defineProps({ subject: Object, overview: Object, services: { type: Array, default: () => [] } })
const emit = defineEmits(['go', 'aktivieren'])
const reading = inject('reading')

const pensen = ref([])
async function ladenPensen() {
  try { pensen.value = await reading.list(props.subject.id) } catch { pensen.value = [] }
}
onMounted(ladenPensen)

function pensumStatus(pensumId) {
  const t = pensen.value.find((p) => p.id === pensumId)
  return t ? READING_STATUS[t.forecast.status] : null
}

const aktiveDienste = computed(() => new Set(props.subject.aktive_dienste || []))
const optionaleDienste = computed(() => props.services.filter((s) => OPTIONAL_SERVICES.includes(s.name)))

const dienstRows = computed(() => props.overview.parts
  .filter((p) => aktiveDienste.value.has(p.service))
  .map((p) => {
    const st = props.overview.status[p.service]
    const row = { key: p.service, label: p.label, progress: p.progress, text: '', chip: null }
    if (!p.online || !st) { row.text = 'nicht erreichbar'; return row }
    if (p.service === 'karteikarten') {
      row.text = st.card_count
        ? `${st.mastered} von ${st.card_count} Karten sicher gelernt, ${st.due_count} fällig`
        : 'Noch keine Karten'
    } else if (p.service === 'register') {
      row.text = st.entries
        ? `${st.entries} ${st.entries === 1 ? 'Eintrag' : 'Einträge'} in ${st.registers} ${st.registers === 1 ? 'Register' : 'Registern'}`
        : st.registers ? `${st.registers} Register, noch ohne Einträge` : 'Noch kein Register'
    } else {
      const fields = props.services.find((s) => s.name === p.service)?.fields ?? []
      row.text = fields.map((f) => `${st[f.key]} ${f.label}`).join(', ')
    }
    return row
  }))
</script>

<template>
  <div>
    <h2 class="mb-3 text-lg font-semibold">Aufgaben</h2>
    <ul v-if="subject.aufgaben.length" class="grid gap-3 sm:grid-cols-2">
      <li v-for="a in subject.aufgaben" :key="a.id">
        <button type="button" class="panel w-full p-4 text-left transition hover:-translate-y-0.5 hover:shadow-md" @click="emit('go', 'aufgaben')">
          <div class="flex items-start justify-between gap-2">
            <span class="text-sm font-medium">{{ a.titel }}</span>
            <template v-if="a.pensum_id && pensumStatus(a.pensum_id)">
              <span class="shrink-0 rounded-full px-2 py-0.5 text-xs" :class="TONE_CLASSES[pensumStatus(a.pensum_id).tone]">
                {{ pensumStatus(a.pensum_id).label }}
              </span>
            </template>
            <span v-else class="shrink-0 rounded-full px-2 py-0.5 text-xs font-medium"
              :class="a.erledigt ? 'bg-teal-100 text-teal-800 dark:bg-teal-500/15 dark:text-teal-300' : 'bg-highlight opacity-70'">
              {{ a.erledigt ? 'Erledigt' : 'Offen' }}
            </span>
          </div>
          <p v-if="a.art !== 'allgemein' || !a.zaehlt" class="mt-1 text-xs opacity-70">
            {{ artInfo(a.art).label }}<template v-if="!a.zaehlt"> · nur zum Lernen</template>
          </p>
          <p v-if="a.frist" class="mt-1.5 text-xs opacity-70">
            {{ artInfo(a.art).frist }} {{ formatDate(a.frist) }}<template v-if="!a.erledigt"> ({{ tageBisText(a.frist) }})</template>
          </p>
          <p v-if="artInfo(a.art).umfang && a.soll" class="mt-1 text-xs opacity-70">{{ a.ist ?? 0 }} von {{ a.soll }} {{ a.einheit }} · {{ a.fortschritt }} %</p>
        </button>
      </li>
    </ul>
    <p v-else class="text-sm opacity-70">Noch keine Aufgabe – im Reiter „Aufgaben“ eintragen.</p>

    <h2 class="mb-3 mt-8 text-lg font-semibold">Weitere Felder</h2>
    <ul class="grid gap-4 sm:grid-cols-2">
      <li v-for="s in optionaleDienste" :key="s.name">
        <button v-if="aktiveDienste.has(s.name)" type="button"
          class="panel w-full p-4 text-left transition hover:-translate-y-0.5 hover:shadow-md" @click="emit('go', s.name)">
          <div class="flex items-center justify-between gap-2">
            <span class="flex items-center gap-2 text-sm font-medium">
              <AppIcon :name="TAB_ICONS[s.name] || 'baustein'" class="h-4 w-4 opacity-70" />
              {{ s.label }}
            </span>
            <span v-if="dienstRows.find((r) => r.key === s.name)?.progress != null" class="text-sm tabular-nums opacity-70">
              {{ dienstRows.find((r) => r.key === s.name).progress }} %
            </span>
          </div>
          <div v-if="dienstRows.find((r) => r.key === s.name)?.progress != null" class="mt-2 h-1.5 overflow-hidden rounded-full bg-highlight" aria-hidden="true">
            <div class="h-full rounded-full" :class="BAR_CLASSES.teal" :style="{ width: dienstRows.find((r) => r.key === s.name).progress + '%' }"></div>
          </div>
          <p class="mt-2 text-xs opacity-70">{{ dienstRows.find((r) => r.key === s.name)?.text }}</p>
        </button>
        <button v-else type="button"
          class="panel flex h-full w-full flex-col items-center justify-center gap-2 p-4 text-sm font-medium opacity-70 hover:opacity-100"
          @click="emit('aktivieren', s.name)">
          <AppIcon name="plus" class="h-5 w-5" />
          {{ s.label }} hinzufügen
        </button>
      </li>
    </ul>
  </div>
</template>
