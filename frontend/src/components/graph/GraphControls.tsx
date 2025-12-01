/**
 * GraphControls Component
 * 
 * Controls for the graph visualization.
 */

import { useGraphStore } from '@/stores/graphStore'

interface GraphControlsProps {
  onZoomToFit: () => void
  onRefresh: () => void
}

export function GraphControls({ onZoomToFit, onRefresh }: GraphControlsProps) {
  const { 
    isLoading, 
    showLabels, 
    setShowLabels, 
    colorMode, 
    setColorMode,
    graphDimension,
    setGraphDimension,
    navigationStack,
    navigateBack,
    resetNavigation,
  } = useGraphStore()

  const hasNavigation = navigationStack.length > 0

  return (
    <div className="flex flex-col gap-2">
      {/* Main controls row */}
      <div className="flex items-center gap-2 p-2 bg-slate-800/50 rounded-lg backdrop-blur">
        {/* Zoom to Fit */}
        <button
          onClick={onZoomToFit}
          className="p-2 rounded hover:bg-slate-700 transition-colors"
          title="Zoom to fit"
        >
          <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 text-slate-300" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 8V4m0 0h4M4 4l5 5m11-1V4m0 0h-4m4 0l-5 5M4 16v4m0 0h4m-4 0l5-5m11 5l-5-5m5 5v-4m0 4h-4" />
          </svg>
        </button>

        {/* Refresh */}
        <button
          onClick={onRefresh}
          disabled={isLoading}
          className="p-2 rounded hover:bg-slate-700 transition-colors disabled:opacity-50"
          title="Refresh graph"
        >
          <svg 
            xmlns="http://www.w3.org/2000/svg" 
            className={`h-5 w-5 text-slate-300 ${isLoading ? 'animate-spin' : ''}`}
            fill="none" 
            viewBox="0 0 24 24" 
            stroke="currentColor"
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
          </svg>
        </button>

        <div className="w-px h-6 bg-slate-600" />

        {/* 2D/3D Toggle */}
        <div className="flex rounded overflow-hidden">
          <button
            onClick={() => setGraphDimension('2d')}
            className={`px-3 py-1.5 text-sm transition-colors ${
              graphDimension === '2d' ? 'bg-indigo-600 text-white' : 'bg-slate-700 text-slate-300 hover:bg-slate-600'
            }`}
            title="2D view"
          >
            2D
          </button>
          <button
            onClick={() => setGraphDimension('3d')}
            className={`px-3 py-1.5 text-sm transition-colors ${
              graphDimension === '3d' ? 'bg-indigo-600 text-white' : 'bg-slate-700 text-slate-300 hover:bg-slate-600'
            }`}
            title="3D view"
          >
            3D
          </button>
        </div>

        <div className="w-px h-6 bg-slate-600" />

        {/* Toggle Labels */}
        <button
          onClick={() => setShowLabels(!showLabels)}
          className={`px-3 py-1.5 rounded text-sm transition-colors ${
            showLabels ? 'bg-indigo-600 text-white' : 'bg-slate-700 text-slate-300'
          }`}
          title="Toggle labels"
        >
          Labels
        </button>

        {/* Color Mode */}
        <select
          value={colorMode}
          onChange={(e) => setColorMode(e.target.value as 'type' | 'language' | 'complexity')}
          className="px-2 py-1.5 rounded text-sm bg-slate-700 text-slate-200 border-none outline-none"
        >
          <option value="type">Color by Type</option>
          <option value="language">Color by Language</option>
          <option value="complexity">Color by Complexity</option>
        </select>
      </div>

      {/* Navigation breadcrumb row - only show when navigating */}
      {hasNavigation && (
        <div className="flex items-center gap-2 p-2 bg-slate-800/50 rounded-lg backdrop-blur">
          {/* Back button */}
          <button
            onClick={navigateBack}
            className="p-2 rounded hover:bg-slate-700 transition-colors"
            title="Go back"
          >
            <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 text-slate-300" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
            </svg>
          </button>

          {/* Home/Reset button */}
          <button
            onClick={resetNavigation}
            className="p-2 rounded hover:bg-slate-700 transition-colors"
            title="Return to full graph"
          >
            <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 text-slate-300" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" />
            </svg>
          </button>

          <div className="w-px h-6 bg-slate-600" />

          {/* Breadcrumb trail */}
          <div className="flex items-center gap-1 text-sm text-slate-300 overflow-x-auto max-w-md">
            <span 
              className="text-slate-400 cursor-pointer hover:text-white"
              onClick={resetNavigation}
            >
              Full Graph
            </span>
            {navigationStack.map((entry, index) => (
              <span key={entry.nodeId} className="flex items-center gap-1">
                <span className="text-slate-500">→</span>
                <span 
                  className={`${index === navigationStack.length - 1 ? 'text-indigo-400 font-medium' : 'text-slate-400 cursor-pointer hover:text-white'}`}
                  title={`${entry.nodeType}: ${entry.nodeName}`}
                >
                  {entry.nodeName.length > 20 ? `${entry.nodeName.substring(0, 20)}...` : entry.nodeName}
                </span>
              </span>
            ))}
          </div>

          {/* Node count info */}
          <div className="ml-auto text-xs text-slate-500">
            Depth: {navigationStack.length}
          </div>
        </div>
      )}

      {/* Hint for drill-down */}
      {!hasNavigation && (
        <div className="text-xs text-slate-500 px-2">
          💡 Double-click a node to drill into its local subgraph
        </div>
      )}
    </div>
  )
}
