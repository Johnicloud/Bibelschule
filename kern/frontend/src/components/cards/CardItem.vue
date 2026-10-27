<script setup>
import KindBadge from '../ui/KindBadge.vue'
import DueBadge from '../ui/DueBadge.vue'
import BoxDots from '../ui/BoxDots.vue'

defineProps({ card: Object, showDeck: Boolean, nummer: Number })
defineEmits(['delete'])
</script>

<template>
  <li class="panel flex items-start justify-between gap-4 p-4">
    <div class="min-w-0 flex-1">
      <div class="mb-2 flex flex-wrap items-center gap-2">
        <span v-if="nummer" class="rounded-full bg-slate-100 px-2.5 py-0.5 text-xs font-semibold text-slate-600 dark:bg-slate-800 dark:text-slate-300" :title="`Nummer ${nummer} (wie auf dem Druckbogen)`">{{ nummer }}</span>
        <KindBadge :kind="card.kind" />
        <span v-if="card.set_name" class="rounded-full bg-slate-100 px-2.5 py-0.5 text-xs text-primary dark:bg-slate-800" title="Set">{{ card.set_name }}</span>
        <DueBadge :card="card" />
        <span v-if="showDeck" class="rounded-full bg-slate-100 px-2.5 py-0.5 text-xs text-slate-600 dark:bg-slate-800 dark:text-slate-300">
          {{ card.deck_name }}
        </span>
      </div>
      <p class="font-medium">{{ card.front }}</p>
      <p class="mt-0.5 text-sm text-slate-500 dark:text-slate-400">Antwort: {{ card.back }}</p>
      <div class="mt-3"><BoxDots :box="card.box" /></div>
    </div>
    <button class="btn btn-danger !px-3 !py-1.5" @click="$emit('delete')">Löschen</button>
  </li>
</template>
