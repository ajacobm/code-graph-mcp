<script setup lang="ts">
import { ref, computed } from 'vue'
import { useGraphStore } from '../stores/graphStore'
import { useFilterStore } from '../stores/filterStore'
import { graphClient } from '../api/graphClient'

const graphStore = useGraphStore()
const filterStore = useFilterStore()

const query = ref('')
const results = ref<any[]>([])
const showResults = ref(false)
const loading = ref(false)

const search = async () => {
  if (!query.value.trim()) {
    results.value = []
    return
  }

  loading.value = true
  try {
    const res = await graphClient.searchNodes(
      query.value,
      filterStore.languages[0],
      undefined,
      10
    )
    results.value = res.results
    showResults.value = true
  } catch (err) {
    console.error('Search failed:', err)
  } finally {
    loading.value = false
  }
}

const selectResult = async (nodeId: string) => {
  graphStore.selectNode(nodeId)
  await graphStore.traverse(nodeId, 5)
  showResults.value = false
  query.value = ''
}
</script>

<template>
  <div class="relative">
    <input
      v-model="query"
      @input="search"
      @focus="showResults = true"
      type="text"
      placeholder="Search nodes..."
      class="w-full px-4 py-2 bg-gray-700 text-white rounded focus:outline-none focus:ring-2 focus:ring-indigo-500"
    />

    <div v-if="showResults && (results.length > 0 || loading)" class="absolute top-full mt-1 w-full bg-gray-700 rounded shadow-lg z-10 max-h-64 overflow-y-auto">
      <div v-if="loading" class="p-2 text-gray-300 text-sm">Searching...</div>

      <button
        v-for="result in results"
        :key="result.id"
        @click="selectResult(result.id)"
        class="w-full text-left px-4 py-2 hover:bg-gray-600 text-gray-200 text-sm border-b border-gray-600 last:border-b-0 flex justify-between"
      >
        <span>{{ result.name }}</span>
        <span class="text-xs text-gray-400">{{ result.language }}</span>
      </button>
    </div>
  </div>
</template>
