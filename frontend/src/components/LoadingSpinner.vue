<script setup lang="ts">
defineProps<{
  message?: string
}>()
</script>

<template>
  <div class="flex flex-col items-center justify-center h-full gap-4">
    <div class="w-12 h-12 border-4 border-gray-600 border-t-indigo-500 rounded-full animate-spin"></div>
    <p v-if="message" class="text-gray-400">{{ message }}</p>
  </div>
</template>
