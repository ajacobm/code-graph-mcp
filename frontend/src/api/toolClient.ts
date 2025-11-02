import axios from 'axios'
import type { AxiosInstance } from 'axios'

export interface QueryResultItem {
  [key: string]: any
}

export interface QueryResultResponse {
  symbol: string
  total_callers?: number
  total_callees?: number
  total_references?: number
  callers?: QueryResultItem[]
  callees?: QueryResultItem[]
  references?: QueryResultItem[]
  execution_time_ms: number
}

export class ToolClient {
  private client: AxiosInstance

  constructor(baseURL = '/api') {
    this.client = axios.create({
      baseURL,
      timeout: 30000,
    })
  }

  async findCallers(symbol: string): Promise<QueryResultResponse> {
    const { data } = await this.client.get('/graph/query/callers', {
      params: { symbol },
    })
    return data
  }

  async findCallees(symbol: string): Promise<QueryResultResponse> {
    const { data } = await this.client.get('/graph/query/callees', {
      params: { symbol },
    })
    return data
  }

  async findReferences(symbol: string): Promise<QueryResultResponse> {
    const { data } = await this.client.get('/graph/query/references', {
      params: { symbol },
    })
    return data
  }
}

export const toolClient = new ToolClient()
