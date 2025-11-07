import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { Node, Edge, NodeResponse, RelationshipResponse, GraphStatsResponse } from '../types/graph'
import { graphClient } from '../api/graphClient'

export const useGraphStore = defineStore('graph', () => {
  // State
  const nodes = ref<Node[]>([])
  const relationships = ref<Edge[]>([])
  const selectedNodeId = ref<string | null>(null)
  const isLoading = ref(false)
  const error = ref<string | null>(null)
  const stats = ref<GraphStatsResponse | null>(null)

  // Computed
  const selectedNode = computed(() => {
    return nodes.value.find(n => n.id === selectedNodeId.value) || null
  })

  // Helper to convert API node to internal format
  function toInternalNode(n: NodeResponse): Node {
    return {
      id: n.id,
      name: n.name,
      node_type: n.node_type,
      language: n.language || 'unknown',
      complexity: n.complexity || 0,
      location: n.location,
      metadata: n.metadata
    }
  }

  // Helper to convert API relationship to internal format
  function toInternalEdge(r: RelationshipResponse): Edge {
    return {
      id: r.id || `${r.source_id}-${r.target_id}`,
      source: r.source_id,
      target: r.target_id,
      relationship_type: r.relationship_type,
      isSeam: r.relationship_type === 'seam'
    }
  }

  // Actions
  async function loadStats() {
    try {
      isLoading.value = true
      error.value = null
      stats.value = await graphClient.getStats()
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Failed to load stats'
      console.error('Failed to load stats:', err)
    } finally {
      isLoading.value = false
    }
  }

  async function loadFullGraph() {
    try {
      isLoading.value = true
      error.value = null
      
      // Get all nodes via search with empty query
      const searchResults = await graphClient.searchNodes('')
      const apiNodes = searchResults.results || []
      
      // Convert to internal format
      nodes.value = apiNodes.map(toInternalNode)
      
      // For now, don't load all relationships (too many)
      // Instead, load on-demand when a node is selected
      relationships.value = []
      
      console.log(`Loaded ${nodes.value.length} nodes`)
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Failed to load graph'
      console.error('Failed to load graph:', err)
    } finally {
      isLoading.value = false
    }
  }

  async function loadNodeConnections(nodeId: string) {
    try {
      isLoading.value = true
      error.value = null
      
      // Get node and its immediate connections
      const node = nodes.value.find(n => n.id === nodeId)
      if (!node) return
      
      // Load callers and callees
      const symbol = node.name
      const [callersResult, calleesResult] = await Promise.all([
        graphClient.findCallers(symbol).catch(() => ({ results: [] })),
        graphClient.findCallees(symbol).catch(() => ({ results: [] }))
      ])
      
      // Add any new nodes we discovered
      const discoveredNodes = [
        ...(callersResult.results || []),
        ...(calleesResult.results || [])
      ]
      
      discoveredNodes.forEach((n: any) => {
        if (!nodes.value.find(existing => existing.id === n.id)) {
          nodes.value.push({
            id: n.id,
            name: n.name,
            node_type: n.node_type,
            language: n.language || 'unknown',
            complexity: n.complexity || 0,
            location: n.location,
            metadata: {}
          })
        }
      })
      
      // Create relationship edges
      const newEdges: Edge[] = []
      
      callersResult.results?.forEach((caller: any) => {
        newEdges.push({
          id: `${caller.id}-${nodeId}`,
          source: caller.id,
          target: nodeId,
          relationship_type: 'calls',
          isSeam: false
        })
      })
      
      calleesResult.results?.forEach((callee: any) => {
        newEdges.push({
          id: `${nodeId}-${callee.id}`,
          source: nodeId,
          target: callee.id,
          relationship_type: 'calls',
          isSeam: false
        })
      })
      
      // Add edges that don't already exist
      newEdges.forEach(edge => {
        if (!relationships.value.find(e => e.id === edge.id)) {
          relationships.value.push(edge)
        }
      })
      
      console.log(`Loaded connections for ${node.name}: ${callersResult.results?.length || 0} callers, ${calleesResult.results?.length || 0} callees`)
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Failed to load node connections'
      console.error('Failed to load node connections:', err)
    } finally {
      isLoading.value = false
    }
  }

  async function reanalyze() {
    try {
      isLoading.value = true
      error.value = null
      
      const response = await fetch('http://localhost:8000/api/graph/admin/reanalyze', {
        method: 'POST'
      })
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }
      
      const result = await response.json()
      console.log('Re-analysis complete:', result)
      
      // Reload graph data
      await loadFullGraph()
      await loadStats()
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Failed to re-analyze'
      console.error('Failed to re-analyze:', err)
    } finally {
      isLoading.value = false
    }
  }

  function selectNode(nodeId: string | null) {
    selectedNodeId.value = nodeId
    // Auto-load connections when a node is selected
    if (nodeId) {
      loadNodeConnections(nodeId)
    }
  }

  function clearGraph() {
    nodes.value = []
    relationships.value = []
    selectedNodeId.value = null
  }

  return {
    // State
    nodes,
    relationships,
    selectedNodeId,
    isLoading,
    error,
    stats,
    
    // Computed
    selectedNode,
    
    // Actions
    loadStats,
    loadFullGraph,
    loadNodeConnections,
    reanalyze,
    selectNode,
    clearGraph
  }
})
