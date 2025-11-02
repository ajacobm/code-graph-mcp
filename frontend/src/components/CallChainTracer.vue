<script setup lang="ts">
import { computed } from 'vue'
import { useGraphStore } from '../stores/graphStore'

const graphStore = useGraphStore()

const currentStepIndex = computed(() => {
  const selected = graphStore.selectedNode
  if (!selected) return -1
  return graphStore.nodeArray.findIndex((n) => n.id === selected.id)
})

const canPreviousStep = computed(() => currentStepIndex.value > 0)
const canNextStep = computed(() => currentStepIndex.value < graphStore.nodeArray.length - 1)

const previousStep = () => {
  if (canPreviousStep.value) {
    graphStore.selectNode(graphStore.nodeArray[currentStepIndex.value - 1].id)
  }
}

const nextStep = () => {
  if (canNextStep.value) {
    graphStore.selectNode(graphStore.nodeArray[currentStepIndex.value + 1].id)
  }
}

const reset = () => {
  if (graphStore.nodeArray.length > 0) {
    graphStore.selectNode(graphStore.nodeArray[0].id)
  }
}

const exportChain = () => {
  const chain = graphStore.nodeArray.map((n) => ({
    id: n.id,
    name: n.name,
    language: n.language,
    type: n.type,
  }))
  const json = JSON.stringify(chain, null, 2)
  const blob = new Blob([json], { type: 'application/json' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = 'call-chain.json'
  a.click()
  URL.revokeObjectURL(url)
}
</script>

<template>
  <div v-if="graphStore.viewMode === 'call_chain'" class="bg-gray-800 border-b border-gray-700 p-4">
    <div class="flex items-center justify-between mb-4">
      <h3 class="text-sm font-bold text-white">
        Call Chain ({{ currentStepIndex + 1 }} / {{ graphStore.nodeArray.length }})
      </h3>
      <button
        @click="exportChain"
        class="px-3 py-1 bg-gray-700 hover:bg-gray-600 text-white text-xs rounded"
      >
        Export
      </button>
    </div>

    <div class="flex items-center justify-between">
      <button
        @click="previousStep"
        :disabled="!canPreviousStep"
        class="px-4 py-2 bg-gray-700 hover:bg-gray-600 disabled:opacity-50 text-white rounded text-sm font-medium"
      >
        Previous
      </button>

      <div v-if="graphStore.selectedNode" class="flex-1 mx-4 text-center">
        <p class="text-white font-semibold">{{ graphStore.selectedNode.name }}</p>
        <p class="text-xs text-gray-400">{{ graphStore.selectedNode.language }}</p>
      </div>

      <button
        @click="nextStep"
        :disabled="!canNextStep"
        class="px-4 py-2 bg-gray-700 hover:bg-gray-600 disabled:opacity-50 text-white rounded text-sm font-medium"
      >
        Next
      </button>
    </div>

    <button
      @click="reset"
      class="w-full mt-3 px-3 py-1 bg-indigo-600 hover:bg-indigo-700 text-white text-sm rounded"
    >
      Reset
    </button>
  </div>
</template>
