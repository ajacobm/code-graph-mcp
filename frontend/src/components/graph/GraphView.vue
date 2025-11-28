<script setup lang="ts">
import { ref, onMounted, computed, watch } from 'vue'
import ForceGraphVue from './ForceGraph.vue'
import GraphControls from './GraphControls.vue'
import NodeDetails from './NodeDetails.vue'
import type { GraphData, ForceGraphNode, GraphExportResponse } from '../../types/forceGraph'
import { graphClient } from '../../api/graphClient'

const props = defineProps<{
  autoLoad?: boolean
}>()

const emit = defineEmits<{
  nodeSelected: [nodeId: string]
}>()

// State
const graphData = ref<GraphData | null>(null)
const isLoading = ref(false)
const error = ref<string | null>(null)
const selectedNode = ref<ForceGraphNode | null>(null)
const hoveredNode = ref<ForceGraphNode | null>(null)
const highlightedNodeIds = ref<string[]>([])

// Display options
const showLabels = ref(true)
const colorByLanguage = ref(false)
const colorByType = ref(true)

// Filter state
const languageFilter = ref<string | null>(null)
const typeFilter = ref<string | null>(null)
const searchQuery = ref('')

// Reference to ForceGraph component
const forceGraphRef = ref<InstanceType<typeof ForceGraphVue> | null>(null)

// Stats
const stats = computed(() => graphData.value?.stats || null)

const availableLanguages = computed(() => {
  if (!stats.value?.languages) return []
  return Object.keys(stats.value.languages).sort()
})

const availableTypes = computed(() => {
  if (!stats.value?.nodeTypes) return []
  return Object.keys(stats.value.nodeTypes).sort()
})

// Filter the search results for highlighting
const filteredNodeIds = computed(() => {
  if (!searchQuery.value || !graphData.value) return []
  const query = searchQuery.value.toLowerCase()
  return graphData.value.nodes
    .filter(n => n.name.toLowerCase().includes(query))
    .map(n => n.id)
})

// Watch search query to update highlights
watch(searchQuery, (query) => {
  if (query) {
    highlightedNodeIds.value = filteredNodeIds.value
  } else {
    highlightedNodeIds.value = []
  }
})

async function loadGraph() {
  isLoading.value = true
  error.value = null
  
  try {
    const url = `${graphClient.baseURL}/graph/export`
    const params = new URLSearchParams()
    params.set('limit', '5000')
    params.set('include_metadata', 'true')
    if (languageFilter.value) {
      params.set('language', languageFilter.value)
    }
    if (typeFilter.value) {
      params.set('node_type', typeFilter.value)
    }
    
    const response = await fetch(`${url}?${params.toString()}`)
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`)
    }
    
    const data: GraphExportResponse = await response.json()
    
    graphData.value = {
      nodes: data.nodes,
      links: data.links,
      stats: data.stats
    }
    
    // Zoom to fit after loading
    setTimeout(() => {
      forceGraphRef.value?.zoomToFit()
    }, 500)
    
  } catch (err) {
    error.value = err instanceof Error ? err.message : 'Failed to load graph'
    console.error('Error loading graph:', err)
  } finally {
    isLoading.value = false
  }
}

function handleNodeClick(node: ForceGraphNode) {
  selectedNode.value = node
  emit('nodeSelected', node.id)
}

function handleNodeHover(node: ForceGraphNode | null) {
  hoveredNode.value = node
}

function handleBackgroundClick() {
  selectedNode.value = null
}

function handleZoomToFit() {
  forceGraphRef.value?.zoomToFit()
}

function handleCenterNode(nodeId: string) {
  forceGraphRef.value?.centerNode(nodeId)
}

function handleShowConnections(nodeId: string) {
  emit('nodeSelected', nodeId)
}

function clearFilters() {
  languageFilter.value = null
  typeFilter.value = null
  searchQuery.value = ''
  highlightedNodeIds.value = []
}

onMounted(() => {
  if (props.autoLoad !== false) {
    loadGraph()
  }
})

// Expose methods to parent
defineExpose({
  loadGraph,
  zoomToFit: handleZoomToFit
})
</script>

<template>
  <div class="graph-view flex flex-col h-full">
    <!-- Top Bar with Controls -->
    <div class="flex items-center justify-between gap-4 p-3 bg-slate-800/80 border-b border-slate-700">
      <!-- Left: Controls -->
      <div class="flex items-center gap-3">
        <GraphControls
          :show-labels="showLabels"
          :color-by-language="colorByLanguage"
          :color-by-type="colorByType"
          :is-loading="isLoading"
          @update:show-labels="showLabels = $event"
          @update:color-by-language="colorByLanguage = $event"
          @update:color-by-type="colorByType = $event"
          @zoom-to-fit="handleZoomToFit"
          @refresh="loadGraph"
        />

        <!-- Divider -->
        <div class="w-px h-6 bg-slate-600"></div>

        <!-- Search -->
        <div class="form-control">
          <input
            v-model="searchQuery"
            type="text"
            placeholder="Search nodes..."
            class="input input-sm input-bordered bg-slate-900 w-48"
          />
        </div>

        <!-- Language Filter -->
        <select 
          v-model="languageFilter"
          class="select select-sm select-bordered bg-slate-900"
          @change="loadGraph"
        >
          <option :value="null">All Languages</option>
          <option v-for="lang in availableLanguages" :key="lang" :value="lang">
            {{ lang }}
          </option>
        </select>

        <!-- Type Filter -->
        <select 
          v-model="typeFilter"
          class="select select-sm select-bordered bg-slate-900"
          @change="loadGraph"
        >
          <option :value="null">All Types</option>
          <option v-for="type in availableTypes" :key="type" :value="type">
            {{ type }}
          </option>
        </select>

        <!-- Clear Filters -->
        <button 
          v-if="languageFilter || typeFilter || searchQuery"
          @click="clearFilters(); loadGraph()"
          class="btn btn-sm btn-ghost"
        >
          ✕ Clear
        </button>
      </div>

      <!-- Right: Stats -->
      <div v-if="stats" class="flex items-center gap-4 text-sm text-slate-400">
        <span>
          <span class="font-semibold text-slate-200">{{ stats.totalNodes }}</span> nodes
        </span>
        <span>
          <span class="font-semibold text-slate-200">{{ stats.totalLinks }}</span> edges
        </span>
        <span v-if="highlightedNodeIds.length > 0" class="text-yellow-400">
          {{ highlightedNodeIds.length }} matches
        </span>
      </div>
    </div>

    <!-- Main Graph Area -->
    <div class="flex-1 relative">
      <!-- Loading State -->
      <div 
        v-if="isLoading"
        class="absolute inset-0 flex items-center justify-center bg-slate-900/80 z-10"
      >
        <div class="text-center">
          <span class="loading loading-spinner loading-lg text-primary"></span>
          <p class="mt-2 text-slate-300">Loading graph...</p>
        </div>
      </div>

      <!-- Error State -->
      <div 
        v-if="error && !isLoading"
        class="absolute inset-0 flex items-center justify-center bg-slate-900/80 z-10"
      >
        <div class="alert alert-error max-w-md">
          <svg xmlns="http://www.w3.org/2000/svg" class="stroke-current shrink-0 h-6 w-6" fill="none" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <div>
            <h3 class="font-bold">Error loading graph</h3>
            <div class="text-sm">{{ error }}</div>
          </div>
          <button @click="loadGraph" class="btn btn-sm">Retry</button>
        </div>
      </div>

      <!-- Force Graph -->
      <ForceGraphVue
        ref="forceGraphRef"
        :graph-data="graphData"
        :selected-node-id="selectedNode?.id"
        :highlighted-node-ids="highlightedNodeIds"
        :show-labels="showLabels"
        :color-by-language="colorByLanguage"
        :color-by-type="colorByType"
        @node-click="handleNodeClick"
        @node-hover="handleNodeHover"
        @background-click="handleBackgroundClick"
      />

      <!-- Node Details Panel (floating) -->
      <div 
        v-if="selectedNode"
        class="absolute top-4 right-4 z-20"
      >
        <NodeDetails
          :node="selectedNode"
          @close="selectedNode = null"
          @navigate="handleCenterNode"
          @show-connections="handleShowConnections"
        />
      </div>

      <!-- Hover Tooltip -->
      <div
        v-if="hoveredNode && hoveredNode !== selectedNode"
        class="absolute bottom-4 left-4 z-20 p-3 bg-slate-800/90 border border-slate-600 rounded-lg text-sm max-w-xs"
      >
        <div class="font-bold text-slate-100">{{ hoveredNode.name }}</div>
        <div class="text-slate-400">{{ hoveredNode.nodeType }} | {{ hoveredNode.language }}</div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.graph-view {
  min-height: 500px;
}
</style>
