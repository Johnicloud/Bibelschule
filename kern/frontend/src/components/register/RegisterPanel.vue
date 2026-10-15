<script setup>
import { computed, inject, nextTick, onMounted, ref, watch } from 'vue'
import RegisterTabs from './RegisterTabs.vue'
import EmptyState from '../ui/EmptyState.vue'
import { zielBibelstelle } from '../../state/bibelNavigation'

const props = defineProps({ subjectId: String })
const emit = defineEmits(['changed'])
const register = inject('register')

const registers = ref([])
const selectedId = ref('')
const entries = ref([])
const passages = ref([])
const view = ref('name') // 'name' | 'bibel' | 'stellen'
const loaded = ref(false)
const loadError = ref('')
const createError = ref('')
const error = ref('')
const form = ref({ name: '', refs: '' })
const nameInput = ref(null)
const renaming = ref(false)
const renameValue = ref('')
const vorhandeneNamen = ref(new Set())

const storeKey = computed(() => `bibelschule.register.${props.subjectId}`)
const current = computed(() => registers.value.find((r) => r.id === selectedId.value) || null)
const empty = computed(() => (view.value === 'stellen' ? !passages.value.length : !entries.value.length))
const focusName = () => nextTick(() => nameInput.value?.focus())
// Name im Register ist eindeutig (Groß/Klein egal) – bei Eingabe sofort zeigen, ob es ihn schon gibt
// (dann ergänzt das Eintragen nur die Stellen), verschwindet sobald die Eingabe nicht mehr passt.
const nameExistiertSchon = computed(() => vorhandeneNamen.value.has(form.value.name.trim().toLowerCase()))

async function ladenNamen() {
  if (!current.value) { vorhandeneNamen.value = new Set(); return }
  try { vorhandeneNamen.value = new Set((await register.entries(selectedId.value, 'name')).map((e) => e.name.toLowerCase())) }
  catch { /* Hinweis bleibt dann einfach aus */ }
}

// Das zuletzt benutzte Register des Fachs merkt sich der Browser.
function remember(id) { try { localStorage.setItem(storeKey.value, id) } catch { /* Speicher gesperrt */ } }
function recall() { try { return localStorage.getItem(storeKey.value) || '' } catch { return '' } }

async function loadRegisters(preferId = '') {
  try {
    registers.value = await register.registers(props.subjectId)
    loadError.value = ''
    const wanted = preferId || selectedId.value || recall()
    selectedId.value = registers.value.some((r) => r.id === wanted) ? wanted : registers.value[0]?.id || ''
  } catch (e) { loadError.value = e.message }
  loaded.value = true
}
async function loadEntries() {
  if (!current.value) { entries.value = []; passages.value = []; return }
  try {
    if (view.value === 'stellen') passages.value = await register.passages(selectedId.value)
    else entries.value = await register.entries(selectedId.value, view.value)
    loadError.value = ''
  } catch (e) { loadError.value = e.message }
}

async function createRegister(name) {
  createError.value = ''
  try {
    const r = await register.create(props.subjectId, name)
    await loadRegisters(r.id)
    emit('changed')
    focusName()
    return true
  } catch (e) { createError.value = e.message; return false }
}
function startRename() { renameValue.value = current.value.name; renaming.value = true; error.value = '' }
async function saveRename() {
  error.value = ''
  try {
    await register.rename(selectedId.value, renameValue.value)
    renaming.value = false
    await loadRegisters(selectedId.value)
  } catch (e) { error.value = e.message }
}
async function removeRegister() {
  const r = current.value
  const note = r.entry_count ? ` mit ${r.entry_count} ${r.entry_count === 1 ? 'Eintrag' : 'Einträgen'}` : ''
  if (!confirm(`Register „${r.name}“${note} löschen?`)) return
  await register.remove(r.id)
  selectedId.value = ''
  await loadRegisters()
  emit('changed')
}

async function add() {
  error.value = ''
  try {
    await register.add(selectedId.value, form.value)
    form.value = { name: '', refs: '' }
    await Promise.all([loadRegisters(selectedId.value), loadEntries(), ladenNamen()]) // auch die Zahlen auf den Reitern
    emit('changed')
    focusName() // gleich der nächste Eintrag
  } catch (e) { error.value = e.message }
}
async function removeEntry(entry) {
  if (!confirm(`„${entry.name}“ aus dem Register löschen?`)) return
  await register.removeEntry(entry.id)
  await Promise.all([loadRegisters(selectedId.value), loadEntries(), ladenNamen()])
  emit('changed')
}
function inBibelOeffnen(text) {
  zielBibelstelle.value = text
}

const exportError = ref('')
async function exportieren(format) {
  exportError.value = ''
  try {
    await register.exportieren(selectedId.value, { sort: view.value, format }, `${current.value.name}-${view.value}.${format}`)
  } catch (e) { exportError.value = e.message }
}

watch(selectedId, (id) => { if (id) remember(id); renaming.value = false; error.value = ''; loadEntries(); ladenNamen() })
watch(view, loadEntries)
onMounted(() => loadRegisters())
</script>

<template>
  <p v-if="loadError && !registers.length" class="text-sm text-rose-600 dark:text-rose-400">{{ loadError }}</p>
  <template v-else-if="loaded">
    <RegisterTabs v-model="selectedId" :registers="registers" :creator="createRegister" :error="createError" />

    <EmptyState v-if="!current" class="mt-6" title="Noch kein Register"
      text="Lege ein Register an, zum Beispiel Namen oder Orte. Du kannst beliebig viele anlegen.">
      <div class="flex flex-wrap justify-center gap-2">
        <button class="btn btn-primary" @click="createRegister('Namen')">Namen anlegen</button>
        <button class="btn btn-outline" @click="createRegister('Orte')">Orte anlegen</button>
      </div>
    </EmptyState>

    <template v-else>
      <div class="mt-6 flex flex-wrap items-center gap-2">
        <template v-if="!renaming">
          <h2 class="mr-auto text-lg font-semibold">{{ current.name }}</h2>
          <button class="btn btn-ghost !py-1.5" @click="startRename">Umbenennen</button>
          <button class="btn btn-danger !py-1.5" @click="removeRegister">Register löschen</button>
        </template>
        <form v-else class="flex w-full items-center gap-2" @submit.prevent="saveRename">
          <input v-model="renameValue" class="input" aria-label="Neuer Name des Registers" @keydown.esc="renaming = false" />
          <button class="btn btn-primary">Speichern</button>
          <button type="button" class="btn btn-ghost" @click="renaming = false">Abbrechen</button>
        </form>
      </div>

      <form class="panel mt-3 grid gap-3 p-4 sm:grid-cols-[1fr_2fr_auto] sm:items-start" @submit.prevent="add">
        <div>
          <input ref="nameInput" v-model="form.name" class="input" placeholder="Name oder Begriff" aria-label="Name oder Begriff" />
          <p v-if="nameExistiertSchon" class="mt-1 text-xs text-amber-700 dark:text-amber-300">Gibt es schon – Stellen werden ergänzt.</p>
        </div>
        <input v-model="form.refs" class="input" placeholder="Bibelstellen, z. B. 1Mo 12,1-3; Hebr 11,8" aria-label="Bibelstellen" />
        <button class="btn btn-primary">Eintragen</button>
        <p class="text-xs text-slate-500 dark:text-slate-400 sm:col-span-3">
          Mehrere Stellen mit Semikolon trennen, kurz oder ausgeschrieben (Apg 8,26-40 oder Apostelgeschichte 8,26-40).
          Gibt es den Namen in diesem Register schon, kommen die Stellen dazu.
        </p>
        <p v-if="error" class="text-sm text-rose-600 dark:text-rose-400 sm:col-span-3">{{ error }}</p>
      </form>

      <div class="mb-4 mt-8 flex flex-wrap items-center gap-2">
        <span class="mr-auto text-sm text-slate-500 dark:text-slate-400">{{ current.entry_count }} {{ current.entry_count === 1 ? 'Eintrag' : 'Einträge' }}</span>
        <select v-model="view" class="input !w-auto" aria-label="Sortierung">
          <option value="name">Alphabetisch</option>
          <option value="bibel">Nach Bibelreihenfolge</option>
          <option value="stellen">Nach Bibelstelle</option>
        </select>
        <template v-if="!empty">
          <button type="button" class="btn btn-outline !py-2" @click="exportieren('csv')">Export CSV</button>
          <button type="button" class="btn btn-outline !py-2" @click="exportieren('txt')">Export Text</button>
        </template>
      </div>
      <p v-if="exportError" class="mb-4 text-sm text-rose-600 dark:text-rose-400">{{ exportError }}</p>

      <p v-if="loadError" class="text-sm text-rose-600 dark:text-rose-400">{{ loadError }}</p>
      <EmptyState v-else-if="empty" title="Noch keine Einträge in diesem Register"
        text="Trage oben einen Namen mit seinen Bibelstellen ein." />

      <ul v-else-if="view !== 'stellen'" class="grid gap-3 md:grid-cols-2">
        <li v-for="e in entries" :key="e.id" class="panel p-4">
          <div class="flex items-start justify-between gap-2">
            <span class="font-semibold">{{ e.name }}</span>
            <button class="btn btn-danger !px-2.5 !py-1" :aria-label="`${e.name} löschen`" @click="removeEntry(e)">Löschen</button>
          </div>
          <div class="mt-3 flex flex-wrap gap-1.5">
            <button v-for="r in e.refs" :key="r.text" type="button" :title="`${r.book_name} – in der Bibel öffnen`"
              class="rounded-lg bg-teal-50 px-2 py-0.5 text-sm tabular-nums text-teal-800 transition hover:bg-teal-100 dark:bg-teal-500/10 dark:text-teal-300 dark:hover:bg-teal-500/20"
              @click="inBibelOeffnen(r.text)">
              {{ r.text }}
            </button>
          </div>
        </li>
      </ul>

      <ul v-else class="panel divide-y divide-slate-200 dark:divide-slate-800">
        <li v-for="p in passages" :key="p.text" class="flex flex-wrap items-baseline gap-x-4 gap-y-1 px-4 py-3">
          <button type="button" class="w-32 shrink-0 text-left font-medium tabular-nums text-primary hover:underline"
            :title="`${p.book_name} – in der Bibel öffnen`" @click="inBibelOeffnen(p.text)">{{ p.text }}</button>
          <span class="flex flex-wrap gap-x-3 gap-y-1 text-sm">
            <span v-for="e in p.entries" :key="e.id">{{ e.name }}</span>
          </span>
        </li>
      </ul>
    </template>
  </template>
</template>
