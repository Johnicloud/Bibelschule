<script setup>
defineProps({ box: { type: Number, default: 0 } })
</script>

<template>
  <span class="inline-flex gap-1" :title="`Lernstufe ${box} von 5`" role="img" :aria-label="`Lernstufe ${box} von 5`">
    <span v-for="n in 5" :key="n" class="h-1.5 w-4 rounded-full"
      :class="n <= box ? 'bg-teal-500' : 'bg-slate-200 dark:bg-slate-700'"></span>
  </span>
</template>
