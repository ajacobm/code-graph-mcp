<template>
  <div class="bg-slate-800/50 border border-slate-700 rounded-lg p-4 space-y-3">
    <!-- Header -->
    <div class="flex items-center justify-between">
      <h3 class="text-sm font-semibold text-slate-300">📋 Event Log</h3>
      <button
        v-if="events.length > 0"
        @click="clearEvents"
        class="text-xs text-slate-500 hover:text-slate-400 transition-colors"
      >
        Clear
      </button>
    </div>

    <!-- Event List -->
    <div class="space-y-2 max-h-80 overflow-y-auto">
      <div v-if="events.length === 0" class="text-xs text-slate-500 py-4 text-center">
        No events yet
      </div>

      <div
        v-for="(event, idx) in events"
        :key="`${event.event_id}-${idx}`"
        class="text-xs p-2 bg-slate-700/30 rounded border border-slate-600/30 hover:border-slate-600 transition-colors"
      >
        <div class="flex items-center justify-between mb-1">
          <span class="font-mono font-semibold" :class="getEventColor(event.event_type)">
            {{ formatEventType(event.event_type) }}
          </span>
          <span class="text-slate-500">{{ formatTime(event.timestamp) }}</span>
        </div>

        <div class="text-slate-400 space-y-0.5">
          <div v-if="event.entity_type">
            <span class="text-slate-600">Entity:</span>
            <span class="ml-1 text-slate-300 font-mono">{{ event.entity_type }}</span>
          </div>
          <div v-if="event.entity_id" class="truncate">
            <span class="text-slate-600">ID:</span>
            <span class="ml-1 text-slate-300 font-mono text-xs truncate">{{ event.entity_id }}</span>
          </div>
          <div v-if="eventDataSummary(event)" class="text-slate-500 truncate">
            {{ eventDataSummary(event) }}
          </div>
        </div>
      </div>
    </div>

    <!-- Filter Options -->
    <div class="border-t border-slate-700 pt-3 space-y-2">
      <div class="text-xs text-slate-500 mb-2">Filter by type:</div>
      <div class="flex flex-wrap gap-1">
        <button
          v-for="type in availableEventTypes"
          :key="type"
          @click="toggleEventFilter(type)"
          :class="[
            'px-2 py-1 text-xs rounded transition-colors',
            activeFilters.has(type)
              ? 'bg-indigo-600/50 text-indigo-200'
              : 'bg-slate-700/30 text-slate-400 hover:bg-slate-700/50'
          ]"
        >
          {{ formatEventType(type) }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { useEvents } from '../composables/useEvents'

interface CDCEvent {
  event_id: string
  event_type: string
  timestamp: string
  entity_id: string
  entity_type: string
  data?: Record<string, any>
}

const { subscribe } = useEvents()

const events = ref<CDCEvent[]>([])
const activeFilters = ref<Set<string>>(new Set())

const availableEventTypes = computed(() => {
  const types = new Set<string>()
  events.value.forEach(e => types.add(e.event_type))
  return Array.from(types).sort()
})

const filteredEvents = computed(() => {
  if (activeFilters.value.size === 0) return events.value
  return events.value.filter(e => activeFilters.value.has(e.event_type))
})

const formatEventType = (type: string) => {
  return type
    .split('_')
    .map(w => w.charAt(0).toUpperCase() + w.slice(1))
    .join(' ')
}

const getEventColor = (type: string) => {
  if (type.includes('added')) return 'text-green-400'
  if (type.includes('deleted')) return 'text-red-400'
  if (type.includes('completed')) return 'text-blue-400'
  if (type.includes('progress')) return 'text-yellow-400'
  return 'text-slate-300'
}

const formatTime = (timestamp: string) => {
  try {
    const date = new Date(timestamp)
    const now = new Date()
    const diffMs = now.getTime() - date.getTime()
    const diffSecs = Math.floor(diffMs / 1000)

    if (diffSecs < 60) return `${diffSecs}s`
    const diffMins = Math.floor(diffSecs / 60)
    if (diffMins < 60) return `${diffMins}m`
    return date.toLocaleTimeString()
  } catch {
    return '?'
  }
}

const eventDataSummary = (event: CDCEvent): string => {
  if (!event.data || typeof event.data !== 'object') return ''
  const summary = Object.entries(event.data)
    .slice(0, 2)
    .map(([k, v]) => `${k}: ${String(v).slice(0, 20)}`)
    .join(', ')
  return summary ? `[${summary}]` : ''
}

const toggleEventFilter = (type: string) => {
  if (activeFilters.value.has(type)) {
    activeFilters.value.delete(type)
  } else {
    activeFilters.value.add(type)
  }
}

const clearEvents = () => {
  events.value = []
}

const handleCDCEvent = (event: any) => {
  const cdcEvent: CDCEvent = {
    event_id: event.event_id || `event-${Date.now()}`,
    event_type: event.event_type || 'unknown',
    timestamp: event.timestamp || new Date().toISOString(),
    entity_id: event.entity_id || '',
    entity_type: event.entity_type || '',
    data: event.data,
  }

  events.value.unshift(cdcEvent)

  // Keep only last 100 events
  if (events.value.length > 100) {
    events.value = events.value.slice(0, 100)
  }
}

onMounted(() => {
  // Subscribe to all CDC events
  subscribe('*', handleCDCEvent)
})
</script>
