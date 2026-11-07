<script setup>
import { computed, inject, onBeforeUnmount, onMounted, ref } from 'vue'
import AppIcon from '../components/ui/AppIcon.vue'
import EmptyState from '../components/ui/EmptyState.vue'

// 3-2-1-Methode, so wie sie tatsächlich geübt wird: Runde 1 sind 3 Minuten im ganzen Kapitel, danach markiert
// man, wie weit man gekommen ist. Runde 2 (2 Minuten) und Runde 3 (1 Minute) zeigen nur noch genau diesen
// Abschnitt – derselbe, schon bekannte Text, aber mit immer weniger Zeit. Gleicher Rhythmus wie im
// Schnelllesen-Dienst (siehe dessen domain/models.py).
const ZIEL_SEKUNDEN = [180, 120, 60]

const schnelllesen = inject('schnelllesen')

const buecher = ref([])
const ladeFehler = ref('')

const gewaehltesBuch = ref('')
const gewaehlteKapitel = ref(1)
const startFehler = ref('')
const startLaedt = ref(false)

const einheit = ref(null)
const laufend = ref(false)
const markierungsModus = ref(false)   // Runde 1, Zeit um: jetzt anklicken, bis wohin gelesen wurde
const vergangen = ref(0)
let startZeit = 0
let timer = null

const rundeFehler = ref('')
const abschliessenLaedt = ref(false)

const verlauf = ref([])
const verlaufFehler = ref('')

const maxKapitel = computed(() => buecher.value.find((b) => b.short === gewaehltesBuch.value)?.kapitel_gesamt || 1)
const zielDieserRunde = computed(() => einheit.value ? ZIEL_SEKUNDEN[einheit.value.naechste_runde - 1] : null)
const verbleibend = computed(() => zielDieserRunde.value == null ? 0 : zielDieserRunde.value - vergangen.value)
const zeitUm = computed(() => verbleibend.value <= 0)
const woerterDesTexts = computed(() => einheit.value ? einheit.value.text.split(/\s+/).filter(Boolean) : [])

function formatZeit(sekunden) {
  const s = Math.max(0, Math.round(sekunden))
  return `${Math.floor(s / 60)}:${String(s % 60).padStart(2, '0')}`
}

async function load() {
  try {
    buecher.value = await schnelllesen.buecher()
    ladeFehler.value = ''
  } catch (e) { ladeFehler.value = e.message }
}

async function ladeVerlauf() {
  try { verlauf.value = await schnelllesen.liste(); verlaufFehler.value = '' }
  catch (e) { verlaufFehler.value = e.message }
}

async function starten() {
  if (!gewaehltesBuch.value) return
  startFehler.value = ''
  startLaedt.value = true
  try {
    einheit.value = await schnelllesen.starten(gewaehltesBuch.value, gewaehlteKapitel.value)
    markierungsModus.value = false
  } catch (e) { startFehler.value = e.message }
  finally { startLaedt.value = false }
}

function timerAnhalten() {
  clearInterval(timer)
  timer = null
  laufend.value = false
}

function rundeStarten() {
  vergangen.value = 0
  startZeit = performance.now()
  laufend.value = true
  const istRundeEins = einheit.value.naechste_runde === 1
  timer = setInterval(() => {
    vergangen.value = (performance.now() - startZeit) / 1000
    // Runde 1 ist strikt auf 3 Minuten begrenzt: erst lesen, DANACH sagen, wie weit man gekommen ist.
    // Ab Runde 2 läuft die Zeit nur noch als Vergleich weiter – „Fertig“ bleibt dem Lesenden überlassen.
    if (istRundeEins && vergangen.value >= ZIEL_SEKUNDEN[0]) {
      vergangen.value = ZIEL_SEKUNDEN[0]
      timerAnhalten()
      markierungsModus.value = true
    }
  }, 100)
}

async function wortAuswaehlen(index) {
  rundeFehler.value = ''
  abschliessenLaedt.value = true
  try {
    einheit.value = await schnelllesen.durchgangAbschliessen(einheit.value.id, vergangen.value, index + 1)
    markierungsModus.value = false
  } catch (e) { rundeFehler.value = e.message }
  finally { abschliessenLaedt.value = false }
}

async function rundeFertig() {
  const sekunden = vergangen.value
  timerAnhalten()
  rundeFehler.value = ''
  abschliessenLaedt.value = true
  try {
    einheit.value = await schnelllesen.durchgangAbschliessen(einheit.value.id, sekunden)
    if (einheit.value.fertig) ladeVerlauf()
  } catch (e) { rundeFehler.value = e.message }
  finally { abschliessenLaedt.value = false }
}

function neuesTraining() {
  einheit.value = null
  vergangen.value = 0
  markierungsModus.value = false
  rundeFehler.value = ''
}

async function loeschen(id) {
  try { await schnelllesen.loeschen(id); verlauf.value = verlauf.value.filter((e) => e.id !== id) }
  catch (e) { verlaufFehler.value = e.message }
}

onBeforeUnmount(() => clearInterval(timer))
onMounted(() => { load(); ladeVerlauf() })
</script>

<template>
  <h1 class="text-3xl font-semibold tracking-tight">Schnelllesen</h1>
  <p class="mt-1 text-slate-500 dark:text-slate-400">
    Die 3-2-1-Methode: erst 3 Minuten im Kapitel lesen und markieren, wie weit es ging – dann denselben
    Abschnitt noch zweimal, in 2 und dann in 1 Minute. Der Text kommt vom Bibel-Dienst.
  </p>

  <p v-if="ladeFehler" class="mt-6 text-sm text-rose-600 dark:text-rose-400">{{ ladeFehler }}</p>

  <!-- Auswahl, solange kein Training läuft -->
  <div v-if="!einheit" class="panel mt-6 p-5">
    <form class="flex flex-wrap items-end gap-3" @submit.prevent="starten">
      <div>
        <label class="mb-1 block text-sm text-slate-500 dark:text-slate-400">Buch</label>
        <select v-model="gewaehltesBuch" class="input" required>
          <option value="" disabled>Buch wählen …</option>
          <option v-for="b in buecher" :key="b.short" :value="b.short">{{ b.name }}</option>
        </select>
      </div>
      <div class="w-28">
        <label class="mb-1 block text-sm text-slate-500 dark:text-slate-400">Kapitel</label>
        <input v-model.number="gewaehlteKapitel" type="number" min="1" :max="maxKapitel" class="input" required />
      </div>
      <button class="btn btn-primary" :disabled="startLaedt || !gewaehltesBuch">
        {{ startLaedt ? 'Lädt …' : 'Training starten' }}
      </button>
    </form>
    <p v-if="startFehler" class="mt-3 text-sm text-rose-600 dark:text-rose-400">{{ startFehler }}</p>
  </div>

  <!-- Laufendes Training -->
  <div v-else class="panel mt-6 p-5">
    <div class="flex flex-wrap items-center justify-between gap-3">
      <h2 class="text-xl font-semibold">{{ einheit.buch_name }} {{ einheit.kapitel }}</h2>
      <span class="text-sm text-slate-500 dark:text-slate-400">
        {{ einheit.naechste_runde === 1 || einheit.naechste_runde == null
          ? `${einheit.wortanzahl} Wörter im Kapitel` : `Abschnitt: ${einheit.text.split(/\s+/).length} Wörter` }}
      </span>
    </div>

    <!-- Abgeschlossene Durchgänge -->
    <ul v-if="einheit.durchgaenge.length" class="mt-4 flex flex-wrap gap-2">
      <li v-for="d in einheit.durchgaenge" :key="d.runde"
          class="rounded-lg bg-backdrop px-3 py-1.5 text-sm">
        Runde {{ d.runde }}: {{ formatZeit(d.sekunden) }} <span class="opacity-60">· {{ d.wpm }} Wörter/Min</span>
      </li>
    </ul>

    <template v-if="!einheit.fertig">
      <div class="mt-4 flex items-center gap-3 text-sm text-slate-500 dark:text-slate-400">
        <AppIcon name="stoppuhr" class="h-4 w-4" />
        <span v-if="einheit.naechste_runde === 1">
          Runde 1 von 3 – 3 Minuten lesen, danach markieren, wie weit du gekommen bist
        </span>
        <span v-else>Runde {{ einheit.naechste_runde }} von 3 – nur noch dieser Abschnitt, Ziel: unter
          {{ formatZeit(zielDieserRunde) }}</span>
      </div>

      <!-- Runde 1, Zeit um: Text zum Anklicken, bis wohin gelesen wurde -->
      <template v-if="markierungsModus">
        <p class="mt-3 text-sm font-medium text-primary">Zeit um! Auf das letzte gelesene Wort klicken.</p>
        <p class="mt-2 font-serif text-lg leading-[2.3] text-slate-800 dark:text-slate-200">
          <button v-for="(w, i) in woerterDesTexts" :key="i" type="button"
                  class="cursor-pointer rounded px-0.5 hover:bg-primary/15 hover:ring-1 hover:ring-primary/30"
                  :disabled="abschliessenLaedt" @click="wortAuswaehlen(i)">{{ w }}</button>
        </p>
      </template>

      <template v-else>
        <p class="mt-4 font-serif text-lg leading-[2.1] text-slate-800 dark:text-slate-200">{{ einheit.text }}</p>

        <div class="mt-5 flex items-center gap-3">
          <button v-if="!laufend" class="btn btn-primary" @click="rundeStarten">
            Los lesen ({{ formatZeit(zielDieserRunde) }})
          </button>
          <template v-else>
            <span class="font-mono text-lg tabular-nums" :class="einheit.naechste_runde > 1 && zeitUm ? 'text-rose-600 dark:text-rose-400' : ''">
              {{ formatZeit(verbleibend) }}
            </span>
            <button v-if="einheit.naechste_runde > 1" class="btn btn-primary" :disabled="abschliessenLaedt" @click="rundeFertig">
              {{ abschliessenLaedt ? 'Speichert …' : 'Fertig gelesen' }}
            </button>
          </template>
        </div>
      </template>
      <p v-if="rundeFehler" class="mt-3 text-sm text-rose-600 dark:text-rose-400">{{ rundeFehler }}</p>
    </template>

    <template v-else>
      <p class="mt-4 text-sm text-slate-500 dark:text-slate-400">
        Alle drei Durchgänge geschafft
        <span v-if="einheit.durchgaenge[2].wpm > einheit.durchgaenge[0].wpm">– schneller als im ersten Durchgang.</span>
      </p>
      <button class="btn btn-outline mt-4" @click="neuesTraining">Neues Training</button>
    </template>
  </div>

  <h2 class="mb-3 mt-8 text-lg font-semibold">Verlauf</h2>
  <p v-if="verlaufFehler" class="text-sm text-rose-600 dark:text-rose-400">{{ verlaufFehler }}</p>
  <EmptyState v-else-if="verlauf.length === 0" title="Noch kein Training" text="Oben ein Buch und Kapitel wählen und starten." />
  <ul v-else class="grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
    <li v-for="e in verlauf" :key="e.id" class="panel p-3">
      <div class="flex items-start justify-between gap-2">
        <p class="font-medium">{{ e.buch_name }} {{ e.kapitel }}</p>
        <button class="btn btn-ghost !p-1.5" :aria-label="`${e.buch_name} ${e.kapitel} löschen`" @click="loeschen(e.id)">
          <AppIcon name="x" class="h-3.5 w-3.5" />
        </button>
      </div>
      <p v-if="e.durchgaenge.length" class="mt-1 text-sm text-slate-500 dark:text-slate-400">
        {{ e.durchgaenge.map((d) => `${d.wpm}`).join(' → ') }} Wörter/Min
      </p>
      <p v-else class="mt-1 text-sm text-slate-500 dark:text-slate-400">Noch kein Durchgang</p>
    </li>
  </ul>
</template>
