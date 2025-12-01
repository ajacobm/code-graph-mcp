/**
 * BreadcrumbNavigation Component
 * 
 * Shows the navigation path and allows jumping to any level in the hierarchy.
 */

import { type KeyboardEvent } from 'react'
import { clsx } from 'clsx'

export interface NavigationItem {
  nodeId: string
  nodeName: string
  nodeType: string
}

export interface BreadcrumbNavigationProps {
  path: NavigationItem[]
  onNavigateToLevel: (index: number) => void
  onHome: () => void
  className?: string
}

/**
 * BreadcrumbNavigation Component
 */
export function BreadcrumbNavigation({
  path,
  onNavigateToLevel,
  onHome,
  className,
}: BreadcrumbNavigationProps) {
  // Don't render if there's no navigation path
  if (path.length === 0) {
    return null
  }

  const handleHomeClick = () => {
    onHome()
  }

  const handleHomeKeyDown = (e: KeyboardEvent<HTMLButtonElement>) => {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault()
      onHome()
    }
  }

  const handleLevelClick = (index: number) => {
    // Don't navigate if clicking the current (last) item
    if (index === path.length - 1) return
    onNavigateToLevel(index)
  }

  const handleLevelKeyDown = (e: KeyboardEvent<HTMLButtonElement>, index: number) => {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault()
      handleLevelClick(index)
    }
  }

  // Truncate path if too long (show first 2, ellipsis, last 2)
  const shouldTruncate = path.length > 5
  const displayPath = shouldTruncate
    ? [
        ...path.slice(0, 2),
        { nodeId: 'ellipsis', nodeName: '...', nodeType: 'ellipsis' } as NavigationItem,
        ...path.slice(-2),
      ]
    : path

  // Get the actual index for a display path item
  const getActualIndex = (displayIndex: number): number => {
    if (!shouldTruncate) return displayIndex
    if (displayIndex < 2) return displayIndex
    if (displayPath[displayIndex].nodeId === 'ellipsis') return -1
    return path.length - (displayPath.length - displayIndex)
  }

  return (
    <nav
      className={clsx(
        'flex items-center gap-2 px-4 py-2 bg-slate-800/80 rounded-lg border border-slate-700',
        className
      )}
      aria-label="Navigation breadcrumb"
      data-test="breadcrumb-navigation"
    >
      {/* Home button */}
      <button
        onClick={handleHomeClick}
        onKeyDown={handleHomeKeyDown}
        className={clsx(
          'flex items-center gap-1 px-2 py-1 rounded text-sm',
          'text-slate-300 hover:text-white hover:bg-slate-700',
          'focus:outline-none focus:ring-2 focus:ring-indigo-500',
          'transition-colors duration-150'
        )}
        aria-label="Go to home/root level"
        title="Return to full graph"
        data-test="nav-home-button"
      >
        <span aria-hidden="true">🏠</span>
        <span className="hidden sm:inline">Home</span>
      </button>

      {/* Path segments */}
      {displayPath.map((item, displayIndex) => {
        const actualIndex = getActualIndex(displayIndex)
        const isLast = displayIndex === displayPath.length - 1
        const isEllipsis = item.nodeId === 'ellipsis'
        const isClickable = !isLast && !isEllipsis

        return (
          <div key={`${item.nodeId}-${displayIndex}`} className="flex items-center gap-2">
            {/* Separator */}
            <span className="text-slate-600" aria-hidden="true">/</span>

            {/* Path segment */}
            {isEllipsis ? (
              <span
                className="text-slate-500 px-2"
                aria-hidden="true"
                title="Hidden navigation levels"
              >
                ...
              </span>
            ) : (
              <button
                onClick={() => isClickable && handleLevelClick(actualIndex)}
                onKeyDown={(e) => isClickable && handleLevelKeyDown(e, actualIndex)}
                className={clsx(
                  'px-2 py-1 rounded text-sm max-w-[150px] truncate',
                  'focus:outline-none focus:ring-2 focus:ring-indigo-500',
                  'transition-colors duration-150',
                  isLast
                    ? 'text-white font-medium bg-slate-700/50'
                    : 'text-slate-300 hover:text-white hover:bg-slate-700 cursor-pointer',
                  !isClickable && !isLast && 'cursor-default'
                )}
                aria-current={isLast ? 'page' : undefined}
                title={item.nodeName}
                disabled={isLast}
                data-test={`breadcrumb-${actualIndex}`}
              >
                {item.nodeName}
              </button>
            )}
          </div>
        )
      })}

      {/* Back button (for quick navigation) */}
      {path.length > 0 && (
        <button
          onClick={() => onNavigateToLevel(path.length - 2)}
          className={clsx(
            'ml-2 flex items-center gap-1 px-2 py-1 rounded text-sm',
            'text-slate-400 hover:text-white hover:bg-slate-700',
            'focus:outline-none focus:ring-2 focus:ring-indigo-500',
            'transition-colors duration-150',
            path.length <= 1 && 'opacity-50 cursor-not-allowed'
          )}
          aria-label="Go back one level"
          title="Go back"
          disabled={path.length <= 1}
          data-test="nav-back-button"
        >
          <span aria-hidden="true">←</span>
          <span className="hidden sm:inline">Back</span>
        </button>
      )}
    </nav>
  )
}

BreadcrumbNavigation.displayName = 'BreadcrumbNavigation'
