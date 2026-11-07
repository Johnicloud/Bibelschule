<script setup>
import { onBeforeUnmount, onMounted, ref } from 'vue'
import AppIcon from './AppIcon.vue'

// Drei-Punkte-Menü: items = [{ label, icon, danger, action }]. Schließt beim Klick daneben und mit Escape.
defineProps({ items: { type: Array, required: true }, label: { type: String, default: 'Weitere Aktionen' } })
const offen = ref(false)
const wurzel = ref(null)
const aussen = (e) => { if (wurzel.value && !wurzel.value.contains(e.target)) offen.value = false }
const escape = (e) => { if (e.key === 'Escape') offen.value = false }
onMounted(() => { document.addEventListener('click', aussen); document.addEventListener('keydown', escape) })
onBeforeUnmount(() => { document.removeEventListener('click', aussen); document.removeEventListener('keydown', escape) })
function wahl(item) { offen.value = false; item.action() }
</script>

<template>
  <div ref="wurzel" class="relative shrink-0">
    <button type="button" class="grid h-9 w-9 place-items-center rounded-full transition hover:bg-highlight" :aria-label="label" :title="label"
      aria-haspopup="menu" :aria-expanded="offen" @click="offen = !offen">
      <AppIcon name="mehr" class="h-6 w-6" stroke-width="3" />
    </button>
    <div v-if="offen" role="menu" class="absolute right-0 top-full z-20 mt-1 min-w-[13rem] rounded-xl border border-highlight bg-theme p-1 shadow-lg">
      <button v-for="(item, i) in items" :key="i" type="button" role="menuitem"
        class="flex w-full items-center gap-2.5 rounded-lg px-3 py-2 text-left text-sm transition hover:bg-highlight"
        :class="item.danger ? 'text-rose-600 dark:text-rose-400' : ''" @click="wahl(item)">
        <AppIcon v-if="item.icon" :name="item.icon" class="h-4 w-4 shrink-0" /> {{ item.label }}
      </button>
    </div>
  </div>
</template>
