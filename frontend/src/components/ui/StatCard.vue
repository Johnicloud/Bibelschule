<script setup>
defineProps({ label: String, value: [Number, String], tone: { type: String, default: 'slate' } })
const tones = {
  slate: 'text-slate-900 dark:text-slate-100',
  teal: 'text-teal-600 dark:text-teal-400',
  amber: 'text-amber-600 dark:text-amber-400',
  violet: 'text-violet-600 dark:text-violet-400',
}
</script>

<template>
  <div class="panel p-4">
    <div class="text-3xl font-semibold tabular-nums" :class="tones[tone]">{{ value }}</div>
    <div class="mt-1 text-sm text-slate-500 dark:text-slate-400">{{ label }}</div>
  </div>
</template>
