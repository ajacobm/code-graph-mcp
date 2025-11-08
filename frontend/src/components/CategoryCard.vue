<template>
  <button
    @click="$emit('click')"
    :disabled="loading"
    class="bg-slate-800 hover:bg-slate-700 disabled:opacity-50 border border-slate-700 rounded-lg p-6 text-left transition-colors"
  >
    <div class="text-4xl mb-3">{{ emoji }}</div>
    <h3 class="font-bold text-slate-100 mb-1">{{ title }}</h3>
    <p class="text-sm text-slate-400">{{ description }}</p>
  </button>
</template>

<script setup lang="ts">
defineProps<{
  emoji: string
  title: string
  description: string
  loading?: boolean
}>()

defineEmits<{
  click: []
}>()
</script>
