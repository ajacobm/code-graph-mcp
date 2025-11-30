/**
 * ForceGraph Component
 * 
 * React wrapper for the force-graph library with 2D/3D support.
 * 
 * Note: The force-graph library uses a factory pattern where the default export
 * returns a function that creates graph instances. TypeScript struggles with this
 * pattern, so we use a type assertion to work around it. The library does ship
 * with proper type definitions in dist/force-graph.d.ts.
 */

import { useEffect, useRef, useCallback, forwardRef, useImperativeHandle } from 'react'
import ForceGraph2D from 'force-graph'
import ForceGraph3D from '3d-force-graph'
import type { GraphData, ForceGraphNode, ForceGraphLink, GraphDimension } from '@/types'

/**
 * ForceGraph instance type - represents a configured force-graph instance.
 * The library's TypeScript definitions are complex due to the factory pattern,
 * so we define a simplified interface for the methods we use.
 */
interface ForceGraphInstance {
  graphData: (data?: { nodes: object[]; links: object[] }) => ForceGraphInstance
  nodeId: (accessor: string) => ForceGraphInstance
  nodeLabel: (fn: (node: ForceGraphNode) => string) => ForceGraphInstance
  nodeColor: (fn: (node: ForceGraphNode) => string) => ForceGraphInstance
  nodeVal: (fn: (node: ForceGraphNode) => number) => ForceGraphInstance
  linkColor: (fn: (link: ForceGraphLink) => string) => ForceGraphInstance
  linkWidth: (fn: (link: ForceGraphLink) => number) => ForceGraphInstance
  linkDirectionalArrowLength: (length: number) => ForceGraphInstance
  linkDirectionalArrowRelPos: (pos: number) => ForceGraphInstance
  onNodeClick: (fn: (node: ForceGraphNode) => void) => ForceGraphInstance
  onNodeHover: (fn: (node: ForceGraphNode | null) => void) => ForceGraphInstance
  onBackgroundClick: (fn: () => void) => ForceGraphInstance
  cooldownTicks: (ticks: number) => ForceGraphInstance
  backgroundColor: (color: string) => ForceGraphInstance
  nodeCanvasObject?: (fn: (node: ForceGraphNode, ctx: CanvasRenderingContext2D, globalScale: number) => void) => ForceGraphInstance
  nodeThreeObject?: (fn: (node: ForceGraphNode) => object) => ForceGraphInstance
  zoomToFit: (duration: number, padding: number) => void
  centerAt: (x: number | undefined, y: number | undefined, duration: number) => void
  zoom: (factor: number, duration: number) => void
  width: (width: number) => ForceGraphInstance
  height: (height: number) => ForceGraphInstance
  cameraPosition?: (position: { x: number; y: number; z: number }, lookAt?: { x: number; y: number; z: number }, transitionDuration?: number) => void
}

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
  dimension?: GraphDimension
  onNodeClick?: (node: ForceGraphNode) => void
  onNodeDoubleClick?: (node: ForceGraphNode) => void
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
  dimension = '2d',
  onNodeClick,
  onNodeDoubleClick,
  onNodeHover,
  onBackgroundClick,
}, ref) => {
  const containerRef = useRef<HTMLDivElement>(null)
  const graphRef = useRef<ForceGraphInstance | null>(null)
  const lastClickTimeRef = useRef<number>(0)
  const lastClickNodeRef = useRef<string | null>(null)

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

  // Handle click with double-click detection
  const handleNodeClick = useCallback((node: ForceGraphNode) => {
    const now = Date.now()
    const DOUBLE_CLICK_THRESHOLD = 300 // ms

    if (
      lastClickNodeRef.current === node.id &&
      now - lastClickTimeRef.current < DOUBLE_CLICK_THRESHOLD
    ) {
      // Double-click detected
      onNodeDoubleClick?.(node)
      lastClickNodeRef.current = null
      lastClickTimeRef.current = 0
    } else {
      // Single click
      onNodeClick?.(node)
      lastClickNodeRef.current = node.id
      lastClickTimeRef.current = now
    }
  }, [onNodeClick, onNodeDoubleClick])

  // Expose methods to parent via ref
  useImperativeHandle(ref, () => ({
    zoomToFit: (duration = 500) => {
      graphRef.current?.zoomToFit(duration, 50)
    },
    centerNode: (nodeId: string) => {
      if (!graphRef.current || !data) return
      const node = data.nodes.find(n => n.id === nodeId) as ForceGraphNode | undefined
      if (node && node.x !== undefined && node.y !== undefined) {
        if (dimension === '3d' && graphRef.current.cameraPosition) {
          graphRef.current.cameraPosition(
            { x: node.x, y: node.y, z: (node.z || 0) + 200 },
            { x: node.x, y: node.y, z: node.z || 0 },
            500
          )
        } else {
          graphRef.current.centerAt(node.x, node.y, 500)
          graphRef.current.zoom(2, 500)
        }
      }
    }
  }), [data, dimension])

  // Initialize graph
  useEffect(() => {
    if (!containerRef.current) return

    // Store ref for cleanup
    const container = containerRef.current

    // Clear existing
    container.innerHTML = ''

    /**
     * Initialize the force-graph instance.
     * The library uses a factory pattern: ForceGraph2D/3D() returns a function
     * that takes an HTMLElement and returns a chainable graph instance.
     */
    let graph: ForceGraphInstance

    if (dimension === '3d') {
      const ForceGraph3DFactory = ForceGraph3D as unknown as () => (container: HTMLElement) => ForceGraphInstance
      graph = ForceGraph3DFactory()(container)
        .graphData({ nodes: [], links: [] })
        .nodeId('id')
        .nodeLabel((node: ForceGraphNode) => {
          return `${node.name}\n${node.type} | ${node.language}\nComplexity: ${node.complexity}`
        })
        .nodeColor((node: ForceGraphNode) => getNodeColor(node))
        .nodeVal((node: ForceGraphNode) => getNodeSize(node))
        .linkColor((link: ForceGraphLink) => {
          return link.isSeam ? '#f59e0b' : '#475569'
        })
        .linkWidth((link: ForceGraphLink) => {
          return link.isSeam ? 2 : 1
        })
        .linkDirectionalArrowLength(6)
        .linkDirectionalArrowRelPos(1)
        .onNodeClick((node: ForceGraphNode) => {
          handleNodeClick(node)
        })
        .onNodeHover((node: ForceGraphNode | null) => {
          onNodeHover?.(node)
        })
        .onBackgroundClick(() => {
          onBackgroundClick?.()
        })
        .cooldownTicks(100)
        .backgroundColor('#0f172a')
    } else {
      const ForceGraphFactory = ForceGraph2D as unknown as () => (container: HTMLElement) => ForceGraphInstance
      graph = ForceGraphFactory()(container)
        .graphData({ nodes: [], links: [] })
        .nodeId('id')
        .nodeLabel((node: ForceGraphNode) => {
          return `${node.name}\n${node.type} | ${node.language}\nComplexity: ${node.complexity}`
        })
        .nodeColor((node: ForceGraphNode) => getNodeColor(node))
        .nodeVal((node: ForceGraphNode) => getNodeSize(node))
        .linkColor((link: ForceGraphLink) => {
          return link.isSeam ? '#f59e0b' : '#475569'
        })
        .linkWidth((link: ForceGraphLink) => {
          return link.isSeam ? 2 : 1
        })
        .linkDirectionalArrowLength(6)
        .linkDirectionalArrowRelPos(1)
        .onNodeClick((node: ForceGraphNode) => {
          handleNodeClick(node)
        })
        .onNodeHover((node: ForceGraphNode | null) => {
          onNodeHover?.(node)
        })
        .onBackgroundClick(() => {
          onBackgroundClick?.()
        })
        .cooldownTicks(100)
        .backgroundColor('#0f172a')

      // Custom node rendering with labels (2D only)
      if (showLabels && graph.nodeCanvasObject) {
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
    }

    graphRef.current = graph

    // Cleanup
    return () => {
      container.innerHTML = ''
      graphRef.current = null
    }
  }, [showLabels, dimension, getNodeColor, getNodeSize, handleNodeClick, onNodeHover, onBackgroundClick])

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

    const container = containerRef.current
    const graph = graphRef.current

    const resizeObserver = new ResizeObserver(() => {
      if (graph && container) {
        graph.width(container.clientWidth)
        graph.height(container.clientHeight)
      }
    })

    resizeObserver.observe(container)
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
