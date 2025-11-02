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
      graphStore.languages[0],
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
  <div class="form-control relative">
    <div class="input-group">
      <input
        v-model="query"
        @input="search"
        @focus="showResults = true"
        type="text"
        placeholder="Search nodes..."
        class="input input-bordered input-primary w-full"
      />
      <button class="btn btn-square btn-primary">
        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" class="w-5 h-5 stroke-current">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
        </svg>
      </button>
    </div>

    <div v-if="showResults && (results.length > 0 || loading)" class="dropdown-content menu bg-base-200 rounded-box shadow-2xl z-50 w-full mt-2 p-2 max-h-96 overflow-y-auto">
      <div v-if="loading" class="p-4 text-center">
        <span class="loading loading-spinner loading-md text-primary"></span>
      </div>

      <li v-for="result in results" :key="result.id">
        <button
          @click="selectResult(result.id)"
          class="flex justify-between items-center hover:bg-base-300 rounded-lg p-3"
        >
          <span class="font-mono text-sm font-semibold truncate">{{ result.name }}</span>
          <span class="badge badge-primary badge-sm">{{ result.language }}</span>
        </button>
      </li>
    </div>
  </div>
</template>
