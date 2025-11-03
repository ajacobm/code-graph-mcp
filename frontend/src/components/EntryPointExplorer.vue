<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useEntryPointStore } from '../stores/entryPointStore'
import { useGraphStore } from '../stores/graphStore'
import { graphClient } from '../api/graphClient'
import LoadingSpinner from './LoadingSpinner.vue'

const entryPointStore = useEntryPointStore()
const graphStore = useGraphStore()

const isLoading = ref(false)
const showFilters = ref(false)
const confidenceThreshold = ref(0.5)
const entryLimit = ref(50)

const confidenceLevels = [
  { value: 0.1, label: 'Low (0.1+)' },
  { value: 0.5, label: 'Medium (0.5+)' },
  { value: 1.0, label: 'High (1.0+)' },
  { value: 2.0, label: 'Very High (2.0+)' },
]

const languageIcons: Record<string, string> = {
  python: '🐍',
  javascript: '🟨',
  typescript: '📘',
  java: '☕',
  csharp: '☪️',
  go: '🐹',
  rust: '🦀',
  cpp: '🅒',
  c: '🅒',
  php: '🐘',
  ruby: '💎',
  kotlin: ' Kotlin',
  swift: '🕊️',
}

const filteredEntryPoints = computed(() => {
  return entryPointStore.entryPoints.filter(ep => 
    ep.confidence_score >= confidenceThreshold.value
  )
})

const paginatedEntryPoints = computed(() => {
  return filteredEntryPoints.value.slice(0, entryLimit.value)
})

const groupedByLanguage = computed(() => {
  const groups: Record<string, typeof entryPointStore.entryPoints> = {}
  paginatedEntryPoints.value.forEach(ep => {
    if (!groups[ep.language]) {
      groups[ep.language] = []
    }
    groups[ep.language].push(ep)
  })
  return groups
})

const loadEntryPoints = async () => {
  isLoading.value = true
  try {
    await entryPointStore.loadEntryPoints()
  } finally {
    isLoading.value = false
  }
}

const selectEntryPoint = async (entryPointId: string) => {
  entryPointStore.selectEntryPoint(entryPointId)
  // Load the node in the graph viewer
  await graphStore.traverse(entryPointId, 3)
  graphStore.selectNode(entryPointId)
}

const getConfidenceColor = (score: number): string => {
  if (score >= 2.0) return 'text-success'
  if (score >= 1.0) return 'text-warning'
  if (score >= 0.5) return 'text-info'
  return 'text-gray-500'
}

const getConfidenceLevel = (score: number): string => {
  if (score >= 2.0) return 'Very High'
  if (score >= 1.0) return 'High'
  if (score >= 0.5) return 'Medium'
  return 'Low'
}

const refreshEntryPoints = async () => {
  entryPointStore.setConfidenceThreshold(confidenceThreshold.value)
  entryPointStore.setLimit(entryLimit.value)
  await loadEntryPoints()
}

onMounted(() => {
  loadEntryPoints()
})
</script>

<template>
  <div class="entry-point-explorer">
    <div class="card bg-base-100 shadow-xl">
      <div class="card-body p-4">
        <div class="flex items-center justify-between mb-4">
          <h2 class="card-title text-lg">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
            </svg>
            Entry Point Explorer
          </h2>
          <div class="flex gap-2">
            <button 
              @click="showFilters = !showFilters"
              class="btn btn-sm btn-ghost"
            >
              <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 4a1 1 0 011-1h16a1 1 0 011 1v2.586a1 1 0 01-.293.707l-6.414 6.414a1 1 0 00-.293.707V17l-4 4v-6.586a1 1 0 00-.293-.707L3.293 7.293A1 1 0 013 6.586V4z" />
              </svg>
            </button>
            <button 
              @click="refreshEntryPoints"
              class="btn btn-sm btn-ghost"
              :disabled="isLoading"
            >
              <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
              </svg>
            </button>
          </div>
        </div>

        <!-- Filters -->
        <div v-if="showFilters" class="mb-4 p-3 bg-base-200 rounded-lg">
          <div class="grid grid-cols-1 md:grid-cols-2 gap-3">
            <div class="form-control">
              <label class="label">
                <span class="label-text text-sm">Confidence Threshold</span>
              </label>
              <select 
                v-model="confidenceThreshold" 
                class="select select-bordered select-sm"
                @change="refreshEntryPoints"
              >
                <option 
                  v-for="level in confidenceLevels" 
                  :key="level.value" 
                  :value="level.value"
                >
                  {{ level.label }}
                </option>
              </select>
            </div>
            
            <div class="form-control">
              <label class="label">
                <span class="label-text text-sm">Limit</span>
              </label>
              <select 
                v-model="entryLimit" 
                class="select select-bordered select-sm"
                @change="refreshEntryPoints"
              >
                <option :value="10">10 entries</option>
                <option :value="25">25 entries</option>
                <option :value="50">50 entries</option>
                <option :value="100">100 entries</option>
              </select>
            </div>
          </div>
        </div>

        <!-- Stats -->
        <div class="stats stats-vertical md:stats-horizontal w-full mb-4">
          <div class="stat">
            <div class="stat-title text-xs">Total Entry Points</div>
            <div class="stat-value text-2xl">{{ entryPointStore.entryPoints.length }}</div>
            <div class="stat-desc text-xs">detected</div>
          </div>
          <div class="stat">
            <div class="stat-title text-xs">High Confidence</div>
            <div class="stat-value text-2xl">{{ entryPointStore.highConfidenceEntries.length }}</div>
            <div class="stat-desc text-xs">score ≥ 2.0</div>
          </div>
          <div class="stat">
            <div class="stat-title text-xs">Languages</div>
            <div class="stat-value text-2xl">{{ Object.keys(entryPointStore.entryPointsByLanguage).length }}</div>
            <div class="stat-desc text-xs">detected</div>
          </div>
        </div>

        <!-- Loading State -->
        <div v-if="isLoading" class="flex justify-center py-8">
          <LoadingSpinner />
        </div>

        <!-- Error State -->
        <div v-else-if="entryPointStore.error" class="alert alert-error">
          <svg xmlns="http://www.w3.org/2000/svg" class="stroke-current shrink-0 h-6 w-6" fill="none" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <span>{{ entryPointStore.error }}</span>
        </div>

        <!-- Empty State -->
        <div v-else-if="entryPointStore.entryPoints.length === 0" class="text-center py-8">
          <svg xmlns="http://www.w3.org/2000/svg" class="h-12 w-12 mx-auto text-base-content/30 mb-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
          </svg>
          <p class="text-base-content/70">No entry points detected</p>
          <button @click="refreshEntryPoints" class="btn btn-sm btn-primary mt-2">Scan Again</button>
        </div>

        <!-- Entry Points List -->
        <div v-else class="space-y-4">
          <div 
            v-for="(entryPoints, language) in groupedByLanguage" 
            :key="language"
            class="collapse collapse-arrow bg-base-200"
          >
            <input type="checkbox" class="peer" checked /> 
            <div class="collapse-title font-medium flex items-center gap-2">
              <span class="text-lg">{{ languageIcons[language] || '📄' }}</span>
              <span class="capitalize">{{ language }}</span>
              <div class="badge badge-sm">{{ entryPoints.length }}</div>
            </div>
            <div class="collapse-content">
              <div class="space-y-2">
                <div
                  v-for="entryPoint in entryPoints"
                  :key="entryPoint.id"
                  class="card bg-base-100 border border-base-300 hover:border-primary transition-colors cursor-pointer"
                  :class="{ 'border-primary': entryPointStore.selectedEntryPointId === entryPoint.id }"
                  @click="selectEntryPoint(entryPoint.id)"
                >
                  <div class="card-body p-3">
                    <div class="flex justify-between items-start">
                      <div class="flex-1 min-w-0">
                        <h3 class="font-medium truncate">{{ entryPoint.name }}</h3>
                        <p class="text-sm text-base-content/70 truncate">{{ entryPoint.file_path }}</p>
                        <div class="flex items-center gap-2 mt-1">
                          <span class="text-xs px-2 py-1 rounded-full bg-base-300">
                            Line {{ entryPoint.line_number }}
                          </span>
                          <span class="text-xs px-2 py-1 rounded-full bg-accent text-accent-content">
                            {{ entryPoint.pattern_matched }}
                          </span>
                        </div>
                      </div>
                      <div class="flex flex-col items-end ml-2">
                        <div class="badge badge-sm" :class="getConfidenceColor(entryPoint.confidence_score)">
                          {{ entryPoint.confidence_score.toFixed(1) }}
                        </div>
                        <span class="text-xs text-base-content/50 mt-1">
                          {{ getConfidenceLevel(entryPoint.confidence_score) }}
                        </span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.entry-point-explorer {
  height: 100%;
  overflow-y: auto;
}
</style>