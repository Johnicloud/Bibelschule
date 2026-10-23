<script setup>
import { inject, ref } from 'vue'
import AppIcon from '../components/ui/AppIcon.vue'
import EmptyState from '../components/ui/EmptyState.vue'

const bibel = inject('bibel')
const notizen = inject('notizen')

// Bibelstelle frei eintippen (wie bei BibelView) -> der Bibel-Dienst löst Buch/Kapitel/Vers auf, daraus
// bauen wir die kanonische Adresse ("Joh.3.16", siehe Projektnotizen) selbst zusammen – der Bibel-Dienst
// liefert schon den kanonischen Kurznamen des Buchs (BOOKS[...].short), nur noch mit Kapitel/Vers verbinden.
const sucheText = ref('')
const sucheFehler = ref('')
const sucheLaedt = ref(false)

const aktuelleStelle = ref('')     // kanonisch, z. B. "Joh.3.16"
const anzeigeStelle = ref('')      // für Menschen, z. B. "Johannes 3,16"

const kommentare = ref([])
const listeFehler = ref('')

const neuerText = ref('')
const anlegenFehler = ref('')
const anlegenLaedt = ref(false)

async function stelleAufrufen() {
  if (!sucheText.value.trim()) return
  sucheFehler.value = ''
  sucheLaedt.value = true
  try {
    const ergebnis = await bibel.nachschlagen(sucheText.value)
    if (ergebnis.markiert == null) {
      sucheFehler.value = 'Bitte auch den Vers angeben (z. B. „Joh 3,16“, nicht nur „Joh 3“).'
      return
    }
    aktuelleStelle.value = `${ergebnis.buch}.${ergebnis.kapitel}.${ergebnis.markiert}`
    anzeigeStelle.value = `${ergebnis.name} ${ergebnis.kapitel},${ergebnis.markiert}`
    await ladeKommentare()
  } catch (e) { sucheFehler.value = e.message }
  finally { sucheLaedt.value = false }
}

async function ladeKommentare() {
  try { kommentare.value = await notizen.liste(aktuelleStelle.value); listeFehler.value = '' }
  catch (e) { listeFehler.value = e.message }
}

async function kommentarAnlegen() {
  if (!neuerText.value.trim()) return
  anlegenFehler.value = ''
  anlegenLaedt.value = true
  try {
    kommentare.value = [...kommentare.value, await notizen.anlegen(aktuelleStelle.value, neuerText.value)]
    neuerText.value = ''
  } catch (e) { anlegenFehler.value = e.message }
  finally { anlegenLaedt.value = false }
}

async function kommentarLoeschen(id) {
  try { await notizen.loeschen(id); kommentare.value = kommentare.value.filter((k) => k.id !== id) }
  catch (e) { listeFehler.value = e.message }
}

function formatDatum(iso) {
  return new Date(iso).toLocaleDateString('de-DE', { day: '2-digit', month: '2-digit', year: 'numeric' })
}
</script>

<template>
  <h1 class="text-3xl font-semibold tracking-tight">Notizen</h1>
  <p class="mt-1 text-slate-500 dark:text-slate-400">
    Eigene Gedanken an einer Bibelstelle. Jeder Kommentar meldet sich beim Bibel-Dienst als Verweis an, damit
    „was verweist hierher?“ dort über alle Dienste hinweg beantwortbar bleibt.
  </p>

  <div class="panel mt-6 p-5">
    <form class="flex flex-wrap items-end gap-3" @submit.prevent="stelleAufrufen">
      <div class="min-w-48 flex-1">
        <label class="mb-1 block text-sm text-slate-500 dark:text-slate-400">Bibelstelle</label>
        <input v-model="sucheText" type="text" class="input" placeholder="z. B. Joh 3,16" />
      </div>
      <button class="btn btn-primary" :disabled="sucheLaedt">{{ sucheLaedt ? 'Lädt …' : 'Stelle aufrufen' }}</button>
    </form>
    <p v-if="sucheFehler" class="mt-3 text-sm text-rose-600 dark:text-rose-400">{{ sucheFehler }}</p>
  </div>

  <template v-if="aktuelleStelle">
    <h2 class="mb-3 mt-8 text-lg font-semibold">{{ anzeigeStelle }}</h2>

    <div class="panel p-5">
      <form class="flex flex-wrap items-end gap-3" @submit.prevent="kommentarAnlegen">
        <div class="min-w-48 flex-1">
          <label class="mb-1 block text-sm text-slate-500 dark:text-slate-400">Neuer Kommentar</label>
          <input v-model="neuerText" type="text" class="input" placeholder="Eigener Gedanke dazu …" />
        </div>
        <button class="btn btn-primary" :disabled="anlegenLaedt">{{ anlegenLaedt ? 'Speichert …' : 'Hinzufügen' }}</button>
      </form>
      <p v-if="anlegenFehler" class="mt-3 text-sm text-rose-600 dark:text-rose-400">{{ anlegenFehler }}</p>
    </div>

    <p v-if="listeFehler" class="mt-4 text-sm text-rose-600 dark:text-rose-400">{{ listeFehler }}</p>
    <EmptyState v-else-if="kommentare.length === 0" title="Noch kein Kommentar" text="Oben den ersten Gedanken dazu eintragen." class="mt-4" />
    <ul v-else class="mt-4 grid gap-2">
      <li v-for="k in kommentare" :key="k.id" class="panel flex items-start justify-between gap-3 p-3">
        <div>
          <p>{{ k.text }}</p>
          <p class="mt-1 text-sm text-slate-500 dark:text-slate-400">{{ formatDatum(k.erstellt) }}</p>
        </div>
        <button class="btn btn-ghost !p-1.5 shrink-0" aria-label="Kommentar löschen" @click="kommentarLoeschen(k.id)">
          <AppIcon name="x" class="h-3.5 w-3.5" />
        </button>
      </li>
    </ul>
  </template>
</template>
