<script setup>
import { computed, inject, onMounted, ref } from 'vue'
import AppIcon from '../ui/AppIcon.vue'
import EmptyState from '../ui/EmptyState.vue'
import { formatDate } from '../../domain/status'

const props = defineProps({ subjectId: String })
const emit = defineEmits(['changed'])
const subjects = inject('subjects')
const aufgabenleser = inject('aufgabenleser')
const reading = inject('reading')

// Erkennt Vorschläge, die eigentlich ein Lesepensum sind (z. B. „Pflicht-Lektüre 600 Seiten“), an der
// Mengenangabe im Titel – der aufgabenleser-Dienst kennt den Lesenachweis nicht, das bleibt reine
// Frontend-Orchestrierung (wie die Dozentenzuordnung beim Fach-Anlegen, siehe Projektnotizen).
const LESE_MUSTER = /(\d+)\s*(seiten|kapitel)\b/i
function leseErkennung(titel) {
  const treffer = (titel || '').match(LESE_MUSTER)
  if (!treffer) return null
  return { total: Number(treffer[1]), unit: treffer[2].toLowerCase() === 'kapitel' ? 'Kapitel' : 'Seiten' }
}

const aufgaben = ref([])
const pensen = ref([])   // Lesenachweis-Pensen dieses Fachs, zum Verknüpfen mit einer Aufgabe
const loadError = ref('')
const error = ref('')
const anlegen = ref(false)
const titel = ref('')
const frist = ref('')
const gewichtung = ref('')

// Aufgabenblatt (PDF) von Ollama lesen lassen: liefert nur Vorschläge, der Nutzer wählt aus, nichts wird
// automatisch angelegt (siehe Projektnotizen, Entscheidungen: Ergebnisse der KI sind immer nur Vorschläge).
const dateiInput = ref(null)
const liestEin = ref(false)
const leseFehler = ref('')
const rohtextKi = ref('')
const vorschlaege = ref([])        // [{ titel, frist, gewichtung, ausgewaehlt }]
const legtAn = ref(false)

async function load() {
  try {
    aufgaben.value = (await subjects.get(props.subjectId)).aufgaben
    loadError.value = ''
  } catch (e) { loadError.value = e.message }
  try { pensen.value = await reading.list(props.subjectId) } catch { pensen.value = [] }
}
async function refresh() { await load(); emit('changed') }
async function pensumSetzen(a, pensumId) {
  await subjects.setAufgabePensum(props.subjectId, a.id, pensumId || null)
  await refresh()
}

async function add() {
  error.value = ''
  try {
    await subjects.addAufgabe(props.subjectId, titel.value, frist.value, gewichtung.value)
    anlegen.value = false
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
      if (v.lese) await reading.add(props.subjectId, { title: v.titel, unit: v.lese.unit, total: v.lese.total, passes: 1, start: '', deadline: v.frist || '' })
      else await subjects.addAufgabe(props.subjectId, v.titel, v.frist, v.gewichtung)
    }
    vorschlaege.value = []
    rohtextKi.value = ''
    await refresh()
  } catch (e) { leseFehler.value = e.message }
  finally { legtAn.value = false }
}
function vorschlaegeVerwerfen() { vorschlaege.value = []; rohtextKi.value = ''; leseFehler.value = '' }

onMounted(load)
</script>

<template>
  <div class="mb-3 flex items-center justify-between">
    <h2 class="text-lg font-semibold">Umfang dieses Fachs</h2>
    <div class="flex gap-2">
      <label class="btn btn-outline !py-1.5 inline-flex cursor-pointer" :title="'Lädt ein Aufgabenblatt (PDF) hoch; eine lokale KI (Ollama) schlägt daraus Aufgaben vor – nur ein Vorschlag, geprüft wird vor dem Anlegen.'">
        {{ liestEin ? 'Liest ein …' : 'PDF auswählen' }}
        <input ref="dateiInput" type="file" accept="application/pdf" class="hidden" :disabled="liestEin" @change="dateiGewaehlt" />
      </label>
      <button v-if="!anlegen && aufgaben.length" type="button" class="btn btn-outline !py-1.5" @click="anlegen = true">+ Neue Aufgabe</button>
    </div>
  </div>

  <p v-if="leseFehler" class="mb-4 text-sm text-rose-600 dark:text-rose-400">{{ leseFehler }}</p>

  <div v-if="vorschlaege.length" class="panel mb-4 p-4">
      <div v-if="aufgabenVorschlaege.length" class="mt-4">
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
    <button class="btn btn-primary">Aufgabe anlegen</button>
    <button type="button" class="btn btn-ghost" @click="anlegen = false">Abbrechen</button>
    <p v-if="error" class="text-sm text-rose-600 dark:text-rose-400 sm:col-span-4">{{ error }}</p>
    <p class="text-xs text-slate-500 dark:text-slate-400 sm:col-span-4">
      Gewichtung = anteilige Bewertung wie im Aufgabenblatt (z. B. Klausur 50 %). Ohne Gewichtung zählt jede Aufgabe gleich viel.
    </p>
  </form>

  <p v-if="loadError" class="text-sm text-rose-600 dark:text-rose-400">{{ loadError }}</p>
  <ul v-else-if="aufgaben.length" class="grid gap-3">
    <li v-for="a in aufgaben" :key="a.id" class="panel flex items-center gap-3 p-4">
      <button type="button" class="grid h-9 w-9 shrink-0 place-items-center rounded-full border transition"
        :class="a.erledigt ? 'border-transparent bg-primary text-white' : 'border-highlight opacity-40 hover:opacity-70'"
        :aria-pressed="a.erledigt" :aria-label="`${a.titel} ${a.erledigt ? 'als offen markieren' : 'als erledigt markieren'}`"
        @click="toggle(a)">
        <AppIcon name="haken" class="h-5 w-5" />
      </button>
      <div class="min-w-0 flex-1">
        <p :class="a.erledigt ? 'text-slate-400 line-through dark:text-slate-500' : ''">{{ a.titel }}</p>
        <p v-if="a.frist || a.gewichtung != null" class="text-sm text-slate-500 dark:text-slate-400">
          <template v-if="a.frist">Frist {{ formatDate(a.frist) }}</template>
          <template v-if="a.frist && a.gewichtung != null"> · </template>
          <template v-if="a.gewichtung != null">{{ a.gewichtung }} % der Bewertung</template>
        </p>
        <select v-if="pensen.length" class="input !mt-1.5 !w-auto !py-1 text-xs" :value="a.pensum_id || ''"
          :aria-label="`${a.titel} mit Lesepensum verknüpfen`" @change="pensumSetzen(a, $event.target.value)">
          <option value="">Kein Lesepensum verknüpft</option>
          <option v-for="p in pensen" :key="p.id" :value="p.id">{{ p.title }}</option>
        </select>
      </div>
      <button class="btn btn-danger !px-2.5 !py-1" :aria-label="`${a.titel} löschen`" @click="remove(a)">Löschen</button>
    </li>
  </ul>
  <EmptyState v-else-if="!anlegen" title="Noch keine Aufgabe" text="Lege die erste Aufgabe an, um den Umfang des Fachs festzuhalten.">
    <button class="btn btn-primary" @click="anlegen = true">Erste Aufgabe anlegen</button>
  </EmptyState>
</template>
