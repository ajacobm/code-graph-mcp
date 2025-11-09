<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { useGraphStore } from '../stores/graphStore'
import NodeTile from './NodeTile.vue'
import { graphClient } from '../api/graphClient'

const graphStore = useGraphStore()

const props = defineProps<{
  nodeId?: string
}>()

const loading = ref(false)
const error = ref<string | null>(null)
const callers = ref<any[]>([])
const callees = ref<any[]>([])
const siblings = ref<any[]>([])

const currentNode = computed(() => {
  if (!props.nodeId) return null
  return graphStore.nodes.find(n => n.id === props.nodeId) || null
})

async function loadConnections() {
  if (!props.nodeId) return
  
  loading.value = true
  error.value = null
  
  try {
    // Extract symbol name from node ID
    const symbol = currentNode.value?.name || props.nodeId.split(':').pop()?.split('/').pop()
    
    if (!symbol) {
      throw new Error('Could not extract symbol name')
    }
    
    // Load callers and callees
    const [callersResult, calleesResult] = await Promise.all([
      graphClient.findCallers(symbol),
      graphClient.findCallees(symbol)
    ])
    
    callers.value = (callersResult.results || []).map((r: any, idx: number) => ({
      ...r,
      distance: idx + 1 // Simple distance based on result order
    }))
    
    callees.value = (calleesResult.results || []).map((r: any, idx: number) => ({
      ...r,
      distance: idx + 1
    }))
    
    // Find siblings (same file)
    if (currentNode.value?.location?.file_path) {
      const filePath = currentNode.value.location.file_path
      siblings.value = graphStore.nodes
        .filter(n => n.location?.file_path === filePath && n.id !== props.nodeId)
        .slice(0, 10)
        .map(n => ({ ...n, distance: 0 }))
    }
    
  } catch (err) {
    error.value = err instanceof Error ? err.message : 'Failed to load connections'
    console.error('Error loading connections:', err)
  } finally {
    loading.value = false
  }
}

function navigateTo(node: any) {
  graphStore.selectNode(node.id)
}

watch(() => props.nodeId, loadConnections, { immediate: true })
</script>

<template>
  <div class="connections-list space-y-6 p-4">
    <!-- Loading State -->
    <div v-if="loading" class="flex justify-center py-8">
      <span class="loading loading-spinner loading-lg text-primary"></span>
    </div>
    
    <!-- Error State -->
    <div v-else-if="error" class="alert alert-error">
      <svg xmlns="http://www.w3.org/2000/svg" class="stroke-current shrink-0 h-6 w-6" fill="none" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z" />
      </svg>
      <span>{{ error }}</span>
    </div>
    
    <!-- No Node Selected -->
    <div v-else-if="!currentNode" class="text-center py-12 opacity-70">
      <div class="text-6xl mb-4">🗺️</div>
      <h3 class="text-xl font-bold mb-2">No Node Selected</h3>
      <p>Select a node to view its connections</p>
    </div>
    
    <!-- Connections View -->
    <div v-else>
      <!-- Current Node Card -->
      <div class="current-node card bg-gradient-to-br from-primary/20 to-accent/20 shadow-xl">
        <div class="card-body">
          <h2 class="card-title text-2xl">
            <span class="text-3xl mr-2">📍</span>
            You are here: {{ currentNode.name }}
          </h2>
          
          <div class="stats stats-horizontal bg-base-200/50 shadow mt-4">
            <div class="stat">
              <div class="stat-title">Type</div>
              <div class="stat-value text-lg">{{ currentNode.node_type }}</div>
            </div>
            <div class="stat">
              <div class="stat-title">Callers</div>
              <div class="stat-value text-2xl text-blue-500">{{ callers.length }}</div>
            </div>
            <div class="stat">
              <div class="stat-title">Callees</div>
              <div class="stat-value text-2xl text-green-500">{{ callees.length }}</div>
            </div>
            <div v-if="currentNode.complexity" class="stat">
              <div class="stat-title">Complexity</div>
              <div class="stat-value text-2xl text-warning">{{ currentNode.complexity }}</div>
            </div>
          </div>
          
          <div v-if="currentNode.location?.file_path" class="mt-2">
            <code class="text-xs opacity-70">{{ currentNode.location.file_path }}</code>
          </div>
        </div>
      </div>

      <!-- Callers Section -->
      <section v-if="callers.length > 0">
        <h3 class="text-lg font-bold mb-3 flex items-center gap-2">
          <span class="text-blue-500">↑</span>
          CALLED BY ({{ callers.length }})
        </h3>
        <div class="space-y-2">
          <NodeTile 
            v-for="caller in callers" 
            :key="caller.id"
            :node="caller"
            :distance="caller.distance"
            direction="inbound"
            :show-distance="true"
            @click="navigateTo(caller)"
          />
        </div>
      </section>

      <!-- Callees Section -->
      <section v-if="callees.length > 0">
        <h3 class="text-lg font-bold mb-3 flex items-center gap-2">
          <span class="text-green-500">↓</span>
          CALLS ({{ callees.length }})
        </h3>
        <div class="space-y-2">
          <NodeTile 
            v-for="callee in callees" 
            :key="callee.id"
            :node="callee"
            :distance="callee.distance"
            direction="outbound"
            :show-distance="true"
            @click="navigateTo(callee)"
          />
        </div>
      </section>

      <!-- Siblings Section -->
      <section v-if="siblings.length > 0">
        <h3 class="text-lg font-bold mb-3 flex items-center gap-2">
          <span class="text-yellow-500">──</span>
          SIBLINGS (same file, {{ siblings.length }})
        </h3>
        <div class="space-y-2">
          <NodeTile 
            v-for="sibling in siblings.slice(0, 5)" 
            :key="sibling.id"
            :node="sibling"
            :distance="0"
            direction="sibling"
            :show-distance="true"
            @click="navigateTo(sibling)"
          />
          <div v-if="siblings.length > 5" class="text-center text-sm opacity-70">
            + {{ siblings.length - 5 }} more in this file
          </div>
        </div>
      </section>

      <!-- Empty State -->
      <div v-if="callers.length === 0 && callees.length === 0 && siblings.length === 0" class="text-center py-8 opacity-70">
        <div class="text-4xl mb-2">🔍</div>
        <p>No connections found for this node</p>
      </div>
    </div>
  </div>
</template>

<style scoped>
.connections-list {
  max-height: 100%;
  overflow-y: auto;
}

section {
  padding-bottom: 1rem;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

section:last-child {
  border-bottom: none;
}
</style>
