<script setup>
import { inject, onMounted, ref } from 'vue'
import EmptyState from '../components/ui/EmptyState.vue'

defineEmits(['open-deck'])
const service = inject('service')
const decks = ref([])
const name = ref('')
const error = ref('')

async function load() { decks.value = await service.listDecks() }
async function create() {
  error.value = ''
  try { await service.createDeck(name.value); name.value = ''; await load() }
  catch (e) { error.value = e.message }
}
async function remove(deck) {
  if (!confirm(`Fach „${deck.name}“ mit allen Karteikarten löschen?`)) return
  await service.deleteDeck(deck.id)
  await load()
}
onMounted(load)
</script>

<template>
  <h1 class="text-3xl font-semibold tracking-tight">Fächer</h1>
  <p class="mt-1 text-slate-500 dark:text-slate-400">Wähle ein Fach, um Karten anzulegen oder zu lernen.</p>

  <form class="mt-6 flex gap-2" @submit.prevent="create">
    <input v-model="name" class="input" placeholder="Neues Fach, z. B. Biologie" aria-label="Name des Fachs" />
    <button class="btn btn-primary shrink-0">Fach anlegen</button>
  </form>
  <p v-if="error" class="mt-2 text-sm text-rose-600 dark:text-rose-400">{{ error }}</p>

  <ul v-if="decks.length" class="mt-6 grid gap-4 sm:grid-cols-2">
    <li v-for="d in decks" :key="d.id" class="panel flex flex-col p-5">
      <button class="text-left text-xl font-semibold hover:text-teal-600 dark:hover:text-teal-400" @click="$emit('open-deck', d.id)">
        {{ d.name }}
      </button>
      <p class="mt-1 text-sm text-slate-500 dark:text-slate-400">{{ d.card_count }} Karten, {{ d.due_count }} fällig</p>
      <div class="mt-4 h-1.5 overflow-hidden rounded-full bg-slate-200 dark:bg-slate-800" aria-hidden="true">
        <div class="h-full rounded-full bg-amber-500"
          :style="{ width: (d.card_count ? (d.due_count / d.card_count) * 100 : 0) + '%' }"></div>
      </div>
      <div class="mt-5 flex gap-2">
        <button class="btn btn-outline" @click="$emit('open-deck', d.id)">Öffnen</button>
        <button class="btn btn-danger ml-auto" @click="remove(d)">Löschen</button>
      </div>
    </li>
  </ul>
  <EmptyState v-else class="mt-6" title="Noch kein Fach" text="Gib oben einen Namen ein und lege dein erstes Fach an." />
</template>
