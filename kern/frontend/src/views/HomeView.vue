<script setup>
import { computed, inject, onMounted, ref } from 'vue'
import StatCard from '../components/ui/StatCard.vue'
import EmptyState from '../components/ui/EmptyState.vue'
import AppIcon from '../components/ui/AppIcon.vue'
import SubjectCreateForm from '../components/ui/SubjectCreateForm.vue'
import { FACH_STATUS, TONE_CLASSES } from '../domain/status'

defineEmits(['open-subject', 'study'])
const subjects = inject('subjects')

const overview = ref(null)
const error = ref('')
const anlegen = ref(false)

async function load() {
  try { overview.value = await subjects.overview(); error.value = '' }
  catch (e) { error.value = e.message }
}
function angelegt() { anlegen.value = false; load() }

const rows = computed(() => overview.value?.subjects ?? [])
const sum = (pick) => rows.value.reduce((n, s) => n + (pick(s.status) ?? 0), 0)
const cardCount = computed(() => sum((s) => s.karteikarten?.card_count))
const dueCount = computed(() => sum((s) => s.karteikarten?.due_count))
const entryCount = computed(() => sum((s) => s.register?.entries))

onMounted(load)
</script>

<template>
  <section class="flex flex-wrap items-end justify-between gap-4">
    <div>
      <h1 class="text-3xl font-semibold tracking-tight">Dein Überblick</h1>
      <p class="mt-1 opacity-70">Status aller Fächer an einem Ort.</p>
    </div>
    <button class="btn btn-primary" :disabled="!dueCount" @click="$emit('study')">
      {{ dueCount ? `${dueCount} fällige Karten lernen` : 'Nichts fällig' }}
    </button>
  </section>

  <p v-if="error" class="mt-4 text-sm text-error">{{ error }}</p>

  <section class="mt-6 grid grid-cols-2 gap-3 sm:grid-cols-4" aria-label="Zahlen">
    <StatCard label="Fächer" :value="rows.length" />
    <StatCard label="Karten" :value="cardCount" tone="violet" />
    <StatCard label="Heute fällig" :value="dueCount" tone="amber" />
    <StatCard label="Register-Einträge" :value="entryCount" tone="teal" />
  </section>

  <section class="mt-10">
    <div class="mb-3 flex items-center justify-between">
      <h2 class="text-lg font-semibold">Fächer</h2>
      <button v-if="!anlegen && rows.length" class="btn btn-outline !py-1.5" @click="anlegen = true">+ Neues Fach</button>
    </div>

    <section v-if="anlegen" class="panel mb-4 p-4">
      <SubjectCreateForm @created="angelegt" @cancel="anlegen = false" />
    </section>

    <ul v-if="rows.length" class="grid gap-4 sm:grid-cols-2">
      <li v-for="s in rows" :key="s.id" class="panel p-5">
        <div class="flex flex-wrap items-center justify-between gap-2">
          <button class="text-left text-xl font-semibold hover:text-primary"
            @click="$emit('open-subject', s.id, 'uebersicht')">{{ s.name }}</button>
          <span v-if="FACH_STATUS[s.stufe]" class="shrink-0 rounded-full px-2 py-0.5 text-xs font-medium" :class="TONE_CLASSES[FACH_STATUS[s.stufe].tone]">
            {{ FACH_STATUS[s.stufe].label }}
          </span>
        </div>
        <span v-if="s.progress != null" class="mt-1 block text-sm opacity-70">
          Gesamtfortschritt
          <span class="font-semibold tabular-nums text-theme-inv">{{ s.progress }} %</span>
        </span>
        <div v-if="s.progress != null" class="mt-2 h-2 overflow-hidden rounded-full bg-highlight"
          role="progressbar" :aria-valuenow="s.progress" aria-valuemin="0" aria-valuemax="100">
          <div class="h-full rounded-full bg-primary" :style="{ width: s.progress + '%' }"></div>
        </div>
      </li>
      <li v-if="!anlegen">
        <button class="panel flex h-full w-full flex-col items-center justify-center gap-2 p-5 text-sm font-medium opacity-70 hover:opacity-100"
          @click="anlegen = true">
          <AppIcon name="plus" class="h-6 w-6" />
          Neues Fach
        </button>
      </li>
    </ul>
    <EmptyState v-else-if="!anlegen" title="Noch kein Fach" text="Lege ein Fach an. Karteikarten, Lesenachweis und Register gehören dann dazu.">
      <button class="btn btn-primary" @click="anlegen = true">Erstes Fach anlegen</button>
    </EmptyState>
  </section>
</template>
