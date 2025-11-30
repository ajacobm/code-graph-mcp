/**
 * Main App Component
 * 
 * Root component for the CodeNavigator graph visualization.
 */

import { useEffect, useRef, useState, useCallback } from 'react'
import { useGraphStore } from '@/stores/graphStore'
import { Header } from '@/components/layout/Header'
import { StatusBar } from '@/components/layout/StatusBar'
import { ToolsPanel } from '@/components/panels/ToolsPanel'
import { DetailsPanel } from '@/components/panels/DetailsPanel'
import { ForceGraph, type ForceGraphRef } from '@/components/graph/ForceGraph'
import { GraphControls } from '@/components/graph/GraphControls'
import { NodeTooltip } from '@/components/graph/NodeTooltip'
import type { ForceGraphNode, GraphNode } from '@/types'

export default function App() {
  const forceGraphRef = useRef<ForceGraphRef>(null)
  const [leftPanelCollapsed, setLeftPanelCollapsed] = useState(false)
  const [rightPanelCollapsed, setRightPanelCollapsed] = useState(false)
  const [hoveredNode, setHoveredNode] = useState<GraphNode | null>(null)

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
  const handleCategorySelect = useCallback((category: string) => {
    console.log('Category selected:', category)
    // TODO: Highlight nodes from this category
  }, [])

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
  }, [loadGraph, filters])

  return (
    <div className="flex flex-col h-screen bg-slate-900 text-slate-100">
      {/* Header */}
      <Header />

      {/* Main Content */}
      <div className="flex-1 flex overflow-hidden">
        {/* Left Panel - Tools */}
        <ToolsPanel 
          isCollapsed={leftPanelCollapsed}
          onToggleCollapse={() => setLeftPanelCollapsed(!leftPanelCollapsed)}
          onCategorySelect={handleCategorySelect}
          onSearch={handleSearch}
        />

        {/* Center - Graph Canvas */}
        <div className="flex-1 flex flex-col relative">
          {/* Graph Controls */}
          <div className="absolute top-4 left-4 z-10">
            <GraphControls 
              onZoomToFit={handleZoomToFit}
              onRefresh={handleRefresh}
            />
          </div>

          {/* Loading Overlay */}
          {isLoading && (
            <div className="absolute inset-0 flex items-center justify-center bg-slate-900/80 z-20">
              <div className="text-center">
                <div className="animate-spin h-12 w-12 border-4 border-indigo-500 border-t-transparent rounded-full mx-auto" />
                <p className="mt-4 text-slate-300">Loading graph...</p>
              </div>
            </div>
          )}

          {/* Error Overlay */}
          {error && !isLoading && (
            <div className="absolute inset-0 flex items-center justify-center bg-slate-900/80 z-20">
              <div className="bg-red-900/50 border border-red-700 rounded-lg p-6 max-w-md">
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

          {/* Force Graph */}
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

          {/* Hover Tooltip */}
          {hoveredNode && hoveredNode.id !== selectedNodeId && (
            <NodeTooltip node={hoveredNode} />
          )}

          {/* Stats Badge */}
          {graphData?.stats && (
            <div className="absolute top-4 right-4 z-10 px-3 py-1.5 bg-slate-800/90 rounded text-sm text-slate-300">
              {graphData.stats.totalNodes.toLocaleString()} nodes · {graphData.stats.totalLinks.toLocaleString()} edges
            </div>
          )}
        </div>

        {/* Right Panel - Details */}
        <DetailsPanel 
          isCollapsed={rightPanelCollapsed}
          onToggleCollapse={() => setRightPanelCollapsed(!rightPanelCollapsed)}
          onCenterNode={handleCenterNode}
        />
      </div>

      {/* Status Bar */}
      <StatusBar />
    </div>
  )
}
