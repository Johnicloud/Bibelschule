<script setup>
import { inject, onMounted, ref } from 'vue'
import { isAdmin, username as currentUsername } from '../state/auth'

defineEmits(['back'])
const auth = inject('auth')

const accounts = ref([])
const loadError = ref('')

const oldPassword = ref('')
const newPassword = ref('')
const newPasswordWiederholt = ref('')
const pwError = ref('')
const pwSuccess = ref(false)

const newUsername = ref('')
const newUserPassword = ref('')
const newUserPasswordWiederholt = ref('')
const newUserIsAdmin = ref(false)
const userError = ref('')

async function load() {
  if (!isAdmin.value) return
  try { accounts.value = await auth.accounts(); loadError.value = '' }
  catch (e) { loadError.value = e.message }
}

async function changePassword() {
  pwError.value = ''
  pwSuccess.value = false
  if (newPassword.value !== newPasswordWiederholt.value) { pwError.value = 'Die beiden neuen Passwörter stimmen nicht überein.'; return }
  try {
    await auth.changePassword(oldPassword.value, newPassword.value)
    oldPassword.value = ''
    newPassword.value = ''
    newPasswordWiederholt.value = ''
    pwSuccess.value = true
  } catch (e) { pwError.value = e.message }
}

async function createAccount() {
  userError.value = ''
  if (newUserPassword.value !== newUserPasswordWiederholt.value) { userError.value = 'Die beiden Passwörter stimmen nicht überein.'; return }
  try {
    await auth.createAccount(newUsername.value, newUserPassword.value, newUserIsAdmin.value)
    newUsername.value = ''
    newUserPassword.value = ''
    newUserPasswordWiederholt.value = ''
    newUserIsAdmin.value = false
    await load()
  } catch (e) { userError.value = e.message }
}

onMounted(load)
</script>

<template>
  <button class="btn btn-ghost !px-2" @click="$emit('back')">Zurück</button>
  <h1 class="mt-2 text-3xl font-semibold tracking-tight">Konto</h1>
  <p class="mt-1 text-slate-500 dark:text-slate-400">Angemeldet als {{ currentUsername }}{{ isAdmin ? ' (Admin)' : '' }}.</p>

  <section class="panel mt-6 p-5">
    <h2 class="text-lg font-semibold">Passwort ändern</h2>
    <form class="mt-4 grid gap-3 sm:max-w-sm" @submit.prevent="changePassword">
      <input v-model="oldPassword" type="password" class="input" placeholder="Bisheriges Passwort" aria-label="Bisheriges Passwort" autocomplete="current-password" />
      <input v-model="newPassword" type="password" class="input" placeholder="Neues Passwort (mind. 8 Zeichen)" aria-label="Neues Passwort" autocomplete="new-password" />
      <input v-model="newPasswordWiederholt" type="password" class="input" placeholder="Neues Passwort wiederholen" aria-label="Neues Passwort wiederholen" autocomplete="new-password" />
      <button class="btn btn-primary justify-self-start">Passwort ändern</button>
      <p v-if="pwError" class="text-sm text-rose-600 dark:text-rose-400">{{ pwError }}</p>
      <p v-if="pwSuccess" class="text-sm text-teal-700 dark:text-teal-400">Passwort geändert.</p>
    </form>
  </section>

  <section v-if="isAdmin" class="panel mt-6 p-5">
    <h2 class="text-lg font-semibold">Benutzer</h2>
    <p v-if="loadError" class="mt-2 text-sm text-rose-600 dark:text-rose-400">{{ loadError }}</p>
    <ul v-else class="mt-3 divide-y divide-slate-200 dark:divide-slate-800">
      <li v-for="a in accounts" :key="a.username" class="flex items-center justify-between py-2 text-sm">
        {{ a.username }}
        <span v-if="a.is_admin" class="rounded-full bg-teal-100 px-2 py-0.5 text-xs text-teal-800 dark:bg-teal-500/15 dark:text-teal-300">Admin</span>
      </li>
    </ul>

    <h3 class="mt-6 text-sm font-medium text-slate-500 dark:text-slate-400">Neuen Benutzer anlegen</h3>
    <form class="mt-2 grid gap-3 sm:max-w-sm" @submit.prevent="createAccount">
      <input v-model="newUsername" class="input" placeholder="Benutzername" aria-label="Benutzername" />
      <input v-model="newUserPassword" type="password" class="input" placeholder="Passwort (mind. 8 Zeichen)" aria-label="Passwort" autocomplete="new-password" />
      <input v-model="newUserPasswordWiederholt" type="password" class="input" placeholder="Passwort wiederholen" aria-label="Passwort wiederholen" autocomplete="new-password" />
      <label class="flex items-center gap-1.5 text-sm">
        <input type="checkbox" v-model="newUserIsAdmin" class="h-4 w-4 rounded" />
        Admin (darf selbst neue Benutzer anlegen)
      </label>
      <button class="btn btn-primary justify-self-start">Anlegen</button>
      <p v-if="userError" class="text-sm text-rose-600 dark:text-rose-400">{{ userError }}</p>
    </form>
  </section>
</template>
