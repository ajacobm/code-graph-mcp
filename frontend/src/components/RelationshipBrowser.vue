<script setup lang="ts">
import { computed } from 'vue'
import { useGraphStore } from '../stores/graphStore'

const graphStore = useGraphStore()

const relationshipGroups = computed(() => {
  if (!graphStore.selectedNode) return {}

  const groups: Record<string, Array<{id: string, label: string}>> = {}

  graphStore.edgeArray.forEach((edge) => {
    if (edge.source === graphStore.selectedNode?.id) {
      const type = edge.type || 'UNKNOWN'
      if (!groups[type]) groups[type] = []

      const targetNode = graphStore.nodes.get(edge.target)
      if (targetNode) {
        groups[type].push({
          id: edge.target,
          label: targetNode.name,
        })
      }
    }
  })

  return groups
})

const handleClickRelated = (nodeId: string) => {
  graphStore.selectNode(nodeId)
}
</script>

<template>
  <div v-if="graphStore.selectedNode" class="space-y-4">
    <h3 class="text-sm font-semibold text-gray-300">Relationships</h3>

    <div v-if="Object.keys(relationshipGroups).length === 0" class="text-xs text-gray-500">
      No relationships from this node
    </div>

    <div v-for="(targets, type) in relationshipGroups" :key="type" class="space-y-2">
      <div class="text-xs font-medium text-indigo-300">{{ type }}</div>
      <div class="space-y-1">
        <button
          v-for="target in targets"
          :key="target.id"
          @click="handleClickRelated(target.id)"
          class="block w-full text-left px-2 py-1 text-xs rounded bg-gray-800 hover:bg-indigo-900 text-gray-100 truncate transition"
        >
          → {{ target.label }}
        </button>
      </div>
    </div>
  </div>
  <div v-else class="text-xs text-gray-500">
    Select a node to see relationships
  </div>
</template>
