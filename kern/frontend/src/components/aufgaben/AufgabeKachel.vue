<script setup>
import { computed, ref } from 'vue'
import AppIcon from '../ui/AppIcon.vue'
import MenuButton from '../ui/MenuButton.vue'
import { artInfo, formatDate, tageBisText } from '../../domain/status'

// Eine Aufgabe als ruhige Kachel: oben Haken, Titel und Menü, darunter eine Zeile mit Angaben (Art, Termin, Gewichtung),
// ein Fortschrittsbalken und die Verknüpfungen (Lesepensum, Karteikarten-Set, Skript, Formular) als kleine Marken.
// Seltenes steht im Menü (Bearbeiten, Verknüpfen, Löschen), nicht dauernd auf der Kachel.
const props = defineProps({
  aufgabe: { type: Object, required: true },
  pensen: { type: Array, default: () => [] },       // Lesepensen des Fachs
  setStaende: { type: Object, default: () => ({}) }, // Set-Name -> { card_count, mastered_count }
  dateien: { type: Array, default: () => [] },      // Dateien im Reiter „Skripte“
})
const emit = defineEmits(['toggle', 'edit', 'remove', 'pensum', 'set', 'skript', 'formular', 'export'])

const a = computed(() => props.aufgabe)
const info = computed(() => artInfo(a.value.art))
const pensum = computed(() => props.pensen.find((p) => p.id === a.value.pensum_id) || null)
const setStand = computed(() => (a.value.set_name ? props.setStaende[a.value.set_name] || null : null))
const dateiName = (id) => props.dateien.find((d) => d.id === id)?.dateiname || 'Datei'
const dateiLink = (id) => `/api/skripte/skripte/${id}/datei`
const formularId = computed(() => (a.value.formular || '').startsWith('skript:') ? a.value.formular.slice(7) : '')

// Fortschritt aus der Quelle, die zur Aufgabe gehört: Lesen, Karten oder Umfang (Ist gegen Soll)
const fortschritt = computed(() => {
  if (pensum.value) {
    const f = pensum.value.forecast
    return { prozent: Math.round(f.percent), text: `${f.done} von ${f.target} ${pensum.value.unit} gelesen` }
  }
  if (a.value.set_name) {
    const s = setStand.value
    const prozent = s && s.card_count ? Math.round((100 * s.mastered_count) / s.card_count) : 0
    return { prozent, text: s ? `${s.mastered_count} von ${s.card_count} Karten sicher gelernt` : 'Noch keine Karten im Set' }
  }
  if (info.value.umfang && a.value.soll) return { prozent: a.value.fortschritt, text: `${a.value.ist ?? 0} von ${a.value.soll} ${a.value.einheit}`.trim() }
  return null
})

const verknuepfenOffen = ref(false)
const menue = computed(() => [
  { label: 'Bearbeiten', icon: 'stift', action: () => emit('edit') },
  { label: 'Verknüpfungen', icon: 'verknuepfen', action: () => { verknuepfenOffen.value = !verknuepfenOffen.value } },
  { label: 'Löschen', icon: 'papierkorb', danger: true, action: () => emit('remove') },
])
const sets = computed(() => Object.keys(props.setStaende))
</script>

<template>
  <li class="panel !gap-0 !p-4">
    <div class="flex items-start gap-3">
      <button type="button" class="mt-0.5 grid h-8 w-8 shrink-0 place-items-center rounded-full border transition"
        :class="a.erledigt ? 'border-transparent bg-primary text-white' : 'border-highlight opacity-50 hover:opacity-80'"
        :aria-pressed="a.erledigt" :aria-label="`${a.titel} ${a.erledigt ? 'als offen markieren' : 'als erledigt markieren'}`" @click="emit('toggle')">
        <AppIcon name="haken" class="h-4 w-4" />
      </button>

      <div class="min-w-0 flex-1">
        <p class="break-words font-medium leading-snug" :class="a.erledigt ? 'opacity-50 line-through' : ''">{{ a.titel }}</p>
        <p class="mt-1 flex flex-wrap items-center gap-x-3 gap-y-1 text-sm opacity-70">
          <span v-if="a.art !== 'allgemein'" class="inline-flex items-center gap-1"><AppIcon :name="info.icon" class="h-4 w-4" />{{ info.label }}</span>
          <span v-if="a.frist">{{ info.frist }} {{ formatDate(a.frist) }}<template v-if="!a.erledigt"> · {{ tageBisText(a.frist) }}</template></span>
          <span v-if="a.gewichtung != null">{{ a.gewichtung }} % der Bewertung</span>
          <span v-if="!a.zaehlt" title="Zählt nicht zum Gesamtfortschritt">nur zum Lernen</span>
        </p>
      </div>

      <MenuButton :items="menue" :label="`Weitere Aktionen für ${a.titel}`" />
    </div>

    <div v-if="fortschritt && !a.erledigt" class="mt-3 pl-11">
      <div class="h-1.5 overflow-hidden rounded-full bg-highlight"><div class="h-full rounded-full bg-primary transition-all" :style="{ width: fortschritt.prozent + '%' }"></div></div>
      <p class="mt-1 text-xs opacity-70">{{ fortschritt.text }} · {{ fortschritt.prozent }} %</p>
    </div>

    <p v-if="a.notiz" class="mt-2 pl-11 text-sm opacity-70">{{ a.notiz }}</p>

    <!-- Verknüpfungen als Marken: nur das, was wirklich verknüpft ist -->
    <div v-if="pensum || a.set_name || formularId || a.formular === 'standard' || a.formular === 'angefragt' || pensum?.skript_id" class="mt-3 flex flex-wrap items-center gap-2 pl-11 text-xs">
      <span v-if="pensum" class="inline-flex items-center gap-1 rounded-full bg-backdrop px-2.5 py-1"><AppIcon name="lesenachweis" class="h-3.5 w-3.5" />{{ pensum.title }}</span>
      <a v-if="pensum?.skript_id" :href="dateiLink(pensum.skript_id)" target="_blank" rel="noopener" class="inline-flex items-center gap-1 rounded-full bg-backdrop px-2.5 py-1 hover:bg-highlight">
        <AppIcon name="skripte" class="h-3.5 w-3.5" />Skript: {{ dateiName(pensum.skript_id) }}
      </a>
      <span v-if="a.set_name" class="inline-flex items-center gap-1 rounded-full bg-backdrop px-2.5 py-1"><AppIcon name="karten" class="h-3.5 w-3.5" />Set: {{ a.set_name }}</span>
      <button v-if="a.formular === 'standard'" type="button" class="inline-flex items-center gap-1 rounded-full bg-primary px-2.5 py-1 text-white" @click="emit('export')">
        <AppIcon name="skripte" class="h-3.5 w-3.5" />Formular als PDF
      </button>
      <span v-else-if="a.formular === 'angefragt'" class="rounded-full bg-amber-100 px-2.5 py-1 text-amber-800 dark:bg-amber-500/15 dark:text-amber-300">Formular angefragt</span>
      <a v-else-if="formularId" :href="dateiLink(formularId)" target="_blank" rel="noopener" class="inline-flex items-center gap-1 rounded-full bg-backdrop px-2.5 py-1 hover:bg-highlight">
        <AppIcon name="skripte" class="h-3.5 w-3.5" />Formular: {{ dateiName(formularId) }}
      </a>
    </div>

    <!-- Verknüpfungen ändern (Menü „Verknüpfungen“) -->
    <div v-if="verknuepfenOffen" class="mt-3 grid gap-2 rounded-xl bg-backdrop p-3 text-sm sm:ml-11">
      <label v-if="pensen.length" class="grid items-center gap-1 sm:grid-cols-[9rem_1fr]">
        <span class="opacity-70">Lesepensum</span>
        <select class="input !py-1.5" :value="a.pensum_id || ''" @change="emit('pensum', $event.target.value)">
          <option value="">Keins verknüpft</option>
          <option v-for="p in pensen" :key="p.id" :value="p.id">{{ p.title }}</option>
        </select>
      </label>
      <label v-if="pensum && dateien.length" class="grid items-center gap-1 sm:grid-cols-[9rem_1fr]">
        <span class="opacity-70">Skript zum Pensum</span>
        <select class="input !py-1.5" :value="pensum.skript_id || ''" @change="emit('skript', pensum.id, $event.target.value)">
          <option value="">Keins hinterlegt</option>
          <option v-for="d in dateien" :key="d.id" :value="d.id">{{ d.dateiname }}</option>
        </select>
      </label>
      <label v-if="sets.length" class="grid items-center gap-1 sm:grid-cols-[9rem_1fr]">
        <span class="opacity-70">Karteikarten-Set</span>
        <select class="input !py-1.5" :value="a.set_name || ''" @change="emit('set', $event.target.value)">
          <option value="">Keins verknüpft</option>
          <option v-for="n in sets" :key="n" :value="n">{{ n }}</option>
        </select>
      </label>
      <template v-if="a.art === 'lesen_pflicht'">
        <label class="grid items-center gap-1 sm:grid-cols-[9rem_1fr]">
          <span class="opacity-70">Formular</span>
          <select class="input !py-1.5" :value="formularId ? 'skript' : a.formular" @change="emit('formular', $event.target.value === 'skript' ? '' : $event.target.value)">
            <option value="">Keins</option>
            <option value="standard">Standard-Formular (Lesenachweis Pflichtlektüre)</option>
            <option value="angefragt">Formular angefragt</option>
            <option v-if="formularId" value="skript">Verknüpfte Datei</option>
          </select>
        </label>
        <label v-if="dateien.length && a.formular !== 'standard'" class="grid items-center gap-1 sm:grid-cols-[9rem_1fr]">
          <span class="opacity-70">Erhaltenes Formular</span>
          <select class="input !py-1.5" :value="formularId" @change="emit('formular', $event.target.value ? 'skript:' + $event.target.value : 'angefragt')">
            <option value="">Datei wählen …</option>
            <option v-for="d in dateien" :key="d.id" :value="d.id">{{ d.dateiname }}</option>
          </select>
        </label>
      </template>
      <p v-if="!pensen.length && !sets.length && !dateien.length" class="opacity-70">Noch nichts zum Verknüpfen: lege ein Lesepensum, ein Karteikarten-Set oder eine Datei im Fach an.</p>
    </div>
  </li>
</template>
