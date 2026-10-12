<script setup>
import { computed } from 'vue'
import { dueInfo } from '../../domain/due'

const props = defineProps({ card: Object })
const info = computed(() => dueInfo(props.card))
</script>

<template>
  <span class="inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-xs font-medium"
    :class="info.due
      ? 'bg-amber-100 text-amber-800 dark:bg-amber-500/15 dark:text-amber-300'
      : 'bg-slate-100 text-slate-600 dark:bg-slate-800 dark:text-slate-400'">
    <span class="h-1.5 w-1.5 rounded-full" :class="info.due ? 'bg-amber-500' : 'bg-slate-400'"></span>
    {{ info.text }}
  </span>
</template>
