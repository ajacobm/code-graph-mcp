<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useGraphStore } from '../stores/graphStore'
import { graphClient } from '../api/graphClient'

const graphStore = useGraphStore()

interface NodeCategory {
  label: string
  icon: string
  description: string
  value: 'entry_points' | 'hubs' | 'leaves'
  color: string
}

const categories: NodeCategory[] = [
  {
    label: 'Entry Points',
    icon: '🚀',
    description: 'Top-level functions with no callers',
    value: 'entry_points',
    color: 'from-cyan-500 to-blue-500'
  },
  {
    label: 'Junction Nodes',
    icon: '🔀',
    description: 'Highly connected hub functions',
    value: 'hubs',
    color: 'from-amber-500 to-orange-500'
  },
  {
    label: 'Leaf Nodes',
    icon: '🍃',
    description: 'Utilities and workers with no callees',
    value: 'leaves',
    color: 'from-green-500 to-emerald-500'
  }
]

const selectedCategory = ref<'entry_points' | 'hubs' | 'leaves'>('entry_points')
const nodes = ref<any[]>([])
const totalCount = ref(0)
const isLoading = ref(false)
const currentPage = ref(0)
const pageSize = 12

const currentCategory = computed(() => categories.find(c => c.value === selectedCategory.value))

const totalPages = computed(() => Math.ceil(totalCount.value / pageSize))

const loadCategory = async () => {
  isLoading.value = true
  try {
    const result = await graphClient.getNodesByCategory(
      selectedCategory.value,
      pageSize,
      currentPage.value * pageSize
    )
    nodes.value = result.nodes || []
    totalCount.value = result.total || 0
  } catch (error) {
    graphStore.error = `Failed to load ${selectedCategory.value}`
    nodes.value = []
  } finally {
    isLoading.value = false
  }
}

const selectNode = async (node: any) => {
  isLoading.value = true
  try {
    graphStore.selectNode(node.id)
    await graphStore.traverse(node.id, 3)
  } finally {
    isLoading.value = false
  }
}

const nextPage = () => {
  if (currentPage.value < totalPages.value - 1) {
    currentPage.value++
    loadCategory()
  }
}

const prevPage = () => {
  if (currentPage.value > 0) {
    currentPage.value--
    loadCategory()
  }
}

onMounted(() => {
  loadCategory()
})

const handleCategoryChange = (category: 'entry_points' | 'hubs' | 'leaves') => {
  selectedCategory.value = category
  currentPage.value = 0
  loadCategory()
}
</script>

<template>
  <div class="min-h-screen bg-gradient-to-br from-base-900 to-base-950 p-8">
    <!-- Header -->
    <div class="max-w-7xl mx-auto mb-12">
      <h1 class="text-5xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-primary via-secondary to-accent mb-3">
        Code Graph Explorer
      </h1>
      <p class="text-lg text-base-content/70">
        Navigate your codebase by discovering entry points, critical junctions, and utility nodes
      </p>
    </div>

    <!-- Category Selector -->
    <div class="max-w-7xl mx-auto mb-12">
      <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
        <button
          v-for="cat in categories"
          :key="cat.value"
          @click="handleCategoryChange(cat.value)"
          :class="[
            'relative overflow-hidden group card bg-base-200 hover:bg-base-100 transition-all duration-300 cursor-pointer border-2',
            selectedCategory === cat.value 
              ? 'border-primary shadow-2xl shadow-primary/50' 
              : 'border-transparent hover:border-base-300'
          ]"
        >
          <div :class="`absolute inset-0 bg-gradient-to-r ${cat.color} opacity-0 group-hover:opacity-10 transition-opacity`"></div>
          <div class="card-body items-center text-center p-6">
            <div class="text-4xl mb-2">{{ cat.icon }}</div>
            <h3 class="card-title text-lg">{{ cat.label }}</h3>
            <p class="text-sm text-base-content/70">{{ cat.description }}</p>
            <div class="badge badge-primary mt-3">{{ totalCount }} nodes</div>
          </div>
        </button>
      </div>
    </div>

    <!-- Nodes Grid -->
    <div class="max-w-7xl mx-auto mb-8">
      <div v-if="isLoading" class="flex justify-center items-center py-20">
        <span class="loading loading-spinner loading-lg text-primary"></span>
      </div>

      <div v-else-if="nodes.length === 0" class="card bg-base-200 shadow-xl">
        <div class="card-body items-center text-center py-16">
          <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" class="w-16 h-16 stroke-base-content/30 mb-4">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293h-3.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 006.586 13H4" />
          </svg>
          <p class="text-xl font-semibold mb-2">No nodes found</p>
          <p class="text-base-content/60">Try exploring another category</p>
        </div>
      </div>

      <div v-else class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
        <button
          v-for="node in nodes"
          :key="node.id"
          @click="selectNode(node)"
          class="group card bg-base-200 hover:bg-base-100 shadow-md hover:shadow-xl transition-all duration-300 transform hover:-translate-y-1 cursor-pointer border border-base-300 hover:border-primary"
        >
          <div class="card-body p-4 space-y-2">
            <div class="flex items-start justify-between">
              <h4 class="font-semibold text-sm font-mono line-clamp-2 group-hover:text-primary transition-colors flex-1">
                {{ node.name }}
              </h4>
              <div v-if="node.language" class="badge badge-sm badge-primary ml-1 flex-shrink-0">
                {{ node.language }}
              </div>
            </div>

            <div class="flex items-center gap-2 text-xs text-base-content/60">
              <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" class="w-3 h-3 stroke-current">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A1.994 1.994 0 013 12V7a4 4 0 014-4z" />
              </svg>
              <span class="truncate">{{ node.type }}</span>
            </div>

            <div v-if="node.file_path" class="text-xs text-base-content/50 font-mono truncate">
              {{ node.file_path.split('/').pop() }}
            </div>

            <div v-if="node.complexity" class="text-xs text-base-content/60">
              <span class="inline-block bg-base-300 px-2 py-1 rounded">
                Complexity: {{ node.complexity }}
              </span>
            </div>
          </div>
        </button>
      </div>
    </div>

    <!-- Pagination -->
    <div v-if="nodes.length > 0" class="max-w-7xl mx-auto flex items-center justify-between">
      <div class="text-sm text-base-content/70">
        Page <span class="font-semibold">{{ currentPage + 1 }}</span> of
        <span class="font-semibold">{{ totalPages }}</span>
        · Showing
        <span class="font-semibold">{{ nodes.length }}</span> of
        <span class="font-semibold">{{ totalCount }}</span> nodes
      </div>

      <div class="flex gap-2">
        <button
          @click="prevPage"
          :disabled="currentPage === 0"
          class="btn btn-sm btn-outline gap-2"
        >
          <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" class="w-4 h-4 stroke-current">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" />
          </svg>
          Previous
        </button>

        <button
          @click="nextPage"
          :disabled="currentPage >= totalPages - 1"
          class="btn btn-sm btn-outline gap-2"
        >
          Next
          <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" class="w-4 h-4 stroke-current">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
          </svg>
        </button>
      </div>
    </div>
  </div>
</template>
