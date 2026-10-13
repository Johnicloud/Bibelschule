<script setup>
import { inject, ref } from 'vue'
import { loggedIn, username as currentUsername } from '../state/auth'

const auth = inject('auth')
const username = ref('')
const password = ref('')
const error = ref('')
const busy = ref(false)

async function submit() {
  error.value = ''
  busy.value = true
  try {
    const res = await auth.login(username.value, password.value)
    currentUsername.value = res.username
    loggedIn.value = true
  } catch (e) { error.value = e.message }
  finally { busy.value = false }
}
</script>

<template>
  <div class="mx-auto mt-24 max-w-sm px-4">
    <h1 class="text-2xl font-semibold tracking-tight">Anmelden</h1>
    <p class="mt-1 text-sm text-slate-500 dark:text-slate-400">Bibelschule ist nur für eingeladene Konten.</p>
    <form class="panel mt-6 grid gap-3 p-5" @submit.prevent="submit">
      <input v-model="username" class="input" placeholder="Benutzername" aria-label="Benutzername" autocomplete="username" autofocus />
      <input v-model="password" type="password" class="input" placeholder="Passwort" aria-label="Passwort" autocomplete="current-password" />
      <button class="btn btn-primary" :disabled="busy">{{ busy ? 'Melde an …' : 'Anmelden' }}</button>
      <p v-if="error" class="text-sm text-rose-600 dark:text-rose-400">{{ error }}</p>
    </form>
  </div>
</template>
