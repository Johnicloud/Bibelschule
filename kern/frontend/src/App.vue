<script setup>
import { computed, inject, onBeforeUnmount, onMounted, ref } from 'vue'
import AppHeader from './components/ui/AppHeader.vue'
import AppNav from './components/ui/AppNav.vue'
import StudyFab from './components/ui/StudyFab.vue'
import HomeView from './views/HomeView.vue'
import SubjectsView from './views/SubjectsView.vue'
import SubjectView from './views/SubjectView.vue'
import CardsView from './views/CardsView.vue'
import StudyView from './views/StudyView.vue'
import LoginView from './views/LoginView.vue'
import ProfileView from './views/ProfileView.vue'
import AdressbuchView from './views/AdressbuchView.vue'
import NotenView from './views/NotenView.vue'
import BibelView from './views/BibelView.vue'
import PasswortAendernPflichtView from './views/PasswortAendernPflichtView.vue'
import { abmeldeHinweis, gemeinde, isAdmin, loggedIn, mussPasswortAendern, nachname, username, vorname } from './state/auth'

const IDLE_LOGOUT_MINUTEN = 15   // wie beim Server (MemorySessionStore): 15 Minuten ohne Aktivität
const IDLE_LOGOUT_MS = IDLE_LOGOUT_MINUTEN * 60 * 1000

const auth = inject('auth')
const view = ref('home') // 'home' | 'subjects' | 'subject' | 'cards' | 'study' | 'profile' | 'adressbuch' | 'noten' | 'bibel'
const subjectId = ref(null) // aktuelles Fach (Fach-Ansicht oder Lernen eines Fachs)
const tab = ref('uebersicht') // Reiter im Fach = Name des Dienstes (oder 'aufgaben'/'uebersicht')

function go(next, id = null, nextTab = null) {
  view.value = next
  subjectId.value = id
  if (nextTab) tab.value = nextTab
}
function nav(id) { go(id) } // Lernen über die Navigation = alle fälligen Karten
async function logout() { await auth.logout().catch(() => {}); loggedIn.value = false }
// Wie bei der Finanzapp: nach Inaktivitäts-Abmeldung steht auf der Anmeldeseite ein Hinweis, warum man
// plötzlich dort landet, statt kommentarlos zurück zum Login-Formular zu springen.
async function idleLogout() {
  await logout()
  abmeldeHinweis.value = `Du wurdest nach ${IDLE_LOGOUT_MINUTEN} Minuten ohne Benutzung abgemeldet.`
}
const active = computed(() => (view.value === 'subject' ? 'subjects' : view.value))

// Automatische Abmeldung nach Inaktivität (wie bei einer Finanz-App): irgendeine Nutzereingabe setzt den
// Timer zurück; läuft er ab, wird wie bei einer abgelaufenen Sitzung abgemeldet.
let idleTimer = null
function resetIdleTimer() {
  if (loggedIn.value !== true) return
  clearTimeout(idleTimer)
  idleTimer = setTimeout(idleLogout, IDLE_LOGOUT_MS)
}
const AKTIVITAET = ['mousedown', 'keydown', 'touchstart', 'scroll']
onMounted(() => {
  AKTIVITAET.forEach((ev) => window.addEventListener(ev, resetIdleTimer))
})
onBeforeUnmount(() => {
  clearTimeout(idleTimer)
  AKTIVITAET.forEach((ev) => window.removeEventListener(ev, resetIdleTimer))
})

onMounted(async () => {
  try {
    const me = await auth.me()
    username.value = me.username
    isAdmin.value = me.is_admin
    vorname.value = me.vorname || ''
    nachname.value = me.nachname || ''
    gemeinde.value = me.gemeinde || ''
    mussPasswortAendern.value = me.muss_passwort_aendern || false
    loggedIn.value = true
    resetIdleTimer()
  } catch { loggedIn.value = false }
})
</script>

<template>
  <LoginView v-if="loggedIn === false" />
  <PasswortAendernPflichtView v-else-if="loggedIn && mussPasswortAendern" @erledigt="mussPasswortAendern = false" @logout="logout" />
  <template v-else-if="loggedIn">
    <AppHeader :username="username" :zurueck="view === 'subject'" @nav="nav" @logout="logout" @profile="go('profile')" @back="go('subjects')" />
    <div class="mx-auto max-w-5xl px-4 pt-4">
      <AppNav :active="active" @nav="nav" />
    </div>
    <main class="mx-auto max-w-5xl px-4 pb-24 pt-6">
      <HomeView v-if="view === 'home'" @open-subject="(id, t) => go('subject', id, t)" @study="go('study')" @nav="nav" />
      <SubjectsView v-else-if="view === 'subjects'" @open-subject="(id) => go('subject', id, 'uebersicht')" />
      <SubjectView v-else-if="view === 'subject'" :key="subjectId" :subject-id="subjectId" v-model:tab="tab"
        @study="go('study', subjectId)" />
      <CardsView v-else-if="view === 'cards'" />
      <ProfileView v-else-if="view === 'profile'" @back="go('home')" />
      <AdressbuchView v-else-if="view === 'adressbuch'" />
      <NotenView v-else-if="view === 'noten'" />
      <BibelView v-else-if="view === 'bibel'" />
      <StudyView v-else :deck-id="subjectId" @back="subjectId ? go('subject', subjectId) : go('home')" />
    </main>
    <StudyFab @study="go('study')" />
  </template>
</template>
