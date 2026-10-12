<script setup>
import { inject, onMounted, ref } from 'vue'
import DeckPanel from './DeckPanel.vue'
import ReadingPanel from '../components/reading/ReadingPanel.vue'
import RegisterPanel from '../components/register/RegisterPanel.vue'

const props = defineProps({ subjectId: String, tab: { type: String, default: 'cards' } })
defineEmits(['back', 'study', 'update:tab'])
const subjects = inject('subjects')
const subject = ref(null)
const error = ref('')

const tabs = [
  { id: 'cards', label: 'Karteikarten' },
  { id: 'reading', label: 'Lesenachweis' },
  { id: 'register', label: 'Register' },
]

onMounted(async () => {
  try { subject.value = await subjects.get(props.subjectId) }
  catch (e) { error.value = e.message }
})
</script>

<template>
  <button class="btn btn-ghost !px-2" @click="$emit('back')">Zurück zu den Fächern</button>
  <p v-if="error" class="mt-4 text-sm text-rose-600 dark:text-rose-400">{{ error }}</p>
  <template v-if="subject">
    <h1 class="mt-2 text-3xl font-semibold tracking-tight">{{ subject.name }}</h1>

    <div class="mt-5 flex gap-1 border-b border-slate-200 dark:border-slate-800" role="tablist">
      <button v-for="t in tabs" :key="t.id" role="tab" :aria-selected="tab === t.id"
        class="-mb-px border-b-2 px-4 py-2.5 text-sm font-medium transition"
        :class="tab === t.id
          ? 'border-teal-600 text-teal-700 dark:border-teal-400 dark:text-teal-300'
          : 'border-transparent text-slate-500 hover:text-slate-900 dark:text-slate-400 dark:hover:text-slate-100'"
        @click="$emit('update:tab', t.id)">
        {{ t.label }}
      </button>
    </div>

    <div class="mt-6" role="tabpanel">
      <DeckPanel v-if="tab === 'cards'" :deck-id="subjectId" @study="$emit('study')" />
      <ReadingPanel v-else-if="tab === 'reading'" :subject-id="subjectId" />
      <RegisterPanel v-else :subject-id="subjectId" />
    </div>
  </template>
</template>
