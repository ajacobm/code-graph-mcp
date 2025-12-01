/**
 * Graph Data Types
 * 
 * Types for the code graph visualization data structures.
 */

// Node in the force-directed graph
export interface GraphNode {
  id: string
  name: string
  type: string
  language: string
  complexity: number
  file: string
  line: number
  metadata?: {
    docstring?: string
    line_count?: number
    end_line?: number
  }
}

// Link/edge in the force-directed graph
export interface GraphLink {
  source: string
  target: string
  type: string
  isSeam: boolean
}

// Graph statistics
export interface GraphStats {
  totalNodes: number
  totalLinks: number
  languages: Record<string, number>
  nodeTypes: Record<string, number>
  avgComplexity: number
}

// Complete graph data structure from API
export interface GraphData {
  nodes: GraphNode[]
  links: GraphLink[]
  stats: GraphStats
  execution_time_ms: number
}

// Force graph node with position data (2D and 3D support)
export interface ForceGraphNode extends GraphNode {
  x?: number
  y?: number
  z?: number // 3D support
  vx?: number
  vy?: number
  vz?: number // 3D support
  fx?: number | null
  fy?: number | null
  fz?: number | null // 3D support
  val?: number
  color?: string
}

// Force graph link with resolved nodes
export interface ForceGraphLink {
  source: string | ForceGraphNode
  target: string | ForceGraphNode
  type: string
  isSeam: boolean
}

// Filter options
export interface FilterOptions {
  languages: string[]
  nodeTypes: string[]
  searchQuery: string
  minComplexity: number
  maxComplexity: number
  showSeamsOnly: boolean
}

// API response for graph stats
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

// Category response
export interface CategoryResponse {
  category: string
  total: number
  offset: number
  limit: number
  nodes: GraphNode[]
  execution_time_ms: number
}

// Navigation stack entry for drill-down navigation
export interface NavigationEntry {
  nodeId: string
  nodeName: string
  nodeType: string
  timestamp: number
}

// Graph display mode
export type GraphDimension = '2d' | '3d'
