<script setup>
import { KINDS } from '../../domain/kinds'
defineProps({ kind: String })
</script>

<template>
  <span class="inline-flex rounded-full px-2.5 py-0.5 text-xs font-medium" :class="KINDS[kind].badge">
    {{ KINDS[kind].label }}
  </span>
</template>
