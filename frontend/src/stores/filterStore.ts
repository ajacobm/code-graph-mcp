import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useFilterStore = defineStore('filter', () => {
  const languages = ref<string[]>([])
  const nodeTypes = ref<string[]>([])
  const seamOnly = ref(false)
  const complexityRange = ref<[number, number]>([0, 50])
  const searchQuery = ref('')

  function setLanguages(langs: string[]) {
    languages.value = langs
  }

  function setNodeTypes(types: string[]) {
    nodeTypes.value = types
  }

  function setSeamOnly(value: boolean) {
    seamOnly.value = value
  }

  function setComplexityRange(range: [number, number]) {
    complexityRange.value = range
  }

  function setSearchQuery(query: string) {
    searchQuery.value = query
  }

  function reset() {
    languages.value = []
    nodeTypes.value = []
    seamOnly.value = false
    complexityRange.value = [0, 50]
    searchQuery.value = ''
  }

  return {
    languages,
    nodeTypes,
    seamOnly,
    complexityRange,
    searchQuery,
    setLanguages,
    setNodeTypes,
    setSeamOnly,
    setComplexityRange,
    setSearchQuery,
    reset,
  }
})
