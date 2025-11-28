<script setup lang="ts">
import { computed } from 'vue'
import type { ForceGraphNode } from '../../types/forceGraph'

const props = defineProps<{
  node: ForceGraphNode | null
}>()

const emit = defineEmits<{
  close: []
  navigate: [nodeId: string]
  showConnections: [nodeId: string]
}>()

const nodeTypeIcon = computed(() => {
  if (!props.node) return '•'
  switch (props.node.nodeType?.toLowerCase()) {
    case 'function': return '⚙️'
    case 'class': return '📦'
    case 'method': return '🔧'
    case 'module': return '📄'
    case 'import': return '📥'
    default: return '•'
  }
})

const languageColor = computed(() => {
  if (!props.node) return '#64748b'
  const colors: Record<string, string> = {
    python: '#3776AB',
    typescript: '#3178C6',
    javascript: '#F7DF1E',
    'c#': '#68217A',
    java: '#ED8B00',
    go: '#00ADD8',
    rust: '#CE412B',
    ruby: '#CC342D',
    php: '#777BB4',
  }
  return colors[props.node.language?.toLowerCase() || ''] || '#64748b'
})

const fileName = computed(() => {
  if (!props.node?.file) return 'Unknown file'
  return props.node.file.split('/').pop() || props.node.file
})

const complexityClass = computed(() => {
  if (!props.node) return 'badge-ghost'
  const complexity = props.node.complexity || 0
  if (complexity <= 5) return 'badge-success'
  if (complexity <= 10) return 'badge-warning'
  return 'badge-error'
})
</script>

<template>
  <div 
    v-if="node"
    class="node-details card bg-slate-800 border border-slate-600 shadow-xl"
  >
    <div class="card-body p-4">
      <!-- Header -->
      <div class="flex items-start justify-between gap-2">
        <div class="flex items-center gap-2">
          <span class="text-2xl">{{ nodeTypeIcon }}</span>
          <div>
            <h3 class="card-title text-lg text-slate-100 break-all">{{ node.name }}</h3>
            <p class="text-sm text-slate-400">{{ node.nodeType }}</p>
          </div>
        </div>
        <button 
          @click="emit('close')"
          class="btn btn-ghost btn-sm btn-circle"
        >
          ✕
        </button>
      </div>

      <!-- Badges -->
      <div class="flex flex-wrap gap-2 mt-3">
        <span 
          class="badge"
          :style="{ backgroundColor: languageColor, color: 'white' }"
        >
          {{ node.language }}
        </span>
        <span :class="['badge', complexityClass]">
          Complexity: {{ node.complexity }}
        </span>
      </div>

      <!-- Location -->
      <div class="mt-3 space-y-1">
        <div class="text-xs text-slate-400 font-semibold">LOCATION</div>
        <div class="text-sm text-slate-200 font-mono bg-slate-900/50 p-2 rounded break-all">
          {{ fileName }}
          <span v-if="node.line" class="text-slate-400">:{{ node.line }}</span>
        </div>
      </div>

      <!-- Actions -->
      <div class="card-actions justify-end mt-4">
        <button 
          @click="emit('showConnections', node.id)"
          class="btn btn-sm btn-primary"
        >
          🔗 View Connections
        </button>
        <button 
          @click="emit('navigate', node.id)"
          class="btn btn-sm btn-outline"
        >
          📍 Center
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.node-details {
  min-width: 280px;
  max-width: 350px;
}
</style>
