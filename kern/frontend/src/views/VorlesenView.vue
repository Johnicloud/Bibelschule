<script setup>
import { inject, ref } from 'vue'
import AppIcon from '../components/ui/AppIcon.vue'

const vorlesen = inject('vorlesen')
const text = ref('')
const laeuft = ref(false)
const fehler = ref('')
const audioUrl = ref('')

async function vorlesenStarten() {
  fehler.value = ''
  laeuft.value = true
  if (audioUrl.value) URL.revokeObjectURL(audioUrl.value)
  audioUrl.value = ''
  try {
    const blob = await vorlesen.text(text.value)
    audioUrl.value = URL.createObjectURL(blob)
  } catch (e) { fehler.value = e.message }
  finally { laeuft.value = false }
}
</script>

<template>
  <h1 class="text-3xl font-semibold tracking-tight">Vorlesen</h1>
  <p class="mt-1 text-slate-500 dark:text-slate-400">
    Text einfügen und als Audio anhören – läuft lokal und kostenlos, ohne Internet oder Cloud-Dienst.
  </p>

  <form class="panel mt-6 grid gap-3 p-5" @submit.prevent="vorlesenStarten">
    <textarea v-model="text" rows="10" class="input" placeholder="Text hier einfügen oder eintippen …" aria-label="Text zum Vorlesen"></textarea>
    <div class="flex items-center gap-3">
      <button class="btn btn-primary inline-flex items-center gap-2" :disabled="laeuft || !text.trim()">
        <AppIcon name="vorlesen" class="h-4 w-4" />
        {{ laeuft ? 'Erzeugt Audio …' : 'Vorlesen' }}
      </button>
      <span v-if="fehler" class="text-sm text-rose-600 dark:text-rose-400">{{ fehler }}</span>
    </div>
  </form>

  <div v-if="audioUrl" class="panel mt-4 p-5">
    <audio :src="audioUrl" controls autoplay class="w-full"></audio>
  </div>
</template>
