<script setup>
import { useTheme } from '../../composables/useTheme'

const { dark, toggle } = useTheme()
</script>

<template>
  <!-- Schalter wie ThemeToggle.vue der Finanzapp: Kippschalter mit Sonne/Mond statt Textzeile. -->
  <button type="button" role="switch" :aria-checked="dark" aria-label="Dunkles Design"
    class="relative h-6 w-11 shrink-0 rounded-full transition"
    :class="dark ? 'bg-primary' : 'bg-highlight'" @click="toggle">
    <span class="absolute top-0.5 grid h-5 w-5 place-items-center rounded-full bg-white text-primary shadow transition"
      :class="dark ? 'left-[22px]' : 'left-0.5'">
      <svg v-if="dark" class="h-3 w-3" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
        <path d="M21 12.8A9 9 0 1 1 11.2 3a7 7 0 0 0 9.8 9.8z" />
      </svg>
      <svg v-else class="h-3 w-3" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" aria-hidden="true">
        <circle cx="12" cy="12" r="4" /><path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4" />
      </svg>
    </span>
  </button>
</template>
