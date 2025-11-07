<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useGraphStore } from './stores/graphStore'
import ForceGraphViewer from './components/ForceGraphViewer.vue'
import ConnectionsList from './components/ConnectionsList.vue'
import NodeBrowser from './components/NodeBrowser.vue'
import NodeDetails from './components/NodeDetails.vue'
import SearchBar from './components/SearchBar.vue'
import ToolPanel from './components/ToolPanel.vue'
import EntryPointExplorer from './components/EntryPointExplorer.vue'
import RelationshipBrowser from './components/RelationshipBrowser.vue'
import LoadingSpinner from './components/LoadingSpinner.vue'

const graphStore = useGraphStore()
const activeTab = ref('force-graph')
const selectedNodeId = ref<string | null>(null)
const showStats = ref(false)

const tabs = [
  { id: 'force-graph', name: 'Force Graph', icon: '🌐', component: 'force-graph' },
  { id: 'connections', name: 'Connections', icon: '🔗', component: 'connections' },
  { id: 'browser', name: 'Browse Nodes', icon: '📂', component: 'browser' },
  { id: 'entry-points', name: 'Entry Points', icon: '🚀', component: 'entry-points' },
  { id: 'query', name: 'Query Tools', icon: '🔍', component: 'query' },
]

const graphData = computed(() => ({
  nodes: graphStore.nodes,
  relationships: graphStore.relationships
}))

const stats = computed(() => ({
  totalNodes: graphStore.nodes.length,
  totalEdges: graphStore.relationships.length,
  languages: [...new Set(graphStore.nodes.map(n => n.language).filter(Boolean))],
  nodeTypes: [...new Set(graphStore.nodes.map(n => n.node_type))],
}))

function handleNodeClick(node: any) {
  selectedNodeId.value = node.id
  // Switch to connections view if not already there
  if (activeTab.value === 'force-graph') {
    activeTab.value = 'connections'
  }
}

function handleReanalyze() {
  if (confirm('Re-analyze the entire codebase? This may take a moment.')) {
    graphStore.reanalyze()
  }
}

onMounted(async () => {
  await graphStore.loadStats()
  // Load initial graph data if not already loaded
  if (graphStore.nodes.length === 0) {
    await graphStore.loadFullGraph()
  }
})
</script>

<template>
  <div class="app-container flex flex-col h-screen bg-base-200">
    <!-- Header -->
    <header class="bg-base-100 shadow-lg z-10">
      <div class="navbar bg-base-100 min-h-16">
        <div class="flex-1">
          <h1 class="text-2xl font-bold bg-gradient-to-r from-primary to-accent bg-clip-text text-transparent">
            Code Graph Explorer
          </h1>
        </div>
        
        <div class="flex-none gap-2">
          <!-- Stats Button -->
          <button 
            @click="showStats = !showStats"
            class="btn btn-ghost btn-sm gap-2"
            title="Graph Statistics"
          >
            <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
            </svg>
            <span class="hidden sm:inline">{{ stats.totalNodes }} nodes</span>
          </button>
          
          <!-- Re-analyze Button -->
          <button 
            @click="handleReanalyze"
            class="btn btn-primary btn-sm gap-2"
            title="Re-analyze Codebase"
          >
            <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
            </svg>
            <span class="hidden sm:inline">Re-analyze</span>
          </button>
          
          <SearchBar />
        </div>
      </div>
      
      <!-- Stats Panel (collapsible) -->
      <div v-if="showStats" class="bg-base-200 px-4 py-3 border-t border-base-300">
        <div class="stats stats-horizontal shadow w-full">
          <div class="stat">
            <div class="stat-title">Total Nodes</div>
            <div class="stat-value text-primary">{{ stats.totalNodes }}</div>
          </div>
          <div class="stat">
            <div class="stat-title">Relationships</div>
            <div class="stat-value text-secondary">{{ stats.totalEdges }}</div>
          </div>
          <div class="stat">
            <div class="stat-title">Languages</div>
            <div class="stat-value text-accent">{{ stats.languages.length }}</div>
            <div class="stat-desc">{{ stats.languages.join(', ') }}</div>
          </div>
          <div class="stat">
            <div class="stat-title">Node Types</div>
            <div class="stat-value">{{ stats.nodeTypes.length }}</div>
          </div>
        </div>
      </div>
      
      <!-- Tabs -->
      <div class="tabs tabs-boxed bg-base-100 px-4 py-2 flex-nowrap overflow-x-auto">
        <button
          v-for="tab in tabs"
          :key="tab.id"
          class="tab gap-2"
          :class="{ 'tab-active': activeTab === tab.id }"
          @click="activeTab = tab.id"
        >
          <span class="text-lg">{{ tab.icon }}</span>
          <span class="hidden sm:inline">{{ tab.name }}</span>
        </button>
      </div>
    </header>

    <!-- Main Content Area -->
    <div class="flex-1 flex overflow-hidden">
      
      <!-- Main Panel (changes based on active tab) -->
      <div class="flex-1 flex flex-col bg-base-300">
        
        <!-- Force Graph View -->
        <div v-show="activeTab === 'force-graph'" class="w-full h-full">
          <ForceGraphViewer 
            v-if="graphData.nodes.length > 0"
            :graph-data="graphData"
            :selected-node-id="selectedNodeId"
            @node-click="handleNodeClick"
          />
          <div v-else class="flex items-center justify-center h-full">
            <LoadingSpinner message="Loading graph data..." />
          </div>
        </div>
        
        <!-- Connections List View -->
        <div v-show="activeTab === 'connections'" class="w-full h-full overflow-auto">
          <ConnectionsList :node-id="selectedNodeId" />
        </div>
        
        <!-- Node Browser View -->
        <div v-show="activeTab === 'browser'" class="w-full h-full overflow-auto p-4">
          <NodeBrowser />
        </div>
        
        <!-- Entry Points View -->
        <div v-show="activeTab === 'entry-points'" class="w-full h-full overflow-auto p-4">
          <EntryPointExplorer />
        </div>
        
        <!-- Query Tools View -->
        <div v-show="activeTab === 'query'" class="w-full h-full overflow-auto p-4">
          <ToolPanel />
        </div>
        
      </div>

      <!-- Right Sidebar - Node Details (collapsible) -->
      <div 
        v-if="selectedNodeId"
        class="w-80 bg-base-100 border-l border-base-300 flex flex-col overflow-hidden"
      >
        <div class="p-4 border-b border-base-300 flex justify-between items-center">
          <h3 class="font-bold">Node Details</h3>
          <button 
            @click="selectedNodeId = null"
            class="btn btn-ghost btn-xs btn-circle"
          >
            ✕
          </button>
        </div>
        <div class="flex-1 overflow-y-auto">
          <NodeDetails :node-id="selectedNodeId" />
        </div>
      </div>
    </div>
  </div>
</template>

<style>
/* Global scrollbar styling */
::-webkit-scrollbar {
  width: 8px;
  height: 8px;
}

::-webkit-scrollbar-track {
  background: rgba(0, 0, 0, 0.1);
}

::-webkit-scrollbar-thumb {
  background: rgba(129, 140, 248, 0.5);
  border-radius: 4px;
}

::-webkit-scrollbar-thumb:hover {
  background: rgba(129, 140, 248, 0.7);
}

.app-container {
  font-family: Inter, system-ui, Avenir, Helvetica, Arial, sans-serif;
}

/* Smooth tab transitions */
.tabs .tab {
  transition: all 0.2s ease;
}

.tabs .tab-active {
  background: linear-gradient(135deg, #818cf8 0%, #f472b6 100%);
  color: white;
}
</style>
