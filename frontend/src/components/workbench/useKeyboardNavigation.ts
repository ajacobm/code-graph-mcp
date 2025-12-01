/**
 * useKeyboardNavigation Hook
 * 
 * Custom hook for keyboard navigation in the WorkbenchCanvas.
 * Supports:
 * - Arrow keys to navigate between cards
 * - Enter to drill into selected card
 * - Escape to go back one level
 * - Home to go to the root node
 */

import { useCallback, useEffect, useState } from 'react'
import type { GraphNode } from '@/types'

export interface UseKeyboardNavigationOptions {
  /** All navigable nodes */
  nodes: GraphNode[]
  /** Currently selected node ID */
  selectedNodeId: string | null | undefined
  /** Callback to select a node */
  onSelect: (nodeId: string) => void
  /** Callback to drill into a node */
  onDrillDown: (nodeId: string) => void
  /** Callback to go back one level */
  onNavigateBack: () => void
  /** Callback to go to root/home */
  onNavigateHome: () => void
  /** Whether keyboard navigation is enabled */
  enabled?: boolean
  /** Number of columns in grid view (for proper arrow navigation) */
  gridColumns?: number
}

export interface UseKeyboardNavigationResult {
  /** Currently focused node index */
  focusedIndex: number
  /** Set the focused index programmatically */
  setFocusedIndex: (index: number) => void
  /** Whether keyboard navigation is active */
  isKeyboardActive: boolean
  /** Handle keyboard events (attach to container) */
  handleKeyDown: (e: React.KeyboardEvent) => void
}

/**
 * Hook for managing keyboard navigation in a grid/list of nodes
 */
export function useKeyboardNavigation({
  nodes,
  selectedNodeId,
  onSelect,
  onDrillDown,
  onNavigateBack,
  onNavigateHome,
  enabled = true,
  gridColumns = 3,
}: UseKeyboardNavigationOptions): UseKeyboardNavigationResult {
  // Track the currently focused index
  const [focusedIndex, setFocusedIndex] = useState(-1)
  // Track if keyboard navigation is currently active (vs mouse)
  const [isKeyboardActive, setIsKeyboardActive] = useState(false)

  // Sync focused index when selectedNodeId changes from external source
  useEffect(() => {
    if (selectedNodeId && !isKeyboardActive) {
      const index = nodes.findIndex(n => n.id === selectedNodeId)
      if (index !== -1) {
        setFocusedIndex(index)
      }
    }
  }, [selectedNodeId, nodes, isKeyboardActive])

  // Reset focused index when nodes change
  useEffect(() => {
    if (nodes.length === 0) {
      setFocusedIndex(-1)
    } else if (focusedIndex >= nodes.length) {
      setFocusedIndex(nodes.length - 1)
    }
  }, [nodes.length, focusedIndex])

  // Handle keyboard navigation
  const handleKeyDown = useCallback((e: React.KeyboardEvent) => {
    if (!enabled || nodes.length === 0) return

    const { key } = e

    // Only handle navigation keys
    const isNavigationKey = ['ArrowUp', 'ArrowDown', 'ArrowLeft', 'ArrowRight', 'Enter', 'Escape', 'Home', 'End'].includes(key)
    if (!isNavigationKey) return

    // Mark keyboard navigation as active
    setIsKeyboardActive(true)

    // Handle Escape - go back one level
    if (key === 'Escape') {
      e.preventDefault()
      onNavigateBack()
      return
    }

    // Handle Home - go to root
    if (key === 'Home') {
      e.preventDefault()
      if (e.ctrlKey || e.metaKey) {
        onNavigateHome()
      } else {
        setFocusedIndex(0)
        const firstNode = nodes[0]
        if (firstNode) {
          onSelect(firstNode.id)
        }
      }
      return
    }

    // Handle End - go to last node
    if (key === 'End') {
      e.preventDefault()
      const lastIndex = nodes.length - 1
      setFocusedIndex(lastIndex)
      const lastNode = nodes[lastIndex]
      if (lastNode) {
        onSelect(lastNode.id)
      }
      return
    }

    // Handle Enter - drill into selected node
    if (key === 'Enter') {
      e.preventDefault()
      if (focusedIndex >= 0 && focusedIndex < nodes.length) {
        const node = nodes[focusedIndex]
        if (node) {
          onDrillDown(node.id)
        }
      }
      return
    }

    // Handle arrow key navigation
    let newIndex = focusedIndex

    if (focusedIndex === -1) {
      // No current selection, start at first node
      newIndex = 0
    } else {
      switch (key) {
        case 'ArrowUp':
          e.preventDefault()
          // Move up one row
          newIndex = Math.max(0, focusedIndex - gridColumns)
          break
        case 'ArrowDown':
          e.preventDefault()
          // Move down one row
          newIndex = Math.min(nodes.length - 1, focusedIndex + gridColumns)
          break
        case 'ArrowLeft':
          e.preventDefault()
          // Move left one item
          if (focusedIndex > 0) {
            newIndex = focusedIndex - 1
          }
          break
        case 'ArrowRight':
          e.preventDefault()
          // Move right one item
          if (focusedIndex < nodes.length - 1) {
            newIndex = focusedIndex + 1
          }
          break
      }
    }

    // Update focus and selection if index changed
    if (newIndex !== focusedIndex && newIndex >= 0 && newIndex < nodes.length) {
      setFocusedIndex(newIndex)
      const node = nodes[newIndex]
      if (node) {
        onSelect(node.id)
      }
    }
  }, [enabled, nodes, focusedIndex, gridColumns, onSelect, onDrillDown, onNavigateBack, onNavigateHome])

  // Detect mouse activity to disable keyboard active state
  useEffect(() => {
    const handleMouseMove = () => {
      setIsKeyboardActive(false)
    }

    document.addEventListener('mousemove', handleMouseMove)
    return () => {
      document.removeEventListener('mousemove', handleMouseMove)
    }
  }, [])

  return {
    focusedIndex,
    setFocusedIndex,
    isKeyboardActive,
    handleKeyDown,
  }
}

export default useKeyboardNavigation
