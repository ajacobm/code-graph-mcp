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
    setColorMode 
  } = useGraphStore()

  return (
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
  )
}
