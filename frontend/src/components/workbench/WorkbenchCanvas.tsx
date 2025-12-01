/**
 * WorkbenchCanvas Component
 * 
 * The main canvas for the card-based hierarchical navigation view.
 * Displays the root node as a hero card and children in a responsive grid or list layout.
 * 
 * Keyboard Navigation:
 * - Arrow keys: Navigate between cards
 * - Enter: Drill into selected card
 * - Escape: Go back one level
 * - Home: Go to first card (Ctrl+Home: Go to root)
 * - End: Go to last card
 */

import { useCallback, useState, useRef, useEffect, useMemo } from 'react'
import { clsx } from 'clsx'
import type { GraphNode } from '@/types'
import { NodeCard, type NodeCardProps } from './NodeCard'
import { BreadcrumbNavigation, type NavigationItem } from './BreadcrumbNavigation'
import { useKeyboardNavigation } from './useKeyboardNavigation'

export type ViewMode = 'grid' | 'list'
export type SortBy = 'name' | 'complexity' | 'type' | 'lines'

export interface WorkbenchCanvasProps {
  rootNode: GraphNode | null
  childNodes: GraphNode[]
  navigationStack: NavigationItem[]
  viewMode?: ViewMode
  sortBy?: SortBy
  filterBy?: string[]
  onDrillDown: (nodeId: string) => void
  onSelect: (nodeId: string) => void
  onNavigateBack: () => void
  onNavigateToLevel: (index: number) => void
  onNavigateHome: () => void
  selectedNodeId?: string | null
  className?: string
  /** Error message to display when initial loading fails */
  error?: string | null
}

/**
 * Get category badge for a node based on connections
 */
function getNodeCategory(
  _node: GraphNode, 
  incomingCount: number, 
  outgoingCount: number
): NodeCardProps['categoryBadge'] {
  // Entry point: many outgoing, few/no incoming
  if (incomingCount === 0 && outgoingCount > 0) {
    return 'entry-point'
  }
  // Hub: many incoming and outgoing
  if (incomingCount > 3 && outgoingCount > 3) {
    return 'hub'
  }
  // Leaf: no outgoing, some incoming
  if (outgoingCount === 0 && incomingCount > 0) {
    return 'leaf'
  }
  return undefined
}

/**
 * Sort nodes by the specified field
 */
function sortNodes(nodes: GraphNode[], sortBy: SortBy): GraphNode[] {
  return [...nodes].sort((a, b) => {
    switch (sortBy) {
      case 'name':
        return a.name.localeCompare(b.name)
      case 'complexity':
        return b.complexity - a.complexity // Descending
      case 'type':
        return a.type.localeCompare(b.type)
      case 'lines':
        return (b.metadata?.line_count || 0) - (a.metadata?.line_count || 0) // Descending
      default:
        return 0
    }
  })
}

/**
 * Filter nodes by type
 */
function filterNodes(nodes: GraphNode[], filterBy: string[]): GraphNode[] {
  if (filterBy.length === 0) return nodes
  return nodes.filter(node => filterBy.includes(node.type.toLowerCase()))
}

/**
 * WorkbenchCanvas Component
 */
export function WorkbenchCanvas({
  rootNode,
  childNodes,
  navigationStack,
  viewMode = 'grid',
  sortBy = 'complexity',
  filterBy = [],
  onDrillDown,
  onSelect,
  onNavigateBack,
  onNavigateToLevel,
  onNavigateHome,
  selectedNodeId,
  className,
  error,
}: WorkbenchCanvasProps) {
  const [localViewMode, setLocalViewMode] = useState<ViewMode>(viewMode)
  const [localSortBy, setLocalSortBy] = useState<SortBy>(sortBy)
  const containerRef = useRef<HTMLDivElement>(null)

  // Process child nodes: filter and sort
  const processedChildren = useMemo(
    () => sortNodes(filterNodes(childNodes, filterBy), localSortBy),
    [childNodes, filterBy, localSortBy]
  )

  // Calculate grid columns based on container width (responsive)
  const [gridColumns, setGridColumns] = useState(3)
  
  useEffect(() => {
    const updateColumns = () => {
      if (containerRef.current) {
        const width = containerRef.current.offsetWidth
        // Minimum card width is 200px + gap
        const cols = Math.max(1, Math.floor(width / 220))
        setGridColumns(cols)
      }
    }
    
    updateColumns()
    window.addEventListener('resize', updateColumns)
    return () => window.removeEventListener('resize', updateColumns)
  }, [])

  // Keyboard navigation hook
  const { focusedIndex, isKeyboardActive, handleKeyDown } = useKeyboardNavigation({
    nodes: processedChildren,
    selectedNodeId,
    onSelect,
    onDrillDown,
    onNavigateBack,
    onNavigateHome,
    enabled: true,
    gridColumns: localViewMode === 'grid' ? gridColumns : 1,
  })

  const handleNodeClick = useCallback((nodeId: string) => {
    onSelect(nodeId)
  }, [onSelect])

  const handleNodeDoubleClick = useCallback((nodeId: string) => {
    onDrillDown(nodeId)
  }, [onDrillDown])

  // Focus container on mount for keyboard navigation
  useEffect(() => {
    if (containerRef.current && (rootNode || processedChildren.length > 0)) {
      containerRef.current.focus()
    }
  }, [rootNode, processedChildren.length])

  // Determine display states
  const hasNoNodes = !rootNode && childNodes.length === 0
  const shouldShowErrorState = error && hasNoNodes
  const isShowingInitialNodes = !rootNode && childNodes.length > 0

  // Error state - show when there's an error and no nodes
  if (shouldShowErrorState) {
    return (
      <div 
        className={clsx(
          'flex flex-col items-center justify-center h-full p-8',
          'text-slate-400',
          className
        )}
        data-test="workbench-canvas"
        data-testid="workbench-canvas-error"
      >
        <div className="text-6xl mb-4">⚠️</div>
        <h2 className="text-xl font-semibold mb-2 text-red-400">Unable to Load Nodes</h2>
        <p className="text-sm text-slate-500 text-center max-w-md mb-4">
          {error}
        </p>
        <p className="text-xs text-slate-600 text-center max-w-md">
          Make sure the backend server is running and try refreshing the page.
        </p>
      </div>
    )
  }

  // Empty state - only show when there are no nodes at all and no error
  if (hasNoNodes) {
    return (
      <div 
        className={clsx(
          'flex flex-col items-center justify-center h-full p-8',
          'text-slate-400',
          className
        )}
        data-test="workbench-canvas"
        data-testid="workbench-canvas-empty"
      >
        <div className="text-6xl mb-4">📊</div>
        <h2 className="text-xl font-semibold mb-2">Loading Entry Points...</h2>
        <p className="text-sm text-slate-500 text-center max-w-md">
          Fetching initial nodes to get you started.
        </p>
      </div>
    )
  }

  return (
    <div 
      ref={containerRef}
      className={clsx('flex flex-col h-full', className)}
      data-test="workbench-canvas"
      data-testid="workbench-canvas"
      tabIndex={0}
      onKeyDown={handleKeyDown}
      role="application"
      aria-label="Node navigation workbench. Use arrow keys to navigate, Enter to drill down, Escape to go back."
    >
      {/* Breadcrumb Navigation */}
      <div className="flex-shrink-0 p-4 border-b border-slate-700">
        <BreadcrumbNavigation
          path={navigationStack}
          onNavigateToLevel={onNavigateToLevel}
          onHome={onNavigateHome}
        />
      </div>

      {/* View Mode & Sort Controls */}
      <div className="flex-shrink-0 flex items-center justify-between px-4 py-2 border-b border-slate-700/50">
        {/* View mode toggle */}
        <div className="flex items-center gap-2">
          <span className="text-sm text-slate-400">View:</span>
          <button
            onClick={() => setLocalViewMode('grid')}
            className={clsx(
              'px-2 py-1 text-sm rounded transition-colors',
              localViewMode === 'grid'
                ? 'bg-indigo-500 text-white'
                : 'text-slate-400 hover:text-white hover:bg-slate-700'
            )}
            aria-pressed={localViewMode === 'grid'}
            data-test="view-mode-grid"
          >
            Grid
          </button>
          <button
            onClick={() => setLocalViewMode('list')}
            className={clsx(
              'px-2 py-1 text-sm rounded transition-colors',
              localViewMode === 'list'
                ? 'bg-indigo-500 text-white'
                : 'text-slate-400 hover:text-white hover:bg-slate-700'
            )}
            aria-pressed={localViewMode === 'list'}
            data-test="view-mode-list"
          >
            List
          </button>
        </div>

        {/* Sort by dropdown */}
        <div className="flex items-center gap-2">
          <span className="text-sm text-slate-400">Sort by:</span>
          <select
            value={localSortBy}
            onChange={(e) => setLocalSortBy(e.target.value as SortBy)}
            className="bg-slate-700 text-slate-200 text-sm rounded px-2 py-1 border border-slate-600 focus:outline-none focus:ring-2 focus:ring-indigo-500"
            data-test="sort-by-select"
          >
            <option value="complexity">Complexity</option>
            <option value="name">Name</option>
            <option value="type">Type</option>
            <option value="lines">Lines</option>
          </select>
        </div>

        {/* Children count and keyboard hints */}
        <div className="flex items-center gap-3">
          <div className="text-sm text-slate-500">
            {processedChildren.length} items
          </div>
          {isKeyboardActive && (
            <div className="text-xs text-slate-600 hidden md:flex items-center gap-1">
              <kbd className="px-1.5 py-0.5 bg-slate-700 rounded text-slate-400">↑↓←→</kbd>
              <span>navigate</span>
              <kbd className="px-1.5 py-0.5 bg-slate-700 rounded text-slate-400 ml-2">Enter</kbd>
              <span>drill</span>
              <kbd className="px-1.5 py-0.5 bg-slate-700 rounded text-slate-400 ml-2">Esc</kbd>
              <span>back</span>
            </div>
          )}
        </div>
      </div>

      {/* Scrollable content area */}
      <div className="flex-1 overflow-auto p-4">
        {/* Initial nodes header - when showing entry points with no root node */}
        {isShowingInitialNodes && (
          <div className="mb-6">
            <div className="flex items-center gap-3 mb-2">
              <span className="text-3xl">🚀</span>
              <div>
                <h2 className="text-xl font-bold text-slate-100">Entry Points</h2>
                <p className="text-sm text-slate-400">Functions with no callers - great starting points for exploration</p>
              </div>
            </div>
            <p className="text-xs text-slate-500 mt-2">
              Double-click any card to drill into its local context
            </p>
          </div>
        )}

        {/* Root node as hero card */}
        {rootNode && (
          <div className="mb-6 transition-all duration-200">
            <NodeCard
              node={rootNode}
              variant="hero"
              isSelected={selectedNodeId === rootNode.id}
              categoryBadge={getNodeCategory(rootNode, 0, processedChildren.length)}
              onClick={() => handleNodeClick(rootNode.id)}
              onDoubleClick={() => handleNodeDoubleClick(rootNode.id)}
              showConnections={true}
              incomingCount={0}
              outgoingCount={processedChildren.length}
            />
          </div>
        )}

        {/* Section header for children */}
        {processedChildren.length > 0 && !isShowingInitialNodes && (
          <h3 className="text-sm font-medium text-slate-400 mb-3 flex items-center gap-2">
            <span>Related Nodes</span>
            <span className="text-slate-600">({processedChildren.length})</span>
          </h3>
        )}

        {/* Children grid/list */}
        {localViewMode === 'grid' ? (
          <div 
            className="grid gap-4 transition-all duration-200"
            style={{
              gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))',
            }}
            data-test="children-grid"
            role="listbox"
            aria-label="Child nodes"
          >
            {processedChildren.map((node, index) => (
              <NodeCard
                key={node.id}
                node={node}
                variant="grid"
                isSelected={selectedNodeId === node.id}
                isFocused={isKeyboardActive && focusedIndex === index}
                onClick={() => handleNodeClick(node.id)}
                onDoubleClick={() => handleNodeDoubleClick(node.id)}
              />
            ))}
          </div>
        ) : (
          <div 
            className="flex flex-col gap-2 transition-all duration-200" 
            data-test="children-list"
            role="listbox"
            aria-label="Child nodes"
          >
            {processedChildren.map((node, index) => (
              <NodeCard
                key={node.id}
                node={node}
                variant="list"
                isSelected={selectedNodeId === node.id}
                isFocused={isKeyboardActive && focusedIndex === index}
                onClick={() => handleNodeClick(node.id)}
                onDoubleClick={() => handleNodeDoubleClick(node.id)}
              />
            ))}
          </div>
        )}

        {/* Empty children state */}
        {processedChildren.length === 0 && rootNode && (
          <div className="text-center py-8 text-slate-500">
            <div className="text-4xl mb-2">🍃</div>
            <p className="text-sm">This node has no connected children.</p>
          </div>
        )}
      </div>
    </div>
  )
}

WorkbenchCanvas.displayName = 'WorkbenchCanvas'
