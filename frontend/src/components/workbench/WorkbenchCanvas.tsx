/**
 * WorkbenchCanvas Component
 * 
 * The main canvas for the card-based hierarchical navigation view.
 * Displays the root node as a hero card and children in a responsive grid or list layout.
 */

import { useCallback, useState } from 'react'
import { clsx } from 'clsx'
import type { GraphNode } from '@/types'
import { NodeCard, type NodeCardProps } from './NodeCard'
import { BreadcrumbNavigation, type NavigationItem } from './BreadcrumbNavigation'

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
  onNavigateBack: _onNavigateBack,
  onNavigateToLevel,
  onNavigateHome,
  selectedNodeId,
  className,
}: WorkbenchCanvasProps) {
  const [localViewMode, setLocalViewMode] = useState<ViewMode>(viewMode)
  const [localSortBy, setLocalSortBy] = useState<SortBy>(sortBy)

  // Process child nodes: filter and sort
  const processedChildren = sortNodes(filterNodes(childNodes, filterBy), localSortBy)

  const handleNodeClick = useCallback((nodeId: string) => {
    onSelect(nodeId)
  }, [onSelect])

  const handleNodeDoubleClick = useCallback((nodeId: string) => {
    onDrillDown(nodeId)
  }, [onDrillDown])

  // Empty state
  if (!rootNode && childNodes.length === 0) {
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
        <h2 className="text-xl font-semibold mb-2">No Node Selected</h2>
        <p className="text-sm text-slate-500 text-center max-w-md">
          Select a node from the graph view to explore its structure and relationships,
          or double-click to drill into its local context.
        </p>
      </div>
    )
  }

  return (
    <div 
      className={clsx('flex flex-col h-full', className)}
      data-test="workbench-canvas"
      data-testid="workbench-canvas"
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

        {/* Children count */}
        <div className="text-sm text-slate-500">
          {processedChildren.length} items
        </div>
      </div>

      {/* Scrollable content area */}
      <div className="flex-1 overflow-auto p-4">
        {/* Root node as hero card */}
        {rootNode && (
          <div className="mb-6">
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
        {processedChildren.length > 0 && (
          <h3 className="text-sm font-medium text-slate-400 mb-3 flex items-center gap-2">
            <span>Related Nodes</span>
            <span className="text-slate-600">({processedChildren.length})</span>
          </h3>
        )}

        {/* Children grid/list */}
        {localViewMode === 'grid' ? (
          <div 
            className="grid gap-4"
            style={{
              gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))',
            }}
            data-test="children-grid"
          >
            {processedChildren.map((node) => (
              <NodeCard
                key={node.id}
                node={node}
                variant="grid"
                isSelected={selectedNodeId === node.id}
                onClick={() => handleNodeClick(node.id)}
                onDoubleClick={() => handleNodeDoubleClick(node.id)}
              />
            ))}
          </div>
        ) : (
          <div className="flex flex-col gap-2" data-test="children-list">
            {processedChildren.map((node) => (
              <NodeCard
                key={node.id}
                node={node}
                variant="list"
                isSelected={selectedNodeId === node.id}
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
