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
  <div class="h-full bg-gray-800 border-l border-gray-700 flex flex-col">
    <div v-if="!graphStore.selectedNode" class="flex items-center justify-center h-full text-gray-400">
      <p>Select a node to view details</p>
    </div>

    <div v-else class="overflow-y-auto flex-1 p-4">
      <div class="mb-4">
        <h3 class="text-lg font-bold text-white mb-2">{{ graphStore.selectedNode.name }}</h3>
        <div class="grid grid-cols-2 gap-2 text-sm">
          <div class="text-gray-400">Type:</div>
          <div class="text-white font-mono">{{ graphStore.selectedNode.type }}</div>
          <div class="text-gray-400">Language:</div>
          <div class="text-white font-mono">{{ graphStore.selectedNode.language }}</div>
          <div class="text-gray-400">Complexity:</div>
          <div class="text-white font-mono">{{ graphStore.selectedNode.complexity }}</div>
          <div class="text-gray-400">Line:</div>
          <div class="text-white font-mono">{{ graphStore.selectedNode.line }}</div>
        </div>

        <div class="mt-3 p-2 bg-gray-700 rounded text-xs text-gray-300 break-all">
          {{ graphStore.selectedNode.file_path }}
        </div>

        <button
          @click="copyNodeId"
          class="mt-2 w-full px-3 py-1 bg-indigo-600 hover:bg-indigo-700 text-white text-sm rounded"
        >
          Copy ID
        </button>
      </div>

      <div v-if="graphStore.selectedNode.docstring" class="mb-4">
        <h4 class="text-sm font-semibold text-gray-300 mb-2">Docstring</h4>
        <p class="text-xs text-gray-400 bg-gray-700 p-2 rounded">{{ graphStore.selectedNode.docstring }}</p>
      </div>

      <div class="mb-4">
        <h4 class="text-sm font-semibold text-gray-300 mb-2">Incoming ({{ incomingNodes.length }})</h4>
        <div class="space-y-1">
          <button
            v-for="node in incomingNodes"
            :key="node.id"
            @click="selectNodeFromList(node.id)"
            class="w-full text-left p-2 text-xs bg-gray-700 hover:bg-gray-600 rounded text-gray-200 truncate"
          >
            {{ node.name }}
          </button>
        </div>
      </div>

      <div>
        <h4 class="text-sm font-semibold text-gray-300 mb-2">Outgoing ({{ outgoingNodes.length }})</h4>
        <div class="space-y-1">
          <button
            v-for="node in outgoingNodes"
            :key="node.id"
            @click="selectNodeFromList(node.id)"
            class="w-full text-left p-2 text-xs bg-gray-700 hover:bg-gray-600 rounded text-gray-200 truncate"
          >
            {{ node.name }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>
