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
  const nodes = graphStore.nodeArray || []
  nodes.forEach((n) => types.add(n.type))
  return Array.from(types).sort()
})

const toggleLanguage = (lang: string) => {
  const idx = graphStore.languages.indexOf(lang)
  if (idx === -1) {
    graphStore.languages.push(lang)
  } else {
    graphStore.languages.splice(idx, 1)
  }
  graphStore.setLanguages([...graphStore.languages])
}

const toggleNodeType = (type: string) => {
  const idx = graphStore.nodeTypes.indexOf(type)
  if (idx === -1) {
    graphStore.nodeTypes.push(type)
  } else {
    graphStore.nodeTypes.splice(idx, 1)
  }
  graphStore.setNodeTypes([...graphStore.nodeTypes])
}

const applyFilters = () => {
  console.log('Filters applied:', {
    languages: graphStore.languages,
    nodeTypes: graphStore.nodeTypes,
    seamOnly: graphStore.seamOnly,
    complexity: graphStore.complexityRange,
  })
}

const clearFilters = () => {
  graphStore.setLanguages([])
  graphStore.setNodeTypes([])
  graphStore.setSeamOnly(false)
  graphStore.setComplexityRange([0, 50])
  graphStore.setSearchQuery('')
}
</script>

<template>
  <div class="p-6 space-y-6">
    <div class="flex items-center justify-between">
      <h3 class="text-xl font-bold text-base-content flex items-center gap-2">
        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" class="w-6 h-6 stroke-current">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 4a1 1 0 011-1h16a1 1 0 011 1v2.586a1 1 0 01-.293.707l-6.414 6.414a1 1 0 00-.293.707V17l-4 4v-6.586a1 1 0 00-.293-.707L3.293 7.293A1 1 0 013 6.586V4z" />
        </svg>
        Filters
      </h3>
    </div>

    <div class="divider my-0"></div>

    <div class="form-control">
      <label class="label">
        <span class="label-text font-semibold">Languages</span>
        <span class="label-text-alt badge badge-ghost">{{ filterStore.languages.length }} selected</span>
      </label>
      <div class="card bg-base-100 shadow-sm max-h-60 overflow-y-auto">
        <div class="card-body p-3 space-y-2">
          <label v-for="lang in availableLanguages" :key="lang" class="label cursor-pointer justify-start gap-3 py-2 hover:bg-base-200 rounded-lg px-2">
            <input
              :checked="filterStore.languages.includes(lang)"
              @change="toggleLanguage(lang)"
              type="checkbox"
              class="checkbox checkbox-primary checkbox-sm"
            />
            <span class="label-text flex-1">{{ lang }}</span>
            <span class="badge badge-primary badge-sm">{{ graphStore.stats?.languages[lang] || 0 }}</span>
          </label>
        </div>
      </div>
    </div>

    <div class="form-control">
      <label class="label">
        <span class="label-text font-semibold">Node Types</span>
        <span class="label-text-alt badge badge-ghost">{{ filterStore.nodeTypes.length }} selected</span>
      </label>
      <div class="card bg-base-100 shadow-sm max-h-48 overflow-y-auto">
        <div class="card-body p-3 space-y-2">
          <label v-for="type in availableNodeTypes" :key="type" class="label cursor-pointer justify-start gap-3 py-2 hover:bg-base-200 rounded-lg px-2">
            <input
              :checked="filterStore.nodeTypes.includes(type)"
              @change="toggleNodeType(type)"
              type="checkbox"
              class="checkbox checkbox-secondary checkbox-sm"
            />
            <span class="label-text font-mono text-sm">{{ type }}</span>
          </label>
        </div>
      </div>
    </div>

    <div class="form-control">
      <label class="label cursor-pointer">
        <div class="flex items-center gap-2">
          <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" class="w-5 h-5 stroke-current text-accent">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" />
          </svg>
          <span class="label-text font-semibold">SEAM relationships only</span>
        </div>
        <input v-model="filterStore.seamOnly" type="checkbox" class="toggle toggle-accent" />
      </label>
    </div>

    <div class="form-control">
      <label class="label">
        <span class="label-text font-semibold">Complexity Range</span>
        <span class="label-text-alt badge badge-info">
          {{ filterStore.complexityRange[0] }} - {{ filterStore.complexityRange[1] }}
        </span>
      </label>
      <div class="space-y-3">
        <div>
          <div class="flex justify-between text-xs text-base-content/60 mb-1">
            <span>Min: {{ filterStore.complexityRange[0] }}</span>
            <span>0 - 50</span>
          </div>
          <input
            v-model.number="filterStore.complexityRange[0]"
            type="range"
            min="0"
            max="50"
            class="range range-primary range-sm"
          />
        </div>
        <div>
          <div class="flex justify-between text-xs text-base-content/60 mb-1">
            <span>Max: {{ filterStore.complexityRange[1] }}</span>
            <span>0 - 50</span>
          </div>
          <input
            v-model.number="filterStore.complexityRange[1]"
            type="range"
            min="0"
            max="50"
            class="range range-secondary range-sm"
          />
        </div>
      </div>
    </div>

    <div class="divider my-2"></div>

    <div class="flex gap-2">
      <button @click="applyFilters" class="btn btn-primary flex-1 gap-2">
        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" class="w-5 h-5 stroke-current">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
        </svg>
        Apply
      </button>
      <button @click="clearFilters" class="btn btn-ghost flex-1 gap-2">
        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" class="w-5 h-5 stroke-current">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
        </svg>
        Clear
      </button>
    </div>
  </div>
</template>
