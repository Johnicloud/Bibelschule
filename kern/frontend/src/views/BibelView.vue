<script setup>
import { computed, inject, onMounted, ref } from 'vue'
import AppIcon from '../components/ui/AppIcon.vue'
import EmptyState from '../components/ui/EmptyState.vue'

const bibel = inject('bibel')
const index = ref(null)
const loadError = ref('')
const laedtHoch = ref(false)
const hochladenFehler = ref('')
const dateiInput = ref(null)

const bearbeitetIndex = ref(null)
const editSeite = ref('')
const editError = ref('')
const speichert = ref(false)

// Lesen: Kapitel direkt als Text auf der Seite (keine PDF) – entweder über Bibelstelle (nachschlagen,
// markiert einen Vers) oder über Buch/Kapitel-Auswahl zum Durchlesen.
const sucheText = ref('')
const sucheFehler = ref('')
const kapitelLaedt = ref(false)
const gelesenesKapitel = ref(null)
const gewaehltesBuch = ref('')
const gewaehlteKapitelnummer = ref(1)

// Konkordanz/Stichwortsuche (Arbeitspaket B): durchsucht den Verstext aller Bücher, Treffer springen ins
// gelesene Kapitel (gleiche Anzeige wie oben, nur mit dem Treffer-Vers markiert statt einer nachgeschlagenen Stelle).
const sucheWort = ref('')
const sucheTreffer = ref(null)
const sucheLaedt = ref(false)
const sucheFehler2 = ref('')

async function load() {
  try { index.value = await bibel.index(); loadError.value = '' }
  catch (e) { loadError.value = e.message }
}

async function nachschlagen() {
  if (!sucheText.value.trim()) return
  sucheFehler.value = ''
  kapitelLaedt.value = true
  try {
    const ergebnis = await bibel.nachschlagen(sucheText.value)
    gelesenesKapitel.value = ergebnis
    gewaehltesBuch.value = ergebnis.buch
    gewaehlteKapitelnummer.value = ergebnis.kapitel
  } catch (e) { sucheFehler.value = e.message; gelesenesKapitel.value = null }
  finally { kapitelLaedt.value = false }
}

async function kapitelLesen(buch, nummer, markierterVers = null) {
  sucheFehler.value = ''
  kapitelLaedt.value = true
  try {
    const ergebnis = await bibel.kapitel(buch, nummer)
    ergebnis.markiert = markierterVers
    gelesenesKapitel.value = ergebnis
    gewaehltesBuch.value = buch
    gewaehlteKapitelnummer.value = nummer
  } catch (e) { sucheFehler.value = e.message }
  finally { kapitelLaedt.value = false }
}

async function suchen() {
  if (!sucheWort.value.trim()) return
  sucheFehler2.value = ''
  sucheLaedt.value = true
  try { sucheTreffer.value = await bibel.suche(sucheWort.value) }
  catch (e) { sucheFehler2.value = e.message; sucheTreffer.value = null }
  finally { sucheLaedt.value = false }
}

function trefferSpringen(t) {
  kapitelLesen(t.buch, t.kapitel, t.vers)
}

// Bücherregal: je Buch ein Rücken, dicker je mehr Kapitel das Buch hat (drei Stufen). Ein Klick wählt das Buch
// (ohne schon ein Kapitel zu laden), dann das Kapitel aus der Nummernleiste, erst dann steht der Text da.
const TESTAMENT_GRENZE = 39   // die ersten 39 Bücher (Index 0-38) sind das Alte Testament
const regale = computed(() => !index.value ? [] : [
  { titel: 'Altes Testament', buecher: index.value.buecher.filter((b) => b.index < TESTAMENT_GRENZE), farbe: 'bg-teal-800' },
  { titel: 'Neues Testament', buecher: index.value.buecher.filter((b) => b.index >= TESTAMENT_GRENZE), farbe: 'bg-teal-600' },
])
const RUECKEN = { 1: 'w-4 h-32', 2: 'w-5 h-36', 3: 'w-7 h-40' }
function dicke(b) { return b.kapitel_gesamt <= 8 ? 1 : b.kapitel_gesamt <= 29 ? 2 : 3 }
const gewaehltesBuchInfo = computed(() => index.value?.buecher.find((b) => b.short === gewaehltesBuch.value) || null)
function buchWaehlen(b) {
  gewaehltesBuch.value = b.short
  gelesenesKapitel.value = null
  sucheFehler.value = ''
}

function vor() {
  if (gelesenesKapitel.value && gelesenesKapitel.value.kapitel < gelesenesKapitel.value.kapitel_gesamt) {
    kapitelLesen(gewaehltesBuch.value, gelesenesKapitel.value.kapitel + 1)
  }
}
function zurueck() {
  if (gelesenesKapitel.value && gelesenesKapitel.value.kapitel > 1) {
    kapitelLesen(gewaehltesBuch.value, gelesenesKapitel.value.kapitel - 1)
  }
}

async function dateiGewaehlt(e) {
  const datei = e.target.files[0]
  e.target.value = ''
  if (!datei) return
  hochladenFehler.value = ''
  laedtHoch.value = true
  try { index.value = await bibel.hochladen(datei) }
  catch (e) { hochladenFehler.value = e.message }
  finally { laedtHoch.value = false }
}

function openEdit(buch) {
  editError.value = ''
  editSeite.value = buch.seite ?? ''
  bearbeitetIndex.value = buch.index
}
async function saveEdit(buch) {
  editError.value = ''
  speichert.value = true
  try {
    index.value = await bibel.seiteSetzen(buch.index, editSeite.value)
    bearbeitetIndex.value = null
  } catch (e) { editError.value = e.message }
  finally { speichert.value = false }
}

onMounted(load)
</script>

<template>
  <h1 class="text-3xl font-semibold tracking-tight">Bibel</h1>
  <p class="mt-1 text-slate-500 dark:text-slate-400">
    Eine Bibel als PDF, auf die Bibelstellen in der ganzen App verweisen können – ein Klick führt direkt zur
    passenden Seite. Kapitel 1 eines Buches liegt genau auf dessen Startseite, andere Kapitel sind nur ungefähr
    (gleichmäßig zwischen Buchanfang und -ende verteilt), siehe Projektnotizen.
  </p>

  <p v-if="loadError" class="mt-6 text-sm text-rose-600 dark:text-rose-400">{{ loadError }}</p>

  <div v-if="index" class="panel mt-6 p-5">
    <div class="flex flex-wrap items-center justify-between gap-3">
      <div>
        <p class="font-semibold">{{ index.dateiname || 'Noch keine Bibel hinterlegt' }}</p>
        <p v-if="index.dateiname" class="text-sm text-slate-500 dark:text-slate-400">
          <a :href="bibel.dateiUrl()" target="_blank" class="text-primary hover:underline">PDF öffnen</a>
        </p>
      </div>
      <label class="btn btn-outline inline-flex cursor-pointer">
        {{ laedtHoch ? 'Lädt hoch …' : (index.dateiname ? 'Neu hochladen' : 'PDF hochladen') }}
        <input ref="dateiInput" type="file" accept="application/pdf" class="hidden" :disabled="laedtHoch" @change="dateiGewaehlt" />
      </label>
    </div>
    <p v-if="laedtHoch" class="mt-2 text-sm text-slate-500 dark:text-slate-400">
      Seiten werden gerade erkannt (wenige Sekunden) …
    </p>
    <p v-else-if="index.dateiname && !index.hat_verse" class="mt-2 text-sm text-amber-700 dark:text-amber-300">
      Die Verse werden im Hintergrund eingelesen – das dauert bei einer ganzen Bibel 1–2 Minuten. Diese Seite
      später neu laden, um den Stand zu sehen.
    </p>
    <p v-if="hochladenFehler" class="mt-2 text-sm text-rose-600 dark:text-rose-400">{{ hochladenFehler }}</p>
  </div>

  <EmptyState v-else-if="!loadError" title="Lädt …" text="" />

  <template v-if="index && index.dateiname && index.hat_verse">
    <h2 class="mb-3 mt-8 text-lg font-semibold">Lesen</h2>
    <div class="panel p-5">
      <form class="flex flex-wrap items-end gap-3" @submit.prevent="nachschlagen">
        <div class="min-w-48 flex-1">
          <label class="mb-1 block text-sm text-slate-500 dark:text-slate-400">Bibelstelle</label>
          <input v-model="sucheText" type="text" class="input" placeholder="z. B. Joh 3,16" />
        </div>
        <button class="btn btn-primary" :disabled="kapitelLaedt">Nachschlagen</button>
      </form>
      <p v-if="sucheFehler" class="mt-3 text-sm text-rose-600 dark:text-rose-400">{{ sucheFehler }}</p>

      <div v-for="r in regale" :key="r.titel" class="mt-6">
        <p class="mb-2 text-sm font-medium text-slate-500 dark:text-slate-400">{{ r.titel }}</p>
        <div class="flex items-end gap-0.5 overflow-x-auto border-b-8 border-amber-900/70 px-1 pt-3 dark:border-amber-800/70">
          <button v-for="b in r.buecher" :key="b.index" type="button" :title="`${b.name} – ${b.kapitel_gesamt} Kapitel`"
            :aria-label="`${b.name}, ${b.kapitel_gesamt} Kapitel`" :aria-pressed="gewaehltesBuch === b.short"
            class="flex shrink-0 items-start justify-center rounded-t-sm pt-2 text-[11px] font-medium text-white shadow-sm transition hover:-translate-y-1"
            :class="[RUECKEN[dicke(b)], r.farbe, gewaehltesBuch === b.short ? '-translate-y-2 ring-2 ring-amber-400' : '']"
            @click="buchWaehlen(b)">
            <span class="whitespace-nowrap [writing-mode:vertical-rl]">{{ b.name }}</span>
          </button>
        </div>
      </div>

      <div v-if="gewaehltesBuchInfo" class="mt-6">
        <p class="mb-2 text-sm font-medium">{{ gewaehltesBuchInfo.name }} – Kapitel wählen</p>
        <div class="flex flex-wrap gap-1.5">
          <button v-for="n in gewaehltesBuchInfo.kapitel_gesamt" :key="n" type="button"
            class="btn !h-9 !min-w-9 !px-2 !py-0 text-sm tabular-nums"
            :class="gelesenesKapitel && gelesenesKapitel.buch === gewaehltesBuch && gelesenesKapitel.kapitel === n ? 'btn-primary' : 'btn-outline'"
            :disabled="kapitelLaedt" @click="kapitelLesen(gewaehltesBuch, n)">{{ n }}</button>
        </div>
      </div>

      <div v-if="gelesenesKapitel" class="mt-6">
        <div class="mb-4 flex items-center justify-between gap-3">
          <button class="btn btn-ghost !p-2" :disabled="gelesenesKapitel.kapitel <= 1" aria-label="Voriges Kapitel" @click="zurueck">
            <AppIcon name="zurueck" class="h-4 w-4" />
          </button>
          <h3 class="text-xl font-semibold">{{ gelesenesKapitel.name }} {{ gelesenesKapitel.kapitel }}</h3>
          <button class="btn btn-ghost !p-2" :disabled="gelesenesKapitel.kapitel >= gelesenesKapitel.kapitel_gesamt"
                  aria-label="Nächstes Kapitel" @click="vor">
            <AppIcon name="vor" class="h-4 w-4" />
          </button>
        </div>
        <p v-if="gelesenesKapitel.verse.length === 0" class="text-sm text-slate-500 dark:text-slate-400">
          Für dieses Kapitel ist noch kein Verstext eingelesen.
        </p>
        <p v-else class="font-serif text-lg leading-[2.1] text-slate-800 dark:text-slate-200">
          <span v-for="v in gelesenesKapitel.verse" :key="v.id"
                :class="v.vers === gelesenesKapitel.markiert ? 'rounded bg-primary/15 px-1 py-0.5 ring-1 ring-primary/30' : ''">
            <sup class="mr-0.5 font-sans text-xs font-semibold text-primary">{{ v.vers }}</sup>{{ v.text }}{{ ' ' }}
          </span>
        </p>
      </div>
    </div>

    <h2 class="mb-3 mt-8 text-lg font-semibold">Konkordanz</h2>
    <div class="panel p-5">
      <form class="flex flex-wrap items-end gap-3" @submit.prevent="suchen">
        <div class="min-w-48 flex-1">
          <label class="mb-1 block text-sm text-slate-500 dark:text-slate-400">Stichwort</label>
          <input v-model="sucheWort" type="text" class="input" placeholder="z. B. Gnade" />
        </div>
        <button class="btn btn-primary" :disabled="sucheLaedt">{{ sucheLaedt ? 'Sucht …' : 'Suchen' }}</button>
      </form>
      <p v-if="sucheFehler2" class="mt-3 text-sm text-rose-600 dark:text-rose-400">{{ sucheFehler2 }}</p>

      <p v-if="sucheTreffer && sucheTreffer.length === 0" class="mt-4 text-sm text-slate-500 dark:text-slate-400">
        Keine Fundstelle für „{{ sucheWort }}“.
      </p>
      <ul v-else-if="sucheTreffer" class="mt-4 space-y-2">
        <li v-for="t in sucheTreffer" :key="t.stelle">
          <button type="button" class="w-full rounded-lg p-2 text-left hover:bg-slate-100 dark:hover:bg-slate-800"
                  @click="trefferSpringen(t)">
            <span class="font-medium text-primary">{{ t.name }} {{ t.kapitel }},{{ t.vers }}</span>
            <span class="ml-2 text-sm text-slate-600 dark:text-slate-300">{{ t.kontext }}</span>
          </button>
        </li>
      </ul>
    </div>
  </template>

  <template v-if="index && index.dateiname">
    <h2 class="mb-3 mt-8 text-lg font-semibold">Bücher und ihre Seite</h2>
    <p class="mb-4 text-sm text-slate-500 dark:text-slate-400">
      Automatisch erkannte Seiten sind ein Vorschlag aus dem Inhaltsverzeichnis der PDF – bitte stichprobenartig
      prüfen. Fehlende oder falsche Seiten lassen sich hier von Hand eintragen.
    </p>
    <ul class="grid items-start gap-2 sm:grid-cols-2 lg:grid-cols-3">
      <li v-for="b in index.buecher" :key="b.index" class="panel min-w-0 p-3">
        <div v-if="bearbeitetIndex !== b.index" class="flex items-center justify-between gap-2">
          <div class="min-w-0">
            <p class="truncate font-medium">{{ b.name }}</p>
            <p class="text-sm text-slate-500 dark:text-slate-400">
              <span v-if="b.seite != null">Seite {{ b.seite }}<span v-if="b.erkannt"> (erkannt)</span></span>
              <span v-else class="opacity-60">Keine Seite</span>
            </p>
          </div>
          <button class="btn btn-ghost !p-1.5 shrink-0" :aria-label="`Seite für ${b.name} eintragen`" @click="openEdit(b)">
            <AppIcon name="stift" class="h-3.5 w-3.5" />
          </button>
        </div>
        <form v-else class="grid gap-2" @submit.prevent="saveEdit(b)">
          <input v-model="editSeite" type="number" min="1" class="input" placeholder="Seite" :aria-label="`Seite für ${b.name}`" />
          <div class="flex gap-2">
            <button class="btn btn-primary !py-1.5" :disabled="speichert">{{ speichert ? 'Speichert …' : 'Speichern' }}</button>
            <button type="button" class="btn btn-ghost !py-1.5" @click="bearbeitetIndex = null">Abbrechen</button>
          </div>
          <p v-if="editError" class="text-sm text-rose-600 dark:text-rose-400">{{ editError }}</p>
        </form>
      </li>
    </ul>
  </template>
</template>
