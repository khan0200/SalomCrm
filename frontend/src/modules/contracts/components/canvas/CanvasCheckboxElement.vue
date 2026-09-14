<script setup lang="ts">
import { computed } from 'vue'
import { CheckSquare, Square } from 'lucide-vue-next'
import type { CheckboxCanvasElement } from '../../types/contractCanvas'

const props = defineProps<{
  element: CheckboxCanvasElement
  zoomLevel: number
}>()

const emit = defineEmits<{
  'update:checked': [val: boolean]
}>()

function toggle() {
  emit('update:checked', !props.element.checked)
}
</script>

<template>
  <div
    class="canvas-checkbox-element w-full h-full flex items-center gap-2 font-serif select-none cursor-pointer"
    style="font-family: 'Times New Roman', Times, serif;"
    @click="toggle"
  >
    <div class="shrink-0 text-blue-600 dark:text-blue-400">
      <CheckSquare v-if="element.checked" class="w-4 h-4" />
      <Square v-else class="w-4 h-4 text-zinc-400" />
    </div>
    <span
      class="text-xs text-zinc-900 leading-tight font-medium"
      :style="{ fontSize: `${(element.fontSize || 12) * (zoomLevel / 100)}pt` }"
    >
      {{ element.label || 'Checkbox' }}
    </span>
  </div>
</template>
