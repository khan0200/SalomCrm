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
      <!--
        Vertical guide (constant X position across full page height).
        The outer div is positioned so its LEFT edge is at guide.position px.
        The inner line is then shifted left by 0.5px (half its 1px width) so the
        visual centre of the pixel exactly coincides with the document coordinate.
        Using a sub-pixel translate keeps the maths zoom-independent and avoids
        any hardcoded pixel offsets.
      -->
      <div
        v-if="guide.type === 'vertical'"
        class="absolute top-0 bottom-0 w-px pointer-events-none z-50"
        :style="{
          left: `${mmToPx(guide.position)}px`,
          transform: 'translateX(-0.5px)',
          background: 'rgba(37,99,235,0.70)',
        }"
      >
        <span
          v-if="guide.label"
          class="absolute top-2 left-0.5 px-1 py-0.5 rounded bg-blue-500 text-[8px] font-mono text-white font-bold whitespace-nowrap"
        >
          {{ guide.label }}
        </span>
      </div>

      <!--
        Horizontal guide (constant Y position across full page width).
        Same centering logic: translate up by 0.5px so the visual midpoint of
        the 1px-tall line sits exactly on the document coordinate.
      -->
      <div
        v-else-if="guide.type === 'horizontal'"
        class="absolute left-0 right-0 h-px pointer-events-none z-50"
        :style="{
          top: `${mmToPx(guide.position)}px`,
          transform: 'translateY(-0.5px)',
          background: 'rgba(37,99,235,0.70)',
        }"
      >
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

