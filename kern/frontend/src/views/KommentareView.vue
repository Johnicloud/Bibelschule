<script setup>
import { inject, onMounted, ref } from 'vue'
import AppIcon from '../components/ui/AppIcon.vue'
import EmptyState from '../components/ui/EmptyState.vue'

const kommentare = inject('kommentare')

const quellen = ref([])
const loadError = ref('')
const ausgewaehlteQuelle = ref(null)
const eintraege = ref([])
const eintraegeError = ref('')

const blankQuelle = () => ({ titel: '', autor: '', sprache: 'de', lizenz: '', quell_url: '', namensnennung: '' })
const neueQuelle = ref(false)
const quelleForm = ref(blankQuelle())
const quelleError = ref('')

const blankEintrag = () => ({ buch: '', kapitel: '', vers_von: '', vers_bis: '', text: '' })
const neuerEintrag = ref(false)
const eintragForm = ref(blankEintrag())
const eintragError = ref('')

async function ladeQuellen() {
  try { quellen.value = await kommentare.quellen(); loadError.value = '' }
  catch (e) { loadError.value = e.message }
}

async function quelleWaehlen(q) {
  ausgewaehlteQuelle.value = q
  eintraegeError.value = ''
  try { eintraege.value = await kommentare.eintraegeZuQuelle(q.id) }
  catch (e) { eintraegeError.value = e.message }
}

async function quelleAnlegen() {
  quelleError.value = ''
  try {
    const q = await kommentare.quelleAnlegen(quelleForm.value)
    neueQuelle.value = false
    quelleForm.value = blankQuelle()
    await ladeQuellen()
    await quelleWaehlen(q)
  } catch (e) { quelleError.value = e.message }
}

async function quelleLoeschen(q) {
  if (!confirm(`Quelle „${q.titel}" mit allen ihren Kommentar-Einträgen löschen?`)) return
  await kommentare.quelleLoeschen(q.id)
  if (ausgewaehlteQuelle.value?.id === q.id) { ausgewaehlteQuelle.value = null; eintraege.value = [] }
  await ladeQuellen()
}

async function eintragAnlegen() {
  eintragError.value = ''
  try {
    await kommentare.eintragAnlegen({
      quelle_id: ausgewaehlteQuelle.value.id,
      buch: eintragForm.value.buch,
      kapitel: Number(eintragForm.value.kapitel),
      vers_von: Number(eintragForm.value.vers_von),
      vers_bis: Number(eintragForm.value.vers_bis || eintragForm.value.vers_von),
      text: eintragForm.value.text,
    })
    neuerEintrag.value = false
    eintragForm.value = blankEintrag()
    await quelleWaehlen(ausgewaehlteQuelle.value)
  } catch (e) { eintragError.value = e.message }
}

async function eintragLoeschen(e) {
  if (!confirm('Diesen Kommentar-Eintrag löschen?')) return
  await kommentare.eintragLoeschen(e.id)
  await quelleWaehlen(ausgewaehlteQuelle.value)
}

function bereichAnzeige(e) {
  return e.vers_von === e.vers_bis ? `${e.buch} ${e.kapitel},${e.vers_von}` : `${e.buch} ${e.kapitel},${e.vers_von}-${e.vers_bis}`
}

onMounted(ladeQuellen)
</script>

<template>
  <h1 class="text-3xl font-semibold tracking-tight">Kommentare</h1>
  <p class="mt-1 text-slate-500 dark:text-slate-400">
    Bibelkommentare aus gemeinfreien Quellen, je Vers oder Versbereich – unabhängig vom Fach.
  </p>

  <p v-if="loadError" class="mt-6 text-sm text-rose-600 dark:text-rose-400">{{ loadError }}</p>

  <div class="mt-6 flex flex-wrap items-center gap-2">
    <button v-for="q in quellen" :key="q.id" type="button"
      class="rounded-full px-3 py-1.5 text-sm font-medium transition"
      :class="ausgewaehlteQuelle?.id === q.id ? 'bg-primary text-white' : 'bg-backdrop text-theme-inv opacity-80 hover:opacity-100'"
      @click="quelleWaehlen(q)">
      {{ q.titel }}<span v-if="q.sprache && q.sprache !== 'de'" class="ml-1 opacity-70">({{ q.sprache }})</span>
    </button>
    <button v-if="!neueQuelle" type="button" class="btn btn-outline !py-1.5" @click="neueQuelle = true">+ Neue Quelle</button>
  </div>

  <form v-if="neueQuelle" class="panel mt-4 grid gap-3 p-4" @submit.prevent="quelleAnlegen">
    <div class="grid gap-3 sm:grid-cols-2">
      <input v-model="quelleForm.titel" class="input" placeholder="Titel, z. B. Dächsel, Bibelwerk" aria-label="Titel" required />
      <input v-model="quelleForm.autor" class="input" placeholder="Autor" aria-label="Autor" />
    </div>
    <div class="grid gap-3 sm:grid-cols-2">
      <input v-model="quelleForm.lizenz" class="input" placeholder="Lizenz, z. B. gemeinfrei" aria-label="Lizenz" />
      <select v-model="quelleForm.sprache" class="input" aria-label="Sprache">
        <option value="de">Deutsch</option>
        <option value="en">Englisch</option>
      </select>
    </div>
    <input v-model="quelleForm.quell_url" class="input" placeholder="Quell-URL (optional)" aria-label="Quell-URL" />
    <input v-model="quelleForm.namensnennung" class="input" placeholder="Namensnennung für Zitate (optional)" aria-label="Namensnennung" />
    <div>
      <button class="btn btn-primary">Quelle anlegen</button>
      <button type="button" class="btn btn-ghost ml-2" @click="neueQuelle = false; quelleForm = blankQuelle()">Abbrechen</button>
      <span v-if="quelleError" class="ml-3 text-sm text-rose-600 dark:text-rose-400">{{ quelleError }}</span>
    </div>
  </form>

  <EmptyState v-if="!loadError && !quellen.length && !neueQuelle" class="mt-6" title="Noch keine Quelle"
    text="Lege die erste Kommentar-Quelle an, z. B. Dächsels Bibelwerk.">
    <button class="btn btn-primary" @click="neueQuelle = true">Erste Quelle anlegen</button>
  </EmptyState>

  <div v-if="ausgewaehlteQuelle" class="panel mt-6 p-5">
    <div class="flex flex-wrap items-start justify-between gap-3">
      <div>
        <p class="text-lg font-semibold">{{ ausgewaehlteQuelle.titel }}</p>
        <p v-if="ausgewaehlteQuelle.autor" class="text-sm text-slate-500 dark:text-slate-400">{{ ausgewaehlteQuelle.autor }}</p>
        <p v-if="ausgewaehlteQuelle.namensnennung" class="mt-1 text-xs italic text-slate-500 dark:text-slate-400">
          {{ ausgewaehlteQuelle.namensnennung }}
        </p>
        <a v-if="ausgewaehlteQuelle.quell_url" :href="ausgewaehlteQuelle.quell_url" target="_blank"
          class="text-xs text-primary hover:underline">Quelle öffnen</a>
      </div>
      <button class="btn btn-danger !px-2.5 !py-1 shrink-0" @click="quelleLoeschen(ausgewaehlteQuelle)">Quelle löschen</button>
    </div>

    <div class="mt-4 flex items-center justify-between gap-2">
      <h2 class="font-semibold">Einträge</h2>
      <button v-if="!neuerEintrag" type="button" class="btn btn-outline !py-1.5" @click="neuerEintrag = true">+ Neuer Eintrag</button>
    </div>

    <form v-if="neuerEintrag" class="mt-3 grid gap-2" @submit.prevent="eintragAnlegen">
      <div class="grid grid-cols-2 gap-2 sm:grid-cols-4">
        <input v-model="eintragForm.buch" class="input" placeholder="Buch, z. B. Joh" aria-label="Buch" required />
        <input v-model="eintragForm.kapitel" type="number" min="1" class="input" placeholder="Kapitel" aria-label="Kapitel" required />
        <input v-model="eintragForm.vers_von" type="number" min="1" class="input" placeholder="Vers (von)" aria-label="Vers von" required />
        <input v-model="eintragForm.vers_bis" type="number" min="1" class="input" placeholder="bis (optional)" aria-label="Vers bis" />
      </div>
      <textarea v-model="eintragForm.text" class="input" rows="4" placeholder="Kommentartext" aria-label="Kommentartext" required />
      <div>
        <button class="btn btn-primary !py-1.5">Eintrag anlegen</button>
        <button type="button" class="btn btn-ghost ml-2 !py-1.5" @click="neuerEintrag = false; eintragForm = blankEintrag()">Abbrechen</button>
        <span v-if="eintragError" class="ml-3 text-sm text-rose-600 dark:text-rose-400">{{ eintragError }}</span>
      </div>
    </form>

    <p v-if="eintraegeError" class="mt-3 text-sm text-rose-600 dark:text-rose-400">{{ eintraegeError }}</p>
    <ul v-if="eintraege.length" class="mt-3 grid gap-2">
      <li v-for="e in eintraege" :key="e.id" class="rounded-lg bg-backdrop p-3">
        <div class="flex items-start justify-between gap-2">
          <p class="text-sm font-semibold text-primary">{{ bereichAnzeige(e) }}</p>
          <button class="btn btn-ghost !p-1 shrink-0" :aria-label="`${bereichAnzeige(e)} löschen`" @click="eintragLoeschen(e)">
            <AppIcon name="papierkorb" class="h-3.5 w-3.5" />
          </button>
        </div>
        <p class="mt-1 whitespace-pre-line text-sm">{{ e.text }}</p>
      </li>
    </ul>
    <p v-else-if="!eintraegeError" class="mt-3 text-sm text-slate-500 dark:text-slate-400">Noch kein Eintrag zu dieser Quelle.</p>
  </div>
</template>
