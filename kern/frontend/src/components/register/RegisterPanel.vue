<script setup>
import { computed, inject, onMounted, ref, watch } from 'vue'
import EmptyState from '../ui/EmptyState.vue'

const props = defineProps({ subjectId: String })
const register = inject('register')

const entries = ref([])
const passages = ref([])
const kind = ref('') // '' = alle | 'person' | 'place'
const view = ref('name') // 'name' | 'bibel' | 'stellen'
const error = ref('')
const loadError = ref('')
const blank = () => ({ kind: 'person', name: '', refs: '' })
const form = ref(blank())

const KIND_LABEL = { person: 'Name', place: 'Ort' }

async function load() {
  try {
    if (view.value === 'stellen') passages.value = await register.passages(props.subjectId, kind.value)
    else entries.value = await register.list(props.subjectId, { kind: kind.value, sort: view.value })
    loadError.value = ''
  } catch (e) { loadError.value = e.message }
}
async function add() {
  error.value = ''
  try {
    await register.add(props.subjectId, form.value)
    form.value = { ...blank(), kind: form.value.kind }
    await load()
  } catch (e) { error.value = e.message }
}
async function remove(entry) {
  if (!confirm(`„${entry.name}“ aus dem Register löschen?`)) return
  await register.remove(entry.id)
  await load()
}
const exportUrl = (format) => register.exportUrl(props.subjectId, { kind: kind.value, sort: view.value, format })
const empty = computed(() => (view.value === 'stellen' ? !passages.value.length : !entries.value.length))

watch([kind, view], load)
onMounted(load)
</script>

<template>
  <h2 class="mb-3 text-lg font-semibold">Neuer Eintrag</h2>
  <form class="panel grid gap-3 p-4 sm:grid-cols-6" @submit.prevent="add">
    <select v-model="form.kind" class="input sm:col-span-1" aria-label="Art">
      <option value="person">Name</option>
      <option value="place">Ort</option>
    </select>
    <input v-model="form.name" class="input sm:col-span-5" placeholder="z. B. Abraham oder Bethlehem" aria-label="Name oder Ort" />
    <label class="text-sm sm:col-span-6">
      <span class="mb-1 block text-slate-500 dark:text-slate-400">
        Bibelstellen, mit Semikolon oder Zeilenumbruch getrennt. Kurz oder ausgeschrieben, z. B. 1Mo 12,1-3; Hebr 11,8; Mt 5-7
      </span>
      <textarea v-model="form.refs" rows="2" class="input" aria-label="Bibelstellen"></textarea>
    </label>
    <div class="sm:col-span-6">
      <button class="btn btn-primary">Eintragen</button>
      <span v-if="error" class="ml-3 text-sm text-rose-600 dark:text-rose-400">{{ error }}</span>
    </div>
  </form>

  <div class="mb-4 mt-10 flex flex-wrap items-center gap-2">
    <h2 class="mr-auto text-lg font-semibold">Register</h2>
    <select v-model="kind" class="input !w-auto" aria-label="Art filtern">
      <option value="">Namen und Orte</option>
      <option value="person">Nur Namen</option>
      <option value="place">Nur Orte</option>
    </select>
    <select v-model="view" class="input !w-auto" aria-label="Sortierung">
      <option value="name">Alphabetisch</option>
      <option value="bibel">Nach Bibelreihenfolge</option>
      <option value="stellen">Nach Bibelstelle</option>
    </select>
    <template v-if="!empty">
      <a class="btn btn-outline !py-2" :href="exportUrl('csv')" :download="`register-${view}.csv`">Export CSV</a>
      <a class="btn btn-outline !py-2" :href="exportUrl('txt')" :download="`register-${view}.txt`">Export Text</a>
    </template>
  </div>

  <p v-if="loadError" class="text-sm text-rose-600 dark:text-rose-400">{{ loadError }}</p>
  <EmptyState v-else-if="empty" title="Noch keine Einträge" text="Trage oben einen Namen oder Ort mit seinen Bibelstellen ein." />

  <ul v-else-if="view !== 'stellen'" class="grid gap-3 md:grid-cols-2">
    <li v-for="e in entries" :key="e.id" class="panel p-4">
      <div class="flex items-start justify-between gap-2">
        <div>
          <span class="font-semibold">{{ e.name }}</span>
          <span class="ml-2 rounded-full bg-slate-100 px-2 py-0.5 text-xs text-slate-600 dark:bg-slate-800 dark:text-slate-300">
            {{ KIND_LABEL[e.kind] }}
          </span>
        </div>
        <button class="btn btn-danger !px-2.5 !py-1" :aria-label="`${e.name} löschen`" @click="remove(e)">Löschen</button>
      </div>
      <div class="mt-3 flex flex-wrap gap-1.5">
        <span v-for="r in e.refs" :key="r.text" :title="r.book_name"
          class="rounded-lg bg-teal-50 px-2 py-0.5 text-sm tabular-nums text-teal-800 dark:bg-teal-500/10 dark:text-teal-300">
          {{ r.text }}
        </span>
      </div>
    </li>
  </ul>

  <ul v-else class="panel divide-y divide-slate-200 dark:divide-slate-800">
    <li v-for="p in passages" :key="p.text" class="flex flex-wrap items-baseline gap-x-4 gap-y-1 px-4 py-3">
      <span class="w-32 shrink-0 font-medium tabular-nums" :title="p.book_name">{{ p.text }}</span>
      <span class="flex flex-wrap gap-x-3 gap-y-1 text-sm">
        <span v-for="e in p.entries" :key="e.id">
          {{ e.name }}<span class="ml-1 text-xs text-slate-500 dark:text-slate-400">({{ KIND_LABEL[e.kind] }})</span>
        </span>
      </span>
    </li>
  </ul>
</template>
