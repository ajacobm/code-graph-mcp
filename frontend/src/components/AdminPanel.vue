<template>
  <div class="card bg-base-200 shadow-lg p-4">
    <h2 class="card-title text-lg mb-4">Admin & Debug</h2>
    
    <div class="space-y-3">
      <!-- Analysis Status -->
      <div class="bg-base-100 p-3 rounded">
        <h3 class="font-semibold mb-2">Analysis Status</h3>
        <button 
          @click="loadAnalysisStatus" 
          :disabled="loading"
          class="btn btn-sm btn-primary"
        >
          {{ loading ? 'Loading...' : 'Check Status' }}
        </button>
        <div v-if="status" class="mt-2 text-xs space-y-1">
          <div><span class="label-text">Status:</span> <span class="badge badge-sm" :class="status.status === 'initialized' ? 'badge-success' : 'badge-warning'">{{ status.status }}</span></div>
          <div><span class="label-text">Nodes:</span> {{ status.graph_nodes }}</div>
          <div><span class="label-text">Relationships:</span> {{ status.graph_relationships }}</div>
          <div><span class="label-text">Processed Files:</span> {{ status.processed_files_count }}</div>
          <div><span class="label-text">Cache Enabled:</span> {{ status.cache_enabled ? '✓' : '✗' }}</div>
          <div><span class="label-text">File Watcher:</span> {{ status.file_watcher_running ? 'Running' : 'Stopped' }}</div>
        </div>
      </div>

      <!-- Force Re-analysis -->
      <div class="bg-base-100 p-3 rounded">
        <h3 class="font-semibold mb-2">Force Re-analysis</h3>
        <button 
          @click="forceReanalyze" 
          :disabled="loading || reanalyzing"
          class="btn btn-sm btn-warning"
        >
          {{ reanalyzing ? 'Analyzing...' : 'Re-analyze Now' }}
        </button>
        <div v-if="reanalysisResult" class="mt-2 text-xs">
          <div><span class="label-text">Time:</span> {{ reanalysisResult.elapsed_seconds?.toFixed(2) }}s</div>
          <div><span class="label-text">Nodes Found:</span> {{ reanalysisResult.total_nodes }}</div>
          <div><span class="label-text">Relationships:</span> {{ reanalysisResult.total_relationships }}</div>
        </div>
      </div>

      <!-- File List -->
      <div class="bg-base-100 p-3 rounded">
        <h3 class="font-semibold mb-2">Processed Files ({{ fileStats.total }})</h3>
        <button 
          @click="loadFileStats" 
          :disabled="loading"
          class="btn btn-sm btn-info"
        >
          {{ loading ? 'Loading...' : 'Show Files' }}
        </button>
        <div v-if="fileStats.files.length" class="mt-2 max-h-40 overflow-y-auto text-xs">
          <div v-for="file in fileStats.files" :key="file.file_path" class="text-gray-400 truncate">
            {{ file.file_path.split('/').pop() }} ({{ file.node_count }} nodes)
          </div>
        </div>
      </div>

      <!-- Error Display -->
      <div v-if="error" class="alert alert-error">
        <span>{{ error }}</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'

interface StatusData {
  status: string
  graph_nodes: number
  graph_relationships: number
  processed_files_count: number
  cache_enabled: boolean
  file_watcher_running: boolean
  is_analyzed: boolean
}

interface FileInfo {
  file_path: string
  node_count: number
  node_types: Record<string, number>
}

interface FileStats {
  total: number
  showing: number
  files: FileInfo[]
}

const loading = ref(false)
const reanalyzing = ref(false)
const status = ref<StatusData | null>(null)
const error = ref('')
const reanalysisResult = ref<any>(null)
const fileStats = ref<FileStats>({ total: 0, showing: 0, files: [] })

// Use localhost:8000 as fallback (for local dev) or origin's port 8000 (for Docker)
const getApiUrl = () => {
  const env = import.meta.env.VITE_API_URL
  if (env && !env.includes('code-graph-http')) return env
  // Default to localhost:8000 for all cases
  return 'http://localhost:8000'
}
const apiUrl = getApiUrl()

async function loadAnalysisStatus() {
  loading.value = true
  error.value = ''
  try {
    const res = await fetch(`${apiUrl}/api/graph/debug/analysis`)
    if (!res.ok) throw new Error(`HTTP ${res.status}`)
    status.value = await res.json()
  } catch (e: any) {
    error.value = e.message
  } finally {
    loading.value = false
  }
}

async function forceReanalyze() {
  reanalyzing.value = true
  error.value = ''
  try {
    const res = await fetch(`${apiUrl}/api/graph/admin/reanalyze?force=true`, { method: 'POST' })
    if (!res.ok) throw new Error(`HTTP ${res.status}`)
    reanalysisResult.value = await res.json()
    // Refresh status after reanalysis
    await loadAnalysisStatus()
  } catch (e: any) {
    error.value = e.message
  } finally {
    reanalyzing.value = false
  }
}

async function loadFileStats() {
  loading.value = true
  error.value = ''
  try {
    const res = await fetch(`${apiUrl}/api/graph/debug/files?limit=50`)
    if (!res.ok) throw new Error(`HTTP ${res.status}`)
    fileStats.value = await res.json()
  } catch (e: any) {
    error.value = e.message
  } finally {
    loading.value = false
  }
}
</script>
