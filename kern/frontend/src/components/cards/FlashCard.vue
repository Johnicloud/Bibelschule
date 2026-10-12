<script setup>
import KindBadge from '../ui/KindBadge.vue'

defineProps({ card: Object, flipped: Boolean })
defineEmits(['update:flipped'])
</script>

<template>
  <div class="perspective">
    <button type="button" class="relative block h-72 w-full preserve-3d transition-transform duration-500 motion-reduce:transition-none"
      :class="{ 'rotate-y-180': flipped }" :aria-label="flipped ? 'Frage anzeigen' : 'Antwort anzeigen'"
      @click="$emit('update:flipped', !flipped)">
      <span class="panel absolute inset-0 flex flex-col items-center justify-center gap-3 p-8 text-center backface-hidden">
        <KindBadge :kind="card.kind" />
        <span class="text-2xl font-medium leading-snug">{{ card.front }}</span>
        <span class="text-sm text-slate-400">Tippen zum Umdrehen</span>
      </span>
      <span class="absolute inset-0 flex rotate-y-180 flex-col items-center justify-center gap-3 rounded-2xl bg-teal-50 p-8 text-center ring-1 ring-teal-300 backface-hidden dark:bg-teal-950 dark:ring-teal-700">
        <span class="text-sm text-teal-700 dark:text-teal-300">Antwort</span>
        <span class="text-2xl font-medium leading-snug">{{ card.back }}</span>
      </span>
    </button>
  </div>
</template>
