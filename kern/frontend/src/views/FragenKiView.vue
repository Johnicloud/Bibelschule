<script setup>
import { computed, inject, onMounted, ref } from 'vue'
import EmptyState from '../components/ui/EmptyState.vue'

const fragenki = inject('fragenki')
const subjects = inject('subjects')
const service = inject('service') // Karteikarten-Dienst: Deck-ID = Fach-ID

const buecher = ref([])
const faecher = ref([])
const ladeFehler = ref('')

const gewaehltesBuch = ref('')
const gewaehltesKapitel = ref(1)
const generiertFuer = ref(null) // { buch, kapitel } des aktuell angezeigten Ergebnisses
const generiertLaedt = ref(false)
const generierFehler = ref('')
const rohtextKi = ref('')
const vorschlaege = ref([]) // [{ id, frage, antwort, ausgewaehlt }]

const gewaehltesFach = ref('')
const uebernehmenLaedt = ref(false)
const uebernehmenFehler = ref('')
const uebernommen = ref(false)

const maxKapitel = computed(() => buecher.value.find((b) => b.short === gewaehltesBuch.value)?.kapitel_gesamt || 1)

async function load() {
  try {
    buecher.value = await fragenki.buecher()
    ladeFehler.value = ''
  } catch (e) { ladeFehler.value = e.message }
  try { faecher.value = await subjects.list() } catch { faecher.value = [] }
}

async function generieren() {
  if (!gewaehltesBuch.value) return
  generierFehler.value = ''
  uebernehmenFehler.value = ''
  uebernommen.value = false
  vorschlaege.value = []
  rohtextKi.value = ''
  generiertLaedt.value = true
  try {
    const ergebnis = await fragenki.generieren(gewaehltesBuch.value, gewaehltesKapitel.value)
    vorschlaege.value = ergebnis.vorschlaege.map((v, i) => ({ id: i, frage: v.frage, antwort: '', ausgewaehlt: true }))
    rohtextKi.value = ergebnis.rohtext_ki || ''
    generiertFuer.value = { buch: gewaehltesBuch.value, kapitel: gewaehltesKapitel.value }
    if (!vorschlaege.value.length) generierFehler.value = 'Daraus ließ sich keine Frage lesen. Antwort der KI unten.'
  } catch (e) { generierFehler.value = e.message }
  finally { generiertLaedt.value = false }
}

async function uebernehmen() {
  const ausgewaehlt = vorschlaege.value.filter((v) => v.ausgewaehlt)
  if (!ausgewaehlt.length || !gewaehltesFach.value) return
  uebernehmenFehler.value = ''
  uebernehmenLaedt.value = true
  try {
    for (const v of ausgewaehlt) {
      await service.addCard(gewaehltesFach.value, { kind: 'classic', front: v.frage, back: v.antwort, options: [], correct_index: null })
    }
    vorschlaege.value = vorschlaege.value.filter((v) => !v.ausgewaehlt)
    uebernommen.value = true
  } catch (e) { uebernehmenFehler.value = e.message }
  finally { uebernehmenLaedt.value = false }
}

function verwerfen() { vorschlaege.value = []; rohtextKi.value = ''; generierFehler.value = ''; generiertFuer.value = null }

onMounted(load)
</script>

<template>
  <h1 class="text-3xl font-semibold tracking-tight">Fragen und KI</h1>
  <p class="mt-1 text-slate-500 dark:text-slate-400">
    Zu einem Bibelkapitel schlägt eine lokale KI (Ollama) Verständnisfragen vor – der Verstext kommt vom
    Bibel-Dienst. Immer nur ein Vorschlag: geprüft und als Karteikarte übernommen wird von Hand, die Antwort
    trägt man selbst ein.
  </p>

  <p v-if="ladeFehler" class="mt-6 text-sm text-rose-600 dark:text-rose-400">{{ ladeFehler }}</p>

  <div class="panel mt-6 p-5">
    <form class="flex flex-wrap items-end gap-3" @submit.prevent="generieren">
      <div>
        <label class="mb-1 block text-sm text-slate-500 dark:text-slate-400">Buch</label>
        <select v-model="gewaehltesBuch" class="input" required>
          <option value="" disabled>Buch wählen …</option>
          <option v-for="b in buecher" :key="b.short" :value="b.short">{{ b.name }}</option>
        </select>
      </div>
      <div class="w-28">
        <label class="mb-1 block text-sm text-slate-500 dark:text-slate-400">Kapitel</label>
        <input v-model.number="gewaehltesKapitel" type="number" min="1" :max="maxKapitel" class="input" required />
      </div>
      <button class="btn btn-primary" :disabled="generiertLaedt || !gewaehltesBuch">
        {{ generiertLaedt ? 'Fragt die KI …' : 'Fragen generieren' }}
      </button>
    </form>
    <p v-if="generierFehler" class="mt-3 text-sm text-rose-600 dark:text-rose-400">{{ generierFehler }}</p>
  </div>

  <div v-if="vorschlaege.length" class="panel mt-6 p-5">
    <h2 class="mb-3 text-lg font-semibold">
      Vorschläge zu {{ buecher.find((b) => b.short === generiertFuer?.buch)?.name }} {{ generiertFuer?.kapitel }}
    </h2>
    <ul class="grid gap-3">
      <li v-for="v in vorschlaege" :key="v.id" class="flex items-start gap-3 rounded-xl border border-slate-200 p-3 dark:border-slate-700">
        <input type="checkbox" v-model="v.ausgewaehlt" class="mt-1 h-5 w-5 shrink-0 rounded-md" :aria-label="`${v.frage} übernehmen`" />
        <div class="min-w-0 flex-1">
          <p>{{ v.frage }}</p>
          <input v-model="v.antwort" class="input mt-2" placeholder="Antwort (die KI liefert nur die Frage, selbst eintragen)"
            :aria-label="`Antwort zu: ${v.frage}`" />
        </div>
      </li>
    </ul>

    <div class="mt-4 flex flex-wrap items-end gap-3">
      <div>
        <label class="mb-1 block text-sm text-slate-500 dark:text-slate-400">Als Karteikarte in Fach</label>
        <select v-model="gewaehltesFach" class="input">
          <option value="" disabled>Fach wählen …</option>
          <option v-for="f in faecher" :key="f.id" :value="f.id">{{ f.name }}</option>
        </select>
      </div>
      <button class="btn btn-primary" :disabled="uebernehmenLaedt || !gewaehltesFach || !vorschlaege.some((v) => v.ausgewaehlt)" @click="uebernehmen">
        {{ uebernehmenLaedt ? 'Legt an …' : 'Ausgewählte übernehmen' }}
      </button>
      <button type="button" class="btn btn-ghost" @click="verwerfen">Verwerfen</button>
    </div>
    <p v-if="uebernehmenFehler" class="mt-3 text-sm text-rose-600 dark:text-rose-400">{{ uebernehmenFehler }}</p>
    <p v-if="uebernommen" class="mt-3 text-sm text-slate-500 dark:text-slate-400">Als Karteikarten übernommen.</p>

    <details v-if="rohtextKi" class="mt-4 text-sm text-slate-500 dark:text-slate-400">
      <summary class="cursor-pointer">Antwort der KI im Wortlaut</summary>
      <pre class="mt-2 whitespace-pre-wrap">{{ rohtextKi }}</pre>
    </details>
  </div>

  <EmptyState v-else-if="!generiertLaedt && !generierFehler" class="mt-6" title="Noch keine Fragen"
    text="Oben ein Buch und Kapitel wählen und Fragen generieren lassen." />
</template>
