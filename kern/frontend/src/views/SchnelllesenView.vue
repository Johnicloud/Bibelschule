<script setup>
import { computed, inject, onBeforeUnmount, onMounted, ref } from 'vue'
import AppIcon from '../components/ui/AppIcon.vue'
import EmptyState from '../components/ui/EmptyState.vue'

// 3-2-1-Methode: dasselbe Kapitel dreimal lesen, mit sinkender Zielzeit – man übt dadurch, denselben Text
// immer schneller zu lesen. Derselbe Rhythmus wie im Schnelllesen-Dienst (siehe dessen domain/models.py).
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
const vergangen = ref(0)
let startZeit = 0
let timer = null

const rundeFehler = ref('')
const abschliessenLaedt = ref(false)

const verlauf = ref([])
const verlaufFehler = ref('')

const maxKapitel = computed(() => buecher.value.find((b) => b.short === gewaehltesBuch.value)?.kapitel_gesamt || 1)
const zielDieserRunde = computed(() => einheit.value ? ZIEL_SEKUNDEN[einheit.value.naechste_runde - 1] : null)

function formatZeit(sekunden) {
  const s = Math.round(sekunden)
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
  } catch (e) { startFehler.value = e.message }
  finally { startLaedt.value = false }
}

function rundeStarten() {
  vergangen.value = 0
  startZeit = performance.now()
  laufend.value = true
  timer = setInterval(() => { vergangen.value = (performance.now() - startZeit) / 1000 }, 100)
}

function timerAnhalten() {
  clearInterval(timer)
  timer = null
  laufend.value = false
}

async function rundeFertig() {
  const sekunden = (performance.now() - startZeit) / 1000
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
    Ein Kapitel dreimal lesen, nach der 3-2-1-Methode: zuerst mit 3 Minuten Ziel, dann 2, dann 1 – derselbe
    Text, immer schneller. Der Verstext kommt vom Bibel-Dienst.
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
      <span class="text-sm text-slate-500 dark:text-slate-400">{{ einheit.wortanzahl }} Wörter</span>
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
        <span>Runde {{ einheit.naechste_runde }} von 3 – Ziel: unter {{ formatZeit(zielDieserRunde) }}</span>
      </div>

      <p class="mt-4 font-serif text-lg leading-[2.1] text-slate-800 dark:text-slate-200">{{ einheit.text }}</p>

      <div class="mt-5 flex items-center gap-3">
        <button v-if="!laufend" class="btn btn-primary" @click="rundeStarten">Los lesen</button>
        <template v-else>
          <span class="font-mono text-lg tabular-nums">{{ formatZeit(vergangen) }}</span>
          <button class="btn btn-primary" :disabled="abschliessenLaedt" @click="rundeFertig">
            {{ abschliessenLaedt ? 'Speichert …' : 'Fertig gelesen' }}
          </button>
        </template>
      </div>
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
