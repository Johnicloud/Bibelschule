<script setup>
import { computed, inject, onMounted, ref } from 'vue'
import EmptyState from '../components/ui/EmptyState.vue'
import CardForm from '../components/cards/CardForm.vue'
import CardItem from '../components/cards/CardItem.vue'
import { KINDS } from '../domain/kinds'

const service = inject('service')

const decks = ref([])
const cards = ref([])
const q = ref('')
const deckFilter = ref('')
const kindFilter = ref('')
const setFilter = ref('')
const bearbeitetId = ref(null)
const onlyDue = ref(false)
const error = ref('')

async function load() {
  try {
    ;[decks.value, cards.value] = await Promise.all([service.listDecks(), service.allCards()])
    error.value = ''
  } catch (e) { error.value = e.message }
}
async function gespeichert() { bearbeitetId.value = null; await load() }
// Sets des gewählten Fachs (oder aller Fächer): zur Auswahl im Filter
const setOptionen = computed(() => {
  const quellen = deckFilter.value ? decks.value.filter((d) => d.id === deckFilter.value) : decks.value
  return [...new Set(quellen.flatMap((d) => (d.sets || []).map((s) => s.name)))].sort((a, b) => a.localeCompare(b, 'de'))
})
const setsDesFachs = (deckId) => (decks.value.find((d) => d.id === deckId)?.sets || []).map((s) => s.name)
async function remove(card) {
  await service.deleteCard(card.deck_id, card.id)
  await load()
}

const filtered = computed(() => {
  const term = q.value.trim().toLowerCase()
  return cards.value.filter((c) =>
    (!deckFilter.value || c.deck_id === deckFilter.value) &&
    (!kindFilter.value || c.kind === kindFilter.value) &&
    (!setFilter.value || (setFilter.value === '__ohne__' ? !c.set_name : c.set_name === setFilter.value)) &&
    (!onlyDue.value || c.is_due) &&
    (!term || `${c.front} ${c.back}`.toLowerCase().includes(term)))
})

onMounted(load)
</script>

<template>
  <h1 class="text-3xl font-semibold tracking-tight">Alle Karten</h1>
  <p class="mt-1 text-slate-500 dark:text-slate-400">Suche und Filter über alle Fächer.</p>
  <p v-if="error" class="mt-4 text-sm text-rose-600 dark:text-rose-400">{{ error }}</p>

  <section class="mt-6">
    <div class="mb-4 grid gap-2 sm:grid-cols-[1fr_auto_auto_auto_auto]">
      <input v-model="q" class="input" placeholder="Karten durchsuchen" aria-label="Karten durchsuchen" />
      <select v-model="deckFilter" class="input sm:w-44" aria-label="Fach filtern">
        <option value="">Alle Fächer</option>
        <option v-for="d in decks" :key="d.id" :value="d.id">{{ d.name }}</option>
      </select>
      <select v-model="setFilter" class="input sm:w-44" aria-label="Set filtern">
        <option value="">Alle Sets</option>
        <option value="__ohne__">Ohne Set</option>
        <option v-for="s in setOptionen" :key="s" :value="s">Set: {{ s }}</option>
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
      <template v-for="c in filtered" :key="c.id">
        <li v-if="bearbeitetId === c.id" class="md:col-span-2">
          <CardForm :deck-id="c.deck_id" :card="c" :sets="setsDesFachs(c.deck_id)" @saved="gespeichert" @cancel="bearbeitetId = null" />
        </li>
        <CardItem v-else :card="c" show-deck bearbeitbar @edit="bearbeitetId = c.id" @delete="remove(c)" />
      </template>
    </ul>
    <EmptyState v-else :title="cards.length ? 'Keine Karte passt zum Filter' : 'Noch keine Karten'"
      :text="cards.length ? 'Ändere die Suche oder die Filter.' : 'Öffne ein Fach, um die erste Karte anzulegen.'" />
  </section>
</template>
