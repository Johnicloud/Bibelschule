<script setup>
import KindBadge from '../ui/KindBadge.vue'

const props = defineProps({ card: Object, picked: { type: Number, default: null } })
defineEmits(['pick'])

const styles = {
  idle: 'bg-white ring-slate-300 hover:ring-teal-500 dark:bg-slate-900 dark:ring-slate-700 dark:hover:ring-teal-400',
  correct: 'bg-emerald-50 ring-2 ring-emerald-500 dark:bg-emerald-500/10',
  wrong: 'bg-rose-50 ring-2 ring-rose-500 dark:bg-rose-500/10',
  dim: 'bg-white opacity-50 ring-slate-200 dark:bg-slate-900 dark:ring-slate-800',
}

function state(i) {
  if (props.picked === null) return 'idle'
  if (i === props.card.correct_index) return 'correct'
  if (i === props.picked) return 'wrong'
  return 'dim'
}
</script>

<template>
  <div class="panel p-6 sm:p-8">
    <KindBadge :kind="card.kind" />
    <p class="mt-4 text-2xl font-medium leading-snug">{{ card.front }}</p>

    <div class="mt-6 grid gap-3" :class="card.kind === 'truefalse' ? 'sm:grid-cols-2' : 'grid-cols-1'">
      <button v-for="(opt, i) in card.options" :key="i" type="button" :disabled="picked !== null"
        class="flex items-center gap-3 rounded-xl px-4 py-3.5 text-left ring-1 transition focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-teal-500"
        :class="styles[state(i)]" @click="$emit('pick', i)">
        <span v-if="card.kind === 'choice'"
          class="grid h-7 w-7 shrink-0 place-items-center rounded-lg bg-slate-100 text-xs font-semibold dark:bg-slate-800">
          {{ 'ABCD'[i] }}
        </span>
        <span class="flex-1">{{ opt }}</span>
        <span v-if="state(i) === 'correct'" class="text-sm font-medium text-emerald-600 dark:text-emerald-400">Richtig</span>
        <span v-else-if="state(i) === 'wrong'" class="text-sm font-medium text-rose-600 dark:text-rose-400">Falsch</span>
      </button>
    </div>
  </div>
</template>
