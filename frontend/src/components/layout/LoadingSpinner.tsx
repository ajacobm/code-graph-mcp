/**
 * LoadingSpinner Component
 * 
 * A reusable loading spinner with different size variants.
 */

import { clsx } from 'clsx'

export interface LoadingSpinnerProps {
  /** Size variant */
  size?: 'sm' | 'md' | 'lg'
  /** Optional label text */
  label?: string
  /** Additional class names */
  className?: string
}

const sizeClasses = {
  sm: 'h-4 w-4 border-2',
  md: 'h-8 w-8 border-3',
  lg: 'h-12 w-12 border-4',
}

/**
 * LoadingSpinner Component
 */
export function LoadingSpinner({ 
  size = 'md', 
  label,
  className 
}: LoadingSpinnerProps) {
  return (
    <div className={clsx('flex flex-col items-center justify-center gap-2', className)}>
      <div 
        className={clsx(
          'animate-spin rounded-full border-indigo-500 border-t-transparent',
          sizeClasses[size]
        )}
        role="status"
        aria-label={label || 'Loading'}
      />
      {label && (
        <p className="text-sm text-slate-400">{label}</p>
      )}
    </div>
  )
}

LoadingSpinner.displayName = 'LoadingSpinner'
