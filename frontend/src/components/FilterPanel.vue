<script setup lang="ts">
import { ref, computed } from 'vue'
import { useGraphStore } from '../stores/graphStore'
import { useFilterStore } from '../stores/filterStore'

const graphStore = useGraphStore()
const filterStore = useFilterStore()

const availableLanguages = computed(() => {
  return Object.keys(graphStore.stats?.languages || {}).sort()
})

const availableNodeTypes = computed(() => {
  const types = new Set<string>()
  graphStore.nodeArray.forEach((n) => types.add(n.type))
  return Array.from(types).sort()
})

const toggleLanguage = (lang: string) => {
  const idx = filterStore.languages.indexOf(lang)
  if (idx === -1) {
    filterStore.languages.push(lang)
  } else {
    filterStore.languages.splice(idx, 1)
  }
}

const toggleNodeType = (type: string) => {
  const idx = filterStore.nodeTypes.indexOf(type)
  if (idx === -1) {
    filterStore.nodeTypes.push(type)
  } else {
    filterStore.nodeTypes.splice(idx, 1)
  }
}

const applyFilters = () => {
  // TODO: implement graph filtering
  console.log('Filters applied:', {
    languages: filterStore.languages,
    nodeTypes: filterStore.nodeTypes,
    seamOnly: filterStore.seamOnly,
    complexity: filterStore.complexityRange,
  })
}

const clearFilters = () => {
  filterStore.reset()
}
</script>

<template>
  <div class="bg-gray-800 border-b border-gray-700 p-4 overflow-y-auto max-h-96">
    <h3 class="text-sm font-bold text-white mb-4">Filters</h3>

    <div class="mb-4">
      <label class="text-xs text-gray-300 font-semibold block mb-2">Languages</label>
      <div class="space-y-1 max-h-40 overflow-y-auto">
        <label v-for="lang in availableLanguages" :key="lang" class="flex items-center text-sm text-gray-300">
          <input
            :checked="filterStore.languages.includes(lang)"
            @change="toggleLanguage(lang)"
            type="checkbox"
            class="mr-2"
          />
          {{ lang }} ({{ graphStore.stats?.languages[lang] || 0 }})
        </label>
      </div>
    </div>

    <div class="mb-4">
      <label class="text-xs text-gray-300 font-semibold block mb-2">Node Types</label>
      <div class="space-y-1 max-h-40 overflow-y-auto">
        <label v-for="type in availableNodeTypes" :key="type" class="flex items-center text-sm text-gray-300">
          <input
            :checked="filterStore.nodeTypes.includes(type)"
            @change="toggleNodeType(type)"
            type="checkbox"
            class="mr-2"
          />
          {{ type }}
        </label>
      </div>
    </div>

    <div class="mb-4">
      <label class="flex items-center text-sm text-gray-300">
        <input v-model="filterStore.seamOnly" type="checkbox" class="mr-2" />
        SEAM relationships only
      </label>
    </div>

    <div class="mb-4">
      <label class="text-xs text-gray-300 font-semibold block mb-2">
        Complexity: {{ filterStore.complexityRange[0] }} - {{ filterStore.complexityRange[1] }}
      </label>
      <input
        v-model.number="filterStore.complexityRange[0]"
        type="range"
        min="0"
        max="50"
        class="w-full mb-2"
      />
      <input
        v-model.number="filterStore.complexityRange[1]"
        type="range"
        min="0"
        max="50"
        class="w-full"
      />
    </div>

    <div class="flex gap-2">
      <button
        @click="applyFilters"
        class="flex-1 px-3 py-2 bg-indigo-600 hover:bg-indigo-700 text-white text-sm rounded font-medium"
      >
        Apply
      </button>
      <button
        @click="clearFilters"
        class="flex-1 px-3 py-2 bg-gray-700 hover:bg-gray-600 text-white text-sm rounded font-medium"
      >
        Clear
      </button>
    </div>
  </div>
</template>
