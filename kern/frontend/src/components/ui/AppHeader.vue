<script setup>
import AccountMenu from './AccountMenu.vue'
import AppIcon from './AppIcon.vue'

defineProps({ username: String, zurueck: Boolean })
defineEmits(['nav', 'logout', 'profile', 'back'])
</script>

<template>
  <!-- Kopfleiste in Primärfarbe wie bei der Finanzapp (AppRoot .app-header): eigene Markenfarbe statt neutralem Grau.
       Die Reiter stehen seit der Finanzapp-Angleichung nicht mehr hier, sondern in AppNav.vue im Inhalt darunter.
       Pfeil zurück (statt eines Text-Knopfes auf der Fach-Seite) erscheint hier, sobald man in einem Fach ist. -->
  <header class="sticky top-0 z-10 flex h-14 items-center gap-2 bg-primary px-3 text-white sm:gap-4 sm:px-4">
    <button v-if="zurueck" type="button" class="grid h-9 w-9 shrink-0 place-items-center rounded-full text-white transition hover:bg-white/15"
      aria-label="Zurück zu den Fächern" @click="$emit('back')">
      <AppIcon name="zurueck" class="h-5 w-5" />
    </button>
    <button class="flex shrink-0 items-center gap-2 text-lg font-semibold tracking-tight" @click="$emit('nav', 'home')">
      <span class="grid h-8 w-8 place-items-center rounded-lg bg-white/15 text-white" aria-hidden="true">B</span>
      <span class="hidden sm:inline">Bibelschule</span>
    </button>

    <AccountMenu :username="username" class="ml-auto shrink-0" @profile="$emit('profile')" @logout="$emit('logout')" />
  </header>
</template>
