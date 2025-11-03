import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { graphClient, type EntryPointResponse } from '../api/graphClient'

export const useEntryPointStore = defineStore('entryPoints', () => {
  const entryPoints = ref<EntryPointResponse[]>([])
  const isLoading = ref(false)
  const error = ref<string | null>(null)
  const selectedEntryPointId = ref<string | null>(null)
  const minConfidence = ref(0.5)
  const limit = ref(50)

  const selectedEntryPoint = computed(() => {
    if (!selectedEntryPointId.value) return null
    return entryPoints.value.find(ep => ep.id === selectedEntryPointId.value)
  })

  const highConfidenceEntries = computed(() => {
    return entryPoints.value.filter(ep => ep.confidence_score >= 2.0)
  })

  const entryPointsByLanguage = computed(() => {
    const byLanguage: Record<string, EntryPointResponse[]> = {}
    entryPoints.value.forEach(ep => {
      if (!byLanguage[ep.language]) {
        byLanguage[ep.language] = []
      }
      byLanguage[ep.language].push(ep)
    })
    return byLanguage
  })

  const loadEntryPoints = async () => {
    isLoading.value = true
    error.value = null
    
    try {
      const response = await graphClient.getEntryPoints(limit.value, minConfidence.value)
      entryPoints.value = response.entry_points
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Failed to load entry points'
      console.error('Failed to load entry points:', err)
    } finally {
      isLoading.value = false
    }
  }

  const selectEntryPoint = (id: string | null) => {
    selectedEntryPointId.value = id
  }

  const setConfidenceThreshold = (threshold: number) => {
    minConfidence.value = threshold
  }

  const setLimit = (newLimit: number) => {
    limit.value = newLimit
  }

  const clear = () => {
    entryPoints.value = []
    selectedEntryPointId.value = null
    error.value = null
  }

  return {
    // State
    entryPoints,
    isLoading,
    error,
    selectedEntryPointId,
    minConfidence,
    limit,
    
    // Getters
    selectedEntryPoint,
    highConfidenceEntries,
    entryPointsByLanguage,
    
    // Actions
    loadEntryPoints,
    selectEntryPoint,
    setConfidenceThreshold,
    setLimit,
    clear,
  }
})