<script setup lang="ts">
import { ref, computed } from 'vue'
import { useGraphStore } from '../stores/graphStore'

const graphStore = useGraphStore()

const traversalDepth = ref(2)
const traversalDirection = ref<'inbound' | 'outbound' | 'both'>('both')
const isTraversing = ref(false)

const canTraverse = computed(() => graphStore.selectedNode !== null)

const handleTraverse = async () => {
  if (!graphStore.selectedNode || isTraversing.value) return

  isTraversing.value = true
  try {
    if (traversalDirection.value === 'inbound' || traversalDirection.value === 'both') {
      const callers = await graphStore.findCallers(graphStore.selectedNode.name)
    }
    if (traversalDirection.value === 'outbound' || traversalDirection.value === 'both') {
      const callees = await graphStore.findCallees(graphStore.selectedNode.name)
    }
  } catch (error) {
    console.error('Traversal failed:', error)
  } finally {
    isTraversing.value = false
  }
}

const handleClearTraversal = () => {
  graphStore.clearGraph()
}
</script>

<template>
  <div class="space-y-3">
    <div>
      <label class="block text-xs font-medium text-gray-300 mb-2">
        Traversal Depth
      </label>
      <input
        v-model.number="traversalDepth"
        type="range"
        min="1"
        max="5"
        class="w-full"
      />
      <div class="text-xs text-gray-400 mt-1">{{ traversalDepth }} level(s)</div>
    </div>

    <div>
      <label class="block text-xs font-medium text-gray-300 mb-2">
        Direction
      </label>
      <div class="space-y-1">
        <button
          v-for="dir in ['inbound', 'outbound', 'both']"
          :key="dir"
          @click="traversalDirection = dir as any"
          :class="[
            'block w-full text-left px-2 py-1 text-xs rounded transition',
            traversalDirection === dir
              ? 'bg-indigo-600 text-white'
              : 'bg-gray-800 text-gray-300 hover:bg-gray-700'
          ]"
        >
          {{ dir === 'inbound' ? '↑ Inbound (Callers)' : dir === 'outbound' ? '↓ Outbound (Callees)' : '↕ Both Directions' }}
        </button>
      </div>
    </div>

    <div class="flex gap-2">
      <button
        @click="handleTraverse"
        :disabled="!canTraverse || isTraversing"
        :class="[
          'flex-1 px-3 py-2 rounded text-sm font-medium transition',
          canTraverse && !isTraversing
            ? 'bg-indigo-600 hover:bg-indigo-700 text-white'
            : 'bg-gray-700 text-gray-400 cursor-not-allowed'
        ]"
      >
        {{ isTraversing ? '⟳ Traversing...' : '🔍 Traverse' }}
      </button>
      <button
        @click="handleClearTraversal"
        class="flex-1 px-3 py-2 rounded text-sm font-medium bg-gray-700 hover:bg-gray-600 text-gray-300 transition"
      >
        Clear
      </button>
    </div>
  </div>
</template>
