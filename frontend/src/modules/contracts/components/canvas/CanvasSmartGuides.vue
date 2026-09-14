<script setup lang="ts">
import type { AlignmentGuide } from '../../types/contractCanvas'

const props = defineProps<{
  guides: AlignmentGuide[]
  zoomLevel: number
}>()

const MM_TO_PX_BASE = 3.779527559

function mmToPx(mm: number): number {
  return mm * MM_TO_PX_BASE * (props.zoomLevel / 100)
}
</script>

<template>
  <div class="canvas-smart-guides pointer-events-none absolute inset-0 z-50 overflow-visible" aria-hidden="true">
    <template v-for="(guide, index) in guides" :key="index">
      <!-- Vertical guide line (aligned on X axis) -->
      <div
        v-if="guide.type === 'vertical'"
        class="absolute top-0 bottom-0 pointer-events-none z-50"
        :style="{ left: `${mmToPx(guide.position)}px` }"
      >
        <div class="w-px h-full bg-blue-500/70"></div>
        <span
          v-if="guide.label"
          class="absolute top-2 left-1 px-1 py-0.5 rounded bg-blue-500 text-[8px] font-mono text-white font-bold whitespace-nowrap -translate-x-1/2"
        >
          {{ guide.label }}
        </span>
      </div>

      <!-- Horizontal guide line (aligned on Y axis) -->
      <div
        v-else-if="guide.type === 'horizontal'"
        class="absolute left-0 right-0 pointer-events-none z-50"
        :style="{ top: `${mmToPx(guide.position)}px` }"
      >
        <div class="h-px w-full bg-blue-500/70"></div>
        <span
          v-if="guide.label"
          class="absolute left-2 -top-4 px-1 py-0.5 rounded bg-blue-500 text-[8px] font-mono text-white font-bold whitespace-nowrap"
        >
          {{ guide.label }}
        </span>
      </div>
    </template>
  </div>
</template>

