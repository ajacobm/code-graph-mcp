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

  const selectedNode = computed(() => {
    return selectedNodeId.value ? nodes.value.get(selectedNodeId.value) : null
  })

  const nodeArray = computed(() => Array.from(nodes.value.values()))
  const edgeArray = computed(() => Array.from(edges.value.values()))

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

      nodes.value.clear()
      edges.value.clear()

      result.nodes.forEach((n) => {
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

      result.relationships.forEach((r) => {
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
    } finally {
      isLoading.value = false
    }
  }

  async function loadCallChain(startNodeId: string, maxDepth: number = 10) {
    try {
      isLoading.value = true
      error.value = null
      const result = await graphClient.getCallChain(startNodeId, true, maxDepth)

      nodes.value.clear()
      edges.value.clear()

      result.chain.forEach((n) => {
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

      for (let i = 0; i < result.chain.length - 1; i++) {
        const current = result.chain[i]
        const next = result.chain[i + 1]
        if (current && next) {
          const edgeId = `${current.id}-${next.id}`
          edges.value.set(edgeId, {
            id: edgeId,
            source: current.id,
            target: next.id,
            type: 'CALLS',
            isSeam: result.seams.some((s) => s.from_index === i),
          })
        }
      }

      viewMode.value = 'call_chain'
      selectedNodeId.value = startNodeId
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Failed to load call chain'
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

  return {
    nodes,
    edges,
    selectedNodeId,
    isLoading,
    error,
    viewMode,
    stats,
    selectedNode,
    nodeArray,
    edgeArray,
    loadStats,
    traverse,
    loadCallChain,
    selectNode,
    clearGraph,
  }
})
