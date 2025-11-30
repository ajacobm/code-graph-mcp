/**
 * Graph API Client
 * 
 * HTTP client for the code graph API endpoints.
 */

import type { GraphData, GraphStatsResponse, CategoryResponse } from '@/types'

const API_BASE = import.meta.env.VITE_API_URL 
  ? `${import.meta.env.VITE_API_URL}/api`
  : (import.meta.env.DEV ? 'http://localhost:10102/api' : '/api')

export async function fetchGraphExport(options?: {
  limit?: number
  language?: string
  nodeType?: string
  includeMetadata?: boolean
}): Promise<GraphData> {
  const params = new URLSearchParams()
  params.set('limit', String(options?.limit ?? 5000))
  params.set('include_metadata', String(options?.includeMetadata ?? true))
  if (options?.language) params.set('language', options.language)
  if (options?.nodeType) params.set('node_type', options.nodeType)

  const response = await fetch(`${API_BASE}/graph/export?${params.toString()}`)
  if (!response.ok) {
    throw new Error(`Failed to fetch graph: ${response.status}`)
  }
  return response.json()
}

export async function fetchGraphStats(): Promise<GraphStatsResponse> {
  const response = await fetch(`${API_BASE}/graph/stats`)
  if (!response.ok) {
    throw new Error(`Failed to fetch stats: ${response.status}`)
  }
  return response.json()
}

export async function fetchCategory(
  category: 'entry_points' | 'hubs' | 'leaves',
  limit = 50,
  offset = 0
): Promise<CategoryResponse> {
  const params = new URLSearchParams()
  params.set('limit', String(limit))
  params.set('offset', String(offset))

  const response = await fetch(`${API_BASE}/graph/categories/${category}?${params.toString()}`)
  if (!response.ok) {
    throw new Error(`Failed to fetch category: ${response.status}`)
  }
  return response.json()
}

export async function searchNodes(query: string, limit = 50): Promise<{ results: GraphData['nodes']; total: number }> {
  const params = new URLSearchParams()
  params.set('name', query)
  params.set('limit', String(limit))

  const response = await fetch(`${API_BASE}/graph/nodes/search?${params.toString()}`)
  if (!response.ok) {
    throw new Error(`Failed to search nodes: ${response.status}`)
  }
  const data = await response.json()
  return { results: data.results || [], total: data.total_count || 0 }
}

export async function reanalyze(): Promise<{ status: string; message: string }> {
  const response = await fetch(`${API_BASE}/graph/admin/reanalyze`, {
    method: 'POST',
  })
  if (!response.ok) {
    throw new Error(`Failed to reanalyze: ${response.status}`)
  }
  return response.json()
}

// Subgraph response type
export interface SubgraphResponse {
  node_id: string
  depth: number
  nodes: Array<{
    id: string
    name: string
    type: string
    language: string
    file_path: string
    line: number
    complexity: number
  }>
  relationships: Array<{
    id: string
    source: string
    target: string
    type: string
  }>
  execution_time_ms: number
}

export async function fetchSubgraph(
  nodeId: string,
  depth = 2,
  limit = 100
): Promise<SubgraphResponse> {
  const params = new URLSearchParams()
  params.set('node_id', nodeId)
  params.set('depth', String(depth))
  params.set('limit', String(limit))

  const response = await fetch(`${API_BASE}/graph/subgraph?${params.toString()}`, {
    method: 'POST',
  })
  if (!response.ok) {
    throw new Error(`Failed to fetch subgraph: ${response.status}`)
  }
  return response.json()
}
