<script setup>
import { nextTick, ref } from 'vue'

// Alle Register eines Fachs nebeneinander: ein Klick springt hin, dort kann sofort eingetragen werden.
const props = defineProps({
  registers: Array,
  modelValue: String,
  creator: Function, // (name) => Promise<boolean>: legt an; true = geklappt
  error: String,
})
defineEmits(['update:modelValue'])

const creating = ref(false)
const name = ref('')
const input = ref(null)

async function open() {
  creating.value = true
  await nextTick()
  input.value?.focus()
}
async function submit() {
  if (!name.value.trim()) return
  if (await props.creator(name.value)) { name.value = ''; creating.value = false }
}
function cancel() { creating.value = false; name.value = '' }
</script>

<template>
  <div class="flex flex-wrap items-center gap-2" role="tablist" aria-label="Register dieses Fachs">
    <button v-for="r in registers" :key="r.id" type="button" role="tab" :aria-selected="modelValue === r.id"
      class="btn !py-2"
      :class="modelValue === r.id ? 'bg-slate-900 text-white dark:bg-slate-100 dark:text-slate-900' : 'btn-outline'"
      @click="$emit('update:modelValue', r.id)">
      {{ r.name }}
      <span class="rounded-full px-2 text-xs tabular-nums"
        :class="modelValue === r.id ? 'bg-white/20 dark:bg-slate-900/15' : 'bg-slate-100 dark:bg-slate-800'">{{ r.entry_count }}</span>
    </button>

    <form v-if="creating" class="flex items-center gap-2" @submit.prevent="submit">
      <input ref="input" v-model="name" class="input !w-44 !py-2" placeholder="Name des Registers"
        aria-label="Name des neuen Registers" @keydown.esc="cancel" />
      <button class="btn btn-primary !py-2">Anlegen</button>
      <button type="button" class="btn btn-ghost !py-2" @click="cancel">Abbrechen</button>
    </form>
    <button v-else type="button" class="btn btn-ghost !py-2 text-teal-700 dark:text-teal-300" @click="open">+ Neues Register</button>
  </div>
  <p v-if="error" class="mt-2 text-sm text-rose-600 dark:text-rose-400">{{ error }}</p>
</template>
