/**
 * ToolsPanel Component
 * 
 * Left sidebar with tools for graph navigation and filtering.
 */

import { useState } from 'react'
import { useGraphStore } from '@/stores/graphStore'

interface ToolsPanelProps {
  isCollapsed?: boolean
  onToggleCollapse?: () => void
  onCategorySelect?: (category: string) => void
  onSearch?: (query: string) => void
}

const CATEGORIES = [
  { id: 'entry_points', emoji: '🚀', title: 'Entry Points', description: 'Functions with no callers' },
  { id: 'hubs', emoji: '🔀', title: 'Hubs', description: 'Highly connected nodes' },
  { id: 'leaves', emoji: '🍃', title: 'Leaves', description: 'Functions with no callees' },
]

const LEGEND = [
  { color: 'bg-green-500', label: 'Function' },
  { color: 'bg-blue-500', label: 'Class' },
  { color: 'bg-purple-500', label: 'Method' },
  { color: 'bg-amber-500', label: 'Module' },
  { color: 'bg-gray-500', label: 'Import' },
]

export function ToolsPanel({ 
  isCollapsed = false, 
  onToggleCollapse,
  onCategorySelect,
  onSearch 
}: ToolsPanelProps) {
  const [searchQuery, setSearchQuery] = useState('')
  const { filters, setFilter, graphData } = useGraphStore()

  const handleSearch = () => {
    if (searchQuery.trim()) {
      onSearch?.(searchQuery.trim())
      setFilter({ searchQuery: searchQuery.trim() })
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      handleSearch()
    }
  }

  // Get available languages from loaded data
  const availableLanguages = graphData?.stats?.languages 
    ? Object.keys(graphData.stats.languages).sort()
    : []

  const availableTypes = graphData?.stats?.nodeTypes
    ? Object.keys(graphData.stats.nodeTypes).sort()
    : []

  return (
    <div 
      className={`flex flex-col bg-slate-800 border-r border-slate-700 transition-all duration-300 ${
        isCollapsed ? 'w-12' : 'w-64'
      }`}
    >
      {/* Header */}
      <div className="flex items-center justify-between p-3 border-b border-slate-700">
        {!isCollapsed && <h2 className="font-semibold text-slate-200">Tools</h2>}
        <button
          onClick={onToggleCollapse}
          className="p-1.5 rounded hover:bg-slate-700 transition-colors"
        >
          <svg 
            xmlns="http://www.w3.org/2000/svg" 
            className={`h-5 w-5 text-slate-400 transition-transform ${isCollapsed ? 'rotate-180' : ''}`}
            fill="none" 
            viewBox="0 0 24 24" 
            stroke="currentColor"
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 19l-7-7 7-7m8 14l-7-7 7-7" />
          </svg>
        </button>
      </div>

      {/* Content (hidden when collapsed) */}
      {!isCollapsed && (
        <div className="flex-1 overflow-y-auto p-3 space-y-4">
          {/* Search */}
          <div>
            <label className="block text-xs text-slate-400 mb-1.5">Search Nodes</label>
            <div className="flex gap-1">
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="Function name..."
                className="flex-1 px-2 py-1.5 text-sm bg-slate-900 border border-slate-600 rounded text-slate-200 placeholder-slate-500 focus:outline-none focus:border-indigo-500"
              />
              <button 
                onClick={handleSearch}
                className="px-2 py-1.5 bg-indigo-600 text-white rounded hover:bg-indigo-700 transition-colors"
              >
                🔍
              </button>
            </div>
          </div>

          {/* Categories */}
          <div>
            <label className="block text-xs text-slate-400 mb-1.5">Quick Access</label>
            <div className="space-y-1">
              {CATEGORIES.map((cat) => (
                <button
                  key={cat.id}
                  onClick={() => onCategorySelect?.(cat.id)}
                  className="w-full flex items-center gap-2 px-2 py-2 rounded hover:bg-slate-700 transition-colors text-left"
                >
                  <span className="text-lg">{cat.emoji}</span>
                  <div className="flex-1 min-w-0">
                    <div className="text-sm font-medium text-slate-200 truncate">{cat.title}</div>
                    <div className="text-xs text-slate-500 truncate">{cat.description}</div>
                  </div>
                </button>
              ))}
            </div>
          </div>

          {/* Language Filter */}
          {availableLanguages.length > 0 && (
            <div>
              <label className="block text-xs text-slate-400 mb-1.5">Language</label>
              <select
                value={filters.languages[0] || ''}
                onChange={(e) => setFilter({ languages: e.target.value ? [e.target.value] : [] })}
                className="w-full px-2 py-1.5 text-sm bg-slate-900 border border-slate-600 rounded text-slate-200 focus:outline-none focus:border-indigo-500"
              >
                <option value="">All Languages</option>
                {availableLanguages.map((lang) => (
                  <option key={lang} value={lang}>{lang}</option>
                ))}
              </select>
            </div>
          )}

          {/* Type Filter */}
          {availableTypes.length > 0 && (
            <div>
              <label className="block text-xs text-slate-400 mb-1.5">Node Type</label>
              <select
                value={filters.nodeTypes[0] || ''}
                onChange={(e) => setFilter({ nodeTypes: e.target.value ? [e.target.value] : [] })}
                className="w-full px-2 py-1.5 text-sm bg-slate-900 border border-slate-600 rounded text-slate-200 focus:outline-none focus:border-indigo-500"
              >
                <option value="">All Types</option>
                {availableTypes.map((type) => (
                  <option key={type} value={type}>{type}</option>
                ))}
              </select>
            </div>
          )}

          {/* Legend */}
          <div>
            <label className="block text-xs text-slate-400 mb-1.5">Legend</label>
            <div className="space-y-1">
              {LEGEND.map((item) => (
                <div key={item.label} className="flex items-center gap-2 text-xs">
                  <span className={`w-3 h-3 rounded-full ${item.color}`} />
                  <span className="text-slate-300">{item.label}</span>
                </div>
              ))}
              <div className="flex items-center gap-2 text-xs mt-2 pt-2 border-t border-slate-700">
                <span className="w-3 h-1 bg-amber-500" />
                <span className="text-slate-300">Cross-language (Seam)</span>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Collapsed Icons */}
      {isCollapsed && (
        <div className="flex-1 flex flex-col items-center py-3 gap-2">
          {CATEGORIES.map((cat) => (
            <button
              key={cat.id}
              onClick={() => onCategorySelect?.(cat.id)}
              className="p-2 rounded hover:bg-slate-700 transition-colors"
              title={cat.title}
            >
              {cat.emoji}
            </button>
          ))}
        </div>
      )}
    </div>
  )
}
