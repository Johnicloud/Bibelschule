<script setup>
import { inject, onMounted, ref } from 'vue'
import EmptyState from '../components/ui/EmptyState.vue'

const adressbuch = inject('adressbuch')
const liste = ref([])
const loadError = ref('')
const blank = () => ({ name: '', email: '', telefon: '', adresse: '', notiz: '' })
const form = ref(blank())
const error = ref('')

async function load() {
  try { liste.value = await adressbuch.dozenten(); loadError.value = '' }
  catch (e) { loadError.value = e.message }
}
async function add() {
  error.value = ''
  try { await adressbuch.add(form.value); form.value = blank(); await load() }
  catch (e) { error.value = e.message }
}
async function remove(d) {
  if (!confirm(`„${d.name}“ aus dem Adressbuch löschen?`)) return
  await adressbuch.remove(d.id)
  await load()
}
onMounted(load)
</script>

<template>
  <h1 class="text-3xl font-semibold tracking-tight">Adressbuch</h1>
  <p class="mt-1 text-slate-500 dark:text-slate-400">Dozenten, unabhängig vom Fach. Zuordnung zu Fächern passiert im jeweiligen Fach.</p>

  <form class="panel mt-6 grid gap-3 p-4 sm:grid-cols-2" @submit.prevent="add">
    <input v-model="form.name" class="input sm:col-span-2" placeholder="Name" aria-label="Name" />
    <input v-model="form.email" type="email" class="input" placeholder="E-Mail" aria-label="E-Mail" />
    <input v-model="form.telefon" class="input" placeholder="Telefon" aria-label="Telefon" />
    <input v-model="form.adresse" class="input sm:col-span-2" placeholder="Adresse" aria-label="Adresse" />
    <div class="sm:col-span-2">
      <button class="btn btn-primary">Dozent anlegen</button>
      <span v-if="error" class="ml-3 text-sm text-rose-600 dark:text-rose-400">{{ error }}</span>
    </div>
  </form>

  <p v-if="loadError" class="mt-6 text-sm text-rose-600 dark:text-rose-400">{{ loadError }}</p>
  <ul v-else-if="liste.length" class="mt-6 grid gap-3 sm:grid-cols-2">
    <li v-for="d in liste" :key="d.id" class="panel p-4">
      <div class="flex items-start justify-between gap-2">
        <div>
          <p class="font-semibold">{{ d.name }}</p>
          <p v-if="d.email" class="text-sm text-slate-500 dark:text-slate-400">{{ d.email }}</p>
          <p v-if="d.telefon" class="text-sm text-slate-500 dark:text-slate-400">{{ d.telefon }}</p>
          <p v-if="d.adresse" class="text-sm text-slate-500 dark:text-slate-400">{{ d.adresse }}</p>
          <p class="mt-1 text-xs text-slate-400 dark:text-slate-500">
            {{ d.faecher.length }} {{ d.faecher.length === 1 ? 'Fach' : 'Fächer' }} zugeordnet
          </p>
        </div>
        <button class="btn btn-danger !px-2.5 !py-1" :aria-label="`${d.name} löschen`" @click="remove(d)">Löschen</button>
      </div>
    </li>
  </ul>
  <EmptyState v-else class="mt-6" title="Noch kein Dozent" text="Lege oben den ersten Dozenten an." />
</template>
