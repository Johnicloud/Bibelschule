<script setup>
import { onBeforeUnmount, onMounted, ref } from 'vue'
import AppIcon from './AppIcon.vue'

const props = defineProps({ dozenten: { type: Array, default: () => [] }, modelValue: { type: Array, default: () => [] } })
const emit = defineEmits(['update:modelValue'])

const open = ref(false)
function schliessen(e) { if (!e.target.closest('[data-dozenten-auswahl]')) open.value = false }
onMounted(() => document.addEventListener('click', schliessen))
onBeforeUnmount(() => document.removeEventListener('click', schliessen))

function umschalten(id) {
  const next = props.modelValue.includes(id) ? props.modelValue.filter((x) => x !== id) : [...props.modelValue, id]
  emit('update:modelValue', next)
}
</script>

<template>
  <div class="relative" data-dozenten-auswahl>
    <span class="mb-1.5 block text-sm opacity-70">Dozenten (optional)</span>
    <button type="button" class="input flex items-center justify-between text-left" :aria-expanded="open" @click="open = !open">
      <span class="truncate">
        {{ modelValue.length ? dozenten.filter((d) => modelValue.includes(d.id)).map((d) => d.name).join(', ') : 'Keine ausgewählt' }}
      </span>
      <AppIcon name="chevron" class="h-4 w-4 shrink-0 opacity-60" />
    </button>
    <div v-if="open" class="absolute z-10 mt-1 w-full max-h-56 overflow-auto rounded-xl border border-highlight bg-theme p-1.5 shadow-lg">
      <label v-for="d in dozenten" :key="d.id" class="flex items-center gap-2 rounded-lg px-2 py-1.5 text-sm hover:bg-backdrop">
        <input type="checkbox" :checked="modelValue.includes(d.id)" class="h-4 w-4 rounded" @change="umschalten(d.id)" />
        {{ d.name }}
      </label>
      <p v-if="!dozenten.length" class="px-2 py-1.5 text-sm opacity-60">Keine Dozenten im Adressbuch.</p>
    </div>
  </div>
</template>
