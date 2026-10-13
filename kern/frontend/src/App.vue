<script setup>
import { computed, inject, onMounted, ref } from 'vue'
import AppHeader from './components/ui/AppHeader.vue'
import HomeView from './views/HomeView.vue'
import SubjectsView from './views/SubjectsView.vue'
import SubjectView from './views/SubjectView.vue'
import CardsView from './views/CardsView.vue'
import StudyView from './views/StudyView.vue'
import LoginView from './views/LoginView.vue'
import { loggedIn, username } from './state/auth'

const auth = inject('auth')
const view = ref('home') // 'home' | 'subjects' | 'subject' | 'cards' | 'study'
const subjectId = ref(null) // aktuelles Fach (Fach-Ansicht oder Lernen eines Fachs)
const tab = ref('aufgaben') // Reiter im Fach = Name des Dienstes (oder 'aufgaben' für den Umfang)

function go(next, id = null, nextTab = null) {
  view.value = next
  subjectId.value = id
  if (nextTab) tab.value = nextTab
}
function nav(id) { go(id) } // Lernen über die Navigation = alle fälligen Karten
async function logout() { await auth.logout().catch(() => {}); loggedIn.value = false }
const active = computed(() => (view.value === 'subject' ? 'subjects' : view.value))

onMounted(async () => {
  try { username.value = (await auth.me()).username; loggedIn.value = true }
  catch { loggedIn.value = false }
})
</script>

<template>
  <LoginView v-if="loggedIn === false" />
  <template v-else-if="loggedIn">
    <AppHeader :active="active" :username="username" @nav="nav" @logout="logout" />
    <main class="mx-auto max-w-5xl px-4 pb-24 pt-8">
      <HomeView v-if="view === 'home'" @open-subject="(id, t) => go('subject', id, t)" @study="go('study')" @nav="nav" />
      <SubjectsView v-else-if="view === 'subjects'" @open-subject="(id) => go('subject', id, 'aufgaben')" />
      <SubjectView v-else-if="view === 'subject'" :key="subjectId" :subject-id="subjectId" v-model:tab="tab"
        @back="go('subjects')" @study="go('study', subjectId)" />
      <CardsView v-else-if="view === 'cards'" />
      <StudyView v-else :deck-id="subjectId" @back="subjectId ? go('subject', subjectId) : go('home')" />
    </main>
  </template>
</template>
