<script setup lang="ts">
defineProps<{
  message?: string
}>()
</script>

<template>
  <div class="flex flex-col items-center justify-center gap-6 p-8">
    <span class="loading loading-spinner loading-lg text-primary"></span>
    <p v-if="message" class="text-base-content/80 font-medium">{{ message }}</p>
  </div>
</template>
