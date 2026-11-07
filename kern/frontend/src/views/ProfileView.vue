<script setup>
import { computed, inject, onMounted, ref } from 'vue'
import AppIcon from '../components/ui/AppIcon.vue'
import { gemeinde, isAdmin, nachname, username as currentUsername, vorname } from '../state/auth'

defineEmits(['back'])
const auth = inject('auth')
const subjects = inject('subjects')

const profilVorname = ref(vorname.value)
const profilNachname = ref(nachname.value)
const profilGemeinde = ref(gemeinde.value)
const profilError = ref('')
const profilSuccess = ref(false)
async function speichernProfil() {
  profilError.value = ''
  profilSuccess.value = false
  try {
    await auth.updateProfile(profilVorname.value, profilNachname.value, profilGemeinde.value)
    vorname.value = profilVorname.value.trim()
    nachname.value = profilNachname.value.trim()
    gemeinde.value = profilGemeinde.value.trim()
    profilSuccess.value = true
  } catch (e) { profilError.value = e.message }
}

const accounts = ref([])
const loadError = ref('')
const adminError = ref('')
const zurueckgesetzt = ref(null) // { username, temp } – einmalige Anzeige des temporären Passworts

const services = ref([])
const servicesError = ref('')
const syncing = ref(false)
const offline = computed(() => services.value.filter((s) => !s.online))
async function loadServices() {
  try { services.value = await subjects.services(); servicesError.value = '' }
  catch (e) { servicesError.value = e.message }
}
async function sync() {
  syncing.value = true
  try { await subjects.sync() } catch (e) { servicesError.value = e.message }
  syncing.value = false
  await loadServices()
}

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

async function adminUmschalten(a) {
  adminError.value = ''
  try { await auth.setAdmin(a.username, !a.is_admin); await load() }
  catch (e) { adminError.value = e.message }
}
async function passwortZuruecksetzen(a) {
  if (!confirm(`Neues, zufälliges Passwort für „${a.username}“ setzen? Das Konto wird dabei überall abgemeldet und muss sich beim nächsten Anmelden ein eigenes Passwort wählen.`)) return
  adminError.value = ''
  zurueckgesetzt.value = null
  try {
    const { temporaeres_passwort } = await auth.resetPassword(a.username)
    zurueckgesetzt.value = { username: a.username, temp: temporaeres_passwort }
    await load()
  } catch (e) { adminError.value = e.message }
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

onMounted(() => { load(); loadServices() })
</script>

<template>
  <button class="btn btn-ghost !px-2" @click="$emit('back')">Zurück</button>
  <h1 class="mt-2 text-3xl font-semibold tracking-tight">Konto</h1>
  <p class="mt-1 text-slate-500 dark:text-slate-400">Angemeldet als {{ currentUsername }}{{ isAdmin ? ' (Admin)' : '' }}.</p>

  <section class="panel mt-6 p-5">
    <h2 class="text-lg font-semibold">Profil</h2>
    <p class="mt-1 text-sm opacity-70">Vorname, Name und Gemeinde füllen z. B. den Lesenachweis-PDF-Export vor.</p>
    <form class="mt-4 grid gap-3 sm:max-w-sm" @submit.prevent="speichernProfil">
      <input v-model="profilVorname" class="input" placeholder="Vorname" aria-label="Vorname" />
      <input v-model="profilNachname" class="input" placeholder="Name" aria-label="Name" />
      <input v-model="profilGemeinde" class="input" placeholder="Gemeinde" aria-label="Gemeinde" />
      <button class="btn btn-primary justify-self-start">Speichern</button>
      <p v-if="profilError" class="text-sm text-error">{{ profilError }}</p>
      <p v-if="profilSuccess" class="text-sm text-teal-700 dark:text-teal-400">Gespeichert.</p>
    </form>
  </section>

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
    <p v-if="adminError" class="mt-2 text-sm text-error">{{ adminError }}</p>
    <div v-if="zurueckgesetzt" class="mt-2 flex items-start justify-between gap-2 rounded-xl bg-amber-50 px-3 py-2 text-sm text-amber-800 dark:bg-amber-500/10 dark:text-amber-300">
      <span>
        Temporäres Passwort für „{{ zurueckgesetzt.username }}“: <strong class="select-all">{{ zurueckgesetzt.temp }}</strong>
        — steht nur jetzt hier, bitte dem Benutzer mitteilen (z. B. mündlich).
      </span>
      <button type="button" class="btn btn-ghost !p-1.5 shrink-0" aria-label="Hinweis schließen" @click="zurueckgesetzt = null">
        <AppIcon name="x" class="h-3.5 w-3.5" />
      </button>
    </div>
    <ul v-if="!loadError" class="mt-3 divide-y divide-slate-200 dark:divide-slate-800">
      <li v-for="a in accounts" :key="a.username" class="flex flex-wrap items-center justify-between gap-2 py-2 text-sm">
        <span>
          {{ a.username }}
          <span v-if="a.muss_passwort_aendern" class="ml-1.5 rounded-full bg-amber-100 px-2 py-0.5 text-xs text-amber-800 dark:bg-amber-500/15 dark:text-amber-300">
            muss neues Passwort wählen
          </span>
        </span>
        <span class="flex items-center gap-3">
          <label class="flex items-center gap-1.5">
            <input type="checkbox" :checked="a.is_admin" class="h-4 w-4 rounded" @change="adminUmschalten(a)" />
            Admin
          </label>
          <button type="button" class="btn btn-ghost !px-2 !py-1" @click="passwortZuruecksetzen(a)">Passwort neu setzen</button>
        </span>
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

  <section class="panel mt-6 p-5">
    <h2 class="text-lg font-semibold">Dienste</h2>
    <div class="mt-3 flex flex-wrap items-center gap-x-5 gap-y-2 text-sm">
      <span v-for="s in services" :key="s.name" class="flex items-center gap-2">
        <span class="h-2.5 w-2.5 rounded-full" :class="s.online ? 'bg-success' : 'bg-error'" aria-hidden="true"></span>
        {{ s.label }}
        <span class="sr-only">{{ s.online ? 'erreichbar' : 'nicht erreichbar' }}</span>
      </span>
      <span v-if="!services.length" class="opacity-70">Keine Dienste eingetragen.</span>
      <button class="btn btn-outline ml-auto !py-1.5" :disabled="syncing" @click="sync">
        {{ syncing ? 'Gleiche ab …' : 'Dienste abgleichen' }}
      </button>
    </div>
    <p v-if="servicesError" class="mt-2 text-sm text-error">{{ servicesError }}</p>
    <p v-if="offline.length" class="mt-2 text-sm text-amber-700 dark:text-amber-300">
      Nicht erreichbar: {{ offline.map((s) => s.label).join(', ') }}.
      Sobald der Dienst läuft, übernimmt „Dienste abgleichen“ alle Fächer.
    </p>
  </section>
</template>
