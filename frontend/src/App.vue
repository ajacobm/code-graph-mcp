<template>
  <div class="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900">
    <!-- Header -->
    <header class="sticky top-0 z-50 bg-slate-900/95 backdrop-blur border-b border-slate-700">
      <div class="max-w-7xl mx-auto px-4 py-4 flex items-center justify-between">
        <div class="flex items-center gap-3">
          <div class="text-2xl font-bold bg-gradient-to-r from-indigo-400 to-pink-400 bg-clip-text text-transparent">
            📊 Code Graph
          </div>
        </div>
        
        <div class="flex items-center gap-4">
          <button
            @click="graphStore.reanalyze()"
            :disabled="graphStore.isLoading"
            class="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 text-white rounded-lg transition-colors text-sm"
          >
            {{ graphStore.isLoading ? '⏳ Analyzing...' : '🔄 Re-analyze' }}
          </button>
          
          <div v-if="graphStore.stats" class="text-sm text-slate-400 hidden sm:block">
            {{ graphStore.stats.total_nodes }} nodes · {{ graphStore.stats.total_relationships }} edges
          </div>
        </div>
      </div>
    </header>

    <!-- Main Content -->
    <main class="w-full overflow-hidden">
      <!-- Tab Navigation -->
      <div class="flex gap-1 mb-6 border-b border-slate-700 overflow-x-auto px-4">
        <button
          v-for="tab in tabs"
          :key="tab.id"
          @click="activeTab = tab.id"
          :class="[
            'px-4 py-3 font-semibold whitespace-nowrap transition-colors',
            activeTab === tab.id
              ? 'text-indigo-400 border-b-2 border-indigo-400'
              : 'text-slate-400 hover:text-slate-300'
          ]"
        >
          {{ tab.label }}
        </button>
      </div>

      <!-- Error Display -->
      <div v-if="graphStore.error" class="mb-4 p-4 mx-4 bg-red-900/30 border border-red-700 rounded text-red-200 text-sm">
        ⚠️ {{ graphStore.error }}
      </div>

      <!-- Tab Content -->
      <div class="grid grid-cols-1 lg:grid-cols-4 gap-6 px-4 max-w-7xl mx-auto">
        <!-- Main Panel (3 cols on desktop, full width on mobile) -->
        <div class="lg:col-span-3 order-2 lg:order-1">
          <!-- Browse Tab -->
          <div v-if="activeTab === 'browse'" class="space-y-6">
            <!-- Category Cards -->
            <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
              <CategoryCard
                emoji="🚀"
                title="Entry Points"
                description="Functions with no callers"
                @click="loadCategory('entry_points')"
                :loading="categoryLoading === 'entry_points'"
              />
              <CategoryCard
                emoji="🔀"
                title="Hubs"
                description="Highly connected nodes"
                @click="loadCategory('hubs')"
                :loading="categoryLoading === 'hubs'"
              />
              <CategoryCard
                emoji="🍃"
                title="Leaves"
                description="Functions with no callees"
                @click="loadCategory('leaves')"
                :loading="categoryLoading === 'leaves'"
              />
            </div>

            <!-- Category Results Grid -->
            <div v-if="categoryNodes.length > 0" class="space-y-4">
              <div class="flex items-center justify-between">
                <h3 class="text-lg font-semibold text-slate-100">
                  {{ categoryTitle }}
                </h3>
                <div class="text-sm text-slate-400">
                  Showing {{ categoryNodes.length }} of {{ categoryTotal }}
                </div>
              </div>

              <div class="grid grid-cols-1 md:grid-cols-2 gap-4 max-h-96 overflow-y-auto pr-2">
                <NodeTile
                  v-for="node in categoryNodes"
                  :key="node.id"
                  :node="node"
                  @click="selectNodeForConnections(node)"
                />
              </div>
            </div>
          </div>

          <!-- Connections Tab -->
          <div v-else-if="activeTab === 'connections'">
            <ConnectionsList 
              v-if="graphStore.selectedNode"
              :node-id="graphStore.selectedNodeId"
              @select-node="selectNodeForConnections"
            />
            <div v-else class="text-center py-12 text-slate-400">
              <p class="mb-4 text-lg">👉 Select a node to explore connections</p>
              <p class="text-sm">Go to <strong>Browse</strong> tab and click a category to start</p>
            </div>
          </div>
        </div>

        <!-- Right Panel (1 col on desktop) - Node Details -->
        <div class="lg:col-span-1 order-1 lg:order-2">
          <div v-if="graphStore.selectedNode" class="card bg-gradient-to-br from-slate-800 to-slate-700 shadow-xl border border-slate-600 sticky top-24">
            <div class="card-body p-4">
              <h3 class="card-title text-indigo-400 mb-4">
                <span class="text-xl mr-2">📍</span>
                Selected Node
              </h3>
              
              <div class="space-y-3">
                <div>
                  <div class="text-slate-400 text-xs font-semibold">NAME</div>
                  <div class="text-slate-100 font-mono text-sm break-words">{{ graphStore.selectedNode.name }}</div>
                </div>
                
                <div class="grid grid-cols-2 gap-2">
                  <div>
                    <div class="text-slate-400 text-xs font-semibold">TYPE</div>
                    <div class="text-slate-100 text-sm">{{ graphStore.selectedNode.node_type }}</div>
                  </div>
                  <div>
                    <div class="text-slate-400 text-xs font-semibold">LANGUAGE</div>
                    <div class="text-slate-100 text-sm">{{ graphStore.selectedNode.language }}</div>
                  </div>
                </div>
                
                <div>
                  <div class="text-slate-400 text-xs font-semibold">COMPLEXITY</div>
                  <div class="badge badge-primary badge-outline text-sm">{{ graphStore.selectedNode.complexity }}</div>
                </div>
                
                <div v-if="graphStore.selectedNode.location" class="space-y-2">
                  <div class="text-slate-400 text-xs font-semibold">LOCATION</div>
                  <div class="text-slate-100 text-xs font-mono break-words bg-slate-900/50 p-2 rounded">
                    {{ graphStore.selectedNode.location.file_path }}<br/>
                    <span class="text-slate-300">Line {{ graphStore.selectedNode.location.start_line }}</span>
                  </div>
                </div>
              </div>

              <div class="card-actions justify-end mt-4">
                <button
                  @click="graphStore.selectNode(null)"
                  class="btn btn-outline btn-error btn-sm"
                >
                  Clear Selection
                </button>
              </div>
            </div>
          </div>
          <div v-else class="card bg-slate-800 border border-slate-700 text-center p-4 sticky top-24">
            <div class="text-4xl mb-2">🎯</div>
            <p class="text-slate-400 text-sm">No node selected</p>
            <p class="text-slate-500 text-xs mt-1">Select a node to see details</p>
          </div>
        </div>
      </div>
    </main>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useGraphStore } from './stores/graphStore'
import NodeTile from './components/NodeTile.vue'
import ConnectionsList from './components/ConnectionsList.vue'
import CategoryCard from './components/CategoryCard.vue'
import type { NodeResponse, Node } from './types/graph'

const graphStore = useGraphStore()
const activeTab = ref('browse')
const categoryLoading = ref<string | null>(null)
const categoryNodes = ref<NodeResponse[]>([])
const categoryTitle = ref('')
const categoryTotal = ref(0)

const tabs = [
  { id: 'browse', label: '📂 Browse' },
  { id: 'connections', label: '🔗 Connections' }
]

async function loadCategory(category: 'entry_points' | 'hubs' | 'leaves') {
  try {
    categoryLoading.value = category
    const result = await graphStore.getNodesByCategory(category, 20, 0)
    categoryNodes.value = result.nodes
    categoryTotal.value = result.total
    
    // Also add these nodes to the store so selectNode can find them
    result.nodes.forEach((n: NodeResponse) => {
      if (!graphStore.nodes.find(existing => existing.id === n.id)) {
        graphStore.nodes.push({
          id: n.id,
          name: n.name,
          node_type: n.node_type,
          language: n.language || 'unknown',
          complexity: n.complexity || 0,
          location: n.location,
          metadata: n.metadata || {}
        })
      }
    })
    
    const titles: Record<string, string> = {
      'entry_points': '🚀 Entry Points',
      'hubs': '🔀 Hubs',
      'leaves': '🍃 Leaves'
    }
    categoryTitle.value = titles[category]
  } finally {
    categoryLoading.value = null
  }
}

function selectNodeForConnections(node: NodeResponse | any) {
  console.log('selectNodeForConnections called with:', { id: node?.id, name: node?.name, node })
  graphStore.selectNode(node.id)
  console.log('After selectNode, selectedNodeId:', graphStore.selectedNodeId, 'selectedNode:', graphStore.selectedNode)
  activeTab.value = 'connections'
}

onMounted(() => {
  // Do nothing - loadStats is problematic, let it stay as initial false
})
</script>
