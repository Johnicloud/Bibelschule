<script setup>
import { inject, onMounted, ref } from 'vue'
import EmptyState from '../components/ui/EmptyState.vue'
import SubjectCreateForm from '../components/ui/SubjectCreateForm.vue'
import AppIcon from '../components/ui/AppIcon.vue'

defineEmits(['open-subject'])
const subjects = inject('subjects')
const list = ref([])
const anlegen = ref(false)
const error = ref('')

async function load() { list.value = await subjects.list() }
function angelegt() { anlegen.value = false; load() }
async function rename(subject) {
  const next = prompt('Neuer Name des Fachs', subject.name)
  if (next === null || !next.trim() || next.trim() === subject.name) return
  error.value = ''
  try { await subjects.rename(subject.id, next); await load() }
  catch (e) { error.value = e.message }
}
async function remove(subject) {
  if (!confirm(`Fach „${subject.name}“ mit Karteikarten, Lesenachweis und Register löschen?`)) return
  await subjects.remove(subject.id)
  await load()
}
onMounted(load)
</script>

<template>
  <div class="flex flex-wrap items-baseline justify-between gap-4">
    <div>
      <h1 class="text-3xl font-semibold tracking-tight">Fächer</h1>
      <p class="mt-1 opacity-70">Jedes Fach hat Karteikarten, Lesenachweis und Register.</p>
    </div>
    <button v-if="!anlegen" class="btn btn-primary" @click="anlegen = true">+ Neues Fach</button>
  </div>

  <section v-if="anlegen" class="panel mt-6 p-4">
    <SubjectCreateForm @created="angelegt" @cancel="anlegen = false" />
  </section>
  <p v-if="error" class="mt-2 text-sm text-error">{{ error }}</p>

  <ul v-if="list.length" class="mt-6 grid gap-4 sm:grid-cols-2">
    <li v-for="s in list" :key="s.id" class="panel flex flex-col p-5">
      <div class="flex items-start justify-between gap-2">
        <button class="text-left text-xl font-semibold hover:text-primary" @click="$emit('open-subject', s.id)">
          {{ s.name }}
        </button>
        <button class="btn btn-ghost !p-2" aria-label="Fach umbenennen" @click="rename(s)">
          <AppIcon name="stift" class="h-4 w-4" />
        </button>
      </div>
      <p v-if="s.se != null" class="mt-1 text-sm opacity-70">{{ s.se }} SE · {{ (s.se * 1.5).toFixed(1) }} Credits</p>
      <div class="mt-5 flex gap-2">
        <button class="btn btn-outline" @click="$emit('open-subject', s.id)">Öffnen</button>
        <button class="btn btn-danger ml-auto" @click="remove(s)">Löschen</button>
      </div>
    </li>
  </ul>
  <EmptyState v-else class="mt-6" title="Noch kein Fach" text="Lege oben dein erstes Fach an." />
</template>
