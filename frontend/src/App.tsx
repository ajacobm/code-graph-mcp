/**
 * Main App Component
 * 
 * Root component for the CodeNavigator graph visualization.
 * Supports dual-view mode: Workbench (card-based) and Graph (force-directed).
 */

import { useEffect, useRef, useState, useCallback, useMemo, Suspense, lazy } from 'react'
import { useGraphStore } from '@/stores/graphStore'
import { Header } from '@/components/layout/Header'
import { StatusBar } from '@/components/layout/StatusBar'
import { LoadingOverlay } from '@/components/layout/LoadingOverlay'
import { ToolsPanel } from '@/components/panels/ToolsPanel'
import { DetailsPanel } from '@/components/panels/DetailsPanel'
import { GraphControls } from '@/components/graph/GraphControls'
import { NodeTooltip } from '@/components/graph/NodeTooltip'
import { ViewToggle, getSavedViewPreference, type ViewType } from '@/components/ViewToggle'
import { WorkbenchCanvas } from '@/components/workbench/WorkbenchCanvas'
import { fetchCategory } from '@/api/graphApi'
import type { ForceGraphNode, GraphNode, NavigationEntry } from '@/types'
import type { ForceGraphRef } from '@/components/graph/ForceGraph'

// Lazy load the heavy ForceGraph component
const ForceGraph = lazy(() => import('@/components/graph/ForceGraph').then(mod => ({ default: mod.ForceGraph })))

export default function App() {
  const forceGraphRef = useRef<ForceGraphRef>(null)
  const [leftPanelCollapsed, setLeftPanelCollapsed] = useState(false)
  const [rightPanelCollapsed, setRightPanelCollapsed] = useState(false)
  const [hoveredNode, setHoveredNode] = useState<GraphNode | null>(null)
  const [activeView, setActiveView] = useState<ViewType>(() => getSavedViewPreference())
  const [categoryNodes, setCategoryNodes] = useState<GraphNode[]>([])
  const [activeCategory, setActiveCategory] = useState<string | null>(null)
  const [showConnectionsPanel, setShowConnectionsPanel] = useState(false)
  const [connections, setConnections] = useState<{ callers: GraphNode[]; callees: GraphNode[] }>({ callers: [], callees: [] })
  const [connectionsLoading, setConnectionsLoading] = useState(false)

  const { 
    graphData, 
    isLoading, 
    error,
    loadGraph,
    selectedNodeId,
    selectNode,
    highlightedNodeIds,
    highlightNodes,
    showLabels,
    colorMode,
    graphDimension,
    filters,
    drillIntoNode,
    navigationStack,
    navigateBack,
    navigateToLevel,
    resetNavigation,
    focusedNodeId,
    getSelectedNode,
  } = useGraphStore()

  // Load graph on mount
  useEffect(() => {
    loadGraph()
  }, [loadGraph])

  // Handle node click
  const handleNodeClick = useCallback((node: ForceGraphNode) => {
    selectNode(node.id)
  }, [selectNode])

  // Handle node double-click for drill-down navigation
  const handleNodeDoubleClick = useCallback((node: ForceGraphNode) => {
    // Guard against null/undefined node or missing/invalid id
    if (!node || !node.id || typeof node.id !== 'string') {
      console.warn('App: handleNodeDoubleClick called with invalid node', node)
      return
    }
    drillIntoNode(node.id)
  }, [drillIntoNode])

  // Handle node hover
  const handleNodeHover = useCallback((node: ForceGraphNode | null) => {
    setHoveredNode(node as GraphNode | null)
  }, [])

  // Handle background click
  const handleBackgroundClick = useCallback(() => {
    selectNode(null)
  }, [selectNode])

  // Handle category selection
  const handleCategorySelect = useCallback(async (category: string) => {
    if (category === activeCategory) {
      // Deselect category
      setActiveCategory(null)
      setCategoryNodes([])
      return
    }
    
    try {
      const categoryKey = category as 'entry_points' | 'hubs' | 'leaves'
      const response = await fetchCategory(categoryKey)
      setCategoryNodes(response.nodes)
      setActiveCategory(category)
      
      // Highlight category nodes in the graph
      const nodeIds = response.nodes.map(n => n.id)
      highlightNodes(nodeIds)
    } catch (err) {
      console.error('Failed to fetch category:', err)
    }
  }, [activeCategory, highlightNodes])

  // Handle search
  const handleSearch = useCallback((query: string) => {
    if (!graphData) return
    
    const matchingNodeIds = graphData.nodes
      .filter(n => n.name.toLowerCase().includes(query.toLowerCase()))
      .map(n => n.id)
    
    highlightNodes(matchingNodeIds)
  }, [graphData, highlightNodes])

  // Handle zoom to fit
  const handleZoomToFit = useCallback(() => {
    forceGraphRef.current?.zoomToFit()
  }, [])

  // Handle center on node
  const handleCenterNode = useCallback((nodeId: string) => {
    forceGraphRef.current?.centerNode(nodeId)
  }, [])

  // Handle refresh
  const handleRefresh = useCallback(() => {
    const language = filters.languages[0]
    const nodeType = filters.nodeTypes[0]
    loadGraph({ language, nodeType })
    // Clear category selection on refresh
    setActiveCategory(null)
    setCategoryNodes([])
  }, [loadGraph, filters])

  // Handle View Connections button
  const handleViewConnections = useCallback(async (nodeId: string) => {
    if (!graphData) return
    
    setConnectionsLoading(true)
    setShowConnectionsPanel(true)
    
    try {
      // Find connections from the current graph data
      const callers: GraphNode[] = []
      const callees: GraphNode[] = []
      
      // Create a Map for O(1) node lookups
      const nodeMap = new Map(graphData.nodes.map(n => [n.id, n]))
      
      graphData.links.forEach(link => {
        // GraphLink source/target are always strings (node IDs)
        if (link.target === nodeId) {
          const caller = nodeMap.get(link.source)
          if (caller) callers.push(caller)
        }
        if (link.source === nodeId) {
          const callee = nodeMap.get(link.target)
          if (callee) callees.push(callee)
        }
      })
      
      setConnections({ callers, callees })
    } catch (err) {
      console.error('Failed to load connections:', err)
    } finally {
      setConnectionsLoading(false)
    }
  }, [graphData])

  // State for initial workbench nodes (when no node is selected)
  const [initialWorkbenchNodes, setInitialWorkbenchNodes] = useState<GraphNode[]>([])
  const [initialWorkbenchLoading, setInitialWorkbenchLoading] = useState(false)
  const [initialWorkbenchError, setInitialWorkbenchError] = useState<string | null>(null)

  // Get workbench data
  const selectedNode = getSelectedNode()
  const focusedNode = focusedNodeId 
    ? graphData?.nodes.find(n => n.id === focusedNodeId) || null
    : null
  
  // Get child nodes for workbench (nodes connected to focused node)
  const workbenchRootNode = focusedNode || selectedNode
  const workbenchChildren = useMemo(() => {
    if (!graphData || !workbenchRootNode) return []
    return graphData.nodes.filter(n => {
      if (n.id === workbenchRootNode.id) return false
      // Check if there's a link from root to this node or vice versa
      // GraphLink source/target are always strings (node IDs)
      return graphData.links.some(l => 
        (l.source === workbenchRootNode.id && l.target === n.id) ||
        (l.target === workbenchRootNode.id && l.source === n.id)
      )
    })
  }, [graphData, workbenchRootNode])

  // Load initial nodes for workbench when no node is selected
  useEffect(() => {
    const loadInitialWorkbenchNodes = async () => {
      // Only load if in workbench view and no node selected
      // Don't require graphData - we'll fetch entry points directly
      if (activeView === 'workbench' && !workbenchRootNode && initialWorkbenchNodes.length === 0 && !initialWorkbenchLoading) {
        setInitialWorkbenchLoading(true)
        setInitialWorkbenchError(null)
        try {
          // Fetch entry points as the initial view
          const response = await fetchCategory('entry_points')
          setInitialWorkbenchNodes(response.nodes)
        } catch (err) {
          console.error('Failed to load initial workbench nodes:', err)
          setInitialWorkbenchError(err instanceof Error ? err.message : 'Failed to load entry points')
          // Fallback: use top nodes from graph data by complexity if available
          if (graphData) {
            const topNodes = [...graphData.nodes]
              .sort((a, b) => b.complexity - a.complexity)
              .slice(0, 20)
            setInitialWorkbenchNodes(topNodes)
          }
        } finally {
          setInitialWorkbenchLoading(false)
        }
      }
    }
    
    loadInitialWorkbenchNodes()
  }, [activeView, workbenchRootNode, graphData, initialWorkbenchNodes.length, initialWorkbenchLoading])

  // Clear initial nodes when a node is selected or focused
  useEffect(() => {
    if (workbenchRootNode && initialWorkbenchNodes.length > 0) {
      setInitialWorkbenchNodes([])
    }
  }, [workbenchRootNode, initialWorkbenchNodes.length])

  // Use initial nodes when no root node is selected
  const effectiveWorkbenchChildren = workbenchRootNode ? workbenchChildren : initialWorkbenchNodes

  // Convert navigation stack to NavigationItem format
  const navigationItems = navigationStack.map((entry: NavigationEntry) => ({
    nodeId: entry.nodeId,
    nodeName: entry.nodeName,
    nodeType: entry.nodeType,
  }))

  return (
    <div className="flex flex-col h-screen bg-slate-900 text-slate-100">
      {/* Header */}
      <Header />

      {/* View Toggle Bar */}
      <div className="flex items-center justify-between px-4 py-2 border-b border-slate-700 bg-slate-800/50">
        <ViewToggle 
          activeView={activeView} 
          onViewChange={setActiveView}
        />
        {/* Stats Badge */}
        {graphData?.stats && (
          <div className="px-3 py-1.5 bg-slate-800/90 rounded text-sm text-slate-300">
            {graphData.stats.totalNodes.toLocaleString()} nodes · {graphData.stats.totalLinks.toLocaleString()} edges
          </div>
        )}
      </div>

      {/* Main Content */}
      <div className="layout-container overflow-hidden">
        {/* Left Panel - Tools */}
        <ToolsPanel 
          isCollapsed={leftPanelCollapsed}
          onToggleCollapse={() => setLeftPanelCollapsed(!leftPanelCollapsed)}
          onCategorySelect={handleCategorySelect}
          onSearch={handleSearch}
          activeCategory={activeCategory}
          categoryNodes={categoryNodes}
        />

        {/* Center - Main View (Graph or Workbench) */}
        <div className="main-canvas flex flex-col relative min-w-0" id="main-view" role="tabpanel">
          {activeView === 'graph' ? (
            <>
              {/* Graph Controls */}
              <div className="absolute top-4 left-4 z-10">
                <GraphControls 
                  onZoomToFit={handleZoomToFit}
                  onRefresh={handleRefresh}
                />
              </div>

              {/* Loading Overlay */}
              <LoadingOverlay isLoading={isLoading} label="Loading graph..." />

              {/* Error Overlay */}
              {error && !isLoading && (
                <div className="absolute inset-0 flex items-center justify-center bg-slate-900/80 z-20 animate-in fade-in">
                  <div className="bg-red-900/50 border border-red-700 rounded-lg p-6 max-w-md animate-in scale-in">
                    <h3 className="text-lg font-bold text-red-400 mb-2">Error loading graph</h3>
                    <p className="text-red-300 text-sm mb-4">{error}</p>
                    <button 
                      onClick={handleRefresh}
                      className="px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700 transition-colors"
                    >
                      Retry
                    </button>
                  </div>
                </div>
              )}

              {/* Force Graph with Suspense for lazy loading */}
              <Suspense 
                fallback={
                  <div className="flex-1 flex items-center justify-center bg-slate-900">
                    <div className="text-center">
                      <div className="animate-spin h-12 w-12 border-4 border-indigo-500 border-t-transparent rounded-full mx-auto" />
                      <p className="mt-4 text-slate-300">Loading Graph View...</p>
                    </div>
                  </div>
                }
              >
                <ForceGraph
                  ref={forceGraphRef}
                  data={graphData}
                  selectedNodeId={selectedNodeId}
                  highlightedNodeIds={highlightedNodeIds}
                  colorMode={colorMode}
                  showLabels={showLabels}
                  dimension={graphDimension}
                  onNodeClick={handleNodeClick}
                  onNodeDoubleClick={handleNodeDoubleClick}
                  onNodeHover={handleNodeHover}
                  onBackgroundClick={handleBackgroundClick}
                />
              </Suspense>

              {/* Hover Tooltip */}
              {hoveredNode && hoveredNode.id !== selectedNodeId && (
                <NodeTooltip node={hoveredNode} />
              )}
            </>
          ) : (
            /* Workbench View */
            <>
              {/* Loading Overlay */}
              <LoadingOverlay isLoading={isLoading || initialWorkbenchLoading} label="Loading..." />

              <WorkbenchCanvas
                rootNode={workbenchRootNode}
                childNodes={effectiveWorkbenchChildren}
                navigationStack={navigationItems}
                selectedNodeId={selectedNodeId}
                onDrillDown={drillIntoNode}
                onSelect={selectNode}
                onNavigateBack={navigateBack}
                onNavigateToLevel={navigateToLevel}
                onNavigateHome={resetNavigation}
                error={initialWorkbenchError}
              />
            </>
          )}
        </div>

        {/* Right Panel - Details */}
        <DetailsPanel 
          isCollapsed={rightPanelCollapsed}
          onToggleCollapse={() => setRightPanelCollapsed(!rightPanelCollapsed)}
          onCenterNode={handleCenterNode}
          onViewConnections={handleViewConnections}
          showConnectionsPanel={showConnectionsPanel}
          connections={connections}
          connectionsLoading={connectionsLoading}
          onCloseConnections={() => setShowConnectionsPanel(false)}
          onSelectConnection={(nodeId) => {
            selectNode(nodeId)
            setShowConnectionsPanel(false)
          }}
        />
      </div>

      {/* Status Bar */}
      <StatusBar />
    </div>
  )
}
