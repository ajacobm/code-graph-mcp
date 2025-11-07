<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{
  node: any
  distance?: number
  direction?: 'inbound' | 'outbound' | 'sibling'
  showDistance?: boolean
}>()

const emit = defineEmits<{
  click: [node: any]
}>()

const icon = computed(() => {
  if (props.node.metadata?.is_entry_point) return '🚀'
  if (props.node.metadata?.is_hub) return '🔀'
  if (props.node.metadata?.is_leaf) return '🍃'
  if (props.direction === 'inbound') return '🔵'
  if (props.direction === 'outbound') return '🟢'
  if (props.direction === 'sibling') return '🟡'
  
  switch (props.node.node_type) {
    case 'function': return '⚙️'
    case 'class': return '📦'
    case 'module': return '📄'
    case 'import': return '📥'
    default: return '•'
  }
})

const distanceColor = computed(() => {
  if (!props.distance && props.distance !== 0) return 'text-base-content'
  if (props.distance === 0) return 'text-yellow-500'
  if (props.distance <= 2) return 'text-green-500'
  if (props.distance <= 5) return 'text-blue-500'
  return 'text-red-500'
})

const borderColor = computed(() => {
  if (props.direction === 'inbound') return 'border-l-4 border-blue-500'
  if (props.direction === 'outbound') return 'border-l-4 border-green-500'
  if (props.direction === 'sibling') return 'border-l-4 border-yellow-500'
  return ''
})

const distanceText = computed(() => {
  if (!props.showDistance || (!props.distance && props.distance !== 0)) return ''
  if (props.distance === 0) return 'Same file'
  if (props.distance === 1) return '1 hop'
  return `${props.distance} hops`
})

const fileName = computed(() => {
  const parts = props.node.id?.split(':') || []
  if (parts.length >= 2) {
    const path = parts[1]
    return path.split('/').pop() || path
  }
  return props.node.location?.file_path?.split('/').pop() || 'unknown'
})
</script>

<template>
  <div 
    class="node-tile card bg-base-200 hover:bg-base-300 cursor-pointer transition-all hover:shadow-lg"
    :class="borderColor"
    @click="emit('click', node)"
  >
    <div class="card-body p-4">
      <div class="flex items-start gap-3">
        <!-- Icon -->
        <div class="text-2xl flex-shrink-0">{{ icon }}</div>
        
        <!-- Content -->
        <div class="flex-1 min-w-0">
          <h4 class="font-bold truncate">{{ node.name }}</h4>
          <p class="text-sm opacity-70 truncate">{{ fileName }}</p>
          
          <!-- Metadata -->
          <div class="flex gap-2 text-xs mt-2 flex-wrap">
            <span v-if="showDistance && distanceText" class="badge badge-sm">
              {{ distanceText }}
            </span>
            <span class="badge badge-sm badge-outline">
              {{ node.node_type }}
            </span>
            <span v-if="node.complexity" class="badge badge-sm badge-outline">
              C: {{ node.complexity }}
            </span>
            <span v-if="node.language" class="badge badge-sm badge-primary badge-outline">
              {{ node.language }}
            </span>
          </div>
        </div>

        <!-- Distance Indicator -->
        <div v-if="showDistance && (distance || distance === 0)" class="text-right flex-shrink-0">
          <div class="text-2xl font-bold" :class="distanceColor">
            {{ distance }}
          </div>
          <div class="text-xs opacity-70">hops</div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.node-tile {
  transition: all 0.2s ease;
}

.node-tile:hover {
  transform: translateX(4px);
}
</style>
