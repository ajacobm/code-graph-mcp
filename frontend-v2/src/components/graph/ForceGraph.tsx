/**
 * ForceGraph Component
 * 
 * React wrapper for the force-graph library.
 */

import { useEffect, useRef, useCallback, forwardRef, useImperativeHandle } from 'react'
import ForceGraph2D from 'force-graph'
import type { GraphData, ForceGraphNode, ForceGraphLink } from '@/types'

// eslint-disable-next-line @typescript-eslint/no-explicit-any
type ForceGraphInstance = any

// Color mappings
const LANGUAGE_COLORS: Record<string, string> = {
  python: '#3776AB',
  typescript: '#3178C6',
  javascript: '#F7DF1E',
  'c#': '#68217A',
  java: '#ED8B00',
  go: '#00ADD8',
  rust: '#CE412B',
  ruby: '#CC342D',
  php: '#777BB4',
  cpp: '#00599C',
  default: '#64748b',
}

const TYPE_COLORS: Record<string, string> = {
  function: '#22c55e',
  class: '#3b82f6',
  method: '#8b5cf6',
  module: '#f59e0b',
  import: '#6b7280',
  default: '#64748b',
}

interface ForceGraphProps {
  data: GraphData | null
  selectedNodeId?: string | null
  highlightedNodeIds?: string[]
  colorMode?: 'type' | 'language' | 'complexity'
  showLabels?: boolean
  onNodeClick?: (node: ForceGraphNode) => void
  onNodeHover?: (node: ForceGraphNode | null) => void
  onBackgroundClick?: () => void
}

export interface ForceGraphRef {
  zoomToFit: (duration?: number) => void
  centerNode: (nodeId: string) => void
}

export const ForceGraph = forwardRef<ForceGraphRef, ForceGraphProps>(({
  data,
  selectedNodeId,
  highlightedNodeIds = [],
  colorMode = 'type',
  showLabels = true,
  onNodeClick,
  onNodeHover,
  onBackgroundClick,
}, ref) => {
  const containerRef = useRef<HTMLDivElement>(null)
  const graphRef = useRef<ForceGraphInstance>(null)

  const getNodeColor = useCallback((node: ForceGraphNode): string => {
    if (selectedNodeId === node.id) {
      return '#f472b6' // Pink for selected
    }
    if (highlightedNodeIds.includes(node.id)) {
      return '#fbbf24' // Yellow for highlighted
    }
    
    if (colorMode === 'language') {
      const lang = node.language?.toLowerCase() || 'default'
      return LANGUAGE_COLORS[lang] || LANGUAGE_COLORS.default
    }
    
    if (colorMode === 'complexity') {
      const c = node.complexity || 0
      if (c <= 5) return '#22c55e'  // Green - low
      if (c <= 10) return '#f59e0b' // Yellow - medium
      if (c <= 20) return '#f97316' // Orange - high
      return '#ef4444'              // Red - very high
    }
    
    // Default: color by type
    const type = node.type?.toLowerCase() || 'default'
    return TYPE_COLORS[type] || TYPE_COLORS.default
  }, [selectedNodeId, highlightedNodeIds, colorMode])

  const getNodeSize = useCallback((node: ForceGraphNode): number => {
    const baseSize = 4
    const complexityFactor = Math.min(node.complexity || 1, 20) / 5
    return baseSize + complexityFactor
  }, [])

  // Expose methods to parent via ref
  useImperativeHandle(ref, () => ({
    zoomToFit: (duration = 500) => {
      graphRef.current?.zoomToFit(duration, 50)
    },
    centerNode: (nodeId: string) => {
      if (!graphRef.current || !data) return
      const node = data.nodes.find(n => n.id === nodeId) as ForceGraphNode | undefined
      if (node && node.x !== undefined && node.y !== undefined) {
        graphRef.current.centerAt(node.x, node.y, 500)
        graphRef.current.zoom(2, 500)
      }
    }
  }), [data])

  // Initialize graph
  useEffect(() => {
    if (!containerRef.current) return

    // Clear existing
    containerRef.current.innerHTML = ''

    // force-graph uses factory pattern
    const ForceGraphFactory = ForceGraph2D as unknown as () => (container: HTMLElement) => ForceGraphInstance
    const graph = ForceGraphFactory()(containerRef.current)
      .graphData({ nodes: [], links: [] })
      .nodeId('id')
      .nodeLabel((node: ForceGraphNode) => {
        const n = node as ForceGraphNode
        return `${n.name}\n${n.type} | ${n.language}\nComplexity: ${n.complexity}`
      })
      .nodeColor((node: ForceGraphNode) => getNodeColor(node as ForceGraphNode))
      .nodeVal((node: ForceGraphNode) => getNodeSize(node as ForceGraphNode))
      .linkColor((link: ForceGraphLink) => {
        const l = link as ForceGraphLink
        return l.isSeam ? '#f59e0b' : '#475569'
      })
      .linkWidth((link: ForceGraphLink) => {
        const l = link as ForceGraphLink
        return l.isSeam ? 2 : 1
      })
      .linkDirectionalArrowLength(6)
      .linkDirectionalArrowRelPos(1)
      .onNodeClick((node: ForceGraphNode) => {
        onNodeClick?.(node as ForceGraphNode)
      })
      .onNodeHover((node: ForceGraphNode | null) => {
        onNodeHover?.(node as ForceGraphNode | null)
      })
      .onBackgroundClick(() => {
        onBackgroundClick?.()
      })
      .cooldownTicks(100)
      .backgroundColor('#0f172a')

    // Custom node rendering with labels
    if (showLabels) {
      graph.nodeCanvasObject((node: ForceGraphNode, ctx: CanvasRenderingContext2D, globalScale: number) => {
        const n = node as ForceGraphNode
        const size = getNodeSize(n)
        const color = getNodeColor(n)
        
        // Draw node circle
        ctx.beginPath()
        ctx.arc(n.x || 0, n.y || 0, size, 0, 2 * Math.PI)
        ctx.fillStyle = color
        ctx.fill()
        
        // Draw label if zoomed in enough
        if (globalScale > 0.8) {
          const label = n.name
          const fontSize = 10 / globalScale
          ctx.font = `${fontSize}px Sans-Serif`
          ctx.textAlign = 'center'
          ctx.textBaseline = 'middle'
          ctx.fillStyle = '#e2e8f0'
          ctx.fillText(label, n.x || 0, (n.y || 0) + size + fontSize)
        }
      })
    }

    graphRef.current = graph

    // Cleanup
    return () => {
      if (containerRef.current) {
        containerRef.current.innerHTML = ''
      }
      graphRef.current = null
    }
  }, [showLabels]) // Only re-init when showLabels changes

  // Update data
  useEffect(() => {
    if (!graphRef.current || !data) return

    const nodes = data.nodes.map(n => ({
      ...n,
      val: getNodeSize(n as ForceGraphNode),
    }))

    const links = data.links.map(l => ({
      source: l.source,
      target: l.target,
      type: l.type,
      isSeam: l.isSeam,
    }))

    graphRef.current.graphData({ nodes, links })

    // Zoom to fit after loading
    setTimeout(() => {
      graphRef.current?.zoomToFit(500, 50)
    }, 500)
  }, [data, getNodeSize])

  // Update colors when selection/highlights change
  useEffect(() => {
    if (!graphRef.current) return
    graphRef.current.nodeColor((node: ForceGraphNode) => getNodeColor(node as ForceGraphNode))
  }, [selectedNodeId, highlightedNodeIds, colorMode, getNodeColor])

  // Handle resize
  useEffect(() => {
    if (!containerRef.current || !graphRef.current) return

    const resizeObserver = new ResizeObserver(() => {
      if (graphRef.current && containerRef.current) {
        graphRef.current.width(containerRef.current.clientWidth)
        graphRef.current.height(containerRef.current.clientHeight)
      }
    })

    resizeObserver.observe(containerRef.current)
    return () => resizeObserver.disconnect()
  }, [])

  return (
    <div 
      ref={containerRef} 
      className="w-full h-full min-h-[400px] bg-slate-900 rounded-lg overflow-hidden"
    />
  )
})

ForceGraph.displayName = 'ForceGraph'
