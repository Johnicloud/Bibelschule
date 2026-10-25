<script setup>
import { computed, inject, ref } from 'vue'
import AppIcon from '../ui/AppIcon.vue'
import { BAR_CLASSES, READING_STATUS, TONE_CLASSES, formatDate, num } from '../../domain/status'
import { gemeinde as profilGemeinde, nachname as profilNachname, vorname as profilVorname } from '../../state/auth'

const props = defineProps({ task: Object, subjectName: String })
const emit = defineEmits(['changed'])
const reading = inject('reading')
const pdfcreator = inject('pdfcreator')

const amount = ref('')
const day = ref('')
const dayInput = ref(null)
// Bewusst keine stille Vorauswahl des ersten Buches mehr: dadurch landeten Einträge unbemerkt beim falschen
// (nämlich dem per Zufall vorausgewählten) Buch, wenn das Dropdown nicht tatsächlich angefasst wurde.
const buchId = ref('')
// Durchgang: hier ist eine Vorauswahl unproblematisch (anders als beim Buch), weil der „aktive“ Durchgang aus
// echten Daten berechnet ist (der erste noch nicht abgeschlossene), nicht nur zufällig der erste in einer Liste.
const durchlauf = ref(props.task.durchlaeufe?.find((d) => d.aktiv)?.nummer || 1)
const error = ref('')
const today = new Date().toLocaleDateString('sv-SE') // YYYY-MM-DD in der Zeit des Geräts
function dayPickerOeffnen() { dayInput.value?.showPicker ? dayInput.value.showPicker() : dayInput.value?.click() }

const bearbeiten = ref(false)
const editForm = ref(null)
const editMehrereBuecher = ref(false)
const editBuecher = ref([])
const editError = ref('')
const speichert = ref(false)

const exportieren = ref(false)
// Vorbelegt aus dem eigenen Profil (Konto-Seite), bleibt aber änderbar – kein Pflichtfeld.
const exportName = ref([profilVorname.value, profilNachname.value].filter(Boolean).join(' '))
const exportGemeinde = ref(profilGemeinde.value)
const exportError = ref('')
const exportLaeuft = ref(false)

const f = computed(() => props.task.forecast)
const status = computed(() => READING_STATUS[f.value.status])
const heutigesZiel = computed(() => f.value.needed_per_day ?? f.value.plan_per_day)
const heuteSchonGelesen = computed(() => props.task.entries.some((e) => e.day === today))
const zeigeTagesziel = computed(() => f.value.status !== 'done' && !heuteSchonGelesen.value && heutigesZiel.value)
// Einträge ohne Buch-Zuordnung (z. B. aus der Zeit vor der Aufteilung in mehrere Bücher) zählen zwar zum
// Gesamtfortschritt des Pensums, aber zu keinem einzelnen Buch – sonst verschwände die Menge sonst spurlos.
const ohneBuchGelesen = computed(() => props.task.buecher.length
  ? f.value.done - props.task.buecher.reduce((n, b) => n + b.done, 0) : 0)
// Mehrere Durchgänge: abgeschlossene oben nur als Zahl zusammenfassen, noch nicht begonnene (0 gelesen) gar
// nicht erst zeigen – jeder begonnene, aber noch nicht abgeschlossene Durchgang bekommt seine eigene
// Statusleiste (nicht nur der eine "aktive" = erste unvollständige – es kann mehrere gleichzeitig geben,
// z. B. wenn ein späterer Durchgang schon fertig ist, während ein früherer noch offen ist).
const abgeschlosseneDurchlaeufeAnzahl = computed(() => (props.task.durchlaeufe || []).filter((d) => d.abgeschlossen).length)
const laufendeDurchlaeufe = computed(() => (props.task.durchlaeufe || []).filter((d) => d.done > 0 && !d.abgeschlossen))

async function log() {
  error.value = ''
  if (props.task.buecher.length && !buchId.value) { error.value = 'Bitte zuerst ein Buch auswählen.'; return }
  try {
    await reading.log(props.task.id, { amount: amount.value, day: day.value, buchId: buchId.value, durchlauf: durchlauf.value })
    amount.value = ''
    emit('changed')
  } catch (e) { error.value = e.message }
}
function buchTitel(buchId) { return props.task.buecher.find((b) => b.id === buchId)?.title }
async function removeEntry(entry) {
  await reading.deleteEntry(props.task.id, entry.id)
  emit('changed')
}
async function removeTask() {
  if (!confirm(`Pensum „${props.task.title}“ mit dem ganzen Leseprotokoll löschen?`)) return
  await reading.remove(props.task.id)
  emit('changed')
}
async function exportierenAlsPdf() {
  exportError.value = ''
  exportLaeuft.value = true
  try {
    // Tatsächlich gelesene Seiten/Kapitel (b.done bzw. forecast.done), nicht der geplante Umfang (b.total/task.total).
    const buecher = props.task.buecher.length
      ? props.task.buecher.map((b) => ({ titel: b.title, seiten: b.done }))
      : [{ titel: props.task.title, seiten: props.task.forecast.done }]
    await pdfcreator.lesenachweisExportieren(props.subjectName, exportName.value, exportGemeinde.value, buecher)
    exportieren.value = false
  } catch (e) { exportError.value = e.message }
  finally { exportLaeuft.value = false }
}

function openEdit() {
  editError.value = ''
  const t = props.task
  editForm.value = { title: t.title, unit: t.unit, total: t.total, passes: t.passes, start: t.start || '', deadline: t.deadline || '' }
  editMehrereBuecher.value = t.buecher.length > 0
  editBuecher.value = t.buecher.length ? t.buecher.map((b) => ({ title: b.title, total: b.total })) : [{ title: '', total: '' }]
  bearbeiten.value = true
}
function addEditBuchFeld() { editBuecher.value.push({ title: '', total: '' }) }
function removeEditBuchFeld(i) { editBuecher.value.splice(i, 1) }
async function saveEdit() {
  editError.value = ''
  speichert.value = true
  try {
    await reading.update(props.task.id, editForm.value, editMehrereBuecher.value ? editBuecher.value : null)
    bearbeiten.value = false
    emit('changed')
  } catch (e) { editError.value = e.message }
  finally { speichert.value = false }
}
</script>

<template>
  <li class="panel p-5">
    <div v-if="!bearbeiten">
      <div class="flex items-center gap-1.5">
        <h3 class="text-lg font-semibold">{{ task.title }}</h3>
        <button class="btn btn-ghost !p-1.5" aria-label="Pensum bearbeiten" @click="openEdit">
          <AppIcon name="stift" class="h-3.5 w-3.5" />
        </button>
      </div>
      <!-- Minimalistisch auf Wunsch: nur Status (keine Frist mehr) und das Tagesziel als eine Zahl bleiben auf
           den ersten Blick sichtbar; der ausführliche Prognose-Satz und Start/Plan-Details fielen weg. -->
      <div class="mt-1 flex flex-wrap items-center gap-x-3 gap-y-1 text-sm">
        <span class="rounded-full px-2.5 py-0.5 text-xs font-medium" :class="TONE_CLASSES[status.tone]">{{ status.label }}</span>
        <span v-if="zeigeTagesziel" class="font-medium text-amber-700 dark:text-amber-300">{{ num(heutigesZiel) }} {{ task.unit }}/Tag nötig</span>
      </div>
    </div>

    <form v-else class="grid gap-3 sm:grid-cols-6" @submit.prevent="saveEdit">
      <input v-model="editForm.title" class="input sm:col-span-6" placeholder="Titel" aria-label="Titel" />

      <label class="flex items-center gap-1.5 text-sm sm:col-span-6">
        <input type="checkbox" v-model="editMehrereBuecher" class="h-4 w-4 rounded" />
        Aus mehreren Büchern zusammensetzen
      </label>

      <template v-if="editMehrereBuecher">
        <div class="sm:col-span-6">
          <div v-for="(b, i) in editBuecher" :key="i" class="mb-2 flex gap-2">
            <input v-model="b.title" class="input" placeholder="Buchtitel" :aria-label="`Titel Buch ${i + 1}`" />
            <input v-model="b.total" type="number" min="1" class="input !w-32" placeholder="Seiten/Kapitel" :aria-label="`Umfang Buch ${i + 1}`" />
            <button v-if="editBuecher.length > 1" type="button" class="btn btn-ghost !px-2.5" aria-label="Buch entfernen" @click="removeEditBuchFeld(i)">✕</button>
          </div>
          <button type="button" class="btn btn-outline !py-1.5" @click="addEditBuchFeld">+ Weiteres Buch</button>
        </div>
        <label class="text-sm sm:col-span-2">
          <span class="mb-1 block text-slate-500 dark:text-slate-400">Einheit</span>
          <select v-model="editForm.unit" class="input" aria-label="Einheit">
            <option>Seiten</option>
            <option>Kapitel</option>
          </select>
        </label>
      </template>
      <label v-else class="text-sm sm:col-span-2">
        <span class="mb-1 block text-slate-500 dark:text-slate-400">Umfang</span>
        <span class="flex gap-2">
          <input v-model="editForm.total" type="number" min="1" class="input" aria-label="Umfang" />
          <select v-model="editForm.unit" class="input !w-auto" aria-label="Einheit">
            <option>Seiten</option>
            <option>Kapitel</option>
          </select>
        </span>
      </label>
      <label class="text-sm sm:col-span-2">
        <span class="mb-1 block text-slate-500 dark:text-slate-400">Durchgänge</span>
        <input v-model="editForm.passes" type="number" min="1" max="20" class="input" />
      </label>
      <label class="text-sm sm:col-span-2">
        <span class="mb-1 block text-slate-500 dark:text-slate-400">Start (optional)</span>
        <input v-model="editForm.start" type="date" class="input" />
      </label>
      <label class="text-sm sm:col-span-2">
        <span class="mb-1 block text-slate-500 dark:text-slate-400">Frist (optional)</span>
        <input v-model="editForm.deadline" type="date" class="input" />
      </label>
      <div class="flex gap-2 sm:col-span-6">
        <button class="btn btn-primary" :disabled="speichert">{{ speichert ? 'Speichert …' : 'Speichern' }}</button>
        <button type="button" class="btn btn-ghost" @click="bearbeiten = false">Abbrechen</button>
      </div>
      <p v-if="editError" class="text-sm text-rose-600 dark:text-rose-400 sm:col-span-6">{{ editError }}</p>
    </form>

    <div v-if="!bearbeiten" class="mt-3 h-1.5 overflow-hidden rounded-full bg-highlight" role="progressbar"
      :aria-valuenow="f.percent" aria-valuemin="0" aria-valuemax="100" :aria-label="`${num(f.percent)} % gelesen`">
      <div class="h-full rounded-full" :class="BAR_CLASSES[status.tone]" :style="{ width: f.percent + '%' }"></div>
    </div>

    <!-- Eigene, schlichte Statusleiste je Buch (Seitenzahl darüber), statt einer reinen Textzeile. -->
    <div v-if="!bearbeiten && task.buecher.length" class="mt-3 grid gap-2">
      <div v-for="b in task.buecher" :key="b.id">
        <div class="flex items-center justify-between text-xs">
          <span class="truncate">{{ b.title }}</span>
          <span class="shrink-0 tabular-nums opacity-70">{{ num(b.done) }}/{{ num(b.total) }}</span>
        </div>
        <div class="mt-1 h-1.5 overflow-hidden rounded-full bg-highlight" role="progressbar"
          :aria-valuenow="b.total ? Math.min(100, Math.round(b.done / b.total * 100)) : 0" aria-valuemin="0" aria-valuemax="100" :aria-label="b.title">
          <div class="h-full rounded-full bg-primary" :style="{ width: Math.min(100, b.total ? (b.done / b.total * 100) : 0) + '%' }"></div>
        </div>
      </div>
      <div v-if="ohneBuchGelesen > 0">
        <div class="flex items-center justify-between text-xs opacity-70">
          <span>Ohne Buch zugeordnet</span>
          <span class="shrink-0 tabular-nums">{{ num(ohneBuchGelesen) }}</span>
        </div>
      </div>
    </div>

    <!-- Mehrere Durchgänge: abgeschlossene nur als Zahl oben, noch nicht begonnene Durchgänge erscheinen hier
         gar nicht erst – jeder begonnene, offene Durchgang bekommt seine eigene Statusleiste. -->
    <div v-if="!bearbeiten && task.passes > 1" class="mt-3 grid gap-2">
      <p v-if="abgeschlosseneDurchlaeufeAnzahl" class="text-xs opacity-70">
        {{ abgeschlosseneDurchlaeufeAnzahl }} von {{ task.passes }} {{ task.passes === 1 ? 'Durchgang' : 'Durchgängen' }} abgeschlossen
      </p>
      <div v-for="d in laufendeDurchlaeufe" :key="d.nummer">
        <div class="flex items-center justify-between text-xs">
          <span>Durchgang {{ d.nummer }}</span>
          <span class="shrink-0 tabular-nums opacity-70">{{ num(d.done) }}/{{ num(d.total) }}</span>
        </div>
        <div class="mt-1 h-1.5 overflow-hidden rounded-full bg-highlight" role="progressbar"
          :aria-valuenow="Math.min(100, Math.round(d.done / d.total * 100))" aria-valuemin="0" aria-valuemax="100"
          :aria-label="`Durchgang ${d.nummer}`">
          <div class="h-full rounded-full bg-primary" :style="{ width: Math.min(100, d.done / d.total * 100) + '%' }"></div>
        </div>
      </div>
    </div>

    <!-- Buchname bekommt den meisten Platz (voller Titel statt abgeschnitten), Datum nur als Kalender-Symbol
         (öffnet den nativen Datumswähler), Eintragen als Haken-Symbol statt Textknopf. -->
    <form v-if="!bearbeiten" class="mt-4 flex flex-wrap items-center gap-2" @submit.prevent="log">
      <select v-if="task.buecher.length" v-model="buchId" class="input min-w-0 flex-1 basis-32" aria-label="Buch">
        <option value="" disabled>Buch wählen</option>
        <option v-for="b in task.buecher" :key="b.id" :value="b.id">{{ b.title }}</option>
      </select>
      <select v-if="task.passes > 1" v-model="durchlauf" class="input w-auto shrink-0" aria-label="Durchgang">
        <option v-for="d in task.durchlaeufe" :key="d.nummer" :value="d.nummer">Durchgang {{ d.nummer }}</option>
      </select>
      <input v-model="amount" type="number" min="1" class="input w-20 shrink-0" :placeholder="task.unit" :aria-label="`Gelesene ${task.unit}`" />
      <div class="relative shrink-0">
        <input ref="dayInput" v-model="day" type="date" :max="today" class="sr-only" aria-label="Datum (leer = heute)" />
        <button type="button" class="btn btn-outline !px-2.5" :aria-label="day ? `Datum: ${formatDate(day)}` : 'Datum wählen (leer = heute)'" @click="dayPickerOeffnen">
          <AppIcon name="kalender" class="h-4 w-4" />
        </button>
      </div>
      <button type="submit" class="btn btn-primary !px-2.5 shrink-0" aria-label="Eintragen">
        <AppIcon name="haken" class="h-4 w-4" />
      </button>
    </form>
    <p v-if="!bearbeiten && error" class="mt-2 text-sm text-rose-600 dark:text-rose-400">{{ error }}</p>

    <details v-if="!bearbeiten && task.entries.length" class="mt-4">
      <summary class="cursor-pointer text-sm text-slate-500 dark:text-slate-400">
        Leseprotokoll ({{ task.entries.length }} {{ task.entries.length === 1 ? 'Eintrag' : 'Einträge' }})
      </summary>
      <ul class="mt-2 divide-y divide-slate-200 text-sm dark:divide-slate-800">
        <li v-for="e in task.entries" :key="e.id" class="flex items-center gap-3 py-2">
          <span class="w-24 shrink-0 tabular-nums text-slate-500 dark:text-slate-400">{{ formatDate(e.day) }}</span>
          <span class="w-28 shrink-0 tabular-nums">{{ num(e.amount) }} {{ task.unit }}</span>
          <span v-if="task.passes > 1" class="w-24 shrink-0 text-slate-500 dark:text-slate-400">Durchgang {{ e.durchlauf }}</span>
          <span v-if="e.buch_id" class="min-w-0 flex-1 truncate text-slate-500 dark:text-slate-400">{{ buchTitel(e.buch_id) }}</span>
          <span v-else class="min-w-0 flex-1 truncate text-slate-500 dark:text-slate-400">{{ e.note }}</span>
          <button class="btn btn-danger !px-2.5 !py-1" :aria-label="`Eintrag vom ${formatDate(e.day)} löschen`" @click="removeEntry(e)">Löschen</button>
        </li>
      </ul>
    </details>

    <form v-if="!bearbeiten && exportieren" class="mt-4 grid gap-2 border-t border-highlight pt-4 sm:grid-cols-2" @submit.prevent="exportierenAlsPdf">
      <input v-model="exportName" class="input" placeholder="Name (optional)" aria-label="Name" />
      <input v-model="exportGemeinde" class="input" placeholder="Gemeinde (optional)" aria-label="Gemeinde" />
      <div class="flex gap-2 sm:col-span-2">
        <button class="btn btn-primary !py-1.5" :disabled="exportLaeuft">{{ exportLaeuft ? 'Erzeugt PDF …' : 'PDF erzeugen' }}</button>
        <button type="button" class="btn btn-ghost !py-1.5" @click="exportieren = false">Abbrechen</button>
        <span v-if="exportError" class="ml-1 text-sm text-rose-600 dark:text-rose-400">{{ exportError }}</span>
      </div>
    </form>

    <div v-if="!bearbeiten" class="mt-4 flex justify-between">
      <button class="btn btn-outline !py-1.5" @click="exportieren = true">Als PDF exportieren</button>
      <button class="btn btn-danger !py-1.5" @click="removeTask">Pensum löschen</button>
    </div>
  </li>
</template>
