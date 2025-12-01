/**
 * Graph Store
 * 
 * Zustand store for graph state management.
 */

import { create } from 'zustand'
import type { GraphData, GraphNode, FilterOptions, NavigationEntry, GraphDimension } from '@/types'
import { fetchGraphExport, fetchSubgraph, type SubgraphResponse } from '@/api/graphApi'

// Helper type for subgraph node mapping
interface SubgraphNode {
  id: string
  name: string
  type: string
  language: string
  complexity: number
  file_path: string
  line: number
}

// Helper function to convert subgraph response to GraphData format
function convertSubgraphToGraphData(subgraph: SubgraphResponse): GraphData {
  const nodes = subgraph.nodes.map((n: SubgraphNode) => ({
    id: n.id,
    name: n.name,
    type: n.type,
    language: n.language,
    complexity: n.complexity,
    file: n.file_path,
    line: n.line,
  }))

  // Compute stats from the nodes
  const languages: Record<string, number> = {}
  const nodeTypes: Record<string, number> = {}
  let totalComplexity = 0

  for (const node of nodes) {
    languages[node.language] = (languages[node.language] || 0) + 1
    nodeTypes[node.type] = (nodeTypes[node.type] || 0) + 1
    totalComplexity += node.complexity
  }

  return {
    nodes,
    links: subgraph.relationships.map((r: { source: string; target: string; type: string }) => ({
      source: r.source,
      target: r.target,
      type: r.type,
      isSeam: r.type === 'seam',
    })),
    stats: {
      totalNodes: subgraph.nodes.length,
      totalLinks: subgraph.relationships.length,
      languages,
      nodeTypes,
      avgComplexity: nodes.length > 0 ? totalComplexity / nodes.length : 0,
    },
    execution_time_ms: subgraph.execution_time_ms,
  }
}

interface GraphState {
  // Graph data
  graphData: GraphData | null
  fullGraphData: GraphData | null // Cache of full graph for navigation
  isLoading: boolean
  error: string | null
  
  // Selection state
  selectedNodeId: string | null
  highlightedNodeIds: string[]
  hoveredNodeId: string | null
  
  // Navigation state
  navigationStack: NavigationEntry[]
  focusedNodeId: string | null
  
  // Filter state
  filters: FilterOptions
  
  // Display options
  showLabels: boolean
  colorMode: 'type' | 'language' | 'complexity'
  graphDimension: GraphDimension
  
  // Actions
  loadGraph: (options?: { language?: string; nodeType?: string }) => Promise<void>
  selectNode: (nodeId: string | null) => void
  hoverNode: (nodeId: string | null) => void
  highlightNodes: (nodeIds: string[]) => void
  setFilter: (filter: Partial<FilterOptions>) => void
  setShowLabels: (show: boolean) => void
  setColorMode: (mode: 'type' | 'language' | 'complexity') => void
  setGraphDimension: (dimension: GraphDimension) => void
  getSelectedNode: () => GraphNode | null
  
  // Navigation actions
  drillIntoNode: (nodeId: string) => Promise<void>
  navigateBack: () => void
  resetNavigation: () => void
}

const defaultFilters: FilterOptions = {
  languages: [],
  nodeTypes: [],
  searchQuery: '',
  minComplexity: 0,
  maxComplexity: 100,
  showSeamsOnly: false,
}

export const useGraphStore = create<GraphState>((set, get) => ({
  // Initial state
  graphData: null,
  fullGraphData: null,
  isLoading: false,
  error: null,
  selectedNodeId: null,
  highlightedNodeIds: [],
  hoveredNodeId: null,
  navigationStack: [],
  focusedNodeId: null,
  filters: defaultFilters,
  showLabels: true,
  colorMode: 'type',
  graphDimension: '2d',

  // Actions
  loadGraph: async (options) => {
    set({ isLoading: true, error: null })
    try {
      const data = await fetchGraphExport({
        limit: 5000,
        language: options?.language,
        nodeType: options?.nodeType,
        includeMetadata: true,
      })
      set({ 
        graphData: data, 
        fullGraphData: data, // Cache for navigation
        isLoading: false,
        navigationStack: [],
        focusedNodeId: null,
      })
    } catch (err) {
      set({ 
        error: err instanceof Error ? err.message : 'Failed to load graph',
        isLoading: false 
      })
    }
  },

  selectNode: (nodeId) => {
    set({ selectedNodeId: nodeId })
  },

  hoverNode: (nodeId) => {
    set({ hoveredNodeId: nodeId })
  },

  highlightNodes: (nodeIds) => {
    set({ highlightedNodeIds: nodeIds })
  },

  setFilter: (filter) => {
    set((state) => ({
      filters: { ...state.filters, ...filter }
    }))
  },

  setShowLabels: (show) => {
    set({ showLabels: show })
  },

  setColorMode: (mode) => {
    set({ colorMode: mode })
  },

  setGraphDimension: (dimension) => {
    set({ graphDimension: dimension })
  },

  getSelectedNode: () => {
    const { graphData, selectedNodeId } = get()
    if (!graphData || !selectedNodeId) return null
    return graphData.nodes.find(n => n.id === selectedNodeId) || null
  },

  // Navigation: drill into a node to see its local subgraph
  drillIntoNode: async (nodeId: string) => {
    // Guard against invalid nodeId
    if (!nodeId) {
      console.warn('drillIntoNode: called with invalid nodeId', nodeId)
      return
    }

    const { graphData, navigationStack } = get()
    if (!graphData) {
      console.warn('drillIntoNode: no graphData available')
      return
    }

    const node = graphData.nodes.find(n => n.id === nodeId)
    if (!node) {
      // Node not found in current graph data - this can happen if the graph
      // was updated between the click events or if the node reference is stale
      console.warn(`drillIntoNode: node not found in current graph data: ${nodeId}`)
      return
    }

    set({ isLoading: true, error: null })

    try {
      // Fetch subgraph centered on the node
      const subgraph = await fetchSubgraph(nodeId, 2, 100)
      
      // Create a new navigation entry
      const entry: NavigationEntry = {
        nodeId: node.id,
        nodeName: node.name,
        nodeType: node.type,
        timestamp: Date.now(),
      }

      // Convert subgraph response to GraphData format
      const focusedGraphData = convertSubgraphToGraphData(subgraph)

      set({
        graphData: focusedGraphData,
        navigationStack: [...navigationStack, entry],
        focusedNodeId: nodeId,
        selectedNodeId: nodeId,
        isLoading: false,
      })
    } catch (err) {
      set({ 
        error: err instanceof Error ? err.message : 'Failed to load subgraph',
        isLoading: false 
      })
    }
  },

  // Navigate back in the stack
  navigateBack: async () => {
    const { navigationStack, fullGraphData } = get()
    
    if (navigationStack.length === 0) return

    const newStack = [...navigationStack]
    newStack.pop()
    
    if (newStack.length === 0) {
      // Return to full graph
      set({
        graphData: fullGraphData,
        navigationStack: [],
        focusedNodeId: null,
        selectedNodeId: null,
      })
    } else {
      // Navigate to previous level - fetch the subgraph directly
      const previousEntry = newStack[newStack.length - 1]
      set({ isLoading: true, error: null })
      
      try {
        const subgraph = await fetchSubgraph(previousEntry.nodeId, 2, 100)
        const focusedGraphData = convertSubgraphToGraphData(subgraph)

        set({
          graphData: focusedGraphData,
          navigationStack: newStack,
          focusedNodeId: previousEntry.nodeId,
          selectedNodeId: previousEntry.nodeId,
          isLoading: false,
        })
      } catch (err) {
        set({ 
          error: err instanceof Error ? err.message : 'Failed to navigate back',
          isLoading: false 
        })
      }
    }
  },

  // Reset navigation to full graph
  resetNavigation: () => {
    const { fullGraphData } = get()
    set({
      graphData: fullGraphData,
      navigationStack: [],
      focusedNodeId: null,
      selectedNodeId: null,
    })
  },
}))
