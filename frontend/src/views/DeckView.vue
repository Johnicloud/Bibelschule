<script setup>
import { inject, onMounted, ref } from 'vue'
import CardForm from '../components/cards/CardForm.vue'
import CardItem from '../components/cards/CardItem.vue'
import EmptyState from '../components/ui/EmptyState.vue'

const props = defineProps({ deckId: String })
defineEmits(['back', 'study'])
const service = inject('service')
const deck = ref(null)

async function load() { deck.value = await service.openDeck(props.deckId) }
async function remove(card) {
  await service.deleteCard(props.deckId, card.id)
  await load()
}
onMounted(load)
</script>

<template>
  <template v-if="deck">
    <button class="btn btn-ghost !px-2" @click="$emit('back')">Zurück zu den Fächern</button>
    <div class="mt-2 flex flex-wrap items-end justify-between gap-4">
      <div>
        <h1 class="text-3xl font-semibold tracking-tight">{{ deck.name }}</h1>
        <p class="mt-1 text-slate-500 dark:text-slate-400">{{ deck.card_count }} Karten, {{ deck.due_count }} fällig</p>
      </div>
      <button class="btn btn-primary" :disabled="!deck.due_count" @click="$emit('study')">
        {{ deck.due_count ? `${deck.due_count} Karten lernen` : 'Nichts fällig' }}
      </button>
    </div>

    <h2 class="mb-3 mt-8 text-lg font-semibold">Neue Karte</h2>
    <CardForm :deck-id="deckId" @added="load" />

    <h2 class="mb-3 mt-10 text-lg font-semibold">Karten in diesem Fach</h2>
    <ul v-if="deck.cards.length" class="grid gap-3 md:grid-cols-2">
      <CardItem v-for="c in deck.cards" :key="c.id" :card="c" @delete="remove(c)" />
    </ul>
    <EmptyState v-else title="Noch keine Karten" text="Lege oben die erste Karte an." />
  </template>
</template>
