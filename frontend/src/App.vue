<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useGraphStore } from './stores/graphStore'
import GraphViewer from './components/GraphViewer.vue'
import NodeDetails from './components/NodeDetails.vue'
import SearchBar from './components/SearchBar.vue'
import FilterPanel from './components/FilterPanel.vue'
import CallChainTracer from './components/CallChainTracer.vue'
import LoadingSpinner from './components/LoadingSpinner.vue'

const graphStore = useGraphStore()
const rootNode = ref('')
const showFilters = ref(false)
const errorDismissTimer = ref<NodeJS.Timeout | null>(null)

onMounted(async () => {
  await graphStore.loadStats()
  const stats = graphStore.stats
  if (stats && stats.top_functions.length > 0) {
    rootNode.value = stats.top_functions[0].id
    await graphStore.traverse(rootNode.value, 5)
  }
})

const loadFromNode = async () => {
  if (rootNode.value) {
    await graphStore.traverse(rootNode.value, 5)
  }
}

const loadCallChain = async () => {
  if (rootNode.value) {
    await graphStore.loadCallChain(rootNode.value, 10)
  }
}

const clearGraph = () => {
  graphStore.clearGraph()
}
</script>

<template>
  <div class="h-screen w-screen bg-gray-900 flex flex-col">
    <!-- Header -->
    <header class="bg-gray-950 border-b border-gray-700 px-6 py-4 flex items-center justify-between">
      <div>
        <h1 class="text-2xl font-bold text-white">Code Graph Visualizer</h1>
        <p v-if="graphStore.stats" class="text-sm text-gray-400">
          {{ graphStore.stats.total_nodes }} nodes • {{ graphStore.stats.total_relationships }} relationships
        </p>
      </div>

      <div class="flex items-center gap-3">
        <div class="w-64">
          <SearchBar />
        </div>
        <button
          @click="showFilters = !showFilters"
          class="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded font-medium text-sm"
        >
          {{ showFilters ? 'Hide' : 'Show' }} Filters
        </button>
        <button
          @click="clearGraph"
          class="px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded font-medium text-sm"
        >
          Clear
        </button>
      </div>
    </header>

    <!-- Main layout -->
    <div class="flex-1 flex overflow-hidden">
      <!-- Left sidebar: Filters -->
      <div v-if="showFilters" class="w-64 border-r border-gray-700 overflow-y-auto">
        <FilterPanel />
      </div>

      <!-- Center: Graph + Controls -->
      <div class="flex-1 flex flex-col overflow-hidden">
        <!-- Call chain tracer -->
        <CallChainTracer />

        <!-- Traverse controls -->
        <div v-if="graphStore.viewMode === 'full'" class="bg-gray-800 border-b border-gray-700 px-4 py-3 flex items-center gap-3">
          <input
            v-model="rootNode"
            type="text"
            placeholder="Enter node ID..."
            class="flex-1 px-3 py-2 bg-gray-700 text-white rounded focus:outline-none focus:ring-2 focus:ring-indigo-500 text-sm"
          />
          <button
            @click="loadFromNode"
            class="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded font-medium text-sm"
          >
            Traverse
          </button>
          <button
            @click="loadCallChain"
            class="px-4 py-2 bg-purple-600 hover:bg-purple-700 text-white rounded font-medium text-sm"
          >
            Call Chain
          </button>
        </div>

        <!-- Graph viewer -->
        <div class="flex-1 overflow-hidden">
          <GraphViewer />
        </div>
      </div>

      <!-- Right sidebar: Node details -->
      <div class="w-80 border-l border-gray-700 flex flex-col">
        <NodeDetails />
      </div>
    </div>

    <!-- Loading indicator -->
    <div v-if="graphStore.isLoading" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <LoadingSpinner message="Loading graph..." />
    </div>

    <!-- Error message -->
    <transition
      enter-active-class="transition duration-300 ease-out"
      enter-from-class="translate-x-full opacity-0"
      enter-to-class="translate-x-0 opacity-100"
      leave-active-class="transition duration-300 ease-in"
      leave-from-class="translate-x-0 opacity-100"
      leave-to-class="translate-x-full opacity-0"
    >
      <div
        v-if="graphStore.error"
        class="fixed bottom-4 right-4 bg-red-600 text-white px-6 py-4 rounded shadow-lg max-w-md"
      >
        <div class="flex items-center justify-between gap-4">
          <p>{{ graphStore.error }}</p>
          <button
            @click="graphStore.error = null"
            class="text-white hover:text-red-100 font-bold"
          >
            ×
          </button>
        </div>
      </div>
    </transition>
  </div>
</template>
