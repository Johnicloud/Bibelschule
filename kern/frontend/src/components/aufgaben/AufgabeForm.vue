<script setup>
import { computed, inject, ref, watch } from 'vue'
import AppIcon from '../ui/AppIcon.vue'
import { AUFGABEN_ARTEN, artInfo } from '../../domain/status'

// Ein Formular für alle Arten von Aufgaben – zum Anlegen (ohne `aufgabe`) und zum Bearbeiten (mit `aufgabe`).
// Welche Felder erscheinen, bestimmt die Art (domain/status.js, AUFGABEN_ARTEN).
const props = defineProps({ subjectId: String, aufgabe: Object })
const emit = defineEmits(['saved', 'cancel'])
const subjects = inject('subjects')
const flash = inject('service')       // Karteikarten (Deck-ID = Fach-ID)
const skripte = inject('skripte')

const a = props.aufgabe
const art = ref(a?.art || 'allgemein')
const titel = ref(a?.titel || '')
const frist = ref(a?.frist || '')
const gewichtung = ref(a?.gewichtung ?? '')
const zaehlt = ref(a ? a.zaehlt !== false : true)
const notiz = ref(a?.notiz || '')
const soll = ref(a?.soll ?? '')
const ist = ref(a?.ist ?? '')
const einheit = ref(a?.einheit || '')
const error = ref('')

// Orientierungsfragen: die Fragen werden zu einem Karteikarten-Set dieses Fachs (entsteht automatisch), die Aufgabe merkt sich
// nur den Namen des Sets. Quelle: eintippen/einfügen oder eine Datei im Fach (Fragenliste, Druckbogen mit Antworten).
const OHNE_ANTWORT = '(Antwort noch nicht eingetragen)'
const setName = ref(a?.set_name || '')
const setVonHand = ref(!!a?.set_name)          // sonst folgt der Set-Name dem Titel
const quelle = ref('text')
const fragenText = ref('')
const dateien = ref([])
const dateiId = ref('')
const vorhandeneSets = ref([])
watch(titel, (t) => { if (!a && !setVonHand.value) setName.value = t })
watch(art, async (neu) => {
  if (neu !== 'fragen') return
  try { dateien.value = await skripte.dateienMitFragen(props.subjectId) } catch { dateien.value = [] }
  try { vorhandeneSets.value = (await flash.openDeck(props.subjectId)).sets.map((x) => x.name) } catch { vorhandeneSets.value = [] }
}, { immediate: true })

const NUMMER = /^\s*(?:\d{1,3}\s*[.)]|[-*•])\s*/
const fragenAusText = (text) => text.split('\n').map((z) => z.replace(NUMMER, '').trim()).filter(Boolean).map((frage) => ({ frage, antwort: '' }))

async function fragenAlsSetAnlegen() {
  const karten = quelle.value === 'datei' ? (dateiId.value ? (await skripte.karten(dateiId.value)).karten : []) : fragenAusText(fragenText.value)
  if (!karten.length) throw new Error('Bitte Fragen eintippen oder eine Datei mit Fragen wählen.')
  const name = (setName.value || titel.value).trim()
  if (!name) throw new Error('Bitte einen Titel oder Set-Namen eingeben.')
  const deck = await flash.openDeck(props.subjectId)
  if (!deck.sets.some((x) => x.name.toLowerCase() === name.toLowerCase())) await flash.createSet(props.subjectId, name)
  const schonDa = new Set(deck.cards.map((c) => c.front))
  for (const k of karten) {
    if (schonDa.has(k.frage)) continue
    await flash.addCard(props.subjectId, { kind: 'classic', front: k.frage, back: k.antwort || OHNE_ANTWORT, options: [], correct_index: null, set_name: name })
  }
  // der Reiter „Karteikarten“ muss im Fach sichtbar sein, sonst findet man das Set nicht
  const fach = await subjects.get(props.subjectId)
  if (!(fach.aktive_dienste || []).includes('karteikarten')) await subjects.setAktiveDienste(props.subjectId, [...(fach.aktive_dienste || []), 'karteikarten'])
  return name
}
const busy = ref(false)
const info = computed(() => artInfo(art.value))

async function submit() {
  error.value = ''
  busy.value = true
  const felder = { art: art.value, titel: titel.value, frist: frist.value, gewichtung: gewichtung.value, zaehlt: zaehlt.value,
    notiz: notiz.value, soll: info.value.umfang ? soll.value : '', ist: info.value.umfang ? ist.value : '', einheit: info.value.umfang ? einheit.value : '' }
  try {
    if (info.value.fragen && !a) felder.set_name = await fragenAlsSetAnlegen()
    else if (info.value.fragen) felder.set_name = setName.value
    if (a) await subjects.updateAufgabe(props.subjectId, a.id, felder)
    else await subjects.createAufgabe(props.subjectId, felder)
    emit('saved')
  } catch (e) { error.value = e.message } finally { busy.value = false }
}
</script>

<template>
  <form class="panel space-y-3 p-4" @submit.prevent="submit">
    <div class="grid gap-2 sm:grid-cols-3" role="group" aria-label="Art der Aufgabe">
      <button v-for="(k, id) in AUFGABEN_ARTEN" :key="id" type="button" :aria-pressed="art === id"
        class="flex items-center gap-2 rounded-xl p-3 text-left ring-1 transition focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-teal-500"
        :class="art === id ? 'bg-teal-50 ring-2 ring-teal-500 dark:bg-teal-500/10' : 'ring-slate-300 hover:bg-slate-50 dark:ring-slate-700 dark:hover:bg-slate-800'"
        @click="art = id">
        <AppIcon :name="k.icon" class="h-5 w-5 shrink-0" />
        <span><span class="block text-sm font-medium">{{ k.label }}</span><span class="block text-xs text-slate-500 dark:text-slate-400">{{ k.hinweis }}</span></span>
      </button>
    </div>

    <div class="grid gap-3 sm:grid-cols-[1fr_10rem_8rem]">
      <input v-model="titel" class="input" placeholder="Titel, z. B. Exegese Kapitel 3" aria-label="Titel der Aufgabe" />
      <input v-model="frist" type="date" class="input" :aria-label="`${info.frist} (optional)`" :title="info.frist" />
      <input v-model="gewichtung" type="number" min="0" max="100" step="any" class="input" placeholder="Gewichtung %" aria-label="Anteilige Bewertung in Prozent (optional)" />
    </div>

    <div v-if="info.umfang" class="grid gap-3 sm:grid-cols-3">
      <input v-model="soll" type="number" min="0" step="any" class="input" placeholder="Umfang (Soll)" aria-label="Umfang (Soll)" />
      <input v-model="ist" type="number" min="0" step="any" class="input" placeholder="Stand (Ist)" aria-label="Erreichter Stand (Ist)" />
      <input v-model="einheit" list="aufgabe-einheiten" class="input" placeholder="Einheit, z. B. Seiten" aria-label="Einheit" />
      <datalist id="aufgabe-einheiten"><option>Seiten</option><option>Wörter</option><option>Einträge</option></datalist>
    </div>

    <div v-if="info.fragen && !a" class="space-y-2 rounded-xl p-3 ring-1 ring-slate-300 dark:ring-slate-700">
      <div class="flex flex-wrap gap-4 text-sm" role="radiogroup" aria-label="Woher kommen die Fragen?">
        <label class="flex items-center gap-1.5"><input v-model="quelle" type="radio" value="text" class="accent-teal-600" /> Fragen eintippen oder einfügen</label>
        <label class="flex items-center gap-1.5"><input v-model="quelle" type="radio" value="datei" class="accent-teal-600" /> Aus einer Datei in diesem Fach</label>
      </div>
      <textarea v-if="quelle === 'text'" v-model="fragenText" class="input min-h-[120px]" rows="5" placeholder="Eine Frage pro Zeile (Nummern vorne werden entfernt)" aria-label="Fragen"></textarea>
      <select v-else v-model="dateiId" class="input" aria-label="Datei mit Fragen">
        <option value="">{{ dateien.length ? 'Datei wählen …' : 'Keine passende Datei im Reiter „Skripte“' }}</option>
        <option v-for="d in dateien" :key="d.id" :value="d.id">{{ d.dateiname }}</option>
      </select>
      <input v-model="setName" class="input" placeholder="Name des Karteikarten-Sets" aria-label="Name des Karteikarten-Sets" @input="setVonHand = true" />
      <p class="text-xs text-slate-500 dark:text-slate-400">Das Set entsteht automatisch im Reiter „Karteikarten“. Fehlende Antworten trägst du dort nach. Der Fortschritt dieser Aufgabe ist der Anteil sicher gelernter Karten.</p>
    </div>
    <div v-else-if="info.fragen" class="space-y-1">
      <select v-model="setName" class="input" aria-label="Karteikarten-Set dieser Aufgabe">
        <option value="">Kein Set verknüpft</option>
        <option v-if="setName && !vorhandeneSets.includes(setName)" :value="setName">{{ setName }}</option>
        <option v-for="n in vorhandeneSets" :key="n" :value="n">Set: {{ n }}</option>
      </select>
    </div>

    <textarea v-model="notiz" class="input min-h-[60px]" rows="2" placeholder="Notiz (optional)" aria-label="Notiz"></textarea>

    <label class="flex items-start gap-2 text-sm">
      <input v-model="zaehlt" type="checkbox" class="mt-0.5 h-4 w-4 accent-teal-600" />
      <span>Zählt zum Gesamtfortschritt
        <span class="block text-xs text-slate-500 dark:text-slate-400">Aus: nur zum Lernen, die Aufgabe bleibt sichtbar, hebt den Fortschritt aber nicht. Ohne Gewichtung zählt jede Aufgabe gleich viel.</span>
      </span>
    </label>

    <p v-if="error" class="text-sm text-rose-600 dark:text-rose-400">{{ error }}</p>
    <div class="flex gap-2">
      <button class="btn btn-primary" :disabled="busy">{{ a ? 'Speichern' : 'Aufgabe anlegen' }}</button>
      <button type="button" class="btn btn-ghost" @click="$emit('cancel')">Abbrechen</button>
    </div>
  </form>
</template>
