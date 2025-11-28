<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch } from 'vue'
import ForceGraph from 'force-graph'
import type { GraphData, ForceGraphNode, ForceGraphLink } from '../../types/forceGraph'

// eslint-disable-next-line @typescript-eslint/no-explicit-any
type ForceGraphInstance = any

const props = defineProps<{
  graphData: GraphData | null
  selectedNodeId?: string | null
  highlightedNodeIds?: string[]
  showLabels?: boolean
  colorByLanguage?: boolean
  colorByType?: boolean
}>()

const emit = defineEmits<{
  nodeClick: [node: ForceGraphNode]
  nodeHover: [node: ForceGraphNode | null]
  backgroundClick: []
}>()

const containerRef = ref<HTMLElement | null>(null)
let graph: ForceGraphInstance = null

// Color mapping for languages
const languageColors: Record<string, string> = {
  python: '#3776AB',
  typescript: '#3178C6',
  javascript: '#F7DF1E',
  'c#': '#68217A',
  java: '#ED8B00',
  go: '#00ADD8',
  rust: '#CE412B',
  ruby: '#CC342D',
  php: '#777BB4',
  cpp: '#00599C',
  default: '#64748b'
}

// Color mapping for node types
const typeColors: Record<string, string> = {
  function: '#22c55e',
  class: '#3b82f6',
  method: '#8b5cf6',
  module: '#f59e0b',
  import: '#6b7280',
  default: '#64748b'
}

const getNodeColor = (node: ForceGraphNode): string => {
  if (props.selectedNodeId === node.id) {
    return '#f472b6' // Pink for selected
  }
  if (props.highlightedNodeIds?.includes(node.id)) {
    return '#fbbf24' // Yellow for highlighted
  }
  if (props.colorByLanguage) {
    return languageColors[node.language?.toLowerCase() || 'default'] || languageColors.default
  }
  if (props.colorByType) {
    return typeColors[node.nodeType?.toLowerCase() || 'default'] || typeColors.default
  }
  return typeColors[node.nodeType?.toLowerCase() || 'default'] || typeColors.default
}

const getNodeSize = (node: ForceGraphNode): number => {
  // Base size on complexity
  const baseSize = 4
  const complexityFactor = Math.min(node.complexity || 1, 20) / 5
  return baseSize + complexityFactor
}

const initGraph = () => {
  if (!containerRef.value) return

  // Clear any existing graph
  if (graph) {
    containerRef.value.innerHTML = ''
    graph = null
  }

  // Force-graph library uses factory pattern
  const ForceGraphFactory = ForceGraph as unknown as () => (container: HTMLElement) => ForceGraphInstance
  graph = ForceGraphFactory()(containerRef.value)
    .graphData({ nodes: [], links: [] })
    .nodeId('id')
    .nodeLabel((node: ForceGraphNode) => {
      const n = node as ForceGraphNode
      return `${n.name}\n${n.nodeType} | ${n.language}\nComplexity: ${n.complexity}`
    })
    .nodeColor((node: ForceGraphNode) => getNodeColor(node as ForceGraphNode))
    .nodeVal((node: ForceGraphNode) => getNodeSize(node as ForceGraphNode))
    .linkColor((link: ForceGraphLink) => {
      const l = link as ForceGraphLink
      return l.isSeam ? '#f59e0b' : '#475569'
    })
    .linkWidth((link: ForceGraphLink) => {
      const l = link as ForceGraphLink
      return l.isSeam ? 2 : 1
    })
    .linkDirectionalArrowLength(6)
    .linkDirectionalArrowRelPos(1)
    .onNodeClick((node: ForceGraphNode) => {
      emit('nodeClick', node as ForceGraphNode)
    })
    .onNodeHover((node: ForceGraphNode | null) => {
      emit('nodeHover', node as ForceGraphNode | null)
    })
    .onBackgroundClick(() => {
      emit('backgroundClick')
    })
    .cooldownTicks(100)
    .onEngineStop(() => {
      // Graph has stabilized
    })

  // Add labels if enabled
  if (props.showLabels) {
    graph.nodeCanvasObject((node: ForceGraphNode, ctx: CanvasRenderingContext2D, globalScale: number) => {
      const n = node as ForceGraphNode
      const label = n.name
      const fontSize = 12 / globalScale
      ctx.font = `${fontSize}px Sans-Serif`
      ctx.textAlign = 'center'
      ctx.textBaseline = 'middle'
      ctx.fillStyle = getNodeColor(n)
      
      // Draw node circle
      const size = getNodeSize(n)
      ctx.beginPath()
      ctx.arc(node.x || 0, node.y || 0, size, 0, 2 * Math.PI)
      ctx.fill()
      
      // Draw label if zoomed in enough
      if (globalScale > 0.8) {
        ctx.fillStyle = '#e2e8f0'
        ctx.fillText(label, node.x || 0, (node.y || 0) + size + fontSize)
      }
    })
  }

  // Update with initial data if available
  if (props.graphData) {
    updateGraphData(props.graphData)
  }
}

const updateGraphData = (data: GraphData) => {
  if (!graph) return

  // Transform data for force-graph format
  const nodes: ForceGraphNode[] = data.nodes.map(n => ({
    id: n.id,
    name: n.name,
    nodeType: n.type,
    language: n.language,
    complexity: n.complexity || 0,
    file: n.file,
    line: n.line,
    val: getNodeSize(n as unknown as ForceGraphNode)
  }))

  const links: ForceGraphLink[] = data.links.map(l => ({
    source: l.source,
    target: l.target,
    type: l.type,
    isSeam: l.isSeam || false
  }))

  graph.graphData({ nodes, links })
}

const zoomToFit = (duration: number = 500) => {
  if (graph) {
    graph.zoomToFit(duration, 50)
  }
}

const centerNode = (nodeId: string) => {
  if (!graph) return
  const node = (graph.graphData().nodes as ForceGraphNode[]).find(n => n.id === nodeId)
  if (node) {
    graph.centerAt(node.x, node.y, 500)
    graph.zoom(2, 500)
  }
}

// Watch for data changes
watch(() => props.graphData, (newData) => {
  if (newData) {
    updateGraphData(newData)
  }
}, { deep: true })

// Watch for selection changes to update colors
watch(() => props.selectedNodeId, () => {
  if (graph) {
    graph.nodeColor((node: ForceGraphNode) => getNodeColor(node as ForceGraphNode))
  }
})

// Watch for highlight changes
watch(() => props.highlightedNodeIds, () => {
  if (graph) {
    graph.nodeColor((node: ForceGraphNode) => getNodeColor(node as ForceGraphNode))
  }
}, { deep: true })

onMounted(() => {
  initGraph()
  
  // Handle resize
  const resizeObserver = new ResizeObserver(() => {
    if (graph && containerRef.value) {
      graph.width(containerRef.value.clientWidth)
      graph.height(containerRef.value.clientHeight)
    }
  })
  
  if (containerRef.value) {
    resizeObserver.observe(containerRef.value)
  }
})

onUnmounted(() => {
  if (containerRef.value) {
    containerRef.value.innerHTML = ''
  }
  graph = null
})

// Expose methods to parent
defineExpose({
  zoomToFit,
  centerNode
})
</script>

<template>
  <div 
    ref="containerRef" 
    class="force-graph-container w-full h-full bg-slate-900 rounded-lg overflow-hidden"
  ></div>
</template>

<style scoped>
.force-graph-container {
  min-height: 400px;
}

.force-graph-container :deep(canvas) {
  width: 100% !important;
  height: 100% !important;
}
</style>
