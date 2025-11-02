<script setup lang="ts">
import { computed, ref } from 'vue'
import { useGraphStore } from './stores/graphStore'
import NodeBrowser from './components/NodeBrowser.vue'
import GraphViewer from './components/GraphViewer.vue'
import NodeDetails from './components/NodeDetails.vue'
import SearchBar from './components/SearchBar.vue'
import FilterPanel from './components/FilterPanel.vue'
import CallChainTracer from './components/CallChainTracer.vue'
import LoadingSpinner from './components/LoadingSpinner.vue'
import RelationshipBrowser from './components/RelationshipBrowser.vue'
import TraversalControls from './components/TraversalControls.vue'
import ToolPanel from './components/ToolPanel.vue'

const graphStore = useGraphStore()
const showFilters = ref(false)

const viewMode = computed(() => graphStore.nodeArray.length > 0 ? 'graph' : 'browse')
</script>

<template>
  <div class="h-screen w-screen bg-base-100 flex flex-col" data-theme="dark">
    <!-- Browse Mode -->
    <template v-if="viewMode === 'browse'">
      <NodeBrowser />
    </template>

    <!-- Graph Mode -->
    <template v-else>
      <header class="bg-base-200 border-b border-base-300 px-6 py-4 shadow-lg">
        <div class="flex items-center justify-between">
          <div>
            <h1 class="text-3xl font-bold bg-gradient-to-r from-primary to-secondary bg-clip-text text-transparent">
              Code Graph Visualizer
            </h1>
            <div v-if="graphStore.stats" class="flex items-center gap-4 mt-2">
              <div class="badge badge-primary badge-lg gap-2">
                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" class="w-4 h-4 stroke-current">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
                </svg>
                {{ graphStore.stats.total_nodes }} nodes
              </div>
              <div class="badge badge-secondary badge-lg gap-2">
                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" class="w-4 h-4 stroke-current">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                {{ graphStore.stats.total_relationships }} edges
              </div>
            </div>
          </div>

          <div class="flex items-center gap-3">
            <div class="w-72">
              <SearchBar />
            </div>
            <button @click="showFilters = !showFilters" class="btn btn-primary gap-2">
              <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" class="w-5 h-5 stroke-current">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 4a1 1 0 011-1h16a1 1 0 011 1v2.586a1 1 0 01-.293.707l-6.414 6.414a1 1 0 00-.293.707V17l-4 4v-6.586a1 1 0 00-.293-.707L3.293 7.293A1 1 0 013 6.586V4z" />
              </svg>
              {{ showFilters ? 'Hide' : 'Show' }} Filters
            </button>
            <button @click="graphStore.clearGraph" class="btn btn-error gap-2">
              <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" class="w-5 h-5 stroke-current">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
              </svg>
              Clear
            </button>
            <button @click="graphStore.clearGraph" class="btn btn-ghost gap-2">
              <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" class="w-5 h-5 stroke-current">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 19l-7-7m0 0l7-7m-7 7h18" />
              </svg>
              Back to Browse
            </button>
          </div>
        </div>
      </header>

      <div class="flex-1 flex overflow-hidden">
        <transition
          enter-active-class="transition-all duration-300 ease-out"
          enter-from-class="-translate-x-full opacity-0"
          enter-to-class="translate-x-0 opacity-100"
          leave-active-class="transition-all duration-300 ease-in"
          leave-from-class="translate-x-0 opacity-100"
          leave-to-class="-translate-x-full opacity-0"
        >
          <aside v-if="showFilters" class="w-80 bg-base-200 border-r border-base-300 overflow-y-auto shadow-xl">
            <FilterPanel />
          </aside>
        </transition>

        <main class="flex-1 flex flex-col overflow-hidden">
          <CallChainTracer />

          <div class="flex-1 overflow-hidden relative">
            <GraphViewer />
          </div>
        </main>

        <aside class="w-96 bg-base-200 border-l border-base-300 flex flex-col overflow-hidden shadow-xl">
          <div class="flex-1 overflow-y-auto">
            <div class="p-6 space-y-6">
              <div class="card bg-base-300 shadow-xl">
                <div class="card-body p-4">
                  <NodeDetails />
                </div>
              </div>

              <div class="card bg-base-300 shadow-xl">
                <div class="card-body p-4">
                  <ToolPanel />
                </div>
              </div>

              <div v-if="graphStore.selectedNode" class="card bg-base-300 shadow-xl">
                <div class="card-body p-4">
                  <RelationshipBrowser />
                </div>
              </div>

              <div v-if="graphStore.selectedNode" class="card bg-base-300 shadow-xl">
                <div class="card-body p-4">
                  <TraversalControls />
                </div>
              </div>
            </div>
          </div>
        </aside>
      </div>
    </template>

    <div v-if="graphStore.isLoading" class="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50">
      <div class="card bg-base-200 shadow-2xl">
        <div class="card-body items-center">
          <LoadingSpinner message="Loading graph..." />
        </div>
      </div>
    </div>

    <transition
      enter-active-class="transition duration-300 ease-out"
      enter-from-class="translate-x-full opacity-0"
      enter-to-class="translate-x-0 opacity-100"
      leave-active-class="transition duration-300 ease-in"
      leave-from-class="translate-x-0 opacity-100"
      leave-to-class="translate-x-full opacity-0"
    >
      <div v-if="graphStore.error" class="toast toast-end toast-bottom z-50">
        <div class="alert alert-error shadow-lg">
          <div class="flex items-center gap-3">
            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" class="w-6 h-6 stroke-current flex-shrink-0">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <span>{{ graphStore.error }}</span>
            <button @click="graphStore.error = null" class="btn btn-sm btn-circle btn-ghost">✕</button>
          </div>
        </div>
      </div>
    </transition>
  </div>
</template>
