<script setup lang="ts">
import { ref, computed } from 'vue'
import { useGraphStore } from '../stores/graphStore'

interface ToolResult {
  symbol: string
  results: any[]
  executionTime: number
  error?: string
}

const graphStore = useGraphStore()
const selectedTool = ref<'callers' | 'callees' | 'references'>('callers')
const symbolInput = ref('')
const toolResults = ref<ToolResult | null>(null)
const isExecuting = ref(false)
const expandedResults = ref(false)

const tools = [
  { value: 'callers', label: 'Find Callers', icon: '↓', description: 'Who calls this function?' },
  { value: 'callees', label: 'Find Callees', icon: '↗', description: 'What does this function call?' },
  { value: 'references', label: 'Find References', icon: '●', description: 'Where is this symbol used?' }
]

const currentTool = computed(() => tools.find(t => t.value === selectedTool.value))

const resultCount = computed(() => {
  if (!toolResults.value) return 0
  return toolResults.value.results.length
})

const hasResults = computed(() => resultCount.value > 0)

const executeTool = async () => {
  if (!symbolInput.value.trim()) {
    graphStore.error = 'Please enter a symbol name'
    return
  }

  isExecuting.value = true
  toolResults.value = null

  try {
    let results: any = []

    switch (selectedTool.value) {
      case 'callers':
        results = await graphStore.findCallers(symbolInput.value)
        break
      case 'callees':
        results = await graphStore.findCallees(symbolInput.value)
        break
      case 'references':
        results = await graphStore.findReferences(symbolInput.value)
        break
    }

    const resultArray = Array.isArray(results) ? results : []
    toolResults.value = {
      symbol: symbolInput.value,
      results: resultArray,
      executionTime: 0,
      error: resultArray.length === 0 ? `No ${selectedTool.value} found` : undefined
    }
  } catch (err) {
    toolResults.value = {
      symbol: symbolInput.value,
      results: [],
      executionTime: 0,
      error: err instanceof Error ? err.message : 'Query failed'
    }
  } finally {
    isExecuting.value = false
  }
}

const selectResult = (result: any) => {
  const nodeId = result.caller_id || result.callee_id || result.reference_id
  if (nodeId) {
    const [file, symbol] = nodeId.split(':')
    graphStore.selectedNodeId = file + ':' + symbol
  }
}

const clearResults = () => {
  toolResults.value = null
  symbolInput.value = ''
}
</script>

<template>
  <div class="space-y-3">
    <h3 class="text-sm font-semibold text-white">Graph Query Tools</h3>

    <!-- Tool selector -->
    <div class="flex gap-1 bg-gray-700 rounded p-1">
      <button
        v-for="tool in tools"
        :key="tool.value"
        @click="selectedTool = tool.value"
        :class="[
          'flex-1 px-3 py-1.5 rounded text-xs font-medium transition',
          selectedTool === tool.value
            ? 'bg-indigo-600 text-white'
            : 'bg-gray-600 text-gray-200 hover:bg-gray-500'
        ]"
        :title="tool.description"
      >
        {{ tool.icon }} {{ tool.label }}
      </button>
    </div>

    <!-- Symbol input -->
    <div class="space-y-2">
      <input
        v-model="symbolInput"
        type="text"
        placeholder="Enter symbol name..."
        @keyup.enter="executeTool"
        class="w-full px-3 py-2 bg-gray-700 text-white rounded text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 placeholder-gray-400"
      />
      <button
        @click="executeTool"
        :disabled="isExecuting"
        class="w-full px-3 py-2 bg-indigo-600 hover:bg-indigo-700 disabled:bg-gray-600 text-white rounded font-medium text-sm transition"
      >
        {{ isExecuting ? 'Executing...' : 'Execute Query' }}
      </button>
    </div>

    <!-- Results -->
    <div v-if="toolResults" class="space-y-2">
      <!-- Error state -->
      <div v-if="toolResults.error" class="p-3 bg-red-900/30 border border-red-700 rounded text-sm text-red-200">
        {{ toolResults.error }}
      </div>

      <!-- Results header -->
      <div v-if="hasResults" class="bg-gray-700 rounded p-2 flex items-center justify-between">
        <span class="text-xs font-medium text-gray-300">
          {{ resultCount }} {{ selectedTool }}
        </span>
        <button
          @click="expandedResults = !expandedResults"
          class="text-xs px-2 py-1 bg-gray-600 hover:bg-gray-500 text-white rounded transition"
        >
          {{ expandedResults ? 'Collapse' : 'Expand' }}
        </button>
      </div>

      <!-- Results list -->
      <div v-if="hasResults && expandedResults" class="space-y-1 max-h-96 overflow-y-auto">
        <div
          v-for="(result, idx) in toolResults.results.slice(0, 20)"
          :key="idx"
          @click="selectResult(result)"
          class="p-2 bg-gray-700 hover:bg-gray-600 rounded text-xs text-gray-200 cursor-pointer transition truncate"
          :title="result.caller || result.callee || result.referencing_symbol"
        >
          <div class="font-medium">{{ result.caller || result.callee || result.referencing_symbol }}</div>
          <div class="text-gray-400 text-xs truncate">{{ result.file }}:{{ result.line }}</div>
        </div>
        <div v-if="resultCount > 20" class="p-2 text-xs text-gray-400 text-center">
          +{{ resultCount - 20 }} more results
        </div>
      </div>

      <!-- Clear button -->
      <button
        @click="clearResults"
        class="w-full px-2 py-1 text-xs bg-gray-700 hover:bg-gray-600 text-gray-200 rounded transition"
      >
        Clear
      </button>
    </div>
  </div>
</template>

<style scoped>
input:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}
</style>
