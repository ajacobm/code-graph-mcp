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

export class GraphClient {
  private client: AxiosInstance

  constructor(baseURL?: string) {
    let apiUrl = baseURL || import.meta.env.VITE_API_URL || ''
    
    // If VITE_API_URL contains 'code-graph-http' (Docker service name),
    // replace it with localhost for browser access
    if (apiUrl.includes('code-graph-http')) {
      apiUrl = apiUrl.replace('code-graph-http', 'localhost')
    }
    
    // Use /api as default if no URL provided
    if (!apiUrl) {
      apiUrl = '/api'
    }
    
    this.client = axios.create({
      baseURL: apiUrl.endsWith('/api') ? apiUrl : `${apiUrl}/api`,
      timeout: 30000,
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
}

export const graphClient = new GraphClient()
