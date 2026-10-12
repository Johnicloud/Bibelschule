<script setup>
import { computed, inject, onMounted, ref } from 'vue'
import FlashCard from '../components/cards/FlashCard.vue'
import ChoiceCard from '../components/cards/ChoiceCard.vue'
import EmptyState from '../components/ui/EmptyState.vue'

const props = defineProps({ deckId: { type: String, default: null } }) // leer = alle Fächer
defineEmits(['back'])
const service = inject('service')

const queue = ref([])
const index = ref(0)
const loaded = ref(false)
const flipped = ref(false)
const picked = ref(null)
const right = ref(0)
const wrong = ref(0)

const card = computed(() => queue.value[index.value])
const done = computed(() => loaded.value && index.value >= queue.value.length)
const percent = computed(() => (queue.value.length ? (index.value / queue.value.length) * 100 : 0))
const isChoice = computed(() => card.value && card.value.kind !== 'classic')
const pickedRight = computed(() => picked.value !== null && picked.value === card.value.correct_index)

async function submit(correct) {
  const current = card.value
  await service.answer(current.deck_id, current.id, correct)
  if (correct) right.value++
  else { wrong.value++; queue.value.push(current) } // falsche Karten kommen in dieser Runde nochmal
  flipped.value = false
  picked.value = null
  index.value++
}
function pick(i) {
  if (picked.value === null) picked.value = i
}

onMounted(async () => {
  queue.value = await service.startSession(props.deckId)
  loaded.value = true
})
</script>

<template>
  <div class="mx-auto max-w-2xl">
    <template v-if="!loaded"></template>

    <EmptyState v-else-if="!queue.length" title="Alles erledigt" text="Gerade ist keine Karte fällig.">
      <button class="btn btn-primary" @click="$emit('back')">Zurück</button>
    </EmptyState>

    <div v-else-if="done" class="panel p-8 text-center">
      <h1 class="text-3xl font-semibold tracking-tight">Geschafft</h1>
      <p class="mt-2 text-slate-500 dark:text-slate-400">
        {{ right }} richtig, {{ wrong }} falsch. Die Stufen deiner Karten sind aktualisiert.
      </p>
      <button class="btn btn-primary mt-6" @click="$emit('back')">Fertig</button>
    </div>

    <template v-else-if="card">
      <div class="mb-2 flex items-center justify-between text-sm text-slate-500 dark:text-slate-400">
        <span>{{ card.deck_name }}</span>
        <span>Karte {{ index + 1 }} von {{ queue.length }}</span>
      </div>
      <div class="mb-6 h-1.5 overflow-hidden rounded-full bg-slate-200 dark:bg-slate-800" role="progressbar"
        :aria-valuenow="Math.round(percent)" aria-valuemin="0" aria-valuemax="100">
        <div class="h-full rounded-full bg-teal-500 transition-all" :style="{ width: percent + '%' }"></div>
      </div>

      <FlashCard v-if="!isChoice" :key="card.id + index" :card="card" v-model:flipped="flipped" />
      <ChoiceCard v-else :card="card" :picked="picked" @pick="pick" />

      <div class="mt-5">
        <template v-if="!isChoice">
          <div v-if="flipped" class="grid grid-cols-2 gap-3">
            <button class="btn bg-rose-600 text-white hover:bg-rose-700" @click="submit(false)">Nicht gewusst</button>
            <button class="btn bg-emerald-600 text-white hover:bg-emerald-700" @click="submit(true)">Gewusst</button>
          </div>
          <p v-else class="text-center text-sm text-slate-500 dark:text-slate-400">Überlege kurz, dann dreh die Karte um.</p>
        </template>
        <template v-else>
          <div v-if="picked !== null" class="flex items-center justify-between gap-4">
            <p class="font-medium" :class="pickedRight ? 'text-emerald-600 dark:text-emerald-400' : 'text-rose-600 dark:text-rose-400'">
              {{ pickedRight ? 'Richtig!' : 'Leider falsch.' }}
            </p>
            <button class="btn btn-primary" @click="submit(pickedRight)">Weiter</button>
          </div>
          <p v-else class="text-center text-sm text-slate-500 dark:text-slate-400">Wähle eine Antwort.</p>
        </template>
      </div>

      <button class="btn btn-ghost mt-8" @click="$emit('back')">Lernen beenden</button>
    </template>
  </div>
</template>
