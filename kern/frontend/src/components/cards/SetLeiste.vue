<script setup>
import { computed, inject, ref } from 'vue'
import AppIcon from '../ui/AppIcon.vue'

// Sets eines Fachs (eine Ebene unter dem Fach): als Auswahlleiste, dazu anlegen, umbenennen und löschen.
// Gemeinsam für die Karten-Ansicht im Fach und „Alle Karten“ – die Auswahl (`modelValue`) ist '' = alle, OHNE_SET = Karten ohne Set,
// sonst der Name eines Sets.
const props = defineProps({
  deckId: { type: String, required: true },
  sets: { type: Array, default: () => [] },      // [{ name, card_count, due_count }]
  alle: { type: Number, default: 0 },            // Anzahl aller Karten des Fachs
  ohne: { type: Number, default: 0 },            // Karten ohne Set
  modelValue: { type: String, default: '' },
})
const emit = defineEmits(['update:modelValue', 'changed'])
const service = inject('service')
const OHNE_SET = '__ohne__'

const aktuell = computed(() => props.sets.find((s) => s.name === props.modelValue) || null)
const setFehler = ref('')
const neuesSetOffen = ref(false)
const neuerSetName = ref('')
const umbenennenOffen = ref(false)
const umbenennenName = ref('')
const loeschenOffen = ref(false)

async function setAktion(fn) {
  setFehler.value = ''
  try { await fn(); emit('changed'); return true } catch (e) { setFehler.value = e.message; return false }
}
async function setAnlegen() {
  const name = neuerSetName.value.trim()
  if (await setAktion(() => service.createSet(props.deckId, name))) {
    neuesSetOffen.value = false; neuerSetName.value = ''; emit('update:modelValue', name)
  }
}
function umbenennenStarten() { umbenennenName.value = props.modelValue; umbenennenOffen.value = true; loeschenOffen.value = false }
async function setUmbenennen() {
  const neu = umbenennenName.value.trim()
  if (await setAktion(() => service.renameSet(props.deckId, props.modelValue, neu))) {
    umbenennenOffen.value = false; emit('update:modelValue', neu)
  }
}
async function setLoeschen(mitKarten) {
  if (await setAktion(() => service.deleteSet(props.deckId, props.modelValue, mitKarten))) {
    loeschenOffen.value = false; emit('update:modelValue', '')
  }
}
function setWaehlen(wert) {
  emit('update:modelValue', wert); setFehler.value = ''; umbenennenOffen.value = false; loeschenOffen.value = false
}
</script>

<template>
  <div>
    <!-- Sets: eine Ebene unter dem Fach. Ein Klick zeigt nur die Karten dieses Sets. -->
    <div class="mb-3 flex flex-wrap items-center gap-2" role="group" aria-label="Sets">
      <button type="button" class="rounded-full px-3 py-1 text-sm ring-1 ring-slate-300 dark:ring-slate-700"
        :class="modelValue === '' ? 'bg-primary text-white ring-0' : 'hover:bg-slate-100 dark:hover:bg-slate-800'" @click="setWaehlen('')">
        Alle ({{ alle }})
      </button>
      <button v-for="s in sets" :key="s.name" type="button" class="rounded-full px-3 py-1 text-sm ring-1 ring-slate-300 dark:ring-slate-700"
        :class="modelValue === s.name ? 'bg-primary text-white ring-0' : 'hover:bg-slate-100 dark:hover:bg-slate-800'" @click="setWaehlen(s.name)">
        {{ s.name }} ({{ s.card_count }})
      </button>
      <button v-if="sets.length && ohne" type="button" class="rounded-full px-3 py-1 text-sm ring-1 ring-slate-300 dark:ring-slate-700"
        :class="modelValue === OHNE_SET ? 'bg-primary text-white ring-0' : 'hover:bg-slate-100 dark:hover:bg-slate-800'" @click="setWaehlen(OHNE_SET)">
        Ohne Set ({{ ohne }})
      </button>
      <button type="button" class="rounded-full px-3 py-1 text-sm ring-1 ring-slate-300 hover:bg-slate-100 dark:ring-slate-700 dark:hover:bg-slate-800"
        @click="neuesSetOffen = !neuesSetOffen">+ Set</button>
    </div>

    <form v-if="neuesSetOffen" class="mb-3 flex flex-wrap gap-2" @submit.prevent="setAnlegen">
      <input v-model="neuerSetName" class="input !w-auto min-w-[14rem] flex-1" placeholder="Name des neuen Sets" aria-label="Name des neuen Sets" autofocus />
      <button class="btn btn-primary !py-1.5">Set anlegen</button>
      <button type="button" class="btn btn-ghost !py-1.5" @click="neuesSetOffen = false">Abbrechen</button>
    </form>

    <!-- Das gewählte Set: Name, Umbenennen, Löschen -->
    <div v-if="aktuell" class="panel mb-3 space-y-3 p-4">
      <div v-if="!umbenennenOffen" class="flex flex-wrap items-center justify-between gap-2">
        <div>
          <h3 class="font-semibold">Set: {{ aktuell.name }}</h3>
          <p class="text-sm text-slate-500 dark:text-slate-400">{{ aktuell.card_count }} Karten, {{ aktuell.due_count }} fällig</p>
        </div>
        <div class="flex gap-2">
          <button type="button" class="btn btn-outline !px-3 !py-1.5" title="Set umbenennen" aria-label="Set umbenennen" @click="umbenennenStarten">
            <AppIcon name="stift" class="h-4 w-4" />
          </button>
          <button type="button" class="btn btn-danger !px-3 !py-1.5" @click="loeschenOffen = !loeschenOffen; umbenennenOffen = false">Set löschen</button>
        </div>
      </div>
      <form v-else class="flex flex-wrap gap-2" @submit.prevent="setUmbenennen">
        <input v-model="umbenennenName" class="input !w-auto min-w-[14rem] flex-1" aria-label="Neuer Name des Sets" />
        <button class="btn btn-primary !py-1.5">Speichern</button>
        <button type="button" class="btn btn-ghost !py-1.5" @click="umbenennenOffen = false">Abbrechen</button>
      </form>
      <div v-if="loeschenOffen" class="space-y-2 text-sm">
        <p>„{{ aktuell.name }}“ löschen? Die Karten können im Fach bleiben (ohne Set) oder mit gelöscht werden.</p>
        <div class="flex flex-wrap gap-2">
          <button type="button" class="btn btn-outline !py-1.5" @click="setLoeschen(false)">Set löschen, Karten behalten</button>
          <button type="button" class="btn btn-danger !py-1.5" @click="setLoeschen(true)">Set mit {{ aktuell.card_count }} Karten löschen</button>
          <button type="button" class="btn btn-ghost !py-1.5" @click="loeschenOffen = false">Abbrechen</button>
        </div>
      </div>
    </div>
    <p v-if="setFehler" class="mb-3 text-sm text-rose-600 dark:text-rose-400">{{ setFehler }}</p>
  </div>
</template>
