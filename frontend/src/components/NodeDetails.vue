<script setup lang="ts">
import { computed } from 'vue'
import { useGraphStore } from '../stores/graphStore'

const graphStore = useGraphStore()

const incomingEdges = computed(() => {
  if (!graphStore.selectedNode) return []
  return graphStore.edgeArray.filter((e) => e.target === graphStore.selectedNode?.id)
})

const outgoingEdges = computed(() => {
  if (!graphStore.selectedNode) return []
  return graphStore.edgeArray.filter((e) => e.source === graphStore.selectedNode?.id)
})

const incomingNodes = computed(() => {
  return incomingEdges.value
    .map((e) => graphStore.nodes.get(e.source))
    .filter((n) => n !== undefined)
})

const outgoingNodes = computed(() => {
  return outgoingEdges.value
    .map((e) => graphStore.nodes.get(e.target))
    .filter((n) => n !== undefined)
})

const copyNodeId = () => {
  if (graphStore.selectedNode) {
    navigator.clipboard.writeText(graphStore.selectedNode.id)
  }
}

const selectNodeFromList = (nodeId: string) => {
  graphStore.selectNode(nodeId)
  graphStore.traverse(nodeId, 5)
}
</script>

<template>
  <div class="space-y-4">
    <div v-if="!graphStore.selectedNode" class="text-center py-12">
      <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" class="w-16 h-16 mx-auto stroke-base-content/30 mb-4">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
      </svg>
      <p class="text-base-content/60">Select a node to view details</p>
    </div>

    <div v-else class="space-y-4">
      <div>
        <h3 class="text-lg font-bold text-base-content flex items-center gap-2 mb-3">
          <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" class="w-5 h-5 stroke-current text-primary">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
          {{ graphStore.selectedNode.name }}
        </h3>

        <div class="stats stats-vertical shadow bg-base-100 w-full">
          <div class="stat py-3">
            <div class="stat-title text-xs">Type</div>
            <div class="stat-value text-sm font-mono text-primary">{{ graphStore.selectedNode.type }}</div>
          </div>
          
          <div class="stat py-3">
            <div class="stat-title text-xs">Language</div>
            <div class="stat-value text-sm font-mono text-secondary">{{ graphStore.selectedNode.language }}</div>
          </div>
          
          <div class="stat py-3">
            <div class="stat-title text-xs">Complexity</div>
            <div class="stat-value text-sm">
              <div class="badge badge-info badge-lg">{{ graphStore.selectedNode.complexity }}</div>
            </div>
          </div>
          
          <div class="stat py-3">
            <div class="stat-title text-xs">Line</div>
            <div class="stat-value text-sm font-mono">{{ graphStore.selectedNode.line }}</div>
          </div>
        </div>

        <div class="mt-3 mockup-code bg-base-300 text-xs">
          <pre class="px-4"><code class="text-success break-all">{{ graphStore.selectedNode.file_path }}</code></pre>
        </div>

        <button @click="copyNodeId" class="btn btn-primary btn-sm w-full mt-3 gap-2">
          <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" class="w-4 h-4 stroke-current">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
          </svg>
          Copy ID
        </button>
      </div>

      <div v-if="graphStore.selectedNode.docstring" class="card bg-base-100 shadow">
        <div class="card-body p-4">
          <h4 class="card-title text-sm flex items-center gap-2">
            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" class="w-4 h-4 stroke-current">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
            Docstring
          </h4>
          <p class="text-xs text-base-content/80 font-mono whitespace-pre-wrap">{{ graphStore.selectedNode.docstring }}</p>
        </div>
      </div>

      <div class="divider my-2">Connections</div>

      <div class="collapse collapse-arrow bg-base-100 shadow">
        <input type="checkbox" checked />
        <div class="collapse-title font-semibold text-sm flex items-center gap-2">
          <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" class="w-4 h-4 stroke-current text-success">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 16l-4-4m0 0l4-4m-4 4h18" />
          </svg>
          Incoming
          <div class="badge badge-success badge-sm ml-auto">{{ incomingNodes.length }}</div>
        </div>
        <div class="collapse-content space-y-1 max-h-60 overflow-y-auto">
          <button
            v-for="node in incomingNodes"
            :key="node.id"
            @click="selectNodeFromList(node.id)"
            class="btn btn-ghost btn-sm w-full justify-start font-mono text-xs truncate hover:bg-base-200"
          >
            {{ node.name }}
          </button>
          <div v-if="incomingNodes.length === 0" class="text-xs text-base-content/60 text-center py-4">
            No incoming connections
          </div>
        </div>
      </div>

      <div class="collapse collapse-arrow bg-base-100 shadow">
        <input type="checkbox" checked />
        <div class="collapse-title font-semibold text-sm flex items-center gap-2">
          <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" class="w-4 h-4 stroke-current text-warning">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 8l4 4m0 0l-4 4m4-4H3" />
          </svg>
          Outgoing
          <div class="badge badge-warning badge-sm ml-auto">{{ outgoingNodes.length }}</div>
        </div>
        <div class="collapse-content space-y-1 max-h-60 overflow-y-auto">
          <button
            v-for="node in outgoingNodes"
            :key="node.id"
            @click="selectNodeFromList(node.id)"
            class="btn btn-ghost btn-sm w-full justify-start font-mono text-xs truncate hover:bg-base-200"
          >
            {{ node.name }}
          </button>
          <div v-if="outgoingNodes.length === 0" class="text-xs text-base-content/60 text-center py-4">
            No outgoing connections
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
