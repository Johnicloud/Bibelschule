<script setup>
import { computed, inject, onMounted, ref } from 'vue'
import CardForm from '../components/cards/CardForm.vue'
import CardItem from '../components/cards/CardItem.vue'
import AppIcon from '../components/ui/AppIcon.vue'
import EmptyState from '../components/ui/EmptyState.vue'
import { fensterOeffnen } from '../application/pdf'

const props = defineProps({ subjectId: String })
const emit = defineEmits(['study', 'changed'])
const service = inject('service')
const deck = ref(null)
const error = ref('')
const anlegen = ref(false)
const druckFehler = ref('')
const druckt = ref(false)
const druckFormat = ref('a7')
const bearbeitetId = ref(null)   // Karte, die gerade im Bearbeiten-Formular steht
const OHNE_SET = '__ohne__'
const setFilter = ref('')   // '' = alle Karten, OHNE_SET = Karten ohne Set, sonst der Name eines Sets
const setNamen = computed(() => (deck.value?.sets || []).map((s) => s.name))
const aktuellesSet = computed(() => (deck.value?.sets || []).find((s) => s.name === setFilter.value) || null)
const ohneSetAnzahl = computed(() => (deck.value?.cards || []).filter((c) => !c.set_name).length)

// Sets verwalten (eine Ebene unter dem Fach): anlegen, umbenennen, löschen
const setFehler = ref('')
const neuesSetOffen = ref(false)
const neuerSetName = ref('')
const umbenennenOffen = ref(false)
const umbenennenName = ref('')
const loeschenOffen = ref(false)
async function setAktion(fn) {
  setFehler.value = ''
  try { await fn(); await refresh(); return true } catch (e) { setFehler.value = e.message; return false }
}
async function setAnlegen() {
  const name = neuerSetName.value.trim()
  if (await setAktion(() => service.createSet(props.subjectId, name))) {
    neuesSetOffen.value = false; neuerSetName.value = ''; setFilter.value = name
  }
}
function umbenennenStarten() { umbenennenName.value = setFilter.value; umbenennenOffen.value = true; loeschenOffen.value = false }
async function setUmbenennen() {
  const neu = umbenennenName.value.trim()
  if (await setAktion(() => service.renameSet(props.subjectId, setFilter.value, neu))) {
    umbenennenOffen.value = false; setFilter.value = neu
  }
}
async function setLoeschen(mitKarten) {
  if (await setAktion(() => service.deleteSet(props.subjectId, setFilter.value, mitKarten))) {
    loeschenOffen.value = false; setFilter.value = ''
  }
}
function setWaehlen(wert) {
  setFilter.value = wert; setFehler.value = ''; umbenennenOffen.value = false; loeschenOffen.value = false
}

// Nummer = Platz im Fach, genau wie auf dem Druckbogen (der zählt in derselben Reihenfolge)
const nummerierte = computed(() => (deck.value?.cards || []).map((c, i) => ({ c, nummer: i + 1 })))
const sichtbar = computed(() => {
  if (setFilter.value === OHNE_SET) return nummerierte.value.filter((x) => !x.c.set_name)
  return setFilter.value ? nummerierte.value.filter((x) => x.c.set_name === setFilter.value) : nummerierte.value
})

async function load() {
  try { deck.value = await service.openDeck(props.subjectId); error.value = '' }
  catch (e) { error.value = 'Die Karteikarten kennen dieses Fach noch nicht. Gleiche die Dienste auf der Startseite ab.' }
}
async function refresh() { await load(); emit('changed') }
async function hinzugefuegt() { anlegen.value = false; await refresh() }
async function gespeichert() { bearbeitetId.value = null; await refresh() }
async function remove(card) {
  await service.deleteCard(props.subjectId, card.id)
  await refresh()
}
async function drucken() {
  druckFehler.value = ''
  druckt.value = true
  const fenster = fensterOeffnen()   // sofort im Klick öffnen, bevor die PDF geladen ist (siehe pdf.js)
  try { await service.drucken(props.subjectId, deck.value.name, fenster, druckFormat.value) }
  catch (e) { druckFehler.value = e.message; fenster?.close() }
  finally { druckt.value = false }
}
onMounted(load)
</script>

<template>
  <p v-if="error" class="text-sm text-rose-600 dark:text-rose-400">{{ error }}</p>
  <template v-else-if="deck">
    <div class="flex flex-wrap items-center justify-between gap-4">
      <p class="text-slate-500 dark:text-slate-400">{{ deck.card_count }} Karten, {{ deck.due_count }} fällig</p>
      <button class="btn btn-primary" :disabled="!deck.due_count" @click="$emit('study')">
        {{ deck.due_count ? `${deck.due_count} Karten lernen` : 'Nichts fällig' }}
      </button>
    </div>

    <div class="mb-3 mt-6 flex items-center justify-between">
      <h2 class="text-lg font-semibold">Karten in diesem Fach</h2>
      <div class="flex gap-2">
        <select v-if="deck.cards.length" v-model="druckFormat" class="input !w-auto !py-1.5" aria-label="Kartenformat">
          <option value="a7">A7</option>
          <option value="a8">A8</option>
        </select>
        <button v-if="deck.cards.length" type="button" class="btn btn-outline !py-1.5" :disabled="druckt" @click="drucken">
          {{ druckt ? 'Erzeugt PDF …' : 'Als PDF drucken' }}
        </button>
        <button v-if="!anlegen && deck.cards.length" type="button" class="btn btn-outline !py-1.5" @click="anlegen = true">+ Neue Karte</button>
      </div>
    </div>
    <p v-if="druckFehler" class="mb-3 text-sm text-rose-600 dark:text-rose-400">{{ druckFehler }}</p>

    <div v-if="anlegen" class="mb-4">
      <CardForm :deck-id="subjectId" :sets="setNamen" :vorgabe-set="aktuellesSet?.name" @added="hinzugefuegt" />
      <button type="button" class="btn btn-ghost mt-2" @click="anlegen = false">Abbrechen</button>
    </div>

    <!-- Sets: eine Ebene unter dem Fach. Ein Klick zeigt nur die Karten dieses Sets. -->
    <div class="mb-3 flex flex-wrap items-center gap-2" role="group" aria-label="Sets">
      <button type="button" class="rounded-full px-3 py-1 text-sm ring-1 ring-slate-300 dark:ring-slate-700"
        :class="setFilter === '' ? 'bg-primary text-white ring-0' : 'hover:bg-slate-100 dark:hover:bg-slate-800'" @click="setWaehlen('')">
        Alle ({{ deck.card_count }})
      </button>
      <button v-for="s in deck.sets" :key="s.name" type="button" class="rounded-full px-3 py-1 text-sm ring-1 ring-slate-300 dark:ring-slate-700"
        :class="setFilter === s.name ? 'bg-primary text-white ring-0' : 'hover:bg-slate-100 dark:hover:bg-slate-800'" @click="setWaehlen(s.name)">
        {{ s.name }} ({{ s.card_count }})
      </button>
      <button v-if="deck.sets.length && ohneSetAnzahl" type="button" class="rounded-full px-3 py-1 text-sm ring-1 ring-slate-300 dark:ring-slate-700"
        :class="setFilter === OHNE_SET ? 'bg-primary text-white ring-0' : 'hover:bg-slate-100 dark:hover:bg-slate-800'" @click="setWaehlen(OHNE_SET)">
        Ohne Set ({{ ohneSetAnzahl }})
      </button>
      <button type="button" class="rounded-full px-3 py-1 text-sm ring-1 ring-slate-300 hover:bg-slate-100 dark:ring-slate-700 dark:hover:bg-slate-800"
        @click="neuesSetOffen = !neuesSetOffen">+ Set</button>
    </div>

    <form v-if="neuesSetOffen" class="mb-3 flex flex-wrap gap-2" @submit.prevent="setAnlegen">
      <input v-model="neuerSetName" class="input !w-auto min-w-[14rem] flex-1" placeholder="Name des neuen Sets" aria-label="Name des neuen Sets" autofocus />
      <button class="btn btn-primary !py-1.5">Set anlegen</button>
      <button type="button" class="btn btn-ghost !py-1.5" @click="neuesSetOffen = false">Abbrechen</button>
    </form>

    <!-- Das gewählte Set: Name, Umbenennen, Löschen -->
    <div v-if="aktuellesSet" class="panel mb-3 space-y-3 p-4">
      <div v-if="!umbenennenOffen" class="flex flex-wrap items-center justify-between gap-2">
        <div>
          <h3 class="font-semibold">Set: {{ aktuellesSet.name }}</h3>
          <p class="text-sm text-slate-500 dark:text-slate-400">{{ aktuellesSet.card_count }} Karten, {{ aktuellesSet.due_count }} fällig</p>
        </div>
        <div class="flex gap-2">
          <button type="button" class="btn btn-outline !px-3 !py-1.5" title="Set umbenennen" aria-label="Set umbenennen" @click="umbenennenStarten">
            <AppIcon name="stift" class="h-4 w-4" />
          </button>
          <button type="button" class="btn btn-danger !px-3 !py-1.5" @click="loeschenOffen = !loeschenOffen; umbenennenOffen = false">Set löschen</button>
        </div>
      </div>
      <form v-else class="flex flex-wrap gap-2" @submit.prevent="setUmbenennen">
        <input v-model="umbenennenName" class="input !w-auto min-w-[14rem] flex-1" aria-label="Neuer Name des Sets" />
        <button class="btn btn-primary !py-1.5">Speichern</button>
        <button type="button" class="btn btn-ghost !py-1.5" @click="umbenennenOffen = false">Abbrechen</button>
      </form>
      <div v-if="loeschenOffen" class="space-y-2 text-sm">
        <p>„{{ aktuellesSet.name }}“ löschen? Die Karten können im Fach bleiben (ohne Set) oder mit gelöscht werden.</p>
        <div class="flex flex-wrap gap-2">
          <button type="button" class="btn btn-outline !py-1.5" @click="setLoeschen(false)">Set löschen, Karten behalten</button>
          <button type="button" class="btn btn-danger !py-1.5" @click="setLoeschen(true)">Set mit {{ aktuellesSet.card_count }} Karten löschen</button>
          <button type="button" class="btn btn-ghost !py-1.5" @click="loeschenOffen = false">Abbrechen</button>
        </div>
      </div>
    </div>
    <p v-if="setFehler" class="mb-3 text-sm text-rose-600 dark:text-rose-400">{{ setFehler }}</p>

    <ul v-if="deck.cards.length" class="grid gap-3 md:grid-cols-2">
      <template v-for="x in sichtbar" :key="x.c.id">
        <li v-if="bearbeitetId === x.c.id" class="md:col-span-2">
          <CardForm :deck-id="subjectId" :card="x.c" :sets="setNamen" @saved="gespeichert" @cancel="bearbeitetId = null" />
        </li>
        <CardItem v-else :card="x.c" :nummer="x.nummer" bearbeitbar @edit="bearbeitetId = x.c.id" @delete="remove(x.c)" />
      </template>
    </ul>
    <EmptyState v-else-if="!anlegen" title="Noch keine Karten" text="Lege die erste Karte an.">
      <button class="btn btn-primary" @click="anlegen = true">Erste Karte anlegen</button>
    </EmptyState>
  </template>
</template>
