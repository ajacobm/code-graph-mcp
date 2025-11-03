<script setup lang="ts">
import { onMounted, ref, watch, computed, onUnmounted } from 'vue'
import cytoscape from 'cytoscape'
import dagre from 'cytoscape-dagre'
import cola from 'cytoscape-cola'
import klay from 'cytoscape-klay'
import { useGraphStore } from '../stores/graphStore'
import { useEntryPointStore } from '../stores/entryPointStore'
import type { Core, NodeSingular, ElementDefinition } from 'cytoscape'

cytoscape.use(dagre)
cytoscape.use(cola)
cytoscape.use(klay)

const graphStore = useGraphStore()
const entryPointStore = useEntryPointStore()

const container = ref<HTMLElement>()
let cy: Core | null = null

const expandMode = ref<'callers' | 'callees' | 'both'>('both')
const showMinimap = ref(false)
const layoutType = ref<'dagre' | 'breadthfirst' | 'circle' | 'cola' | 'klay'>('dagre')
const showEntryPointHighlights = ref(true)
const nodeSizeMode = ref<'degree' | 'complexity' | 'fixed'>('degree')

// Enhanced color scheme with better contrast
const nodeTypeColors: Record<string, string> = {
  function: '#4F46E5',    // indigo
  class: '#EC4899',       // pink
  method: '#8B5CF6',      // violet
  module: '#10B981',      // emerald
  variable: '#F59E0B',    // amber
  interface: '#06B6D4',   // cyan
  entry_point: '#22D3EE', // sky
  default: '#6B7280'      // gray
}

const entryPoints = computed(() => {
  // Use actual entry point detection from backend when available
  if (entryPointStore.entryPoints.length > 0) {
    return new Set(entryPointStore.entryPoints.map(ep => ep.id))
  }
  
  // Fallback to simple incoming edge detection
  const hasIncoming = new Set<string>()
  const edges = graphStore.edgeArray || []
  const nodes = graphStore.nodeArray || []
  
  edges.forEach(edge => hasIncoming.add(edge.target))
  return new Set(
    nodes
      .filter(node => !hasIncoming.has(node.id))
      .map(node => node.id)
  )
})
  if (entryPointStore.entryPoints.length > 0) {
    return new Set(entryPointStore.entryPoints.map(ep => ep.id))
  }
  
  // Fallback to simple incoming edge detection
  const hasIncoming = new Set<string>()
  const edges = graphStore.edgeArray || []
  const nodes = graphStore.nodeArray || []
  
  edges.forEach(edge => hasIncoming.add(edge.target))
  return new Set(
    nodes
      .filter(node => !hasIncoming.has(node.id))
      .map(node => node.id)
  )
})

const initCytoscape = () => {
  if (!container.value) return

  cy = cytoscape({
    container: container.value,
    elements: [],
    style: [
      {
        selector: 'node',
        style: {
          'content': 'data(label)',
          'background-color': 'data(color)',
          'color': '#FFF',
          'text-valign': 'center',
          'text-halign': 'center',
          'font-size': '10px',
          'font-weight': 'bold',
          'padding': '8px',
          'width': 'data(size)',
          'height': 'data(size)',
          'text-wrap': 'wrap',
          'text-max-width': '80px',
          'border-width': '2px',
          'border-color': '#1F2937',
        },
      },
      {
        selector: 'node.entry-point',
        style: {
          'border-width': '4px',
          'border-color': '#22D3EE',
          'border-style': 'double',
        },
      },
      {
        selector: 'node.hub',
        style: {
          'border-width': '3px',
          'border-color': '#F59E0B',
        },
      },
      {
        selector: 'node:selected',
        style: {
          'background-color': '#EC4899',
          'border-width': '4px',
          'border-color': '#FFF',
          'z-index': 999,
        },
      },

      {
        selector: 'node.expandable',
        style: {
          'background-opacity': 0.9,
        },
      },
      {
        selector: 'edge',
        style: {
          'target-arrow-shape': 'triangle',
          'line-color': '#4B5563',
          'target-arrow-color': '#4B5563',
          'curve-style': 'bezier',
          'width': 2,
          'arrow-scale': 1.2,
        },
      },
      {
        selector: 'edge[isSeam="true"]',
        style: {
          'line-color': '#DC2626',
          'target-arrow-color': '#DC2626',
          'line-style': 'dashed',
          'width': 3,
        },
      },
      {
        selector: 'edge.highlighted',
        style: {
          'line-color': '#22D3EE',
          'target-arrow-color': '#22D3EE',
          'width': 3,
          'z-index': 100,
        },
      },
    ],
    layout: {
      name: 'breadthfirst',
      directed: true,
      spacingFactor: 1.5,
    } as any,
  })

  cy.on('tap', 'node', async (event) => {
    const nodeId = event.target.id()
    graphStore.selectNode(nodeId)
    highlightConnections(nodeId)
  })

  cy.on('dblclick', 'node', async (event) => {
    const nodeId = event.target.id()
    await expandNode(nodeId)
  })

  cy.on('tap', (event) => {
    if (event.target === cy) {
      graphStore.selectNode(null)
      clearHighlights()
    }
  })

  cy.on('mouseover', 'node', (event) => {
    const node = event.target
    node.style({
      'background-color': '#6366F1',
      'border-width': '3px',
      'border-color': '#FCD34D'
    })
  })

  cy.on('mouseout', 'node', (event) => {
    const node = event.target
    const nodeData = graphStore.nodes.get(node.id())
    if (nodeData) {
      node.style({
        'background-color': getNodeColor(nodeData),
        'border-width': '2px',
        'border-color': '#1F2937'
      })
    }
  })
}

const highlightConnections = (nodeId: string) => {
  if (!cy) return
  
  cy.elements().removeClass('highlighted')
  
  const node = cy.getElementById(nodeId)
  const connectedEdges = node.connectedEdges()
  connectedEdges.addClass('highlighted')
}

const clearHighlights = () => {
  if (!cy) return
  cy.elements().removeClass('highlighted')
}

const expandNode = async (nodeId: string) => {
  const node = graphStore.nodes.get(nodeId)
  if (!node) return

  const currentNodeIds = new Set(graphStore.nodeArray.map(n => n.id))

  if (expandMode.value === 'callers' || expandMode.value === 'both') {
    const callers = await graphStore.findCallers(node.name)
    callers.forEach((caller: any) => {
      const callerId = caller.caller_id
      if (!currentNodeIds.has(callerId)) {
        const [file, symbol] = callerId.split(':')
        graphStore.nodes.set(callerId, {
          id: callerId,
          name: caller.caller || symbol,
          type: 'function',
          language: caller.language || 'unknown',
          file_path: caller.file || file,
          line: caller.line || 0,
          complexity: 1,
          docstring: '',
        })
        
        const edgeId = `${callerId}-${nodeId}`
        graphStore.edges.set(edgeId, {
          id: edgeId,
          source: callerId,
          target: nodeId,
          type: 'CALLS',
          isSeam: false,
        })
      }
    })
  }

  if (expandMode.value === 'callees' || expandMode.value === 'both') {
    const callees = await graphStore.findCallees(node.name)
    callees.forEach((callee: any) => {
      const calleeId = callee.callee_id
      if (!currentNodeIds.has(calleeId)) {
        const [file, symbol] = calleeId.split(':')
        graphStore.nodes.set(calleeId, {
          id: calleeId,
          name: callee.callee || symbol,
          type: 'function',
          language: callee.language || 'unknown',
          file_path: callee.file || file,
          line: callee.line || 0,
          complexity: 1,
          docstring: '',
        })
        
        const edgeId = `${nodeId}-${calleeId}`
        graphStore.edges.set(edgeId, {
          id: edgeId,
          source: nodeId,
          target: calleeId,
          type: 'CALLS',
          isSeam: false,
        })
      }
    })
  }

  updateGraph()
}

const calculateNodeSize = (nodeId: string, node: any): number => {
  if (!cy) return 60
  
  switch (nodeSizeMode.value) {
    case 'degree':
      const inDegree = graphStore.edgeArray.filter(e => e.target === nodeId).length
      const outDegree = graphStore.edgeArray.filter(e => e.source === nodeId).length
      const degree = inDegree + outDegree
      const baseSize = 50
      const maxSize = 100
      const sizeIncrement = Math.min(degree * 5, 50)
      return baseSize + sizeIncrement
    
    case 'complexity':
      const complexity = node.complexity || 1
      const minSize = 40
      const maxSize = 120
      return minSize + Math.min(complexity * 8, maxSize - minSize)
    
    case 'fixed':
    default:
      return 60
  }
}

const getNodeColor = (node: any, nodeId: string): string => {
  // Check if this is an entry point
  if (entryPoints.value.has(nodeId)) {
    return nodeTypeColors.entry_point
  }
  
  // Check for specific node types
  if (node.type && nodeTypeColors[node.type]) {
    return nodeTypeColors[node.type]
  }
  
  return nodeTypeColors.default
}

const updateGraph = () => {
  if (!cy) return

  const nodes = (graphStore.nodeArray || []).map((n) => {
    const isEntryPoint = entryPoints.value.has(n.id)
    const size = calculateNodeSize(n.id, n)
    const isHub = size > 80
    
    return {
      data: {
        id: n.id,
        label: n.name.substring(0, 20) + (n.name.length > 20 ? '...' : ''),
        color: getNodeColor(n, n.id),
        size: size,
        type: n.type,
        isEntryPoint,
        isHub,
        complexity: n.complexity || 0,
        language: n.language || 'unknown',
      },
      classes: [
        isEntryPoint ? 'entry-point' : '',
        isHub ? 'hub' : '',
        'expandable'
      ].filter(Boolean).join(' ')
    }
  })

  const edges = (graphStore.edgeArray || []).map((e) => ({
    data: {
      id: e.id,
      source: e.source,
      target: e.target,
      isSeam: e.isSeam,
      type: e.type,
    },
  }))

  cy.elements().remove()
  cy.add([...nodes, ...edges])

  runLayout()
}

const runLayout = () => {
  if (!cy) return
  
  const layoutConfig: any = {
    name: layoutType.value,
    directed: true,
    animate: true,
    animationDuration: 500,
    fit: true,
    padding: 50,
  }

  switch (layoutType.value) {
    case 'dagre':
      layoutConfig.rankDir = 'TB'
      layoutConfig.ranker = 'longest-path'
      layoutConfig.nodeSep = 80
      layoutConfig.rankSep = 100
      break
      
    case 'breadthfirst':
      layoutConfig.spacingFactor = 1.8
      layoutConfig.roots = Array.from(entryPoints.value)
      break
      
    case 'circle':
      layoutConfig.avoidOverlap = true
      layoutConfig.spacingFactor = 1.2
      break
      
    case 'cola':
      layoutConfig.refresh = 10
      layoutConfig.maxSimulationTime = 1500
      layoutConfig.padding = 10
      break
      
    case 'klay':
      layoutConfig.klay = {
        direction: 'RIGHT',
        edgeRouting: 'ORTHOGONAL',
        nodePlacement: 'LINEAR_SEGMENTS'
      }
      break
  }

  cy.layout(layoutConfig).run()
  
  if (graphStore.selectedNodeId) {
    highlightConnections(graphStore.selectedNodeId)
  }
}

const fitGraph = () => {
  if (cy) {
    cy.fit(undefined, 50)
  }
}

const centerOnSelected = () => {
  if (cy && graphStore.selectedNodeId) {
    const node = cy.getElementById(graphStore.selectedNodeId)
    if (node) {
      cy.animate({
        center: { eles: node },
        zoom: 1.5,
      }, {
        duration: 500
      })
    }
  }
}

onMounted(() => {
  initCytoscape()
  updateGraph()
})

watch(() => [graphStore.nodeArray, graphStore.edgeArray], updateGraph, { deep: true })
watch(layoutType, runLayout)
</script>

<template>
  <div class="relative w-full h-full">
    <div ref="container" class="w-full h-full bg-base-100"></div>
    
    <div class="absolute top-4 right-4 flex flex-col gap-2">
      <div class="card bg-base-200/90 backdrop-blur shadow-xl">
        <div class="card-body p-3 space-y-2">
          <div class="text-xs font-bold text-base-content/80">Graph Controls</div>
          
          <div class="form-control">
            <label class="label py-1">
              <span class="label-text text-xs">Layout</span>
            </label>
            <select v-model="layoutType" class="select select-bordered select-xs">
              <option value="dagre">DAG (Hierarchical)</option>
              <option value="breadthfirst">Breadth-First</option>
              <option value="circle">Circular</option>
              <option value="cola">Force-Directed (COLA)</option>
              <option value="klay">KLay</option>
            </select>
          </div>

          <div class="form-control">
            <label class="label py-1">
              <span class="label-text text-xs">Node Size</span>
            </label>
            <select v-model="nodeSizeMode" class="select select-bordered select-xs">
              <option value="degree">By Degree</option>
              <option value="complexity">By Complexity</option>
              <option value="fixed">Fixed Size</option>
            </select>
          </div>

          <div class="form-control">
            <label class="label py-1">
              <span class="label-text text-xs">Expand Mode</span>
            </label>
            <select v-model="expandMode" class="select select-bordered select-xs">
              <option value="both">Both</option>
              <option value="callers">Callers Only</option>
              <option value="callees">Callees Only</option>
            </select>
          </div>

          <div class="form-control">
            <label class="label cursor-pointer py-1">
              <span class="label-text text-xs">Show Entry Points</span>
              <input 
                type="checkbox" 
                class="toggle toggle-primary toggle-xs" 
                v-model="showEntryPointHighlights"
              />
            </label>
          </div>

          <div class="divider my-1"></div>

          <button @click="fitGraph" class="btn btn-primary btn-xs gap-1">
            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" class="w-3 h-3 stroke-current">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 8V4m0 0h4M4 4l5 5m11-1V4m0 0h-4m4 0l-5 5M4 16v4m0 0h4m-4 0l5-5m11 5l-5-5m5 5v-4m0 4h-4" />
            </svg>
            Fit Graph
          </button>

          <button @click="centerOnSelected" :disabled="!graphStore.selectedNodeId" class="btn btn-secondary btn-xs gap-1">
            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" class="w-3 h-3 stroke-current">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
            </svg>
            Center Selected
          </button>
        </div>
      </div>

      <div class="card bg-base-200/90 backdrop-blur shadow-xl">
        <div class="card-body p-3 space-y-1">
          <div class="text-xs font-bold text-base-content/80 mb-1">Legend</div>
          <div class="flex items-center gap-2 text-xs">
            <div class="w-3 h-3 rounded-full border-2 border-accent" style="border-style: double;"></div>
            <span class="text-base-content/70">Entry Point</span>
          </div>
          <div class="flex items-center gap-2 text-xs">
            <div class="w-3 h-3 rounded-full border-2 border-warning"></div>
            <span class="text-base-content/70">Hub Node</span>
          </div>
          <div class="flex items-center gap-2 text-xs">
            <div class="w-8 h-0.5 bg-error" style="border-style: dashed; border-width: 1px;"></div>
            <span class="text-base-content/70">SEAM Edge</span>
          </div>
        </div>
      </div>
    </div>

    <div class="absolute bottom-4 left-4 card bg-base-200/90 backdrop-blur shadow-xl">
      <div class="card-body p-3">
        <div class="text-xs text-base-content/70">
          <strong>Tip:</strong> Double-click nodes to expand
        </div>
      </div>
    </div>
  </div>
</template>
