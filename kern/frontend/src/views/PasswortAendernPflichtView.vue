<script setup>
import { inject, ref } from 'vue'

const emit = defineEmits(['erledigt', 'logout'])
const auth = inject('auth')

const oldPassword = ref('')
const newPassword = ref('')
const newPasswordWiederholt = ref('')
const error = ref('')
const speichert = ref(false)

async function submit() {
  error.value = ''
  if (newPassword.value !== newPasswordWiederholt.value) { error.value = 'Die beiden neuen Passwörter stimmen nicht überein.'; return }
  speichert.value = true
  try {
    await auth.changePassword(oldPassword.value, newPassword.value)
    emit('erledigt')
  } catch (e) { error.value = e.message }
  finally { speichert.value = false }
}
</script>

<template>
  <div class="mx-auto mt-24 max-w-sm px-4">
    <h1 class="text-2xl font-semibold tracking-tight">Neues Passwort wählen</h1>
    <p class="mt-1 text-sm opacity-70">
      Ein Admin hat dein Passwort zurückgesetzt. Gib das temporäre Passwort ein und wähle gleich ein eigenes,
      bevor es weitergeht.
    </p>
    <form class="panel mt-6 grid gap-3 p-5" @submit.prevent="submit">
      <input v-model="oldPassword" type="password" class="input" placeholder="Temporäres Passwort" aria-label="Temporäres Passwort" autocomplete="current-password" autofocus />
      <input v-model="newPassword" type="password" class="input" placeholder="Neues Passwort (mind. 8 Zeichen)" aria-label="Neues Passwort" autocomplete="new-password" />
      <input v-model="newPasswordWiederholt" type="password" class="input" placeholder="Neues Passwort wiederholen" aria-label="Neues Passwort wiederholen" autocomplete="new-password" />
      <button class="btn btn-primary" :disabled="speichert">{{ speichert ? 'Speichert …' : 'Passwort setzen' }}</button>
      <p v-if="error" class="text-sm text-error">{{ error }}</p>
    </form>
    <button class="btn btn-ghost mt-3 w-full" @click="$emit('logout')">Abmelden</button>
  </div>
</template>
