<script setup lang="ts">
import { onMounted, ref, watch } from 'vue'
import cytoscape from 'cytoscape'
import dagre from 'cytoscape-dagre'
import { useGraphStore } from '../stores/graphStore'
import type { Core } from 'cytoscape'

cytoscape.use(dagre)

const graphStore = useGraphStore()

const container = ref<HTMLElement>()
let cy: Core | null = null

const initCytoscape = () => {
  if (!container.value) return

  cy = cytoscape({
    container: container.value,
    elements: [],
    style: [
      {
        selector: 'node',
        style: {
          content: 'data(label)',
          'background-color': '#4F46E5',
          color: '#FFF',
          'text-valign': 'center',
          'text-halign': 'center',
          'font-size': '11px',
          'padding': '8px',
          width: '60px',
          height: '60px',
          'text-wrap': 'wrap',
          'border-width': '1px',
          'border-color': '#818CF8',
        },
      },
      {
        selector: 'node:selected',
        style: {
          'background-color': '#EC4899',
          'border-width': '3px',
          'border-color': '#FFF',
        },
      },
      {
        selector: 'node:hover',
        style: {
          'background-color': '#6366F1',
          'border-width': '2px',
          'border-color': '#FCD34D',
        },
      },
      {
        selector: 'edge',
        style: {
          'target-arrow-shape': 'triangle',
          'line-color': '#9CA3AF',
          'target-arrow-color': '#9CA3AF',
          'curve-style': 'bezier',
          width: '2px',
        },
      },
      {
        selector: 'edge[isSeam="true"]',
        style: {
          'line-color': '#DC2626',
          'target-arrow-color': '#DC2626',
          'line-style': 'dashed',
          width: '3px',
        },
      },
    ],
    layout: {
      name: 'dagre',
      rankDir: 'TB',
    } as any,
  })

  cy.on('tap', 'node', (event) => {
    graphStore.selectNode(event.target.id())
  })

  cy.on('tap', (event) => {
    if (event.target === cy) {
      graphStore.selectNode(null)
    }
  })
}

const updateGraph = () => {
  if (!cy) return

  const nodes = (graphStore.nodeArray || []).map((n) => ({
    data: {
      id: n.id,
      label: n.name.substring(0, 15),
    },
  }))

  const edges = (graphStore.edgeArray || []).map((e) => ({
    data: {
      id: e.id,
      source: e.source,
      target: e.target,
      isSeam: e.isSeam,
    },
  }))

  if (!cy) return
  cy.elements().remove()
  cy.add([...nodes, ...edges])

  cy.layout({ name: 'dagre', directed: true, rankDir: 'TB' } as any).run()
}

onMounted(() => {
  initCytoscape()
  updateGraph()
})

watch(() => [graphStore.nodeArray, graphStore.edgeArray], updateGraph, { deep: true })
</script>

<template>
  <div ref="container" class="w-full h-full bg-gray-900"></div>
</template>
