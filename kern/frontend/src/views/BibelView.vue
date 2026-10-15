<script setup>
import { inject, onMounted, ref, watch } from 'vue'
import AppIcon from '../components/ui/AppIcon.vue'
import EmptyState from '../components/ui/EmptyState.vue'
import { zielBibelstelle } from '../state/bibelNavigation'

const bibel = inject('bibel')
const vorlesen = inject('vorlesen')
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

// Vorlesen des gerade angezeigten Kapitels (lokale KI-Stimme, siehe vorlesen-Dienst) – reiner Text, der
// Dienst kennt die Bibel nicht, bekommt nur den schon geladenen Verstext.
const vorlesenLaeuft = ref(false)
const vorlesenFehler = ref('')
const vorlesenAudioUrl = ref('')

function vorlesenZuruecksetzen() {
  if (vorlesenAudioUrl.value) URL.revokeObjectURL(vorlesenAudioUrl.value)
  vorlesenAudioUrl.value = ''
  vorlesenFehler.value = ''
}

async function kapitelVorlesen() {
  if (!gelesenesKapitel.value || gelesenesKapitel.value.verse.length === 0) return
  vorlesenZuruecksetzen()
  vorlesenLaeuft.value = true
  try {
    const text = gelesenesKapitel.value.verse.map((v) => v.text).join(' ')
    vorlesenAudioUrl.value = URL.createObjectURL(await vorlesen.text(text))
  } catch (e) { vorlesenFehler.value = e.message }
  finally { vorlesenLaeuft.value = false }
}

// Volltextsuche: findet Verse nach Inhalt (nicht nach Bibelstelle wie beim Nachschlagen oben).
const suchwort = ref('')
const suchTreffer = ref(null)
const suchFehler = ref('')
const suchLaedt = ref(false)

async function suchen() {
  if (!suchwort.value.trim()) return
  suchFehler.value = ''
  suchLaedt.value = true
  try { suchTreffer.value = await bibel.suche(suchwort.value) }
  catch (e) { suchFehler.value = e.message; suchTreffer.value = null }
  finally { suchLaedt.value = false }
}

function zumVers(treffer) {
  sucheText.value = `${treffer.name} ${treffer.kapitel},${treffer.vers}`
  nachschlagen()
}

async function load() {
  try { index.value = await bibel.index(); loadError.value = '' }
  catch (e) { loadError.value = e.message }
}

async function nachschlagen() {
  if (!sucheText.value.trim()) return
  sucheFehler.value = ''
  vorlesenZuruecksetzen()
  kapitelLaedt.value = true
  try {
    const ergebnis = await bibel.nachschlagen(sucheText.value)
    gelesenesKapitel.value = ergebnis
    gewaehltesBuch.value = ergebnis.buch
    gewaehlteKapitelnummer.value = ergebnis.kapitel
  } catch (e) { sucheFehler.value = e.message; gelesenesKapitel.value = null }
  finally { kapitelLaedt.value = false }
}

async function kapitelLesen(buch, nummer) {
  sucheFehler.value = ''
  vorlesenZuruecksetzen()
  kapitelLaedt.value = true
  try {
    const ergebnis = await bibel.kapitel(buch, nummer)
    ergebnis.markiert = null
    gelesenesKapitel.value = ergebnis
    gewaehltesBuch.value = buch
    gewaehlteKapitelnummer.value = nummer
  } catch (e) { sucheFehler.value = e.message }
  finally { kapitelLaedt.value = false }
}

function buchGewaehlt() {
  if (gewaehltesBuch.value) kapitelLesen(gewaehltesBuch.value, 1)
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

// Verweis von anderswo (Register, globale Suche): statt der rohen PDF wird die Stelle hier nachgeschlagen.
watch(zielBibelstelle, (stelle) => {
  if (!stelle) return
  sucheText.value = stelle
  nachschlagen()
  zielBibelstelle.value = null
}, { immediate: true })
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
        <div class="h-6 w-px self-center bg-slate-200 dark:bg-slate-700"></div>
        <div>
          <label class="mb-1 block text-sm text-slate-500 dark:text-slate-400">Buch durchlesen</label>
          <select v-model="gewaehltesBuch" class="input" @change="buchGewaehlt">
            <option value="" disabled>Buch wählen …</option>
            <option v-for="b in index.buecher" :key="b.index" :value="b.short">{{ b.name }}</option>
          </select>
        </div>
      </form>
      <p v-if="sucheFehler" class="mt-3 text-sm text-rose-600 dark:text-rose-400">{{ sucheFehler }}</p>

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
        <template v-else>
          <button class="btn btn-outline mb-4 inline-flex items-center gap-2" :disabled="vorlesenLaeuft" @click="kapitelVorlesen">
            <AppIcon name="vorlesen" class="h-4 w-4" />
            {{ vorlesenLaeuft ? 'Erzeugt Audio …' : 'Kapitel vorlesen' }}
          </button>
          <p v-if="vorlesenFehler" class="mb-4 text-sm text-rose-600 dark:text-rose-400">{{ vorlesenFehler }}</p>
          <audio v-if="vorlesenAudioUrl" :src="vorlesenAudioUrl" controls autoplay class="mb-4 w-full"></audio>
          <p class="font-serif text-lg leading-[2.1] text-slate-800 dark:text-slate-200">
            <span v-for="v in gelesenesKapitel.verse" :key="v.id"
                  :class="v.vers === gelesenesKapitel.markiert ? 'rounded bg-primary/15 px-1 py-0.5 ring-1 ring-primary/30' : ''">
              <sup class="mr-0.5 font-sans text-xs font-semibold text-primary">{{ v.vers }}</sup>{{ v.text }}{{ ' ' }}
            </span>
          </p>
        </template>
      </div>
    </div>

    <h2 class="mb-3 mt-8 text-lg font-semibold">Suchen</h2>
    <form class="flex gap-2" @submit.prevent="suchen">
      <input v-model="suchwort" type="text" class="input flex-1" placeholder="Wort oder Satzteil, z. B. „ewiges Leben“" />
      <button class="btn btn-primary" :disabled="suchLaedt">{{ suchLaedt ? 'Sucht …' : 'Suchen' }}</button>
    </form>
    <p v-if="suchFehler" class="mt-2 text-sm text-rose-600 dark:text-rose-400">{{ suchFehler }}</p>
    <p v-else-if="suchTreffer && suchTreffer.length === 0" class="mt-2 text-sm text-slate-500 dark:text-slate-400">
      Keine Verse gefunden.
    </p>
    <ul v-else-if="suchTreffer" class="mt-3 grid gap-2">
      <li v-for="t in suchTreffer" :key="t.id" class="panel p-3">
        <button class="text-left" @click="zumVers(t)">
          <span class="font-medium text-primary hover:underline">{{ t.name }} {{ t.kapitel }},{{ t.vers }}</span>
          <span class="ml-2 text-sm text-slate-600 dark:text-slate-300">{{ t.text }}</span>
        </button>
      </li>
    </ul>
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
