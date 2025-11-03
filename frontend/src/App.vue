<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useGraphStore } from './stores/graphStore'
import GraphViewer from './components/GraphViewer.vue'
import NodeBrowser from './components/NodeBrowser.vue'
import NodeDetails from './components/NodeDetails.vue'
import SearchBar from './components/SearchBar.vue'
import FilterPanel from './components/FilterPanel.vue'
import ToolPanel from './components/ToolPanel.vue'
import TraversalControls from './components/TraversalControls.vue'
import CallChainTracer from './components/CallChainTracer.vue'
import RelationshipBrowser from './components/RelationshipBrowser.vue'
import AdminPanel from './components/AdminPanel.vue'
import EntryPointExplorer from './components/EntryPointExplorer.vue'
import LoadingSpinner from './components/LoadingSpinner.vue'

const graphStore = useGraphStore()
const activeTab = ref('graph')
const showAdmin = ref(false)

const tabs = [
  { id: 'graph', name: 'Graph View', icon: '📊' },
  { id: 'browser', name: 'Node Browser', icon: '📂' },
  { id: 'entry-points', name: 'Entry Points', icon: '🚀' },
  { id: 'relationships', name: 'Relationships', icon: '🔗' },
  { id: 'call-chain', name: 'Call Chain', icon: 'CALLTYPE' },
]

onMounted(() => {
  graphStore.initialize()
})
</script>

<template>
  <div class="app-container flex flex-col h-screen bg-base-200">
    <!-- Header -->
    <header class="bg-base-100 shadow-lg z-10">
      <div class="navbar bg-base-100">
        <div class="flex-1">
          <h1 class="text-xl font-bold bg-gradient-to-r from-primary to-accent bg-clip-text text-transparent">
            Code Graph Visualizer
          </h1>
        </div>
        
        <div class="flex-none gap-2">
          <SearchBar />
          <button 
            @click="showAdmin = !showAdmin"
            class="btn btn-ghost btn-sm"
            title="Admin Panel"
          >
            <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
            </svg>
          </button>
        </div>
      </div>
      
      <!-- Tabs -->
      <div class="tabs tabs-bordered px-4">
        <button
          v-for="tab in tabs"
          :key="tab.id"
          class="tab"
          :class="{ 'tab-active': activeTab === tab.id }"
          @click="activeTab = tab.id"
        >
          <span class="mr-2">{{ tab.icon }}</span>
          {{ tab.name }}
        </button>
      </div>
    </header>

    <!-- Main Content -->
    <div class="flex-1 flex overflow-hidden">
      <!-- Left Sidebar -->
      <div class="w-80 bg-base-100 border-r border-base-300 flex flex-col">
        <div class="p-4 border-b border-base-300">
          <FilterPanel />
        </div>
        
        <div class="flex-1 overflow-y-auto">
          <div v-if="activeTab === 'graph'" class="p-4">
            <TraversalControls />
          </div>
          
          <div v-else-if="activeTab === 'browser'" class="p-4">
            <NodeBrowser />
          </div>
          
          <div v-else-if="activeTab === 'entry-points'" class="p-4">
            <EntryPointExplorer />
          </div>
          
          <div v-else-if="activeTab === 'relationships'" class="p-4">
            <RelationshipBrowser />
          </div>
          
          <div v-else-if="activeTab === 'call-chain'" class="p-4">
            <CallChainTracer />
          </div>
        </div>
      </div>

      <!-- Main Graph Area -->
      <div class="flex-1 relative">
        <div v-if="graphStore.isLoading" class="absolute inset-0 flex items-center justify-center bg-base-200 bg-opacity-70 z-50">
          <LoadingSpinner />
        </div>
        
        <GraphViewer v-if="activeTab === 'graph'" class="w-full h-full" />
        
        <div v-else-if="activeTab === 'browser'" class="w-full h-full flex items-center justify-center bg-base-100">
          <div class="text-center">
            <div class="text-5xl mb-4">📂</div>
            <h2 class="text-xl font-semibold mb-2">Node Browser</h2>
            <p class="text-base-content/70">Switch to Graph View to visualize the code structure</p>
          </div>
        </div>
        
        <div v-else-if="activeTab === 'entry-points'" class="w-full h-full flex items-center justify-center bg-base-100">
          <div class="text-center">
            <div class="text-5xl mb-4">🚀</div>
            <h2 class="text-xl font-semibold mb-2">Entry Point Explorer</h2>
            <p class="text-base-content/70">Switch to Graph View to visualize the code structure</p>
          </div>
        </div>
        
        <div v-else-if="activeTab === 'relationships'" class="w-full h-full flex items-center justify-center bg-base-100">
          <div class="text-center">
            <div class="text-5xl mb-4">🔗</div>
            <h2 class="text-xl font-semibold mb-2">Relationship Browser</h2>
            <p class="text-base-content/70">Switch to Graph View to visualize the code structure</p>
          </div>
        </div>
        
        <div v-else-if="activeTab === 'call-chain'" class="w-full h-full flex items-center justify-center bg-base-100">
          <div class="text-center">
            <div class="text-5xl mb-4">CALLTYPE</div>
            <h2 class="text-xl font-semibold mb-2">Call Chain Tracer</h2>
            <p class="text-base-content/70">Switch to Graph View to visualize the code structure</p>
          </div>
        </div>
      </div>

      <!-- Right Sidebar -->
      <div class="w-80 bg-base-100 border-l border-base-300 flex flex-col">
        <div class="flex-1 overflow-y-auto">
          <ToolPanel class="p-4" />
          <NodeDetails v-if="graphStore.selectedNodeId" class="p-4 border-t border-base-300" />
        </div>
      </div>
    </div>

    <!-- Admin Panel Overlay -->
    <div v-if="showAdmin" class="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center">
      <div class="bg-base-100 rounded-lg shadow-xl w-full max-w-2xl max-h-[90vh] overflow-y-auto">
        <div class="p-6">
          <div class="flex justify-between items-center mb-4">
            <h2 class="text-xl font-bold">Admin Panel</h2>
            <button @click="showAdmin = false" class="btn btn-sm btn-circle">
              <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
          <AdminPanel />
        </div>
      </div>
    </div>

    <!-- Global Error Message -->
    <div v-if="graphStore.error" class="toast toast-top toast-center">
      <div class="alert alert-error">
        <span>{{ graphStore.error }}</span>
      </div>
    </div>
  </div>
</template>

<style>
.app-container {
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, 'Open Sans', 'Helvetica Neue', sans-serif;
}

body {
  margin: 0;
  padding: 0;
  overflow: hidden;
}
</style>