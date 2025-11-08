import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type {
  Node,
  Edge,
  NodeResponse,
  GraphStatsResponse,
} from '../types/graph'
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

  async function getNodesByCategory(category: 'entry_points' | 'hubs' | 'leaves', limit: number, offset: number) {
    try {
      isLoading.value = true
      error.value = null
      const result = await graphClient.getNodesByCategory(category, limit, offset)
      return result
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Failed to load nodes'
      console.error('Failed to load nodes:', err)
      return { nodes: [], total: 0 }
    } finally {
      isLoading.value = false
    }
  }

  async function loadFullGraph() {
    try {
      isLoading.value = true
      error.value = null
      
      // Load nodes from all categories (workaround - backend has no GET /nodes endpoint)
      const [entryPoints, hubs, leaves] = await Promise.all([
        graphClient.getNodesByCategory('entry_points', 500, 0).catch(() => ({ nodes: [] as NodeResponse[], total: 0 })),
        graphClient.getNodesByCategory('hubs', 500, 0).catch(() => ({ nodes: [] as NodeResponse[], total: 0 })),
        graphClient.getNodesByCategory('leaves', 500, 0).catch(() => ({ nodes: [] as NodeResponse[], total: 0 }))
      ])
      
      // Combine and deduplicate
      const allNodes = [...entryPoints.nodes, ...hubs.nodes, ...leaves.nodes]
      const uniqueNodesMap = new Map<string, NodeResponse>()
      allNodes.forEach(n => uniqueNodesMap.set(n.id, n))
      
      // Convert to internal format
      nodes.value = Array.from(uniqueNodesMap.values()).map(toInternalNode)
      relationships.value = []
      
      console.log(`Loaded ${nodes.value.length} nodes from categories`)
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
        graphClient.findCallers(symbol).catch(() => ({ results: [] as any[] })),
        graphClient.findCallees(symbol).catch(() => ({ results: [] as any[] }))
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
    getNodesByCategory,
    loadFullGraph,
    loadNodeConnections,
    reanalyze,
    selectNode,
    clearGraph
  }
})
