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
  { value: 'callers' as const, label: 'Callers', icon: '📥', description: 'Who calls this function?' },
  { value: 'callees' as const, label: 'Callees', icon: '📤', description: 'What does this function call?' },
  { value: 'references' as const, label: 'References', icon: '🔍', description: 'Where is this symbol used?' }
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
  <div class="space-y-4">
    <h3 class="text-lg font-bold text-base-content flex items-center gap-2">
      <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" class="w-5 h-5 stroke-current">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 3v2m6-2v2M9 19v2m6-2v2M5 9H3m2 6H3m18-6h-2m2 6h-2M7 19h10a2 2 0 002-2V7a2 2 0 00-2-2H7a2 2 0 00-2 2v10a2 2 0 002 2zM9 9h6v6H9V9z" />
      </svg>
      Query Tools
    </h3>

    <div class="tabs tabs-boxed bg-base-100 p-1 gap-1">
      <button
        v-for="tool in tools"
        :key="tool.value"
        @click="selectedTool = tool.value"
        :class="['tab gap-2 flex-1', selectedTool === tool.value && 'tab-active']"
        :title="tool.description"
      >
        <span>{{ tool.icon }}</span>
        <span class="text-xs font-medium">{{ tool.label }}</span>
      </button>
    </div>

    <div class="space-y-3">
      <div class="form-control">
        <label class="label">
          <span class="label-text text-xs font-medium">Symbol Name</span>
        </label>
        <input
          v-model="symbolInput"
          type="text"
          :placeholder="`Enter ${currentTool?.label.toLowerCase()} to find...`"
          @keyup.enter="executeTool"
          class="input input-bordered input-sm w-full"
        />
      </div>

      <div class="flex gap-2">
        <button
          @click="executeTool"
          :disabled="isExecuting"
          class="btn btn-primary btn-sm flex-1 gap-2"
        >
          <svg v-if="!isExecuting" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" class="w-4 h-4 stroke-current">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z" />
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <span v-if="isExecuting" class="loading loading-spinner loading-xs"></span>
          {{ isExecuting ? 'Running...' : 'Execute' }}
        </button>
        <button
          v-if="toolResults"
          @click="clearResults"
          class="btn btn-ghost btn-sm gap-2"
        >
          <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" class="w-4 h-4 stroke-current">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
          </svg>
          Clear
        </button>
      </div>
    </div>

    <div v-if="toolResults" class="space-y-3">
      <div v-if="toolResults.error" class="alert alert-warning shadow-lg">
        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" class="stroke-current flex-shrink-0 w-6 h-6">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
        </svg>
        <span class="text-sm">{{ toolResults.error }}</span>
      </div>

      <div v-if="hasResults" class="card bg-base-100 shadow">
        <div class="card-body p-3 space-y-3">
          <div class="flex items-center justify-between">
            <div class="badge badge-primary badge-lg gap-2">
              <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" class="w-4 h-4 stroke-current">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-3 7h3m-3 4h3m-6-4h.01M9 16h.01" />
              </svg>
              {{ resultCount }} {{ selectedTool }}
            </div>
            <button
              @click="expandedResults = !expandedResults"
              class="btn btn-ghost btn-xs gap-1"
            >
              <svg
                xmlns="http://www.w3.org/2000/svg"
                fill="none"
                viewBox="0 0 24 24"
                class="w-4 h-4 stroke-current transition-transform"
                :class="{ 'rotate-180': expandedResults }"
              >
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
              </svg>
              {{ expandedResults ? 'Collapse' : 'Expand' }}
            </button>
          </div>

          <div v-if="expandedResults" class="space-y-2 max-h-80 overflow-y-auto pr-1">
            <div
              v-for="(result, idx) in toolResults.results.slice(0, 20)"
              :key="idx"
              @click="selectResult(result)"
              class="card bg-base-200 hover:bg-base-300 cursor-pointer transition-all duration-200 hover:shadow-md"
            >
              <div class="card-body p-3">
                <div class="font-mono text-sm font-semibold text-primary truncate">
                  {{ result.caller || result.callee || result.referencing_symbol }}
                </div>
                <div class="text-xs text-base-content/60 flex items-center gap-2">
                  <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" class="w-3 h-3 stroke-current">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                  </svg>
                  <span class="truncate">{{ result.file }}:{{ result.line }}</span>
                </div>
              </div>
            </div>

            <div v-if="resultCount > 20" class="alert alert-info shadow-sm">
              <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" class="stroke-current flex-shrink-0 w-5 h-5">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <span class="text-sm">+{{ resultCount - 20 }} more results</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
