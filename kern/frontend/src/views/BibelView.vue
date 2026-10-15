<script setup>
import { inject, onMounted, ref } from 'vue'
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

async function load() {
  try { index.value = await bibel.index(); loadError.value = '' }
  catch (e) { loadError.value = e.message }
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
