<script setup>
import { inject, ref } from 'vue'
import { KINDS } from '../../domain/kinds'

// Ohne `card`: neue Karte anlegen. Mit `card`: diese Karte bearbeiten (Lernstufe und Fälligkeit bleiben erhalten).
const props = defineProps({ deckId: String, card: Object })
const emit = defineEmits(['added', 'saved', 'cancel'])
const service = inject('service')

const bearbeiten = !!props.card
const kind = ref(props.card?.kind || 'classic')
const front = ref(props.card?.front || '')
const back = ref(props.card?.kind === 'classic' ? props.card.back : '')
const options = ref(props.card?.kind === 'choice' ? [...props.card.options] : ['', '', '', ''])
const correct = ref(props.card?.correct_index ?? 0) // Multiple Choice: Index 0-3, Richtig/Falsch: 0 = Richtig, 1 = Falsch
const setName = ref(props.card?.set_name || '')
const error = ref('')
const busy = ref(false)

function setKind(k) {
  kind.value = k
  correct.value = 0
  error.value = ''
}

async function submit() {
  error.value = ''
  busy.value = true
  try {
    const inhalt = {
      kind: kind.value,
      front: front.value,
      back: back.value,
      options: kind.value === 'choice' ? options.value : [],
      correct_index: kind.value === 'classic' ? null : correct.value,
    }
    if (bearbeiten) {
      await service.updateCard(props.deckId, props.card.id, { ...inhalt, set_name: setName.value.trim() })
      emit('saved')
      return
    }
    await service.addCard(props.deckId, { ...inhalt, set_name: setName.value.trim() })
    front.value = ''
    back.value = ''
    options.value = ['', '', '', '']
    correct.value = 0
    emit('added')
  } catch (e) {
    error.value = e.message
  } finally {
    busy.value = false
  }
}
</script>

<template>
  <form class="panel space-y-4 p-5" @submit.prevent="submit">
    <div class="grid gap-2 sm:grid-cols-3" role="group" aria-label="Kartentyp">
      <button v-for="(k, id) in KINDS" :key="id" type="button" :aria-pressed="kind === id"
        class="rounded-xl p-3 text-left ring-1 transition focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-teal-500"
        :class="kind === id
          ? 'bg-teal-50 ring-2 ring-teal-500 dark:bg-teal-500/10'
          : 'ring-slate-300 hover:bg-slate-50 dark:ring-slate-700 dark:hover:bg-slate-800'"
        @click="setKind(id)">
        <span class="block text-sm font-medium">{{ k.label }}</span>
        <span class="block text-xs text-slate-500 dark:text-slate-400">{{ k.hint }}</span>
      </button>
    </div>

    <textarea v-model="front" class="input min-h-[84px]" rows="3"
      :placeholder="kind === 'truefalse' ? 'Aussage, z. B. Wasser kocht bei 100 °C' : 'Frage'"
      :aria-label="kind === 'truefalse' ? 'Aussage' : 'Frage'"></textarea>

    <textarea v-if="kind === 'classic'" v-model="back" class="input min-h-[84px]" rows="3"
      placeholder="Antwort" aria-label="Antwort"></textarea>

    <fieldset v-else-if="kind === 'choice'" class="space-y-2">
      <legend class="mb-2 text-sm text-slate-500 dark:text-slate-400">Vier Antworten, markiere die richtige</legend>
      <label v-for="(_, i) in options" :key="i" class="flex items-center gap-3">
        <input v-model="correct" type="radio" name="correct" :value="i" class="h-4 w-4 accent-teal-600"
          :aria-label="`Antwort ${i + 1} ist richtig`" />
        <input v-model="options[i]" class="input" :placeholder="`Antwort ${i + 1}`" />
      </label>
    </fieldset>

    <fieldset v-else class="flex gap-3">
      <legend class="mb-2 text-sm text-slate-500 dark:text-slate-400">Die Aussage ist</legend>
      <label v-for="(label, i) in ['Richtig', 'Falsch']" :key="i"
        class="flex cursor-pointer items-center gap-2 rounded-xl px-4 py-2.5 ring-1 ring-slate-300 dark:ring-slate-700"
        :class="correct === i ? 'bg-teal-50 ring-2 !ring-teal-500 dark:bg-teal-500/10' : ''">
        <input v-model="correct" type="radio" name="tf" :value="i" class="accent-teal-600" />
        {{ label }}
      </label>
    </fieldset>

    <input v-model="setName" class="input" placeholder="Set (optional)" aria-label="Set" />

    <p v-if="error" class="text-sm text-rose-600 dark:text-rose-400">{{ error }}</p>
    <div class="flex gap-2">
      <button class="btn btn-primary" :disabled="busy">{{ bearbeiten ? 'Speichern' : 'Karte hinzufügen' }}</button>
      <button v-if="bearbeiten" type="button" class="btn btn-ghost" @click="$emit('cancel')">Abbrechen</button>
    </div>
  </form>
</template>
