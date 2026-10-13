<script setup>
import { computed, ref } from 'vue'
import AppHeader from './components/ui/AppHeader.vue'
import HomeView from './views/HomeView.vue'
import SubjectsView from './views/SubjectsView.vue'
import SubjectView from './views/SubjectView.vue'
import CardsView from './views/CardsView.vue'
import StudyView from './views/StudyView.vue'

const view = ref('home') // 'home' | 'subjects' | 'subject' | 'cards' | 'study'
const subjectId = ref(null) // aktuelles Fach (Fach-Ansicht oder Lernen eines Fachs)
const tab = ref('karteikarten') // Reiter im Fach = Name des Dienstes

function go(next, id = null, nextTab = null) {
  view.value = next
  subjectId.value = id
  if (nextTab) tab.value = nextTab
}
function nav(id) { go(id) } // Lernen über die Navigation = alle fälligen Karten
const active = computed(() => (view.value === 'subject' ? 'subjects' : view.value))
</script>

<template>
  <AppHeader :active="active" @nav="nav" />
  <main class="mx-auto max-w-5xl px-4 pb-24 pt-8">
    <HomeView v-if="view === 'home'" @open-subject="(id, t) => go('subject', id, t)" @study="go('study')" @nav="nav" />
    <SubjectsView v-else-if="view === 'subjects'" @open-subject="(id) => go('subject', id, 'karteikarten')" />
    <SubjectView v-else-if="view === 'subject'" :key="subjectId" :subject-id="subjectId" v-model:tab="tab"
      @back="go('subjects')" @study="go('study', subjectId)" />
    <CardsView v-else-if="view === 'cards'" />
    <StudyView v-else :deck-id="subjectId" @back="subjectId ? go('subject', subjectId) : go('home')" />
  </main>
</template>
