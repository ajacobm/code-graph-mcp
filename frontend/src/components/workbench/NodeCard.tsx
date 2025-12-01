/**
 * NodeCard Component
 * 
 * A reusable card component for displaying node information with hero, grid, and list variants.
 * - Hero variant: Full node details for root/focused node
 * - Grid variant: Compact card layout for children
 * - List variant: Row layout for compact lists
 */

import { type MouseEvent, type KeyboardEvent } from 'react'
import { clsx } from 'clsx'
import type { GraphNode } from '@/types'

// Type icons mapping
const TYPE_ICONS: Record<string, string> = {
  function: '⚙️',
  class: '📦',
  method: '🔧',
  module: '📁',
  import: '📥',
  default: '📄',
}

// Language icons/emojis
const LANGUAGE_ICONS: Record<string, string> = {
  python: '🐍',
  typescript: '📘',
  javascript: '📙',
  'c#': '🔷',
  java: '☕',
  go: '🐹',
  rust: '🦀',
  ruby: '💎',
  php: '🐘',
  cpp: '⚡',
  default: '📄',
}

export interface NodeCardProps {
  node: GraphNode
  variant: 'hero' | 'grid' | 'list'
  isSelected?: boolean
  categoryBadge?: 'entry-point' | 'hub' | 'leaf'
  onClick?: () => void
  onDoubleClick?: () => void
  showConnections?: boolean
  incomingCount?: number
  outgoingCount?: number
}

/**
 * Get complexity color based on value
 */
function getComplexityColor(complexity: number): string {
  if (complexity <= 5) return 'text-green-400'
  if (complexity <= 10) return 'text-yellow-400'
  if (complexity <= 20) return 'text-orange-400'
  return 'text-red-400'
}

/**
 * Get category badge color and label
 */
function getCategoryBadge(category: 'entry-point' | 'hub' | 'leaf'): { color: string; label: string } {
  switch (category) {
    case 'entry-point':
      return { color: 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30', label: 'Entry Point' }
    case 'hub':
      return { color: 'bg-purple-500/20 text-purple-400 border-purple-500/30', label: 'Hub' }
    case 'leaf':
      return { color: 'bg-blue-500/20 text-blue-400 border-blue-500/30', label: 'Leaf' }
  }
}

/**
 * Get type icon for a node
 */
function getTypeIcon(type: string): string {
  return TYPE_ICONS[type.toLowerCase()] || TYPE_ICONS.default
}

/**
 * Get language icon for a node
 */
function getLanguageIcon(language: string): string {
  return LANGUAGE_ICONS[language.toLowerCase()] || LANGUAGE_ICONS.default
}

/**
 * NodeCard Component
 */
export function NodeCard({
  node,
  variant,
  isSelected = false,
  categoryBadge,
  onClick,
  onDoubleClick,
  showConnections = false,
  incomingCount = 0,
  outgoingCount = 0,
}: NodeCardProps) {
  const handleClick = (e: MouseEvent<HTMLDivElement>) => {
    e.stopPropagation()
    onClick?.()
  }

  const handleDoubleClick = (e: MouseEvent<HTMLDivElement>) => {
    e.stopPropagation()
    onDoubleClick?.()
  }

  const handleKeyDown = (e: KeyboardEvent<HTMLDivElement>) => {
    if (e.key === 'Enter') {
      e.preventDefault()
      onDoubleClick?.()
    } else if (e.key === ' ') {
      e.preventDefault()
      onClick?.()
    }
  }

  // Base classes for all variants
  const baseClasses = clsx(
    'rounded-lg border transition-all duration-200 cursor-pointer',
    'focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2 focus:ring-offset-slate-900',
    isSelected 
      ? 'border-indigo-500 bg-slate-800/80 shadow-lg shadow-indigo-500/20'
      : 'border-slate-700 bg-slate-800/60 hover:border-slate-600 hover:bg-slate-800/80'
  )

  // Hero variant - Full details for root node
  if (variant === 'hero') {
    return (
      <div
        className={clsx(baseClasses, 'p-6')}
        onClick={handleClick}
        onDoubleClick={handleDoubleClick}
        onKeyDown={handleKeyDown}
        tabIndex={0}
        role="button"
        aria-label={`${node.name} - ${node.type}`}
        data-test={`node-card-${node.id}`}
        data-testid="node-card-hero"
      >
        {/* Header */}
        <div className="flex items-start justify-between mb-4">
          <div className="flex items-center gap-3">
            <span className="text-2xl" aria-hidden="true">{getTypeIcon(node.type)}</span>
            <div>
              <h2 className="text-xl font-bold text-slate-100">{node.name}</h2>
              <span className="text-sm text-slate-400 capitalize">{node.type}</span>
            </div>
          </div>
          <div className="flex items-center gap-2">
            {categoryBadge && (
              <span 
                className={clsx(
                  'px-2 py-1 text-xs font-medium rounded border',
                  getCategoryBadge(categoryBadge).color
                )}
              >
                {getCategoryBadge(categoryBadge).label}
              </span>
            )}
            <span className="px-2 py-1 text-xs bg-slate-700 text-slate-300 rounded capitalize">
              {node.type}
            </span>
          </div>
        </div>

        {/* Divider */}
        <div className="border-t border-slate-700 my-4" />

        {/* File path */}
        <div className="flex items-center gap-2 text-sm text-slate-400 mb-4">
          <span>📍</span>
          <span className="font-mono truncate">{node.file}:{node.line}</span>
        </div>

        {/* Stats row */}
        <div className="flex items-center gap-6 text-sm">
          <div className="flex items-center gap-2">
            <span>📊</span>
            <span className="text-slate-400">Complexity:</span>
            <span className={getComplexityColor(node.complexity)}>{node.complexity}</span>
          </div>
          {node.metadata?.line_count && (
            <div className="flex items-center gap-2">
              <span>📏</span>
              <span className="text-slate-400">Lines:</span>
              <span className="text-slate-200">{node.metadata.line_count}</span>
            </div>
          )}
          <div className="flex items-center gap-2">
            <span>{getLanguageIcon(node.language)}</span>
            <span className="text-slate-200 capitalize">{node.language}</span>
          </div>
        </div>

        {/* Connections */}
        {showConnections && (
          <div className="flex items-center gap-4 mt-4 text-sm text-slate-400">
            <span>{incomingCount} callers</span>
            <span>•</span>
            <span>{outgoingCount} callees</span>
          </div>
        )}

        {/* Double-click hint */}
        <div className="mt-4 text-xs text-slate-500">
          Double-click to drill into this node
        </div>
      </div>
    )
  }

  // Grid variant - Compact card for children
  if (variant === 'grid') {
    return (
      <div
        className={clsx(baseClasses, 'p-4')}
        onClick={handleClick}
        onDoubleClick={handleDoubleClick}
        onKeyDown={handleKeyDown}
        tabIndex={0}
        role="button"
        aria-label={`${node.name} - ${node.type}`}
        data-test={`node-card-${node.id}`}
        data-testid="node-card-grid"
      >
        {/* Header with icon and name */}
        <div className="flex items-center gap-2 mb-2">
          <span className="text-lg" aria-hidden="true">{getTypeIcon(node.type)}</span>
          <h3 className="font-semibold text-slate-100 truncate flex-1">{node.name}</h3>
        </div>

        {/* Category badge if present */}
        {categoryBadge && (
          <div className="mb-2">
            <span 
              className={clsx(
                'px-2 py-0.5 text-xs font-medium rounded border',
                getCategoryBadge(categoryBadge).color
              )}
            >
              {getCategoryBadge(categoryBadge).label}
            </span>
          </div>
        )}

        {/* Stats */}
        <div className="text-sm text-slate-400 space-y-1">
          <div className="flex items-center justify-between">
            <span>Complexity:</span>
            <span className={getComplexityColor(node.complexity)}>{node.complexity}</span>
          </div>
          {node.metadata?.line_count && (
            <div className="flex items-center justify-between">
              <span>Lines:</span>
              <span className="text-slate-200">{node.metadata.line_count}</span>
            </div>
          )}
        </div>

        {/* Language indicator */}
        <div className="mt-2 flex items-center gap-1 text-xs text-slate-500">
          <span>{getLanguageIcon(node.language)}</span>
          <span className="capitalize">{node.language}</span>
        </div>

        {/* Drill-down indicator */}
        <div className="mt-3 text-xs text-slate-500 flex items-center gap-1">
          <span>Double-click</span>
          <span>▶</span>
        </div>
      </div>
    )
  }

  // List variant - Row layout for compact lists
  return (
    <div
      className={clsx(baseClasses, 'p-3 flex items-center gap-4')}
      onClick={handleClick}
      onDoubleClick={handleDoubleClick}
      onKeyDown={handleKeyDown}
      tabIndex={0}
      role="button"
      aria-label={`${node.name} - ${node.type}`}
      data-test={`node-card-${node.id}`}
      data-testid="node-card-list"
    >
      {/* Icon */}
      <span className="text-lg flex-shrink-0" aria-hidden="true">{getTypeIcon(node.type)}</span>

      {/* Name and type */}
      <div className="flex-1 min-w-0">
        <h3 className="font-medium text-slate-100 truncate">{node.name}</h3>
        <span className="text-xs text-slate-500 capitalize">{node.type}</span>
      </div>

      {/* Category badge */}
      {categoryBadge && (
        <span 
          className={clsx(
            'px-2 py-0.5 text-xs font-medium rounded border flex-shrink-0',
            getCategoryBadge(categoryBadge).color
          )}
        >
          {getCategoryBadge(categoryBadge).label}
        </span>
      )}

      {/* Complexity */}
      <div className="flex items-center gap-1 text-sm flex-shrink-0">
        <span className="text-slate-500">C:</span>
        <span className={getComplexityColor(node.complexity)}>{node.complexity}</span>
      </div>

      {/* Language */}
      <span className="text-sm flex-shrink-0" title={node.language}>
        {getLanguageIcon(node.language)}
      </span>

      {/* Drill-down indicator */}
      <span className="text-slate-500 flex-shrink-0">▶</span>
    </div>
  )
}

NodeCard.displayName = 'NodeCard'
