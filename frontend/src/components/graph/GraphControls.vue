<script setup lang="ts">
import { ref } from 'vue'

const props = defineProps<{
  showLabels?: boolean
  colorByLanguage?: boolean
  colorByType?: boolean
  isLoading?: boolean
}>()

const emit = defineEmits<{
  'update:showLabels': [value: boolean]
  'update:colorByLanguage': [value: boolean]
  'update:colorByType': [value: boolean]
  zoomToFit: []
  refresh: []
}>()

const showLabelsLocal = ref(props.showLabels ?? true)
const colorByLanguageLocal = ref(props.colorByLanguage ?? false)
const colorByTypeLocal = ref(props.colorByType ?? true)

const toggleLabels = () => {
  showLabelsLocal.value = !showLabelsLocal.value
  emit('update:showLabels', showLabelsLocal.value)
}

const toggleColorByLanguage = () => {
  colorByLanguageLocal.value = !colorByLanguageLocal.value
  colorByTypeLocal.value = false
  emit('update:colorByLanguage', colorByLanguageLocal.value)
  emit('update:colorByType', false)
}

const toggleColorByType = () => {
  colorByTypeLocal.value = !colorByTypeLocal.value
  colorByLanguageLocal.value = false
  emit('update:colorByType', colorByTypeLocal.value)
  emit('update:colorByLanguage', false)
}
</script>

<template>
  <div class="graph-controls flex items-center gap-2 p-2 bg-slate-800/50 rounded-lg">
    <!-- Zoom to Fit -->
    <button
      @click="emit('zoomToFit')"
      class="btn btn-sm btn-ghost tooltip tooltip-bottom"
      data-tip="Zoom to fit"
    >
      <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 8V4m0 0h4M4 4l5 5m11-1V4m0 0h-4m4 0l-5 5M4 16v4m0 0h4m-4 0l5-5m11 5l-5-5m5 5v-4m0 4h-4" />
      </svg>
    </button>

    <!-- Refresh -->
    <button
      @click="emit('refresh')"
      :disabled="isLoading"
      class="btn btn-sm btn-ghost tooltip tooltip-bottom"
      data-tip="Refresh graph"
    >
      <svg 
        xmlns="http://www.w3.org/2000/svg" 
        class="h-5 w-5" 
        :class="{ 'animate-spin': isLoading }"
        fill="none" 
        viewBox="0 0 24 24" 
        stroke="currentColor"
      >
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
      </svg>
    </button>

    <div class="divider divider-horizontal mx-0"></div>

    <!-- Toggle Labels -->
    <button
      @click="toggleLabels"
      :class="['btn btn-sm', showLabelsLocal ? 'btn-primary' : 'btn-ghost']"
      class="tooltip tooltip-bottom"
      data-tip="Toggle labels"
    >
      <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A1.994 1.994 0 013 12V7a4 4 0 014-4z" />
      </svg>
    </button>

    <!-- Color by Language -->
    <button
      @click="toggleColorByLanguage"
      :class="['btn btn-sm', colorByLanguageLocal ? 'btn-primary' : 'btn-ghost']"
      class="tooltip tooltip-bottom"
      data-tip="Color by language"
    >
      🌐
    </button>

    <!-- Color by Type -->
    <button
      @click="toggleColorByType"
      :class="['btn btn-sm', colorByTypeLocal ? 'btn-primary' : 'btn-ghost']"
      class="tooltip tooltip-bottom"
      data-tip="Color by type"
    >
      📦
    </button>
  </div>
</template>

<style scoped>
.graph-controls {
  backdrop-filter: blur(8px);
}
</style>
