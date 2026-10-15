<script setup>
import { inject, ref } from 'vue'
import { abmeldeHinweis, gemeinde, isAdmin, loggedIn, mussPasswortAendern, nachname, username as currentUsername, vorname } from '../state/auth'

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
    isAdmin.value = res.is_admin
    vorname.value = res.vorname || ''
    nachname.value = res.nachname || ''
    gemeinde.value = res.gemeinde || ''
    mussPasswortAendern.value = res.muss_passwort_aendern || false
    loggedIn.value = true
    abmeldeHinweis.value = ''
  } catch (e) { error.value = e.message }
  finally { busy.value = false }
}
</script>

<template>
  <div class="mx-auto mt-24 max-w-sm px-4">
    <h1 class="text-2xl font-semibold tracking-tight">Anmelden</h1>
    <p class="mt-1 text-sm text-slate-500 dark:text-slate-400">Bibelschule ist nur für eingeladene Konten.</p>
    <p v-if="abmeldeHinweis" class="panel mt-4 p-3 text-sm text-amber-700 dark:text-amber-300">{{ abmeldeHinweis }}</p>
    <form class="panel mt-6 grid gap-3 p-5" @submit.prevent="submit">
      <input v-model="username" class="input" placeholder="Benutzername" aria-label="Benutzername" autocomplete="username" autofocus />
      <input v-model="password" type="password" class="input" placeholder="Passwort" aria-label="Passwort" autocomplete="current-password" />
      <button class="btn btn-primary" :disabled="busy">{{ busy ? 'Melde an …' : 'Anmelden' }}</button>
      <p v-if="error" class="text-sm text-rose-600 dark:text-rose-400">{{ error }}</p>
    </form>
  </div>
</template>
