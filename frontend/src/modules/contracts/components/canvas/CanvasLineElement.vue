<script setup lang="ts">
import type { LineCanvasElement } from '../../types/contractCanvas'

defineProps<{
  element: LineCanvasElement
  zoomLevel: number
}>()
</script>

<template>
  <div class="canvas-line-element w-full h-full flex items-center justify-center pointer-events-none">
    <div
      v-if="element.orientation === 'vertical'"
      class="w-0 h-full"
      :style="{
        borderLeft: `${element.strokeWidth || 1}px ${element.strokeStyle || 'solid'} ${element.strokeColor || '#000000'}`
      }"
    ></div>
    <div
      v-else
      class="w-full h-0"
      :style="{
        borderTop: `${element.strokeWidth || 1}px ${element.strokeStyle || 'solid'} ${element.strokeColor || '#000000'}`
      }"
    ></div>
  </div>
</template>
