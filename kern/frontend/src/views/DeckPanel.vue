<script setup>
import { computed, inject, onMounted, ref } from 'vue'
import CardForm from '../components/cards/CardForm.vue'
import CardItem from '../components/cards/CardItem.vue'
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
const setFilter = ref('')   // '' = alle Karten

// Nummer = Platz im Fach, genau wie auf dem Druckbogen (der zählt in derselben Reihenfolge)
const nummerierte = computed(() => (deck.value?.cards || []).map((c, i) => ({ c, nummer: i + 1 })))
const sets = computed(() => [...new Set((deck.value?.cards || []).map((c) => c.set_name).filter(Boolean))])
const sichtbar = computed(() => (setFilter.value ? nummerierte.value.filter((x) => x.c.set_name === setFilter.value) : nummerierte.value))

async function load() {
  try { deck.value = await service.openDeck(props.subjectId); error.value = '' }
  catch (e) { error.value = 'Die Karteikarten kennen dieses Fach noch nicht. Gleiche die Dienste auf der Startseite ab.' }
}
async function refresh() { await load(); emit('changed') }
async function hinzugefuegt() { anlegen.value = false; await refresh() }
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
      <CardForm :deck-id="subjectId" @added="hinzugefuegt" />
      <button type="button" class="btn btn-ghost mt-2" @click="anlegen = false">Abbrechen</button>
    </div>

    <select v-if="sets.length" v-model="setFilter" class="input mb-3 !w-auto !py-1.5" aria-label="Set wählen">
      <option value="">Alle Karten</option>
      <option v-for="s in sets" :key="s" :value="s">Set: {{ s }}</option>
    </select>
    <ul v-if="deck.cards.length" class="grid gap-3 md:grid-cols-2">
      <CardItem v-for="x in sichtbar" :key="x.c.id" :card="x.c" :nummer="x.nummer" @delete="remove(x.c)" />
    </ul>
    <EmptyState v-else-if="!anlegen" title="Noch keine Karten" text="Lege die erste Karte an.">
      <button class="btn btn-primary" @click="anlegen = true">Erste Karte anlegen</button>
    </EmptyState>
  </template>
</template>
