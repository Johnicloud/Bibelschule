<script setup>
import { computed, inject, onMounted, ref } from 'vue'
import AppIcon from './AppIcon.vue'
import EmptyState from './EmptyState.vue'
import { BAR_CLASSES, OPTIONAL_SERVICES, READING_STATUS, TAB_ICONS, TONE_CLASSES, formatDate } from '../../domain/status'

// Erster Reiter im Fach: die Aufgaben (der Umfang des Fachs) direkt hier abhakbar – kein eigener Aufgaben-Reiter
// mehr (siehe SubjectView.vue). Jede Aufgabe entweder mit einem einfachen Erledigt-Häkchen, oder, ist sie
// mit einem Lesenachweis-Pensum ODER einer Registerkarte verknüpft, mit dessen echtem Stand (Lesestatus bzw.
// Eintragszahl – ein Register meldet keinen echten Status, siehe Projektnotizen) statt eines Häkchens.
// Darunter die optionalen Dienste: aktive als Kachel zum Weiterspringen, inaktive als „+ hinzufügen“-Kachel
// (schaltet den Reiter dafür frei, siehe SubjectView.vue `dienstAktivieren`).
const props = defineProps({ subject: Object, overview: Object, services: { type: Array, default: () => [] } })
const emit = defineEmits(['go', 'aktivieren', 'changed'])
const subjects = inject('subjects')
const reading = inject('reading')
const register = inject('register')
const aufgabenleser = inject('aufgabenleser')

const pensen = ref([])
const registers = ref([])
async function ladenVerweisQuellen() {
  try { pensen.value = await reading.list(props.subject.id) } catch { pensen.value = [] }
  try { registers.value = await register.registers(props.subject.id) } catch { registers.value = [] }
}
onMounted(ladenVerweisQuellen)

function pensumStatus(pensumId) {
  const t = pensen.value.find((p) => p.id === pensumId)
  return t ? READING_STATUS[t.forecast.status] : null
}
function registerEintraege(registerId) {
  return registers.value.find((r) => r.id === registerId)?.entry_count
}

async function refresh() { await ladenVerweisQuellen(); emit('changed') }

async function toggle(a) { await subjects.setAufgabeErledigt(props.subject.id, a.id, !a.erledigt); await refresh() }
async function remove(a) {
  if (!confirm(`Aufgabe „${a.titel}“ löschen?`)) return
  await subjects.removeAufgabe(props.subject.id, a.id)
  await refresh()
}
async function verweisSetzen(a, value) {
  if (value.startsWith('r:')) await subjects.setAufgabeRegister(props.subject.id, a.id, value.slice(2))
  else if (value) await subjects.setAufgabePensum(props.subject.id, a.id, value)
  else if (a.register_id) await subjects.setAufgabeRegister(props.subject.id, a.id, null)
  else await subjects.setAufgabePensum(props.subject.id, a.id, null)
  await refresh()
}

// Neue Aufgabe von Hand anlegen, hinter einem Knopf statt dauerhaft offen (wie Pensum/Dozent/Fach).
const anlegen = ref(false)
const titel = ref('')
const frist = ref('')
const gewichtung = ref('')
const error = ref('')
async function add() {
  error.value = ''
  try {
    await subjects.addAufgabe(props.subject.id, titel.value, frist.value, gewichtung.value)
    anlegen.value = false
    titel.value = ''
    frist.value = ''
    gewichtung.value = ''
    await refresh()
  } catch (e) { error.value = e.message }
}

// Erkennt Vorschläge, die eigentlich ein Lesepensum sind (z. B. „Pflicht-Lektüre 600 Seiten“), an der
// Mengenangabe im Titel – der aufgabenleser-Dienst kennt den Lesenachweis nicht, das bleibt reine
// Frontend-Orchestrierung (wie die Dozentenzuordnung beim Fach-Anlegen, siehe Projektnotizen).
const LESE_MUSTER = /(\d+)\s*(seiten|kapitel)\b/i
function leseErkennung(titelText) {
  const treffer = (titelText || '').match(LESE_MUSTER)
  if (!treffer) return null
  return { total: Number(treffer[1]), unit: treffer[2].toLowerCase() === 'kapitel' ? 'Kapitel' : 'Seiten' }
}
const dateiInput = ref(null)
const liestEin = ref(false)
const leseFehler = ref('')
const rohtextKi = ref('')
const vorschlaege = ref([])        // [{ titel, frist, gewichtung, ausgewaehlt }]
const legtAn = ref(false)
async function dateiGewaehlt(e) {
  const datei = e.target.files[0]
  e.target.value = ''
  if (!datei) return
  leseFehler.value = ''
  vorschlaege.value = []
  rohtextKi.value = ''
  liestEin.value = true
  try {
    const ergebnis = await aufgabenleser.lesen(datei)
    vorschlaege.value = ergebnis.vorschlaege.map((v, i) => ({ ...v, id: i, ausgewaehlt: true, lese: leseErkennung(v.titel) }))
    rohtextKi.value = ergebnis.rohtext_ki || ''
    if (!vorschlaege.value.length) leseFehler.value = 'Daraus ließ sich kein Vorschlag lesen. Antwort der KI unten, Aufgaben ggf. von Hand anlegen.'
  } catch (e) { leseFehler.value = e.message }
  finally { liestEin.value = false }
}
const aufgabenVorschlaege = computed(() => vorschlaege.value.filter((v) => !v.lese))
const leseVorschlaege = computed(() => vorschlaege.value.filter((v) => v.lese))
async function vorschlaegeUebernehmen() {
  const ausgewaehlt = vorschlaege.value.filter((v) => v.ausgewaehlt)
  if (!ausgewaehlt.length) return
  legtAn.value = true
  try {
    for (const v of ausgewaehlt) {
      if (v.lese) await reading.add(props.subject.id, { title: v.titel, unit: v.lese.unit, total: v.lese.total, passes: 1, start: '', deadline: v.frist || '' })
      else await subjects.addAufgabe(props.subject.id, v.titel, v.frist, v.gewichtung)
    }
    vorschlaege.value = []
    rohtextKi.value = ''
    await refresh()
  } catch (e) { leseFehler.value = e.message }
  finally { legtAn.value = false }
}
function vorschlaegeVerwerfen() { vorschlaege.value = []; rohtextKi.value = ''; leseFehler.value = '' }

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
    <div class="mb-3 flex items-center justify-between">
      <h2 class="text-lg font-semibold">Aufgaben</h2>
      <div class="flex gap-2">
        <label class="btn btn-outline !py-1.5 inline-flex cursor-pointer" :title="'Lädt ein Aufgabenblatt (PDF) hoch; eine lokale KI (Ollama) schlägt daraus Aufgaben vor – nur ein Vorschlag, geprüft wird vor dem Anlegen.'">
          {{ liestEin ? 'Liest ein …' : 'PDF auswählen' }}
          <input ref="dateiInput" type="file" accept="application/pdf" class="hidden" :disabled="liestEin" @change="dateiGewaehlt" />
        </label>
        <button type="button" class="btn btn-outline !py-1.5" @click="anlegen = true">+ Aufgabe</button>
      </div>
    </div>

    <p v-if="leseFehler" class="mb-4 text-sm text-rose-600 dark:text-rose-400">{{ leseFehler }}</p>

    <div v-if="vorschlaege.length" class="panel mb-4 p-4">
      <div v-if="aufgabenVorschlaege.length">
        <p class="mb-2 flex items-center gap-1.5 text-xs font-medium uppercase tracking-wide text-slate-400 dark:text-slate-500">
          <AppIcon name="aufgaben" class="h-3.5 w-3.5" /> Aufgaben
        </p>
        <ul class="grid gap-2">
          <li v-for="v in aufgabenVorschlaege" :key="v.id" class="flex items-center gap-3 rounded-xl border border-slate-200 p-3 transition hover:border-primary dark:border-slate-700">
            <input type="checkbox" v-model="v.ausgewaehlt" class="h-5 w-5 shrink-0 rounded-md" :aria-label="`${v.titel} übernehmen`" />
            <div class="min-w-0 flex-1">
              <p>{{ v.titel }}</p>
              <p v-if="v.frist || v.gewichtung != null" class="text-sm text-slate-500 dark:text-slate-400">
                <template v-if="v.frist">Frist {{ formatDate(v.frist) }}</template>
                <template v-if="v.frist && v.gewichtung != null"> · </template>
                <template v-if="v.gewichtung != null">{{ v.gewichtung }} % der Bewertung</template>
              </p>
            </div>
          </li>
        </ul>
      </div>

      <div v-if="leseVorschlaege.length" class="mt-4">
        <p class="mb-2 flex items-center gap-1.5 text-xs font-medium uppercase tracking-wide text-slate-400 dark:text-slate-500">
          <AppIcon name="lesenachweis" class="h-3.5 w-3.5" /> Lesepensen
        </p>
        <ul class="grid gap-2">
          <li v-for="v in leseVorschlaege" :key="v.id" class="flex items-center gap-3 rounded-xl border border-teal-200 bg-teal-50/50 p-3 transition hover:border-primary dark:border-teal-900 dark:bg-teal-500/5">
            <input type="checkbox" v-model="v.ausgewaehlt" class="h-5 w-5 shrink-0 rounded-md" :aria-label="`${v.titel} übernehmen`" />
            <div class="min-w-0 flex-1">
              <p>{{ v.titel }}</p>
              <p class="text-sm text-slate-500 dark:text-slate-400">
                → Lesenachweis · {{ v.lese.total }} {{ v.lese.unit }}
                <template v-if="v.frist"> · Frist {{ formatDate(v.frist) }}</template>
              </p>
            </div>
          </li>
        </ul>
      </div>
      <div class="mt-3 flex gap-2">
        <button class="btn btn-primary" :disabled="legtAn || !vorschlaege.some((v) => v.ausgewaehlt)" @click="vorschlaegeUebernehmen">
          {{ legtAn ? 'Legt an …' : 'Ausgewählte übernehmen' }}
        </button>
        <button class="btn btn-ghost" @click="vorschlaegeVerwerfen">Verwerfen</button>
      </div>

      <details v-if="rohtextKi" class="mt-3 text-sm text-slate-500 dark:text-slate-400">
        <summary class="cursor-pointer">Antwort der KI im Wortlaut</summary>
        <pre class="mt-2 whitespace-pre-wrap">{{ rohtextKi }}</pre>
      </details>
    </div>

    <form v-if="anlegen" class="panel mb-4 grid gap-3 p-4 sm:grid-cols-[1fr_10rem_8rem_auto]" @submit.prevent="add">
      <input v-model="titel" class="input" placeholder="Titel, z. B. Exegese Kapitel 3" aria-label="Titel der Aufgabe" />
      <input v-model="frist" type="date" class="input" aria-label="Frist (optional)" />
      <input v-model="gewichtung" type="number" min="0" max="100" class="input" placeholder="Gewichtung %" aria-label="Anteilige Bewertung in Prozent (optional)" />
      <button class="btn btn-primary">Anlegen</button>
      <button type="button" class="btn btn-ghost" @click="anlegen = false">Abbrechen</button>
      <p v-if="error" class="text-sm text-rose-600 dark:text-rose-400 sm:col-span-4">{{ error }}</p>
    </form>

    <ul v-if="subject.aufgaben.length" class="grid gap-2">
      <li v-for="a in subject.aufgaben" :key="a.id" class="panel flex items-center gap-3 p-3">
        <button v-if="!a.pensum_id && !a.register_id" type="button" class="grid h-8 w-8 shrink-0 place-items-center rounded-full border transition"
          :class="a.erledigt ? 'border-transparent bg-primary text-white' : 'border-highlight opacity-40 hover:opacity-70'"
          :aria-pressed="a.erledigt" :aria-label="`${a.titel} ${a.erledigt ? 'als offen markieren' : 'als erledigt markieren'}`"
          @click="toggle(a)">
          <AppIcon name="haken" class="h-4 w-4" />
        </button>
        <span v-else-if="a.pensum_id && pensumStatus(a.pensum_id)" class="shrink-0 rounded-full px-2 py-0.5 text-xs font-medium" :class="TONE_CLASSES[pensumStatus(a.pensum_id).tone]">
          {{ pensumStatus(a.pensum_id).label }}
        </span>
        <span v-else-if="a.register_id" class="shrink-0 rounded-full bg-highlight px-2 py-0.5 text-xs opacity-70">
          {{ registerEintraege(a.register_id) ?? 0 }} {{ registerEintraege(a.register_id) === 1 ? 'Eintrag' : 'Einträge' }}
        </span>

        <div class="min-w-0 flex-1">
          <p :class="a.erledigt && !a.pensum_id && !a.register_id ? 'text-slate-400 line-through dark:text-slate-500' : ''">{{ a.titel }}</p>
          <p v-if="a.frist" class="text-xs opacity-70">Frist {{ formatDate(a.frist) }}</p>
          <select v-if="pensen.length || registers.length" class="input !mt-1 !w-auto !py-1 text-xs"
            :value="a.register_id ? 'r:' + a.register_id : (a.pensum_id || '')"
            :aria-label="`${a.titel} verknüpfen`" @change="verweisSetzen(a, $event.target.value)">
            <option value="">Kein Verweis</option>
            <optgroup v-if="pensen.length" label="Lesepensum">
              <option v-for="p in pensen" :key="p.id" :value="p.id">{{ p.title }}</option>
            </optgroup>
            <optgroup v-if="registers.length" label="Register">
              <option v-for="r in registers" :key="r.id" :value="'r:' + r.id">{{ r.name }}</option>
            </optgroup>
          </select>
        </div>

        <button type="button" class="btn btn-ghost !p-1.5" :aria-label="`${a.titel} löschen`" @click="remove(a)">
          <AppIcon name="x" class="h-4 w-4" />
        </button>
      </li>
    </ul>
    <EmptyState v-else-if="!anlegen" title="Noch keine Aufgabe" text="Lege die erste Aufgabe an, um den Umfang des Fachs festzuhalten.">
      <button class="btn btn-primary" @click="anlegen = true">Erste Aufgabe anlegen</button>
    </EmptyState>

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
