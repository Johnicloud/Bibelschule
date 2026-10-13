<script setup>
import AppIcon from './AppIcon.vue'

defineEmits(['study'])
</script>

<template>
  <!-- Schnellzugriff "Lernen" wie der Schnellerfassungs-Knopf der Finanzapp: rund, unten rechts, fest. -->
  <button type="button" class="fixed right-6 z-20 grid h-14 w-14 place-items-center rounded-full
    bg-primary text-white shadow-lg transition hover:bg-primary-darker hover:-translate-y-0.5
    focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary"
    style="bottom: calc(1.5rem + env(safe-area-inset-bottom, 0px))"
    aria-label="Lernen – fällige Karten und Verse" @click="$emit('study')">
    <AppIcon name="lernen" class="h-6 w-6" />
  </button>
</template>
