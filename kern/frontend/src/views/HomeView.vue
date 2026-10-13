<script setup>
import { computed, inject, onMounted, ref } from 'vue'
import StatCard from '../components/ui/StatCard.vue'
import EmptyState from '../components/ui/EmptyState.vue'
import { BAR_CLASSES, NATIVE_SERVICES, READING_STATUS, TONE_CLASSES, formatDate, num } from '../domain/status'

const emit = defineEmits(['open-subject', 'study', 'nav'])
const subjects = inject('subjects')

const overview = ref(null)
const error = ref('')
const syncing = ref(false)

async function load() {
  try { overview.value = await subjects.overview(); error.value = '' }
  catch (e) { error.value = e.message }
}
async function sync() {
  syncing.value = true
  try { await subjects.sync() } catch (e) { error.value = e.message }
  syncing.value = false
  await load()
}

const rows = computed(() => overview.value?.subjects ?? [])
const services = computed(() => overview.value?.services ?? [])
const offline = computed(() => services.value.filter((s) => !s.online))
// Dienste ohne eigene Kachel hier: sie zeigen ihre Kennzahlen aus dem Manifest
const extras = computed(() => services.value.filter((x) => !NATIVE_SERVICES.includes(x.name) && x.fields.length))
const sum = (pick) => rows.value.reduce((n, s) => n + (pick(s.status) ?? 0), 0)
const cardCount = computed(() => sum((s) => s.karteikarten?.card_count))
const dueCount = computed(() => sum((s) => s.karteikarten?.due_count))
const entryCount = computed(() => sum((s) => s.register?.entries))
const readingStatus = (r) => (r ? READING_STATUS[r.status] : null)

onMounted(load)
</script>

<template>
  <section class="flex flex-wrap items-end justify-between gap-4">
    <div>
      <h1 class="text-3xl font-semibold tracking-tight">Dein Überblick</h1>
      <p class="mt-1 text-slate-500 dark:text-slate-400">Status aller Fächer an einem Ort.</p>
    </div>
    <button class="btn btn-primary" :disabled="!dueCount" @click="$emit('study')">
      {{ dueCount ? `${dueCount} fällige Karten lernen` : 'Nichts fällig' }}
    </button>
  </section>

  <p v-if="error" class="mt-4 text-sm text-rose-600 dark:text-rose-400">{{ error }}</p>

  <section class="mt-6 grid grid-cols-2 gap-3 sm:grid-cols-4" aria-label="Zahlen">
    <StatCard label="Fächer" :value="rows.length" />
    <StatCard label="Karten" :value="cardCount" tone="violet" />
    <StatCard label="Heute fällig" :value="dueCount" tone="amber" />
    <StatCard label="Register-Einträge" :value="entryCount" tone="teal" />
  </section>

  <section class="mt-10">
    <h2 class="mb-3 text-lg font-semibold">Fächer</h2>
    <ul v-if="rows.length" class="grid gap-4">
      <li v-for="s in rows" :key="s.id" class="panel p-5">
        <div class="flex flex-wrap items-baseline justify-between gap-x-4">
          <button class="text-left text-xl font-semibold hover:text-teal-600 dark:hover:text-teal-400"
            @click="$emit('open-subject', s.id, 'karteikarten')">{{ s.name }}</button>
          <span v-if="s.progress != null" class="text-sm text-slate-500 dark:text-slate-400">
            Gesamtfortschritt
            <span class="text-lg font-semibold tabular-nums text-slate-900 dark:text-slate-100">{{ s.progress }} %</span>
          </span>
        </div>
        <div v-if="s.progress != null" class="mt-2 h-2 overflow-hidden rounded-full bg-slate-200 dark:bg-slate-800"
          role="progressbar" :aria-valuenow="s.progress" aria-valuemin="0" aria-valuemax="100">
          <div class="h-full rounded-full bg-teal-500" :style="{ width: s.progress + '%' }"></div>
        </div>

        <div class="mt-4 grid gap-4 sm:grid-cols-4">
          <div>
            <div class="text-xs font-medium uppercase tracking-wide text-slate-500 dark:text-slate-400">Aufgaben</div>
            <button class="mt-1 text-left text-sm hover:underline" @click="$emit('open-subject', s.id, 'aufgaben')">
              <template v-if="s.status.aufgaben.count">
                <span class="text-lg font-semibold tabular-nums">{{ s.status.aufgaben.done }}</span> von {{ s.status.aufgaben.count }} erledigt
              </template>
              <span v-else class="text-slate-500 dark:text-slate-400">noch keine Aufgabe</span>
            </button>
          </div>

          <div>
            <div class="text-xs font-medium uppercase tracking-wide text-slate-500 dark:text-slate-400">Karteikarten</div>
            <button v-if="s.status.karteikarten" class="mt-1 text-left text-sm hover:underline"
              @click="$emit('open-subject', s.id, 'karteikarten')">
              <span class="text-lg font-semibold tabular-nums">{{ s.status.karteikarten.due_count }}</span> fällig
              <span class="text-slate-500 dark:text-slate-400">von {{ s.status.karteikarten.card_count }}</span>
            </button>
            <p v-else class="mt-1 text-sm text-slate-400">nicht erreichbar</p>
          </div>

          <div>
            <div class="text-xs font-medium uppercase tracking-wide text-slate-500 dark:text-slate-400">Lesenachweis</div>
            <template v-if="s.status.lesenachweis">
              <button v-if="s.status.lesenachweis.task_count" class="mt-1 block w-full text-left text-sm"
                @click="$emit('open-subject', s.id, 'lesenachweis')">
                <span class="text-lg font-semibold tabular-nums">{{ num(s.status.lesenachweis.percent) }} %</span> gelesen
                <span class="ml-1 rounded-full px-2 py-0.5 text-xs" :class="TONE_CLASSES[readingStatus(s.status.lesenachweis).tone]">
                  {{ readingStatus(s.status.lesenachweis).label }}
                </span>
                <span class="mt-2 block h-1.5 overflow-hidden rounded-full bg-slate-200 dark:bg-slate-800" aria-hidden="true">
                  <span class="block h-full rounded-full" :class="BAR_CLASSES[readingStatus(s.status.lesenachweis).tone]"
                    :style="{ width: s.status.lesenachweis.percent + '%' }"></span>
                </span>
                <span v-if="s.status.lesenachweis.next_deadline" class="mt-1 block text-xs text-slate-500 dark:text-slate-400">
                  nächste Frist {{ formatDate(s.status.lesenachweis.next_deadline) }}
                </span>
              </button>
              <p v-else class="mt-1 text-sm text-slate-400">noch kein Pensum</p>
            </template>
            <p v-else class="mt-1 text-sm text-slate-400">nicht erreichbar</p>
          </div>

          <div>
            <div class="text-xs font-medium uppercase tracking-wide text-slate-500 dark:text-slate-400">Register</div>
            <button v-if="s.status.register" class="mt-1 text-left text-sm hover:underline"
              @click="$emit('open-subject', s.id, 'register')">
              <span class="text-lg font-semibold tabular-nums">{{ s.status.register.entries }}</span> Einträge
              <span class="text-slate-500 dark:text-slate-400">in {{ s.status.register.registers }} {{ s.status.register.registers === 1 ? 'Register' : 'Registern' }}</span>
            </button>
            <p v-else class="mt-1 text-sm text-slate-400">nicht erreichbar</p>
          </div>

          <div v-for="x in extras" :key="x.name">
            <div class="text-xs font-medium uppercase tracking-wide text-slate-500 dark:text-slate-400">{{ x.label }}</div>
            <component :is="x.panel ? 'button' : 'p'" v-if="s.status[x.name]" class="mt-1 text-left text-sm"
              :class="x.panel ? 'hover:underline' : ''" @click="x.panel && $emit('open-subject', s.id, x.name)">
              <template v-for="f in x.fields" :key="f.key">
                <span class="text-lg font-semibold tabular-nums">{{ s.status[x.name][f.key] }}</span> {{ f.label }}{{ ' ' }}
              </template>
            </component>
            <p v-else class="mt-1 text-sm text-slate-400">nicht erreichbar</p>
          </div>
        </div>
      </li>
    </ul>
    <EmptyState v-else title="Noch kein Fach" text="Lege ein Fach an. Karteikarten, Lesenachweis und Register gehören dann dazu.">
      <button class="btn btn-primary" @click="$emit('nav', 'subjects')">Erstes Fach anlegen</button>
    </EmptyState>
  </section>

  <section class="mt-10" aria-label="Dienste">
    <h2 class="mb-3 text-lg font-semibold">Dienste</h2>
    <div class="panel flex flex-wrap items-center gap-x-5 gap-y-2 p-4 text-sm">
      <span v-for="s in services" :key="s.name" class="flex items-center gap-2">
        <span class="h-2.5 w-2.5 rounded-full" :class="s.online ? 'bg-teal-500' : 'bg-rose-500'" aria-hidden="true"></span>
        {{ s.label }}
        <span class="sr-only">{{ s.online ? 'erreichbar' : 'nicht erreichbar' }}</span>
      </span>
      <span v-if="!services.length" class="text-slate-500 dark:text-slate-400">Keine Dienste eingetragen.</span>
      <button class="btn btn-outline ml-auto !py-1.5" :disabled="syncing" @click="sync">
        {{ syncing ? 'Gleiche ab …' : 'Dienste abgleichen' }}
      </button>
    </div>
    <p v-if="offline.length" class="mt-2 text-sm text-amber-700 dark:text-amber-300">
      Nicht erreichbar: {{ offline.map((s) => s.label).join(', ') }}.
      Sobald der Dienst läuft, übernimmt „Dienste abgleichen“ alle Fächer.
    </p>
  </section>
</template>
