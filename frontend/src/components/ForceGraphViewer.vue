<script setup lang="ts">
import { ref, onMounted, watch, computed, onBeforeUnmount, nextTick } from 'vue'
import ForceGraph from 'force-graph'
import type { GraphData } from '../types/graph'

const props = defineProps<{
  graphData: GraphData
  selectedNodeId?: string | null
}>()

const emit = defineEmits<{
  nodeClick: [node: any]
  nodeHover: [node: any | null]
}>()

const containerRef = ref<HTMLElement | null>(null)
const graph = ref<any>(null)
const highlightNodes = ref(new Set())
const highlightLinks = ref(new Set())
const hoverNode = ref<any>(null)

const nodeColorByType = {
  'function': '#818cf8',    // indigo
  'class': '#f472b6',       // pink
  'module': '#22d3ee',      // cyan
  'import': '#a78bfa',      // purple
  'variable': '#fb923c',    // orange
  'default': '#6b7280'      // gray
}

const linkColorByType = {
  'calls': '#10b981',       // green
  'imports': '#3b82f6',     // blue
  'contains': '#8b5cf6',    // violet
  'default': '#4b5563'      // gray
}

// Convert our graph data to force-graph format
const forceGraphData = computed(() => {
  const nodes = props.graphData.nodes.map(node => ({
    id: node.id,
    name: node.name,
    type: node.node_type,
    complexity: node.complexity || 0,
    language: node.language,
    isEntry: node.metadata?.is_entry_point || false,
    isHub: node.metadata?.is_hub || false,
    isLeaf: node.metadata?.is_leaf || false,
    // Store original node data
    _data: node
  }))
  
  const links = props.graphData.relationships.map(rel => ({
    source: rel.source_id,
    target: rel.target_id,
    type: rel.relationship_type,
    // Store original relationship data
    _data: rel
  }))
  
  return { nodes, links }
})

function initGraph() {
  if (!containerRef.value) return
  
  const elem = containerRef.value
  const width = elem.clientWidth
  const height = elem.clientHeight
  
  graph.value = ForceGraph()(elem)
    .graphData(forceGraphData.value)
    .width(width)
    .height(height)
    .backgroundColor('#111827')
    .nodeLabel('name')
    .nodeAutoColorBy('type')
    .nodeVal(node => {
      // Size by complexity or connection count
      const complexity = (node as any).complexity || 1
      const baseSize = 4
      return baseSize + (complexity / 10)
    })
    .nodeColor(node => {
      const n = node as any
      // Highlight selected node
      if (props.selectedNodeId && n.id === props.selectedNodeId) {
        return '#fbbf24' // yellow for selected
      }
      // Highlight connected nodes
      if (highlightNodes.value.has(n.id)) {
        return '#f472b6' // pink for connected
      }
      // Color by type
      return nodeColorByType[n.type as keyof typeof nodeColorByType] || nodeColorByType.default
    })
    .nodeCanvasObject((node, ctx, globalScale) => {
      const n = node as any
      const label = n.name
      const fontSize = 12 / globalScale
      const textWidth = ctx.measureText(label).width
      const bckgDimensions = [textWidth, fontSize].map(n => n + fontSize * 0.2)
      
      // Draw node circle
      ctx.beginPath()
      ctx.arc(n.x, n.y, n.val || 5, 0, 2 * Math.PI, false)
      ctx.fillStyle = n.color || '#818cf8'
      ctx.fill()
      
      // Add border for special nodes
      if (n.isEntry || n.isHub || n.isLeaf) {
        ctx.strokeStyle = n.isEntry ? '#22d3ee' : n.isHub ? '#f59e0b' : '#10b981'
        ctx.lineWidth = 2 / globalScale
        ctx.stroke()
      }
      
      // Draw label
      ctx.font = `${fontSize}px Sans-Serif`
      ctx.fillStyle = 'rgba(255, 255, 255, 0.8)'
      ctx.fillText(label, n.x, n.y + (n.val || 5) + fontSize)
    })
    .linkColor(link => {
      const l = link as any
      if (highlightLinks.value.has(l)) {
        return '#fbbf24' // yellow for highlighted
      }
      return linkColorByType[l.type as keyof typeof linkColorByType] || linkColorByType.default
    })
    .linkWidth(link => highlightLinks.value.has(link) ? 2 : 1)
    .linkDirectionalArrowLength(3)
    .linkDirectionalArrowRelPos(1)
    .linkDirectionalParticles(link => highlightLinks.value.has(link) ? 2 : 0)
    .linkDirectionalParticleWidth(2)
    .onNodeClick((node, event) => {
      emit('nodeClick', (node as any)._data)
    })
    .onNodeHover((node) => {
      hoverNode.value = node
      updateHighlight()
      emit('nodeHover', node ? (node as any)._data : null)
      
      // Change cursor
      if (containerRef.value) {
        containerRef.value.style.cursor = node ? 'pointer' : 'default'
      }
    })
    .d3Force('charge', (d3: any) => d3.forceManyBody().strength(-120))
    .d3Force('link', (d3: any) => d3.forceLink().distance(50))
}

function updateHighlight() {
  highlightNodes.value.clear()
  highlightLinks.value.clear()
  
  if (hoverNode.value) {
    highlightNodes.value.add((hoverNode.value as any).id)
    
    // Highlight connected nodes and links
    forceGraphData.value.links.forEach(link => {
      if (link.source === (hoverNode.value as any).id || link.target === (hoverNode.value as any).id) {
        highlightLinks.value.add(link)
        highlightNodes.value.add(typeof link.source === 'object' ? link.source.id : link.source)
        highlightNodes.value.add(typeof link.target === 'object' ? link.target.id : link.target)
      }
    })
  }
  
  if (graph.value) {
    graph.value.nodeColor(graph.value.nodeColor())
    graph.value.linkColor(graph.value.linkColor())
    graph.value.linkWidth(graph.value.linkWidth())
  }
}

function zoomToNode(nodeId: string) {
  if (!graph.value) return
  
  const node = forceGraphData.value.nodes.find(n => n.id === nodeId)
  if (node) {
    graph.value.centerAt(node.x, node.y, 1000)
    graph.value.zoom(3, 1000)
  }
}

function fitView() {
  if (graph.value) {
    graph.value.zoomToFit(400, 50)
  }
}

// Watch for selected node changes
watch(() => props.selectedNodeId, (newId) => {
  if (newId && graph.value) {
    zoomToNode(newId)
  }
})

// Watch for graph data changes
watch(() => props.graphData, (newData) => {
  if (graph.value && newData) {
    graph.value.graphData(forceGraphData.value)
  }
}, { deep: true })

// Handle window resize
const handleResize = () => {
  if (graph.value && containerRef.value) {
    graph.value
      .width(containerRef.value.clientWidth)
      .height(containerRef.value.clientHeight)
  }
}

onMounted(async () => {
  // Wait for DOM to be ready
  await nextTick()
  
  // Ensure container has dimensions
  if (containerRef.value) {
    const width = containerRef.value.clientWidth
    const height = containerRef.value.clientHeight
    
    if (width > 0 && height > 0) {
      initGraph()
      window.addEventListener('resize', handleResize)
      
      // Fit view after initial layout
      setTimeout(() => {
        fitView()
      }, 100)
    } else {
      console.warn('Container has no dimensions yet, retrying...')
      setTimeout(() => {
        initGraph()
        window.addEventListener('resize', handleResize)
      }, 100)
    }
  }
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', handleResize)
  if (graph.value) {
    graph.value._destructor()
  }
})

// Expose methods for parent component
defineExpose({
  fitView,
  zoomToNode
})
</script>

<template>
  <div class="force-graph-viewer relative w-full h-full">
    <div ref="containerRef" class="w-full h-full"></div>
    
    <!-- Controls Overlay -->
    <div class="absolute top-4 right-4 flex flex-col gap-2">
      <button 
        @click="fitView"
        class="btn btn-sm btn-circle btn-primary shadow-lg"
        title="Fit to view"
      >
        <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 8V4m0 0h4M4 4l5 5m11-1V4m0 0h-4m4 0l-5 5M4 16v4m0 0h4m-4 0l5-5m11 5l-5-5m5 5v-4m0 4h-4" />
        </svg>
      </button>
    </div>
    
    <!-- Legend -->
    <div class="absolute bottom-4 left-4 bg-base-100/80 backdrop-blur-sm rounded-lg p-3 shadow-lg text-xs">
      <div class="font-bold mb-2">Node Types</div>
      <div class="space-y-1">
        <div class="flex items-center gap-2">
          <div class="w-3 h-3 rounded-full" style="background-color: #818cf8"></div>
          <span>Function</span>
        </div>
        <div class="flex items-center gap-2">
          <div class="w-3 h-3 rounded-full" style="background-color: #f472b6"></div>
          <span>Class</span>
        </div>
        <div class="flex items-center gap-2">
          <div class="w-3 h-3 rounded-full" style="background-color: #22d3ee"></div>
          <span>Module</span>
        </div>
      </div>
      <div class="font-bold mt-3 mb-2">Special Nodes</div>
      <div class="space-y-1">
        <div class="flex items-center gap-2">
          <div class="w-3 h-3 rounded-full border-2" style="border-color: #22d3ee"></div>
          <span>🚀 Entry Point</span>
        </div>
        <div class="flex items-center gap-2">
          <div class="w-3 h-3 rounded-full border-2" style="border-color: #f59e0b"></div>
          <span>🔀 Hub</span>
        </div>
      </div>
    </div>
    
    <!-- Hover Info -->
    <div 
      v-if="hoverNode" 
      class="absolute top-4 left-4 bg-base-100/90 backdrop-blur-sm rounded-lg p-3 shadow-lg max-w-xs"
    >
      <div class="font-bold">{{ (hoverNode as any).name }}</div>
      <div class="text-xs opacity-70 mt-1">
        Type: {{ (hoverNode as any).type }}
      </div>
      <div v-if="(hoverNode as any).complexity" class="text-xs opacity-70">
        Complexity: {{ (hoverNode as any).complexity }}
      </div>
    </div>
  </div>
</template>

<style scoped>
.force-graph-viewer {
  background: linear-gradient(135deg, #1f2937 0%, #111827 100%);
}
</style>
