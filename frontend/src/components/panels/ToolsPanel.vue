<script setup lang="ts">
import { ref } from 'vue'

const props = defineProps<{
  isCollapsed?: boolean
}>()

const emit = defineEmits<{
  'update:isCollapsed': [value: boolean]
  categorySelected: [category: string]
  searchSubmit: [query: string]
}>()

const collapsed = ref(props.isCollapsed ?? false)
const searchQuery = ref('')

const toggleCollapse = () => {
  collapsed.value = !collapsed.value
  emit('update:isCollapsed', collapsed.value)
}

const handleSearch = () => {
  if (searchQuery.value.trim()) {
    emit('searchSubmit', searchQuery.value.trim())
  }
}

const categories = [
  { id: 'entry_points', emoji: '🚀', title: 'Entry Points', description: 'Functions with no callers' },
  { id: 'hubs', emoji: '🔀', title: 'Hubs', description: 'Highly connected nodes' },
  { id: 'leaves', emoji: '🍃', title: 'Leaves', description: 'Functions with no callees' },
]
</script>

<template>
  <div 
    :class="[
      'tools-panel flex flex-col bg-slate-800 border-r border-slate-700 transition-all duration-300',
      collapsed ? 'w-12' : 'w-64'
    ]"
  >
    <!-- Header -->
    <div class="flex items-center justify-between p-3 border-b border-slate-700">
      <h2 v-if="!collapsed" class="font-semibold text-slate-200">Tools</h2>
      <button
        @click="toggleCollapse"
        class="btn btn-ghost btn-sm btn-circle"
      >
        <svg 
          xmlns="http://www.w3.org/2000/svg" 
          class="h-5 w-5 transition-transform"
          :class="{ 'rotate-180': collapsed }"
          fill="none" 
          viewBox="0 0 24 24" 
          stroke="currentColor"
        >
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 19l-7-7 7-7m8 14l-7-7 7-7" />
        </svg>
      </button>
    </div>

    <!-- Content (hidden when collapsed) -->
    <div v-if="!collapsed" class="flex-1 overflow-y-auto p-3 space-y-4">
      <!-- Search -->
      <div class="form-control">
        <label class="label">
          <span class="label-text text-slate-400">Search Nodes</span>
        </label>
        <div class="input-group">
          <input
            v-model="searchQuery"
            type="text"
            placeholder="Function name..."
            class="input input-sm input-bordered flex-1 bg-slate-900"
            @keyup.enter="handleSearch"
          />
          <button 
            @click="handleSearch"
            class="btn btn-sm btn-primary"
          >
            🔍
          </button>
        </div>
      </div>

      <!-- Categories -->
      <div>
        <label class="label">
          <span class="label-text text-slate-400">Quick Access</span>
        </label>
        <div class="space-y-2">
          <button
            v-for="cat in categories"
            :key="cat.id"
            @click="emit('categorySelected', cat.id)"
            class="w-full btn btn-sm btn-ghost justify-start gap-2 text-left"
          >
            <span class="text-lg">{{ cat.emoji }}</span>
            <div class="flex-1 min-w-0">
              <div class="font-medium truncate">{{ cat.title }}</div>
              <div class="text-xs opacity-70 truncate">{{ cat.description }}</div>
            </div>
          </button>
        </div>
      </div>

      <!-- Filter Presets -->
      <div>
        <label class="label">
          <span class="label-text text-slate-400">Filter Presets</span>
        </label>
        <div class="flex flex-wrap gap-1">
          <button class="btn btn-xs btn-outline">Python</button>
          <button class="btn btn-xs btn-outline">TypeScript</button>
          <button class="btn btn-xs btn-outline">Functions</button>
          <button class="btn btn-xs btn-outline">Classes</button>
        </div>
      </div>

      <!-- Legend -->
      <div>
        <label class="label">
          <span class="label-text text-slate-400">Legend</span>
        </label>
        <div class="space-y-1 text-xs">
          <div class="flex items-center gap-2">
            <span class="w-3 h-3 rounded-full bg-green-500"></span>
            <span class="text-slate-300">Function</span>
          </div>
          <div class="flex items-center gap-2">
            <span class="w-3 h-3 rounded-full bg-blue-500"></span>
            <span class="text-slate-300">Class</span>
          </div>
          <div class="flex items-center gap-2">
            <span class="w-3 h-3 rounded-full bg-purple-500"></span>
            <span class="text-slate-300">Method</span>
          </div>
          <div class="flex items-center gap-2">
            <span class="w-3 h-3 rounded-full bg-amber-500"></span>
            <span class="text-slate-300">Module</span>
          </div>
          <div class="flex items-center gap-2">
            <span class="w-3 h-3 rounded-full bg-gray-500"></span>
            <span class="text-slate-300">Import</span>
          </div>
          <div class="flex items-center gap-2 mt-2 pt-2 border-t border-slate-700">
            <span class="w-3 h-1 bg-amber-500"></span>
            <span class="text-slate-300">Cross-language (Seam)</span>
          </div>
        </div>
      </div>
    </div>

    <!-- Collapsed Icons -->
    <div v-else class="flex-1 flex flex-col items-center py-3 gap-2">
      <button
        v-for="cat in categories"
        :key="cat.id"
        @click="emit('categorySelected', cat.id)"
        class="btn btn-ghost btn-sm btn-circle tooltip tooltip-right"
        :data-tip="cat.title"
      >
        {{ cat.emoji }}
      </button>
    </div>
  </div>
</template>

<style scoped>
.tools-panel {
  min-height: 100%;
}
</style>
