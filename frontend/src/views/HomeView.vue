<script setup>
import { computed, inject, onMounted, ref } from 'vue'
import StatCard from '../components/ui/StatCard.vue'
import EmptyState from '../components/ui/EmptyState.vue'
import CardItem from '../components/cards/CardItem.vue'
import { KINDS } from '../domain/kinds'

const emit = defineEmits(['open-deck', 'study', 'nav'])
const service = inject('service')

const decks = ref([])
const cards = ref([])
const q = ref('')
const deckFilter = ref('')
const kindFilter = ref('')
const onlyDue = ref(false)

async function load() {
  ;[decks.value, cards.value] = await Promise.all([service.listDecks(), service.allCards()])
}
async function remove(card) {
  await service.deleteCard(card.deck_id, card.id)
  await load()
}

const dueCount = computed(() => cards.value.filter((c) => c.is_due).length)
const mastered = computed(() => cards.value.filter((c) => c.box >= 4).length)
const filtered = computed(() => {
  const term = q.value.trim().toLowerCase()
  return cards.value.filter((c) =>
    (!deckFilter.value || c.deck_id === deckFilter.value) &&
    (!kindFilter.value || c.kind === kindFilter.value) &&
    (!onlyDue.value || c.is_due) &&
    (!term || `${c.front} ${c.back}`.toLowerCase().includes(term)))
})

onMounted(load)
</script>

<template>
  <section class="flex flex-wrap items-end justify-between gap-4">
    <div>
      <h1 class="text-3xl font-semibold tracking-tight">Dein Überblick</h1>
      <p class="mt-1 text-slate-500 dark:text-slate-400">Alle Fächer und Karten an einem Ort.</p>
    </div>
    <button class="btn btn-primary" :disabled="!dueCount" @click="$emit('study')">
      {{ dueCount ? `${dueCount} fällige Karten lernen` : 'Nichts fällig' }}
    </button>
  </section>

  <section class="mt-6 grid grid-cols-2 gap-3 sm:grid-cols-4" aria-label="Zahlen">
    <StatCard label="Fächer" :value="decks.length" />
    <StatCard label="Karten" :value="cards.length" tone="violet" />
    <StatCard label="Heute fällig" :value="dueCount" tone="amber" />
    <StatCard label="Sicher gelernt" :value="mastered" tone="teal" />
  </section>

  <section class="mt-10">
    <h2 class="mb-3 text-lg font-semibold">Fächer</h2>
    <div v-if="decks.length" class="flex flex-wrap gap-2">
      <button v-for="d in decks" :key="d.id" class="btn btn-outline" @click="$emit('open-deck', d.id)">
        {{ d.name }}
        <span class="rounded-full bg-slate-100 px-2 text-xs dark:bg-slate-800">{{ d.card_count }}</span>
        <span v-if="d.due_count" class="rounded-full bg-amber-100 px-2 text-xs text-amber-800 dark:bg-amber-500/15 dark:text-amber-300">
          {{ d.due_count }} fällig
        </span>
      </button>
    </div>
    <EmptyState v-else title="Noch kein Fach" text="Lege ein Fach an und füge Karteikarten hinzu.">
      <button class="btn btn-primary" @click="$emit('nav', 'decks')">Erstes Fach anlegen</button>
    </EmptyState>
  </section>

  <section class="mt-10">
    <h2 class="mb-3 text-lg font-semibold">Alle Karten</h2>
    <div class="mb-4 grid gap-2 sm:grid-cols-[1fr_auto_auto_auto]">
      <input v-model="q" class="input" placeholder="Karten durchsuchen" aria-label="Karten durchsuchen" />
      <select v-model="deckFilter" class="input sm:w-44" aria-label="Fach filtern">
        <option value="">Alle Fächer</option>
        <option v-for="d in decks" :key="d.id" :value="d.id">{{ d.name }}</option>
      </select>
      <select v-model="kindFilter" class="input sm:w-44" aria-label="Kartentyp filtern">
        <option value="">Alle Typen</option>
        <option v-for="(k, id) in KINDS" :key="id" :value="id">{{ k.label }}</option>
      </select>
      <label class="flex items-center gap-2 px-2 text-sm">
        <input v-model="onlyDue" type="checkbox" class="h-4 w-4 accent-teal-600" /> Nur fällige
      </label>
    </div>

    <ul v-if="filtered.length" class="grid gap-3 md:grid-cols-2">
      <CardItem v-for="c in filtered" :key="c.id" :card="c" show-deck @delete="remove(c)" />
    </ul>
    <EmptyState v-else :title="cards.length ? 'Keine Karte passt zum Filter' : 'Noch keine Karten'"
      :text="cards.length ? 'Ändere die Suche oder die Filter.' : 'Öffne ein Fach, um die erste Karte anzulegen.'" />
  </section>
</template>
