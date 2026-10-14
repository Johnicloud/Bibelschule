<script setup>
import { inject, onMounted, ref } from 'vue'
import CardForm from '../components/cards/CardForm.vue'
import CardItem from '../components/cards/CardItem.vue'
import EmptyState from '../components/ui/EmptyState.vue'

const props = defineProps({ subjectId: String })
const emit = defineEmits(['study', 'changed'])
const service = inject('service')
const deck = ref(null)
const error = ref('')
const anlegen = ref(false)

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
      <button v-if="!anlegen && deck.cards.length" type="button" class="btn btn-outline !py-1.5" @click="anlegen = true">+ Neue Karte</button>
    </div>

    <div v-if="anlegen" class="mb-4">
      <CardForm :deck-id="subjectId" @added="hinzugefuegt" />
      <button type="button" class="btn btn-ghost mt-2" @click="anlegen = false">Abbrechen</button>
    </div>

    <ul v-if="deck.cards.length" class="grid gap-3 md:grid-cols-2">
      <CardItem v-for="c in deck.cards" :key="c.id" :card="c" @delete="remove(c)" />
    </ul>
    <EmptyState v-else-if="!anlegen" title="Noch keine Karten" text="Lege die erste Karte an.">
      <button class="btn btn-primary" @click="anlegen = true">Erste Karte anlegen</button>
    </EmptyState>
  </template>
</template>
