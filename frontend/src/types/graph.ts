export interface NodeResponse {
  id: string
  name: string
  type: string
  language: string
  file_path: string
  line: number
  column: number
  complexity: number
  docstring?: string
}

export interface RelationshipResponse {
  source_id: string
  target_id: string
  type: string
  metadata?: Record<string, unknown>
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
  top_functions: Array<{
    id: string
    name: string
    call_count: number
  }>
}

export interface SearchResultResponse {
  results: NodeResponse[]
  count: number
}

export interface SeamResponse {
  source_id: string
  target_id: string
  source_language: string
  target_language: string
  seam_type: string
  confidence: number
}

export interface Node {
  id: string
  name: string
  type: string
  language: string
  file_path: string
  line: number
  complexity: number
  docstring?: string
}

export interface Edge {
  id: string
  source: string
  target: string
  type: string
  isSeam: boolean
}

export interface GraphState {
  nodes: Map<string, Node>
  edges: Map<string, Edge>
  selectedNodeId: string | null
  isLoading: boolean
  error: string | null
  viewMode: 'full' | 'call_chain' | 'seams_only'
  stats: GraphStatsResponse | null
}

export interface FilterState {
  languages: string[]
  nodeTypes: string[]
  seamOnly: boolean
  complexityRange: [number, number]
  searchQuery: string
}

export interface QueryResult {
  [key: string]: unknown
}

export interface QueryResultsResponse {
  symbol: string
  total_callers?: number
  total_callees?: number
  total_references?: number
  callers?: QueryResult[]
  callees?: QueryResult[]
  references?: QueryResult[]
  execution_time_ms: number
}
