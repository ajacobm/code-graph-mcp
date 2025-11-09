<template>
  <div v-if="isAnalyzing" class="bg-slate-800/50 border border-slate-700 rounded-lg p-4 space-y-3">
    <!-- Header -->
    <div class="flex items-center justify-between">
      <h3 class="text-sm font-semibold text-slate-300">⚙️ Analysis Progress</h3>
      <span class="text-xs text-slate-500">{{ elapsedTime }}s</span>
    </div>

    <!-- Progress Bar -->
    <div class="space-y-2">
      <div class="w-full bg-slate-700 rounded-full h-2 overflow-hidden">
        <div
          class="bg-gradient-to-r from-indigo-500 to-pink-500 h-full transition-all duration-300"
          :style="{ width: `${progressPercent}%` }"
        ></div>
      </div>
      <div class="flex items-center justify-between text-xs text-slate-400">
        <span>Analyzing codebase...</span>
        <span class="font-mono">{{ progressPercent }}%</span>
      </div>
    </div>

    <!-- Status Details -->
    <div class="border-t border-slate-700 pt-3 space-y-2 text-xs">
      <div v-if="currentStatus" class="text-slate-300">
        <span class="text-slate-500">Status:</span>
        <span class="ml-2">{{ currentStatus }}</span>
      </div>
      <div class="text-slate-300">
        <span class="text-slate-500">Nodes:</span>
        <span class="ml-2 font-mono">{{ nodesProcessed }}</span>
      </div>
      <div v-if="currentFile" class="text-slate-400 truncate">
        <span class="text-slate-500">File:</span>
        <span class="ml-2 font-mono text-xs truncate">{{ currentFile }}</span>
      </div>
    </div>

    <!-- Cancel Button -->
    <button
      @click="cancelAnalysis"
      class="w-full px-3 py-2 text-xs bg-slate-700/50 hover:bg-red-700/50 text-slate-300 hover:text-red-200 rounded transition-colors"
    >
      ⏹️ Cancel Analysis
    </button>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { useEvents } from '../composables/useEvents'
import { useGraphStore } from '../stores/graphStore'

const { subscribe } = useEvents()
const graphStore = useGraphStore()

const isAnalyzing = ref(false)
const elapsedTime = ref(0)
const progressPercent = ref(0)
const currentStatus = ref('')
const nodesProcessed = ref(0)
const currentFile = ref('')

let progressInterval: ReturnType<typeof setInterval> | null = null
let analysisStartTime = 0

const handleAnalysisStarted = () => {
  isAnalyzing.value = true
  analysisStartTime = Date.now()
  progressPercent.value = 5
  currentStatus.value = 'Starting analysis...'
  nodesProcessed.value = 0

  // Simulate progress
  progressInterval = setInterval(() => {
    elapsedTime.value = Math.floor((Date.now() - analysisStartTime) / 1000)
    if (progressPercent.value < 90) {
      progressPercent.value += Math.random() * 15
    }
  }, 500)
}

const handleAnalysisProgress = (event: any) => {
  if (event.data) {
    currentStatus.value = event.data.status || 'Processing...'
    if (event.data.nodes_processed) {
      nodesProcessed.value = event.data.nodes_processed
    }
    if (event.data.current_file) {
      currentFile.value = event.data.current_file
    }
    if (event.data.progress) {
      progressPercent.value = Math.min(85, event.data.progress)
    }
  }
}

const handleAnalysisCompleted = () => {
  isAnalyzing.value = false
  progressPercent.value = 100

  if (progressInterval) {
    clearInterval(progressInterval)
    progressInterval = null
  }

  // Auto-hide after 1 second
  setTimeout(() => {
    if (progressPercent.value === 100) {
      progressPercent.value = 0
    }
  }, 1000)
}

const cancelAnalysis = () => {
  graphStore.cancelAnalysis?.()
  isAnalyzing.value = false

  if (progressInterval) {
    clearInterval(progressInterval)
    progressInterval = null
  }
}

onMounted(() => {
  subscribe('analysis_started', handleAnalysisStarted)
  subscribe('analysis_progress', handleAnalysisProgress)
  subscribe('analysis_completed', handleAnalysisCompleted)
})

onUnmounted(() => {
  if (progressInterval) {
    clearInterval(progressInterval)
  }
})
</script>
