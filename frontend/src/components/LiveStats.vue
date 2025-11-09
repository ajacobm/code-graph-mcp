<template>
  <div class="bg-slate-800/50 border border-slate-700 rounded-lg p-4 space-y-3">
    <!-- Header -->
    <div class="flex items-center justify-between">
      <h3 class="text-sm font-semibold text-slate-300">📡 Live Stats</h3>
      <div :class="['w-2 h-2 rounded-full transition-colors', connectionClass]"></div>
    </div>

    <!-- Connection Status -->
    <div class="text-xs text-slate-400 space-y-2">
      <div class="flex items-center justify-between">
        <span>WebSocket:</span>
        <span :class="['font-mono', statusClass]">{{ connectionStatus }}</span>
      </div>
      <div class="flex items-center justify-between">
        <span>Events:</span>
        <span class="font-mono text-slate-300">{{ eventCount }}</span>
      </div>
    </div>

    <!-- Live Metrics -->
    <div class="border-t border-slate-700 pt-3 space-y-2 text-xs">
      <div class="flex items-center justify-between text-slate-300">
        <span>Nodes:</span>
        <span class="font-mono font-semibold">{{ liveNodeCount }}</span>
      </div>
      <div class="flex items-center justify-between text-slate-300">
        <span>Relationships:</span>
        <span class="font-mono font-semibold">{{ liveRelationshipCount }}</span>
      </div>
    </div>

    <!-- Last Event -->
    <div v-if="lastEvent" class="border-t border-slate-700 pt-3 text-xs">
      <div class="text-slate-400 mb-1">Last Event:</div>
      <div class="text-slate-300 font-mono truncate">{{ lastEvent.event_type }}</div>
      <div class="text-slate-500 text-xs mt-1">{{ formatTime(lastEvent.timestamp) }}</div>
    </div>

    <!-- Ping Status -->
    <div class="border-t border-slate-700 pt-3">
      <button
        @click="sendPing"
        :disabled="!isConnected || pinging"
        class="w-full px-3 py-2 text-xs bg-slate-700/50 hover:bg-slate-700 disabled:opacity-50 text-slate-300 rounded transition-colors"
      >
        {{ pinging ? '⏳ Ping...' : '🔔 Ping Server' }}
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { useEvents } from '../composables/useEvents'
import { useGraphStore } from '../stores/graphStore'

const { isConnected, eventCount, lastEvent, ping } = useEvents()
const graphStore = useGraphStore()

const pinging = ref(false)
const liveNodeCount = ref(0)
const liveRelationshipCount = ref(0)

const connectionStatus = computed(() => {
  if (!isConnected.value) return 'Disconnected'
  return 'Connected'
})

const statusClass = computed(() => {
  if (!isConnected.value) return 'text-red-400'
  return 'text-green-400'
})

const connectionClass = computed(() => {
  if (!isConnected.value) return 'bg-red-500'
  return 'bg-green-500 animate-pulse'
})

const formatTime = (timestamp: string) => {
  try {
    const date = new Date(timestamp)
    const now = new Date()
    const diffMs = now.getTime() - date.getTime()
    const diffSecs = Math.floor(diffMs / 1000)

    if (diffSecs < 60) return `${diffSecs}s ago`
    const diffMins = Math.floor(diffSecs / 60)
    if (diffMins < 60) return `${diffMins}m ago`
    return date.toLocaleTimeString()
  } catch {
    return 'N/A'
  }
}

const sendPing = async () => {
  pinging.value = true
  try {
    await ping()
  } finally {
    pinging.value = false
  }
}

const handleNodeAdded = () => {
  liveNodeCount.value++
}

const handleRelationshipAdded = () => {
  liveRelationshipCount.value++
}

onMounted(async () => {
  // Initialize from store
  if (graphStore.stats) {
    liveNodeCount.value = graphStore.stats.total_nodes
    liveRelationshipCount.value = graphStore.stats.total_relationships
  }

  // Subscribe to CDC events for live updates
  const { subscribe } = useEvents()
  subscribe('node_added', handleNodeAdded)
  subscribe('relationship_added', handleRelationshipAdded)
})

onUnmounted(() => {
  // Cleanup is handled by useEvents composable
})
</script>
