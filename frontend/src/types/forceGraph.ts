/**
 * Force Graph TypeScript Types
 * 
 * Types for force-directed graph visualization data structures.
 */

// Node in the force-directed graph
export interface ForceGraphNode {
  id: string
  name: string
  nodeType: string
  language: string
  complexity: number
  file?: string
  line?: number
  val?: number  // Node size
  color?: string
  
  // Force simulation position (set by library)
  x?: number
  y?: number
  vx?: number
  vy?: number
  
  // Fixed position
  fx?: number
  fy?: number
  
  // Custom state
  highlighted?: boolean
  cluster?: string
}

// Link/edge in the force-directed graph
export interface ForceGraphLink {
  source: string | ForceGraphNode
  target: string | ForceGraphNode
  type: string
  isSeam: boolean
  color?: string
  width?: number
  curvature?: number
}

// Complete graph data structure
export interface GraphData {
  nodes: GraphNode[]
  links: GraphLink[]
  stats?: GraphStats
}

// Raw node from API
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

// Raw link from API
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

// Graph export response from API
export interface GraphExportResponse {
  nodes: GraphNode[]
  links: GraphLink[]
  stats: GraphStats
  execution_time_ms: number
}

// Filter options for graph visualization
export interface GraphFilterOptions {
  nodeTypes: string[]
  languages: string[]
  complexityRange: [number, number]
  relationshipTypes: string[]
  includeSeams: boolean
  namePattern: string
  filePattern: string
  minDegree: number
  maxDepth: number
}

// Highlight options
export interface HighlightOptions {
  mode: 'single' | 'connected' | 'cluster' | 'pathway'
  primaryColor: string
  secondaryColor: string
  fadeOthers: boolean
  pulseEffect: boolean
  trailEffect: boolean
}

// Region/cluster definition
export interface GraphRegion {
  id: string
  name: string
  color: string
  nodeIds: string[]
  isAutoDetected: boolean
}

// Pathway analysis result
export interface PathwayAnalysis {
  startNodeId: string
  endNodeId?: string
  mode: 'call-chain' | 'data-flow' | 'shortest-path' | 'all-paths'
  maxHops: number
  mustPassThrough: string[]
  avoidNodes: string[]
  paths: NodePath[]
  statistics: {
    totalPaths: number
    avgLength: number
    criticalNodes: string[]
  }
}

export interface NodePath {
  nodeIds: string[]
  edges: string[]
  length: number
}
