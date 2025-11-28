/**
 * Header Component
 * 
 * Top navigation bar with branding and stats.
 */

import { useGraphStore } from '@/stores/graphStore'
import { reanalyze } from '@/api/graphApi'
import { useState } from 'react'

export function Header() {
  const { graphData, isLoading, loadGraph } = useGraphStore()
  const [reanalyzing, setReanalyzing] = useState(false)

  const handleReanalyze = async () => {
    setReanalyzing(true)
    try {
      await reanalyze()
      await loadGraph()
    } catch (err) {
      console.error('Reanalysis failed:', err)
    } finally {
      setReanalyzing(false)
    }
  }

  const stats = graphData?.stats

  return (
    <header className="sticky top-0 z-50 bg-slate-900/95 backdrop-blur border-b border-slate-700">
      <div className="px-4 py-3 flex items-center justify-between">
        {/* Logo */}
        <div className="flex items-center gap-3">
          <h1 className="text-xl font-bold bg-gradient-to-r from-indigo-400 to-pink-400 bg-clip-text text-transparent">
            📊 CodeNavigator
          </h1>
          <span className="px-2 py-0.5 text-xs bg-indigo-600/30 text-indigo-300 rounded">
            v2
          </span>
        </div>

        {/* Right side: Stats and Actions */}
        <div className="flex items-center gap-4">
          {/* Re-analyze Button */}
          <button
            onClick={handleReanalyze}
            disabled={isLoading || reanalyzing}
            className="px-4 py-1.5 bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 text-white rounded-lg transition-colors text-sm flex items-center gap-2"
          >
            {reanalyzing ? (
              <>
                <svg className="animate-spin h-4 w-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                Analyzing...
              </>
            ) : (
              <>🔄 Re-analyze</>
            )}
          </button>

          {/* Stats */}
          {stats && (
            <div className="hidden sm:flex items-center gap-3 text-sm text-slate-400">
              <span>
                <span className="font-semibold text-slate-200">{stats.totalNodes.toLocaleString()}</span> nodes
              </span>
              <span className="text-slate-600">·</span>
              <span>
                <span className="font-semibold text-slate-200">{stats.totalLinks.toLocaleString()}</span> edges
              </span>
              {Object.keys(stats.languages).length > 0 && (
                <>
                  <span className="text-slate-600">·</span>
                  <span>
                    <span className="font-semibold text-slate-200">{Object.keys(stats.languages).length}</span> languages
                  </span>
                </>
              )}
            </div>
          )}
        </div>
      </div>
    </header>
  )
}
