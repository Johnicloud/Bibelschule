<script setup>
import { inject, onMounted, ref } from 'vue'
import CardForm from '../components/cards/CardForm.vue'
import CardItem from '../components/cards/CardItem.vue'
import EmptyState from '../components/ui/EmptyState.vue'

const props = defineProps({ subjectId: String })
defineEmits(['study'])
const service = inject('service')
const deck = ref(null)
const error = ref('')

async function load() {
  try { deck.value = await service.openDeck(props.subjectId); error.value = '' }
  catch (e) { error.value = 'Die Karteikarten kennen dieses Fach noch nicht. Gleiche die Dienste auf der Startseite ab.' }
}
async function remove(card) {
  await service.deleteCard(props.subjectId, card.id)
  await load()
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

    <h2 class="mb-3 mt-6 text-lg font-semibold">Neue Karte</h2>
    <CardForm :deck-id="subjectId" @added="load" />

    <h2 class="mb-3 mt-10 text-lg font-semibold">Karten in diesem Fach</h2>
    <ul v-if="deck.cards.length" class="grid gap-3 md:grid-cols-2">
      <CardItem v-for="c in deck.cards" :key="c.id" :card="c" @delete="remove(c)" />
    </ul>
    <EmptyState v-else title="Noch keine Karten" text="Lege oben die erste Karte an." />
  </template>
</template>
