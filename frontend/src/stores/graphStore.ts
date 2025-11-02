import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { Node, Edge } from '../types/graph'
import type { GraphStatsResponse } from '../types/graph'
import { graphClient } from '../api/graphClient'

export const useGraphStore = defineStore('graph', () => {
  const nodes = ref<Map<string, Node>>(new Map())
  const edges = ref<Map<string, Edge>>(new Map())
  const selectedNodeId = ref<string | null>(null)
  const isLoading = ref(false)
  const error = ref<string | null>(null)
  const viewMode = ref<'full' | 'call_chain' | 'seams_only'>('full')
  const stats = ref<GraphStatsResponse | null>(null)

  // Local filter state (avoid circular dependency with filterStore)
  const languages = ref<string[]>([])
  const nodeTypes = ref<string[]>([])
  const seamOnly = ref(false)
  const complexityRange = ref<[number, number]>([0, 50])
  const searchQuery = ref('')

  const selectedNode = computed(() => {
    return selectedNodeId.value ? nodes.value.get(selectedNodeId.value) : null
  })

  const nodeArray = computed(() => Array.from(nodes.value.values()))
  const edgeArray = computed(() => Array.from(edges.value.values()))

  const filteredNodeArray = computed(() => {
    return nodeArray.value.filter((node) => {
      if (languages.value.length > 0 && !languages.value.includes(node.language)) {
        return false
      }
      if (nodeTypes.value.length > 0 && !nodeTypes.value.includes(node.type)) {
        return false
      }
      if (node.complexity < complexityRange.value[0] || node.complexity > complexityRange.value[1]) {
        return false
      }
      if (searchQuery.value && !node.name.toLowerCase().includes(searchQuery.value.toLowerCase())) {
        return false
      }
      return true
    })
  })

  const filteredEdgeArray = computed(() => {
    const nodeIds = new Set(filteredNodeArray.value.map((n) => n.id))
    return edgeArray.value.filter((edge) => {
      if (!nodeIds.has(edge.source) || !nodeIds.has(edge.target)) {
        return false
      }
      if (seamOnly.value && !edge.isSeam) {
        return false
      }
      return true
    })
  })

  async function loadStats() {
    try {
      isLoading.value = true
      error.value = null
      stats.value = await graphClient.getStats()
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Failed to load stats'
    } finally {
      isLoading.value = false
    }
  }

  async function traverse(startNodeId: string, maxDepth: number = 5) {
    try {
      isLoading.value = true
      error.value = null
      const result = await graphClient.traverse(startNodeId, 'dfs', maxDepth, true)

      if (!result.nodes || result.nodes.length === 0) {
        error.value = `No nodes found for ${startNodeId}`
        setTimeout(() => { error.value = null }, 3000)
        return
      }

      nodes.value.clear()
      edges.value.clear()

      const resultNodes = result.nodes || []
      const resultRelationships = result.relationships || []

      resultNodes.forEach((n) => {
        nodes.value.set(n.id, {
          id: n.id,
          name: n.name,
          type: n.type,
          language: n.language,
          file_path: n.file_path,
          line: n.line,
          complexity: n.complexity,
          docstring: n.docstring,
        })
      })

      resultRelationships.forEach((r) => {
        const edgeId = `${r.source_id}-${r.target_id}`
        edges.value.set(edgeId, {
          id: edgeId,
          source: r.source_id,
          target: r.target_id,
          type: r.type,
          isSeam: r.type === 'SEAM',
        })
      })

      viewMode.value = 'full'
      selectedNodeId.value = startNodeId
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Failed to traverse'
      setTimeout(() => { error.value = null }, 3000)
    } finally {
      isLoading.value = false
    }
  }

  async function loadCallChain(startNodeId: string, maxDepth: number = 10) {
    try {
      isLoading.value = true
      error.value = null
      const result = await graphClient.getCallChain(startNodeId, true, maxDepth)

      if (!result.chain || result.chain.length === 0) {
        error.value = `No call chain found for ${startNodeId}`
        setTimeout(() => { error.value = null }, 3000)
        return
      }

      nodes.value.clear()
      edges.value.clear()

      const resultChain = result.chain || []
      const resultSeams = result.seams || []

      resultChain.forEach((n) => {
        nodes.value.set(n.id, {
          id: n.id,
          name: n.name,
          type: n.type,
          language: n.language,
          file_path: n.file_path,
          line: n.line,
          complexity: n.complexity,
          docstring: n.docstring,
        })
      })

      for (let i = 0; i < resultChain.length - 1; i++) {
        const current = resultChain[i]
        const next = resultChain[i + 1]
        if (current && next) {
          const edgeId = `${current.id}-${next.id}`
          edges.value.set(edgeId, {
            id: edgeId,
            source: current.id,
            target: next.id,
            type: 'CALLS',
            isSeam: resultSeams.some((s) => s.from_index === i),
          })
        }
      }

      viewMode.value = 'call_chain'
      selectedNodeId.value = startNodeId
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Failed to load call chain'
      setTimeout(() => { error.value = null }, 3000)
    } finally {
      isLoading.value = false
    }
  }

  function selectNode(nodeId: string | null) {
    selectedNodeId.value = nodeId
  }

  function clearGraph() {
    nodes.value.clear()
    edges.value.clear()
    selectedNodeId.value = null
  }

  function setLanguages(langs: string[]) {
    languages.value = langs
  }

  function setNodeTypes(types: string[]) {
    nodeTypes.value = types
  }

  function setSeamOnly(value: boolean) {
    seamOnly.value = value
  }

  function setComplexityRange(range: [number, number]) {
    complexityRange.value = range
  }

  function setSearchQuery(query: string) {
    searchQuery.value = query
  }

  async function findCallers(symbolName: string) {
    try {
      isLoading.value = true
      error.value = null
      const result = await graphClient.findCallers(symbolName)
      return result.callers || []
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Failed to find callers'
      return []
    } finally {
      isLoading.value = false
    }
  }

  async function findCallees(symbolName: string) {
    try {
      isLoading.value = true
      error.value = null
      const result = await graphClient.findCallees(symbolName)
      return result.callees || []
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Failed to find callees'
      return []
    } finally {
      isLoading.value = false
    }
  }

  async function findReferences(symbolName: string) {
    try {
      isLoading.value = true
      error.value = null
      const result = await graphClient.findReferences(symbolName)
      return result.references || []
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Failed to find references'
      return []
    } finally {
      isLoading.value = false
    }
  }

  return {
    nodes,
    edges,
    selectedNodeId,
    isLoading,
    error,
    viewMode,
    stats,
    languages,
    nodeTypes,
    seamOnly,
    complexityRange,
    searchQuery,
    selectedNode,
    nodeArray,
    edgeArray,
    filteredNodeArray,
    filteredEdgeArray,
    loadStats,
    traverse,
    loadCallChain,
    selectNode,
    clearGraph,
    setLanguages,
    setNodeTypes,
    setSeamOnly,
    setComplexityRange,
    setSearchQuery,
    findCallers,
    findCallees,
    findReferences,
  }
})
