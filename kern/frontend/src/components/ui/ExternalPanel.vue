<script setup>
// Oberfläche eines Dienstes, die der Dienst selbst mitbringt (manifest.panel). So braucht ein neuer Dienst keine Änderung hier.
defineProps({ src: String, title: String })
</script>

<template>
  <iframe :src="src" :title="title"
    class="h-[70vh] w-full rounded-2xl bg-white ring-1 ring-slate-200 dark:bg-slate-900 dark:ring-slate-800"></iframe>
</template>
