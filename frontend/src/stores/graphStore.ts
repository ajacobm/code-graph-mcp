/**
 * Graph Store
 * 
 * Zustand store for graph state management.
 */

import { create } from 'zustand'
import type { GraphData, GraphNode, FilterOptions } from '@/types'
import { fetchGraphExport } from '@/api/graphApi'

interface GraphState {
  // Graph data
  graphData: GraphData | null
  isLoading: boolean
  error: string | null
  
  // Selection state
  selectedNodeId: string | null
  highlightedNodeIds: string[]
  hoveredNodeId: string | null
  
  // Filter state
  filters: FilterOptions
  
  // Display options
  showLabels: boolean
  colorMode: 'type' | 'language' | 'complexity'
  
  // Actions
  loadGraph: (options?: { language?: string; nodeType?: string }) => Promise<void>
  selectNode: (nodeId: string | null) => void
  hoverNode: (nodeId: string | null) => void
  highlightNodes: (nodeIds: string[]) => void
  setFilter: (filter: Partial<FilterOptions>) => void
  setShowLabels: (show: boolean) => void
  setColorMode: (mode: 'type' | 'language' | 'complexity') => void
  getSelectedNode: () => GraphNode | null
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
  isLoading: false,
  error: null,
  selectedNodeId: null,
  highlightedNodeIds: [],
  hoveredNodeId: null,
  filters: defaultFilters,
  showLabels: true,
  colorMode: 'type',

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
      set({ graphData: data, isLoading: false })
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

  getSelectedNode: () => {
    const { graphData, selectedNodeId } = get()
    if (!graphData || !selectedNodeId) return null
    return graphData.nodes.find(n => n.id === selectedNodeId) || null
  },
}))
