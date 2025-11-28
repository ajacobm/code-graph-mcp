<script setup lang="ts">
import { ref, computed } from 'vue'
import type { ForceGraphNode } from '../../types/forceGraph'

const props = defineProps<{
  node: ForceGraphNode | null
  isCollapsed?: boolean
}>()

const emit = defineEmits<{
  'update:isCollapsed': [value: boolean]
  viewConnections: [nodeId: string]
  navigateToNode: [nodeId: string]
}>()

const collapsed = ref(props.isCollapsed ?? false)

const toggleCollapse = () => {
  collapsed.value = !collapsed.value
  emit('update:isCollapsed', collapsed.value)
}

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

const complexityLabel = computed(() => {
  if (!props.node) return { text: 'N/A', class: 'badge-ghost' }
  const complexity = props.node.complexity || 0
  if (complexity <= 5) return { text: 'Low', class: 'badge-success' }
  if (complexity <= 10) return { text: 'Medium', class: 'badge-warning' }
  return { text: 'High', class: 'badge-error' }
})

const fileName = computed(() => {
  if (!props.node?.file) return 'Unknown'
  return props.node.file.split('/').pop() || props.node.file
})

const filePath = computed(() => {
  if (!props.node?.file) return ''
  const parts = props.node.file.split('/')
  return parts.slice(0, -1).join('/')
})
</script>

<template>
  <div 
    :class="[
      'details-panel flex flex-col bg-slate-800 border-l border-slate-700 transition-all duration-300',
      collapsed ? 'w-12' : 'w-80'
    ]"
  >
    <!-- Header -->
    <div class="flex items-center justify-between p-3 border-b border-slate-700">
      <button
        @click="toggleCollapse"
        class="btn btn-ghost btn-sm btn-circle"
      >
        <svg 
          xmlns="http://www.w3.org/2000/svg" 
          class="h-5 w-5 transition-transform"
          :class="{ 'rotate-180': !collapsed }"
          fill="none" 
          viewBox="0 0 24 24" 
          stroke="currentColor"
        >
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 5l7 7-7 7M5 5l7 7-7 7" />
        </svg>
      </button>
      <h2 v-if="!collapsed" class="font-semibold text-slate-200">Details</h2>
    </div>

    <!-- Content -->
    <div v-if="!collapsed" class="flex-1 overflow-y-auto">
      <!-- Node Selected -->
      <div v-if="node" class="p-4 space-y-4">
        <!-- Node Header -->
        <div class="flex items-start gap-3">
          <span class="text-3xl">{{ nodeTypeIcon }}</span>
          <div class="flex-1 min-w-0">
            <h3 class="text-lg font-bold text-slate-100 break-words">{{ node.name }}</h3>
            <p class="text-sm text-slate-400">{{ node.nodeType }}</p>
          </div>
        </div>

        <!-- Quick Stats -->
        <div class="grid grid-cols-2 gap-2">
          <div class="bg-slate-900/50 rounded p-2">
            <div class="text-xs text-slate-400">Language</div>
            <div 
              class="text-sm font-medium"
              :style="{ color: languageColor }"
            >
              {{ node.language }}
            </div>
          </div>
          <div class="bg-slate-900/50 rounded p-2">
            <div class="text-xs text-slate-400">Complexity</div>
            <div class="flex items-center gap-2">
              <span class="text-sm font-mono">{{ node.complexity }}</span>
              <span :class="['badge badge-xs', complexityLabel.class]">
                {{ complexityLabel.text }}
              </span>
            </div>
          </div>
        </div>

        <!-- Location -->
        <div class="bg-slate-900/50 rounded p-3">
          <div class="text-xs text-slate-400 mb-1">Location</div>
          <div class="text-sm font-mono text-slate-200">
            {{ fileName }}
            <span v-if="node.line" class="text-slate-400">:{{ node.line }}</span>
          </div>
          <div v-if="filePath" class="text-xs text-slate-500 mt-1 break-words">
            {{ filePath }}
          </div>
        </div>

        <!-- Actions -->
        <div class="flex flex-col gap-2">
          <button 
            @click="emit('viewConnections', node.id)"
            class="btn btn-sm btn-primary w-full"
          >
            🔗 View Connections
          </button>
          <button 
            @click="emit('navigateToNode', node.id)"
            class="btn btn-sm btn-outline w-full"
          >
            📍 Center in Graph
          </button>
        </div>

        <!-- Metadata Section -->
        <div v-if="node.file" class="collapse collapse-arrow bg-slate-900/50 rounded">
          <input type="checkbox" /> 
          <div class="collapse-title text-sm font-medium text-slate-300">
            Full Path
          </div>
          <div class="collapse-content">
            <code class="text-xs break-all text-slate-400">{{ node.file }}</code>
          </div>
        </div>
      </div>

      <!-- No Node Selected -->
      <div v-else class="p-4 text-center">
        <div class="text-4xl mb-3">🎯</div>
        <h3 class="font-medium text-slate-300">No Node Selected</h3>
        <p class="text-sm text-slate-500 mt-1">
          Click on a node in the graph to view details
        </p>
      </div>
    </div>

    <!-- Collapsed View -->
    <div v-else class="flex-1 flex flex-col items-center py-4">
      <div v-if="node" class="tooltip tooltip-left" :data-tip="node.name">
        <span class="text-2xl">{{ nodeTypeIcon }}</span>
      </div>
      <div v-else class="text-slate-500">
        🎯
      </div>
    </div>
  </div>
</template>

<style scoped>
.details-panel {
  min-height: 100%;
}
</style>
