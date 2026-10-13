<script setup>
import AccountMenu from './AccountMenu.vue'

defineProps({ username: String })
defineEmits(['nav', 'logout', 'profile'])
</script>

<template>
  <!-- Kopfleiste in Primärfarbe wie bei der Finanzapp (AppRoot .app-header): eigene Markenfarbe statt neutralem Grau.
       Die Reiter stehen seit der Finanzapp-Angleichung nicht mehr hier, sondern in AppNav.vue im Inhalt darunter. -->
  <header class="sticky top-0 z-10 flex h-14 items-center gap-2 bg-primary px-3 text-white sm:gap-4 sm:px-4">
    <button class="flex shrink-0 items-center gap-2 text-lg font-semibold tracking-tight" @click="$emit('nav', 'home')">
      <span class="grid h-8 w-8 place-items-center rounded-lg bg-white/15 text-white" aria-hidden="true">B</span>
      <span class="hidden sm:inline">Bibelschule</span>
    </button>

    <AccountMenu :username="username" class="ml-auto shrink-0" @profile="$emit('profile')" @logout="$emit('logout')" />
  </header>
</template>
