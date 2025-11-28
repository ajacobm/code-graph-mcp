// API Response Types (match backend exactly)
export interface NodeResponse {
  id: string
  name: string
  node_type: string
  language: string
  complexity?: number
  docstring?: string
  location?: {
    file_path: string
    start_line: number
    end_line: number
  }
  metadata?: Record<string, any>
}

export interface RelationshipResponse {
  id: string
  source_id: string
  target_id: string
  relationship_type: string
  metadata?: Record<string, any>
}

export interface TraversalResponse {
  start_node: NodeResponse
  nodes: NodeResponse[]
  relationships: RelationshipResponse[]
  stats: {
    total_nodes: number
    total_relationships: number
    traversal_depth: number
    seam_count: number
  }
}

export interface CallChainResponse {
  chain: NodeResponse[]
  seams: Array<{
    from_index: number
    to_index: number
    languages: [string, string]
  }>
  stats: {
    depth: number
    seam_count: number
  }
}

export interface GraphStatsResponse {
  total_nodes: number
  total_relationships: number
  languages: Record<string, number>
  node_types?: Record<string, number>
  top_functions?: Array<{
    id: string
    name: string
    complexity: number
  }>
}

export interface SearchResultResponse {
  results: NodeResponse[]
  total: number
}

export interface QueryResult {
  id: string
  name: string
  node_type: string
  language: string
  complexity?: number
  location?: {
    file_path: string
    start_line: number
  }
}

export interface QueryResultsResponse {
  symbol: string
  results?: QueryResult[]
  callers?: QueryResult[]
  callees?: QueryResult[]
  references?: QueryResult[]
  total_callers?: number
  total_callees?: number
  total_references?: number
  limit?: number
  offset?: number
  execution_time_ms: number
}

export interface SeamResponse {
  id: string
  source_id: string
  target_id: string
  source_language: string
  target_language: string
  confidence: number
}

export interface SubgraphResponse {
  nodes: NodeResponse[]
  relationships: RelationshipResponse[]
  total_nodes: number
  total_relationships: number
}

// Internal Store Types (simplified)
export interface Node {
  id: string
  name: string
  node_type: string
  language: string
  complexity: number
  location?: {
    file_path: string
    start_line: number
  }
  metadata?: Record<string, any>
}

export interface Edge {
  id: string
  source: string
  target: string
  relationship_type: string
  isSeam: boolean
}

// Force Graph Types
export interface GraphData {
  nodes: Node[]
  relationships: Edge[]
}
