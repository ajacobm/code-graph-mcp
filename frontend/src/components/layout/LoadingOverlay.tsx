/**
 * LoadingOverlay Component
 * 
 * A semi-transparent overlay with loading spinner for async operations.
 */

import { clsx } from 'clsx'
import { LoadingSpinner } from './LoadingSpinner'

export interface LoadingOverlayProps {
  /** Whether the overlay is visible */
  isLoading: boolean
  /** Optional label text */
  label?: string
  /** Additional class names */
  className?: string
}

/**
 * LoadingOverlay Component
 */
export function LoadingOverlay({ 
  isLoading, 
  label = 'Loading...',
  className 
}: LoadingOverlayProps) {
  if (!isLoading) return null

  return (
    <div 
      className={clsx(
        'absolute inset-0 flex items-center justify-center bg-slate-900/80 z-20',
        'animate-in fade-in duration-200',
        className
      )}
      role="alert"
      aria-busy="true"
      aria-live="polite"
    >
      <LoadingSpinner size="lg" label={label} />
    </div>
  )
}

LoadingOverlay.displayName = 'LoadingOverlay'
