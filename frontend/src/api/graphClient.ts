import axios from 'axios'
import type { AxiosInstance } from 'axios'
import type {
  NodeResponse,
  TraversalResponse,
  CallChainResponse,
  GraphStatsResponse,
  SearchResultResponse,
  SeamResponse,
  QueryResultsResponse,
} from '../types/graph'

export interface EntryPointResponse {
  id: string
  name: string
  file_path: string
  language: string
  line_number: number
  pattern_matched: string
  confidence_score: number
  complexity: number
  type: string
}

export class GraphClient {
  private client: AxiosInstance
  baseURL: string

  constructor() {
    // Build API URL based on current location
    // Always use direct localhost:8000 when available
    // Vite proxy for /api doesn't work from browser to container
    let baseURL = 'http://localhost:8000/api'
    
    // In production (non-localhost), fall back to relative path
    if (typeof window !== 'undefined' && window.location.hostname !== 'localhost') {
      baseURL = '/api'
    }
    
    this.baseURL = baseURL
    
    this.client = axios.create({
      baseURL,
      timeout: 30000,
      withCredentials: false,
    })
  }

  async getStats(): Promise<GraphStatsResponse> {
    const { data } = await this.client.get('/graph/stats')
    return data
  }

  async getNode(nodeId: string): Promise<NodeResponse> {
    const { data } = await this.client.get(`/graph/nodes/${nodeId}`)
    return data
  }

  async traverse(
    startNode: string,
    queryType: 'dfs' | 'bfs' = 'dfs',
    maxDepth: number = 5,
    includeSeams: boolean = true
  ): Promise<TraversalResponse> {
    const { data } = await this.client.post('/graph/traverse', {
      start_node: startNode,
      query_type: queryType,
      max_depth: maxDepth,
      include_seams: includeSeams,
    })
    return data
  }

  async searchNodes(
    query: string,
    language?: string,
    nodeType?: string,
    limit: number = 50
  ): Promise<SearchResultResponse> {
    const { data } = await this.client.get('/graph/nodes/search', {
      params: {
        q: query,
        language,
        type: nodeType,
        limit,
      },
    })
    return data
  }

  async getSeams(limit: number = 100): Promise<SeamResponse[]> {
    const { data } = await this.client.get('/graph/seams', {
      params: { limit },
    })
    return data
  }

  async getCallChain(
    startNode: string,
    followSeams: boolean = true,
    maxDepth: number = 10
  ): Promise<CallChainResponse> {
    const { data } = await this.client.get(`/graph/call-chain/${startNode}`, {
      params: {
        follow_seams: followSeams,
        max_depth: maxDepth,
      },
    })
    return data
  }

  async findCallers(symbol: string): Promise<QueryResultsResponse> {
    const { data } = await this.client.get('/graph/query/callers', {
      params: { symbol },
    })
    return data
  }

  async findCallees(symbol: string): Promise<QueryResultsResponse> {
    const { data } = await this.client.get('/graph/query/callees', {
      params: { symbol },
    })
    return data
  }

  async findReferences(symbol: string): Promise<QueryResultsResponse> {
    const { data } = await this.client.get('/graph/query/references', {
      params: { symbol },
    })
    return data
  }

  async getNodesByCategory(
    category: 'entry_points' | 'hubs' | 'leaves',
    limit: number = 50,
    offset: number = 0
  ): Promise<{ nodes: NodeResponse[]; total: number }> {
    const { data } = await this.client.get(`/graph/categories/${category}`, {
      params: { limit, offset },
    })
    return data
  }

  async getSubgraph(
    nodeId: string,
    depth: number = 2,
    limit: number = 100
  ): Promise<TraversalResponse> {
    const { data } = await this.client.post('/graph/subgraph', {
      node_id: nodeId,
      depth,
      limit,
    })
    return data
  }

  async getEntryPoints(
    limit: number = 50,
    minConfidence: number = 0.5
  ): Promise<{ entry_points: EntryPointResponse[]; total_count: number }> {
    const { data } = await this.client.get('/graph/entry-points', {
      params: { limit, min_confidence: minConfidence },
    })
    return data
  }
}

export const graphClient = new GraphClient()
