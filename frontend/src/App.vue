<script setup>
import { computed, ref } from 'vue'
import AppHeader from './components/ui/AppHeader.vue'
import HomeView from './views/HomeView.vue'
import DecksView from './views/DecksView.vue'
import DeckView from './views/DeckView.vue'
import StudyView from './views/StudyView.vue'

const view = ref('home') // 'home' | 'decks' | 'deck' | 'study'
const deckId = ref(null) // aktuelles Fach (Detailansicht oder Lernen eines Fachs)

function go(next, id = null) {
  view.value = next
  deckId.value = id
}
function nav(id) { go(id) } // Lernen über die Navigation = alle fälligen Karten
const active = computed(() => (view.value === 'deck' ? 'decks' : view.value))
</script>

<template>
  <AppHeader :active="active" @nav="nav" />
  <main class="mx-auto max-w-5xl px-4 pb-24 pt-8">
    <HomeView v-if="view === 'home'" @open-deck="(id) => go('deck', id)" @study="go('study')" @nav="nav" />
    <DecksView v-else-if="view === 'decks'" @open-deck="(id) => go('deck', id)" />
    <DeckView v-else-if="view === 'deck'" :deck-id="deckId" @back="go('decks')" @study="go('study', deckId)" />
    <StudyView v-else :deck-id="deckId" @back="deckId ? go('deck', deckId) : go('home')" />
  </main>
</template>
