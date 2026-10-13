<script setup>
import { inject, onMounted, ref, watch } from 'vue'
import DozentenAuswahl from './DozentenAuswahl.vue'
import { SERVICE_LABELS } from '../../domain/status'

const emit = defineEmits(['created', 'cancel'])
const subjects = inject('subjects')
const adressbuch = inject('adressbuch')

const name = ref('')
const se = ref('')
const credits = ref('')
const aufgaben = ref([''])
const dozenten = ref([])
const ausgewaehlteDozenten = ref([])
const error = ref('')
const warning = ref('')

let sync = false
watch(se, (v) => { if (sync) return; sync = true; credits.value = v === '' ? '' : (Number(v) * 1.5).toFixed(1); sync = false })
watch(credits, (v) => { if (sync) return; sync = true; se.value = v === '' ? '' : (Number(v) / 1.5).toFixed(1); sync = false })

async function loadDozenten() { try { dozenten.value = await adressbuch.dozenten() } catch { /* Adressbuch gerade nicht erreichbar */ } }
function addAufgabenFeld() { aufgaben.value.push('') }
function removeAufgabenFeld(i) { aufgaben.value.splice(i, 1) }

function warn(synced) {
  const missed = Object.entries(synced || {}).filter(([, ok]) => !ok).map(([n]) => SERVICE_LABELS[n] || n)
  warning.value = missed.length
    ? `${missed.join(', ')} nicht erreichbar. Das Fach ist gespeichert; „Dienste abgleichen“ auf der Startseite holt es nach.`
    : ''
}

async function create() {
  error.value = ''
  warning.value = ''
  try {
    const subject = await subjects.create(name.value, aufgaben.value, se.value)
    await Promise.all(ausgewaehlteDozenten.value.map((id) => adressbuch.assign(id, subject.id).catch(() => {})))
    warn(subject.synced)
    emit('created', subject)
  } catch (e) { error.value = e.message }
}

onMounted(loadDozenten)
</script>

<template>
  <form class="grid gap-3" @submit.prevent="create">
    <input v-model="name" class="input" placeholder="Neues Fach, z. B. Bibelkunde" aria-label="Name des Fachs" />

    <div class="flex flex-wrap items-start gap-4">
      <div class="flex gap-2">
        <input v-model="se" type="number" min="0" step="0.5" class="input !w-24" placeholder="SE" aria-label="Studieneinheiten (optional)" />
        <input v-model="credits" type="number" min="0" step="0.1" class="input !w-28" placeholder="Credits" aria-label="Credits (optional)" />
      </div>
      <DozentenAuswahl v-model="ausgewaehlteDozenten" :dozenten="dozenten" class="flex-1" />
    </div>

    <div>
      <span class="mb-1.5 block text-sm opacity-70">Umfang (optional): die Aufgaben, die in diesem Fach anstehen</span>
      <div v-for="(a, i) in aufgaben" :key="i" class="mb-2 flex gap-2">
        <input v-model="aufgaben[i]" class="input" placeholder="Aufgabe, z. B. Exegese Kapitel 3" :aria-label="`Aufgabe ${i + 1}`" />
        <button v-if="aufgaben.length > 1" type="button" class="btn btn-ghost !px-2.5" aria-label="Aufgabe entfernen" @click="removeAufgabenFeld(i)">✕</button>
      </div>
      <button type="button" class="btn btn-outline !py-1.5" @click="addAufgabenFeld">+ Weitere Aufgabe</button>
    </div>

    <div class="flex gap-2">
      <button class="btn btn-primary justify-self-start">Fach anlegen</button>
      <button type="button" class="btn btn-ghost" @click="$emit('cancel')">Abbrechen</button>
    </div>
    <p v-if="error" class="text-sm text-error">{{ error }}</p>
    <p v-if="warning" class="text-sm text-amber-700 dark:text-amber-300">{{ warning }}</p>
  </form>
</template>
