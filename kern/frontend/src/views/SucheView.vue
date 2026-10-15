<script setup>
import { inject, onMounted, ref } from 'vue'
import AppIcon from '../components/ui/AppIcon.vue'
import { zielBibelstelle } from '../state/bibelNavigation'

// Globale Volltextsuche: fragt alle Dienste mit größeren Textbeständen parallel ab (Bibel, Skripte,
// Bibliothek) und zeigt die Treffer gruppiert – reine Frontend-Orchestrierung, die Dienste kennen sich
// gegenseitig nicht (siehe Projektnotizen, Entscheidungen zu getrennten Diensten).
const emit = defineEmits(['open-subject'])

const bibel = inject('bibel')
const skripte = inject('skripte')
const bibliothek = inject('bibliothek')
const subjects = inject('subjects')

const text = ref('')
const suchend = ref(false)
const fehler = ref('')
const bibelTreffer = ref(null)
const skripteTreffer = ref(null)
const bibliothekTreffer = ref(null)
const faecherName = ref({})

onMounted(async () => {
  try { faecherName.value = Object.fromEntries((await subjects.list()).map((s) => [s.id, s.name])) }
  catch { /* Namen sind nur eine Zugabe, die Suche funktioniert auch ohne */ }
})

async function suchen() {
  if (!text.value.trim()) return
  suchend.value = true
  fehler.value = ''
  bibelTreffer.value = skripteTreffer.value = bibliothekTreffer.value = null
  const [b, s, bi] = await Promise.allSettled([
    bibel.suche(text.value), skripte.suche(text.value), bibliothek.suche(text.value),
  ])
  if (b.status === 'fulfilled') bibelTreffer.value = b.value
  if (s.status === 'fulfilled') skripteTreffer.value = s.value
  if (bi.status === 'fulfilled') bibliothekTreffer.value = bi.value
  if (b.status === 'rejected' && s.status === 'rejected' && bi.status === 'rejected') {
    fehler.value = b.reason?.message || 'Die Suche ist fehlgeschlagen.'
  }
  suchend.value = false
}

function bibelOeffnen(treffer) {
  zielBibelstelle.value = `${treffer.name} ${treffer.kapitel},${treffer.vers}`
}

const keineTreffer = () =>
  [bibelTreffer.value, skripteTreffer.value, bibliothekTreffer.value].some((t) => t != null) &&
  [bibelTreffer.value, skripteTreffer.value, bibliothekTreffer.value].every((t) => t == null || t.length === 0)
</script>

<template>
  <h1 class="text-3xl font-semibold tracking-tight">Suche</h1>
  <p class="mt-1 text-slate-500 dark:text-slate-400">
    Durchsucht alles, wo bereits Text vorliegt: die Bibel (herausgelesene Verse), hochgeladene Skripte (PDF)
    und erkannte Bibliothek-Bücher.
  </p>

  <form class="mt-6 flex gap-2" @submit.prevent="suchen">
    <input v-model="text" type="text" class="input flex-1" placeholder="Wort oder Satzteil suchen …" autofocus />
    <button class="btn btn-primary" :disabled="suchend">{{ suchend ? 'Sucht …' : 'Suchen' }}</button>
  </form>
  <p v-if="fehler" class="mt-2 text-sm text-rose-600 dark:text-rose-400">{{ fehler }}</p>
  <p v-else-if="keineTreffer()" class="mt-2 text-sm text-slate-500 dark:text-slate-400">Keine Treffer.</p>

  <template v-if="bibelTreffer && bibelTreffer.length">
    <h2 class="mb-2 mt-8 flex items-center gap-2 text-lg font-semibold">
      <AppIcon name="buch" class="h-5 w-5" /> Bibel
    </h2>
    <ul class="grid gap-2">
      <li v-for="t in bibelTreffer" :key="t.id" class="panel p-3">
        <button class="text-left" @click="bibelOeffnen(t)">
          <span class="font-medium text-primary hover:underline">{{ t.name }} {{ t.kapitel }},{{ t.vers }}</span>
          <span class="ml-2 text-sm text-slate-600 dark:text-slate-300">{{ t.text }}</span>
        </button>
      </li>
    </ul>
  </template>

  <template v-if="skripteTreffer && skripteTreffer.length">
    <h2 class="mb-2 mt-8 flex items-center gap-2 text-lg font-semibold">
      <AppIcon name="skripte" class="h-5 w-5" /> Skripte
    </h2>
    <ul class="grid gap-2">
      <li v-for="t in skripteTreffer" :key="t.id" class="panel p-3">
        <a :href="skripte.dateiUrl(t.id)" target="_blank" class="block">
          <span class="font-medium text-primary hover:underline">{{ t.dateiname }}</span>
          <span v-if="faecherName[t.subject_id]" class="ml-2 text-xs text-slate-400">({{ faecherName[t.subject_id] }})</span>
          <p class="text-sm text-slate-600 dark:text-slate-300">{{ t.ausschnitt }}</p>
        </a>
      </li>
    </ul>
  </template>

  <template v-if="bibliothekTreffer && bibliothekTreffer.length">
    <h2 class="mb-2 mt-8 flex items-center gap-2 text-lg font-semibold">
      <AppIcon name="bibliothek" class="h-5 w-5" /> Bibliothek
    </h2>
    <ul class="grid gap-2">
      <li v-for="t in bibliothekTreffer" :key="t.id" class="panel p-3">
        <a :href="bibliothek.textDateiUrl(t.id)" target="_blank" class="block">
          <span class="font-medium text-primary hover:underline">{{ t.titel }}</span>
          <p class="text-sm text-slate-600 dark:text-slate-300">{{ t.ausschnitt }}</p>
        </a>
      </li>
    </ul>
  </template>
</template>
