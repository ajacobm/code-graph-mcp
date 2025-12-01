/**
 * ViewToggle Component
 * 
 * Toggle control for switching between Workbench and Graph views.
 * Persists user preference to localStorage.
 */

import { useCallback } from 'react'
import { clsx } from 'clsx'

export type ViewType = 'workbench' | 'graph'

const STORAGE_KEY = 'codenav.defaultView'

interface ViewToggleProps {
  activeView: ViewType
  onViewChange: (view: ViewType) => void
  className?: string
}

/**
 * Get saved view preference from localStorage
 */
export function getSavedViewPreference(): ViewType {
  try {
    const saved = localStorage.getItem(STORAGE_KEY)
    if (saved === 'workbench' || saved === 'graph') {
      return saved
    }
  } catch {
    // localStorage may not be available
  }
  return 'graph' // Default to graph view
}

/**
 * Save view preference to localStorage
 */
export function saveViewPreference(view: ViewType): void {
  try {
    localStorage.setItem(STORAGE_KEY, view)
  } catch {
    // localStorage may not be available
  }
}

/**
 * ViewToggle Component
 */
export function ViewToggle({ activeView, onViewChange, className }: ViewToggleProps) {
  const handleViewChange = useCallback((view: ViewType) => {
    saveViewPreference(view)
    onViewChange(view)
  }, [onViewChange])

  return (
    <div 
      className={clsx('flex items-center gap-1 bg-slate-800 rounded-lg p-1', className)}
      role="tablist"
      aria-label="View mode selection"
    >
      <button
        role="tab"
        aria-selected={activeView === 'workbench'}
        aria-controls="main-view"
        onClick={() => handleViewChange('workbench')}
        className={clsx(
          'flex items-center gap-2 px-3 py-1.5 rounded-md text-sm font-medium transition-all',
          activeView === 'workbench'
            ? 'bg-indigo-600 text-white shadow-sm'
            : 'text-slate-400 hover:text-white hover:bg-slate-700'
        )}
      >
        <span aria-hidden="true">📋</span>
        <span>Workbench</span>
      </button>
      <button
        role="tab"
        aria-selected={activeView === 'graph'}
        aria-controls="main-view"
        onClick={() => handleViewChange('graph')}
        className={clsx(
          'flex items-center gap-2 px-3 py-1.5 rounded-md text-sm font-medium transition-all',
          activeView === 'graph'
            ? 'bg-indigo-600 text-white shadow-sm'
            : 'text-slate-400 hover:text-white hover:bg-slate-700'
        )}
      >
        <span aria-hidden="true">🔗</span>
        <span>Graph</span>
      </button>
    </div>
  )
}

ViewToggle.displayName = 'ViewToggle'
