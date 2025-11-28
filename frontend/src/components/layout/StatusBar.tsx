/**
 * StatusBar Component
 * 
 * Bottom status bar with connection status and performance metrics.
 */

import { useGraphStore } from '@/stores/graphStore'

interface StatusBarProps {
  wsConnected?: boolean
}

export function StatusBar({ wsConnected = false }: StatusBarProps) {
  const { graphData, isLoading, error } = useGraphStore()
  const stats = graphData?.stats

  return (
    <footer className="bg-slate-900 border-t border-slate-700 px-4 py-2 flex items-center justify-between text-xs text-slate-400">
      <div className="flex items-center gap-4">
        {/* Node count */}
        {stats && (
          <>
            <span>Nodes: <span className="text-slate-200">{stats.totalNodes}</span></span>
            <span>Edges: <span className="text-slate-200">{stats.totalLinks}</span></span>
          </>
        )}
        
        {/* Loading indicator */}
        {isLoading && (
          <span className="flex items-center gap-1 text-indigo-400">
            <span className="animate-pulse">●</span> Loading...
          </span>
        )}
        
        {/* Error indicator */}
        {error && (
          <span className="flex items-center gap-1 text-red-400" title={error}>
            ⚠️ Error
          </span>
        )}
      </div>

      <div className="flex items-center gap-4">
        {/* WebSocket status */}
        <span className="flex items-center gap-1">
          WebSocket: 
          <span className={wsConnected ? 'text-green-400' : 'text-slate-500'}>
            {wsConnected ? '● Connected' : '○ Disconnected'}
          </span>
        </span>

        {/* Average complexity */}
        {stats?.avgComplexity !== undefined && (
          <span>
            Avg Complexity: <span className="text-slate-200">{stats.avgComplexity.toFixed(1)}</span>
          </span>
        )}
      </div>
    </footer>
  )
}
