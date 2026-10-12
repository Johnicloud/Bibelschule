<script setup>
defineProps({ title: String, text: String })
</script>

<template>
  <div class="panel border-dashed px-6 py-10 text-center">
    <p class="font-medium">{{ title }}</p>
    <p v-if="text" class="mt-1 text-sm text-slate-500 dark:text-slate-400">{{ text }}</p>
    <div class="mt-4 flex justify-center"><slot /></div>
  </div>
</template>
