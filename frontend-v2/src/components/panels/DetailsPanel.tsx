/**
 * DetailsPanel Component
 * 
 * Right sidebar showing details of the selected node.
 */

import { useGraphStore } from '@/stores/graphStore'

interface DetailsPanelProps {
  isCollapsed?: boolean
  onToggleCollapse?: () => void
  onViewConnections?: (nodeId: string) => void
  onCenterNode?: (nodeId: string) => void
}

const TYPE_ICONS: Record<string, string> = {
  function: '⚙️',
  class: '📦',
  method: '🔧',
  module: '📄',
  import: '📥',
}

const LANGUAGE_COLORS: Record<string, string> = {
  python: '#3776AB',
  typescript: '#3178C6',
  javascript: '#F7DF1E',
  'c#': '#68217A',
  java: '#ED8B00',
  go: '#00ADD8',
  default: '#64748b',
}

export function DetailsPanel({ 
  isCollapsed = false, 
  onToggleCollapse,
  onViewConnections,
  onCenterNode 
}: DetailsPanelProps) {
  const { getSelectedNode, selectNode } = useGraphStore()
  const node = getSelectedNode()

  const icon = node ? TYPE_ICONS[node.type?.toLowerCase()] || '•' : '🎯'
  const fileName = node?.file?.split('/').pop() || 'Unknown'
  const filePath = node?.file?.split('/').slice(0, -1).join('/') || ''
  const langColor = LANGUAGE_COLORS[node?.language?.toLowerCase() || 'default'] || LANGUAGE_COLORS.default

  const getComplexityLabel = (complexity: number) => {
    if (complexity <= 5) return { text: 'Low', class: 'bg-green-500/20 text-green-400' }
    if (complexity <= 10) return { text: 'Medium', class: 'bg-yellow-500/20 text-yellow-400' }
    return { text: 'High', class: 'bg-red-500/20 text-red-400' }
  }

  const complexityInfo = node ? getComplexityLabel(node.complexity || 0) : null

  return (
    <div 
      className={`flex flex-col bg-slate-800 border-l border-slate-700 transition-all duration-300 ${
        isCollapsed ? 'w-12' : 'w-80'
      }`}
    >
      {/* Header */}
      <div className="flex items-center justify-between p-3 border-b border-slate-700">
        <button
          onClick={onToggleCollapse}
          className="p-1.5 rounded hover:bg-slate-700 transition-colors"
        >
          <svg 
            xmlns="http://www.w3.org/2000/svg" 
            className={`h-5 w-5 text-slate-400 transition-transform ${!isCollapsed ? 'rotate-180' : ''}`}
            fill="none" 
            viewBox="0 0 24 24" 
            stroke="currentColor"
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 5l7 7-7 7M5 5l7 7-7 7" />
          </svg>
        </button>
        {!isCollapsed && <h2 className="font-semibold text-slate-200">Details</h2>}
      </div>

      {/* Content */}
      {!isCollapsed && (
        <div className="flex-1 overflow-y-auto">
          {node ? (
            <div className="p-4 space-y-4">
              {/* Node Header */}
              <div className="flex items-start gap-3">
                <span className="text-3xl">{icon}</span>
                <div className="flex-1 min-w-0">
                  <h3 className="text-lg font-bold text-slate-100 break-words">{node.name}</h3>
                  <p className="text-sm text-slate-400">{node.type}</p>
                </div>
              </div>

              {/* Quick Stats */}
              <div className="grid grid-cols-2 gap-2">
                <div className="bg-slate-900/50 rounded p-2">
                  <div className="text-xs text-slate-400">Language</div>
                  <div className="text-sm font-medium" style={{ color: langColor }}>
                    {node.language}
                  </div>
                </div>
                <div className="bg-slate-900/50 rounded p-2">
                  <div className="text-xs text-slate-400">Complexity</div>
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-mono text-slate-200">{node.complexity}</span>
                    {complexityInfo && (
                      <span className={`px-1.5 py-0.5 text-xs rounded ${complexityInfo.class}`}>
                        {complexityInfo.text}
                      </span>
                    )}
                  </div>
                </div>
              </div>

              {/* Location */}
              <div className="bg-slate-900/50 rounded p-3">
                <div className="text-xs text-slate-400 mb-1">Location</div>
                <div className="text-sm font-mono text-slate-200">
                  {fileName}
                  <span className="text-slate-400">:{node.line}</span>
                </div>
                {filePath && (
                  <div className="text-xs text-slate-500 mt-1 break-words">
                    {filePath}
                  </div>
                )}
              </div>

              {/* Actions */}
              <div className="flex flex-col gap-2">
                <button 
                  onClick={() => onViewConnections?.(node.id)}
                  className="w-full px-3 py-2 bg-indigo-600 text-white rounded hover:bg-indigo-700 transition-colors text-sm"
                >
                  🔗 View Connections
                </button>
                <button 
                  onClick={() => onCenterNode?.(node.id)}
                  className="w-full px-3 py-2 bg-slate-700 text-slate-200 rounded hover:bg-slate-600 transition-colors text-sm"
                >
                  📍 Center in Graph
                </button>
                <button 
                  onClick={() => selectNode(null)}
                  className="w-full px-3 py-2 text-slate-400 rounded hover:bg-slate-700 transition-colors text-sm"
                >
                  ✕ Clear Selection
                </button>
              </div>

              {/* Full Path (collapsible) */}
              {node.file && (
                <details className="bg-slate-900/50 rounded">
                  <summary className="px-3 py-2 text-sm text-slate-300 cursor-pointer hover:bg-slate-800 rounded">
                    Full Path
                  </summary>
                  <div className="px-3 pb-2">
                    <code className="text-xs text-slate-400 break-all">{node.file}</code>
                  </div>
                </details>
              )}
            </div>
          ) : (
            /* No Node Selected */
            <div className="p-4 text-center">
              <div className="text-4xl mb-3">🎯</div>
              <h3 className="font-medium text-slate-300">No Node Selected</h3>
              <p className="text-sm text-slate-500 mt-1">
                Click on a node in the graph to view details
              </p>
            </div>
          )}
        </div>
      )}

      {/* Collapsed View */}
      {isCollapsed && (
        <div className="flex-1 flex flex-col items-center py-4">
          <div title={node?.name || 'No selection'}>
            <span className="text-2xl">{icon}</span>
          </div>
        </div>
      )}
    </div>
  )
}
