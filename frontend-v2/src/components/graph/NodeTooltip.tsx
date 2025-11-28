/**
 * NodeTooltip Component
 * 
 * Tooltip displayed when hovering over a node.
 */

import type { GraphNode } from '@/types'

interface NodeTooltipProps {
  node: GraphNode | null
  position?: { x: number; y: number }
}

const TYPE_ICONS: Record<string, string> = {
  function: '⚙️',
  class: '📦',
  method: '🔧',
  module: '📄',
  import: '📥',
}

export function NodeTooltip({ node }: NodeTooltipProps) {
  if (!node) return null

  const icon = TYPE_ICONS[node.type?.toLowerCase()] || '•'
  const fileName = node.file?.split('/').pop() || 'unknown'

  return (
    <div className="absolute bottom-4 left-4 z-20 p-3 bg-slate-800/95 border border-slate-600 rounded-lg text-sm max-w-xs backdrop-blur">
      <div className="flex items-start gap-2">
        <span className="text-xl">{icon}</span>
        <div className="flex-1 min-w-0">
          <div className="font-bold text-slate-100 truncate">{node.name}</div>
          <div className="text-slate-400 text-xs">
            {node.type} | {node.language}
          </div>
          <div className="text-slate-500 text-xs mt-1 truncate">
            {fileName}:{node.line}
          </div>
          <div className="flex gap-2 mt-2">
            <span className="px-1.5 py-0.5 text-xs bg-slate-700 rounded">
              C: {node.complexity}
            </span>
          </div>
        </div>
      </div>
    </div>
  )
}
