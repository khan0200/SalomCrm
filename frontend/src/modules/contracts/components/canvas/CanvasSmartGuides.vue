<script setup lang="ts">
import type { AlignmentGuide, DistanceGuide } from '../../types/contractCanvas'

const props = withDefaults(
  defineProps<{
    guides?: AlignmentGuide[]
    distanceGuides?: DistanceGuide[]
    zoomLevel: number
  }>(),
  {
    guides: () => [],
    distanceGuides: () => [],
  }
)

const MM_TO_PX_BASE = 3.779527559

function mmToPx(mm: number): number {
  return mm * MM_TO_PX_BASE * (props.zoomLevel / 100)
}
</script>

<template>
  <div class="canvas-smart-guides pointer-events-none absolute inset-0 z-50 overflow-visible" aria-hidden="true">
    <!-- 1. Smart Alignment Guides (Snap Lines) -->
    <template v-for="(guide, index) in (guides || [])" :key="`align-${index}`">
      <!-- Vertical guide (constant X position across full page height) -->
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
          class="absolute top-2 left-0.5 px-1 py-0.5 rounded bg-blue-500 text-[8px] font-mono text-white font-bold whitespace-nowrap shadow-sm"
        >
          {{ guide.label }}
        </span>
      </div>

      <!-- Horizontal guide (constant Y position across full page width) -->
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
          class="absolute left-2 -top-4 px-1 py-0.5 rounded bg-blue-500 text-[8px] font-mono text-white font-bold whitespace-nowrap shadow-sm"
        >
          {{ guide.label }}
        </span>
      </div>
    </template>

    <!-- 2. Smart Distance Guides (Canva/Figma Style) -->
    <template v-for="guide in (distanceGuides || [])" :key="guide.id">
      <!-- Horizontal Distance Guide (connects left edge to right edge) -->
      <div
        v-if="guide.axis === 'horizontal'"
        class="absolute pointer-events-none z-50 select-none"
        :style="{
          left: `${mmToPx(guide.startPos)}px`,
          top: `${mmToPx(guide.crossPos)}px`,
          width: `${Math.max(1, mmToPx(guide.endPos - guide.startPos))}px`,
        }"
      >
        <!-- Hairline measurement line -->
        <div
          class="absolute inset-x-0 h-px -translate-y-1/2"
          :style="{ background: guide.isEqualSpacing ? '#d946ef' : '#f43f5e' }"
        ></div>

        <!-- Left end T-bar tick -->
        <div
          class="absolute left-0 top-1/2 -translate-y-1/2 -translate-x-1/2 w-px h-2.5 rounded-full"
          :style="{ background: guide.isEqualSpacing ? '#d946ef' : '#f43f5e' }"
        ></div>

        <!-- Right end T-bar tick -->
        <div
          class="absolute right-0 top-1/2 -translate-y-1/2 translate-x-1/2 w-px h-2.5 rounded-full"
          :style="{ background: guide.isEqualSpacing ? '#d946ef' : '#f43f5e' }"
        ></div>

        <!-- Optional vertical dashed projection lines (if element is offset in cross-axis) -->
        <div
          v-if="guide.projectionFrom"
          class="absolute w-px border-l border-dashed"
          :style="{
            left: '0px',
            top: `${mmToPx(guide.projectionFrom.start) - mmToPx(guide.crossPos)}px`,
            height: `${Math.max(1, mmToPx(guide.projectionFrom.end - guide.projectionFrom.start))}px`,
            borderColor: guide.isEqualSpacing ? '#d946ef' : '#f43f5e',
            opacity: 0.6,
          }"
        ></div>
        <div
          v-if="guide.projectionTo"
          class="absolute w-px border-l border-dashed"
          :style="{
            right: '0px',
            top: `${mmToPx(guide.projectionTo.start) - mmToPx(guide.crossPos)}px`,
            height: `${Math.max(1, mmToPx(guide.projectionTo.end - guide.projectionTo.start))}px`,
            borderColor: guide.isEqualSpacing ? '#d946ef' : '#f43f5e',
            opacity: 0.6,
          }"
        ></div>

        <!-- Centered distance pill badge -->
        <div
          class="absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 rounded-full px-1.5 py-0.5 text-[9px] font-mono font-bold text-white flex items-center whitespace-nowrap leading-none tracking-tight shadow-sm"
          :class="guide.isEqualSpacing ? 'bg-fuchsia-600 ring-2 ring-fuchsia-300 shadow-md scale-105 font-extrabold' : 'bg-rose-500 ring-1 ring-white/30'"
        >
          <span v-if="guide.isEqualSpacing" class="mr-0.5 opacity-90 text-[8px] font-sans">=</span>
          <span>{{ guide.label || `${guide.distanceMm} mm` }}</span>
        </div>
      </div>

      <!-- Vertical Distance Guide (connects top edge to bottom edge) -->
      <div
        v-else-if="guide.axis === 'vertical'"
        class="absolute pointer-events-none z-50 select-none"
        :style="{
          left: `${mmToPx(guide.crossPos)}px`,
          top: `${mmToPx(guide.startPos)}px`,
          height: `${Math.max(1, mmToPx(guide.endPos - guide.startPos))}px`,
        }"
      >
        <!-- Hairline measurement line -->
        <div
          class="absolute inset-y-0 w-px -translate-x-1/2"
          :style="{ background: guide.isEqualSpacing ? '#d946ef' : '#f43f5e' }"
        ></div>

        <!-- Top end T-bar tick -->
        <div
          class="absolute top-0 left-1/2 -translate-x-1/2 -translate-y-1/2 h-px w-2.5 rounded-full"
          :style="{ background: guide.isEqualSpacing ? '#d946ef' : '#f43f5e' }"
        ></div>

        <!-- Bottom end T-bar tick -->
        <div
          class="absolute bottom-0 left-1/2 -translate-x-1/2 translate-y-1/2 h-px w-2.5 rounded-full"
          :style="{ background: guide.isEqualSpacing ? '#d946ef' : '#f43f5e' }"
        ></div>

        <!-- Optional horizontal dashed projection lines (if element is offset in cross-axis) -->
        <div
          v-if="guide.projectionFrom"
          class="absolute h-px border-t border-dashed"
          :style="{
            top: '0px',
            left: `${mmToPx(guide.projectionFrom.start) - mmToPx(guide.crossPos)}px`,
            width: `${Math.max(1, mmToPx(guide.projectionFrom.end - guide.projectionFrom.start))}px`,
            borderColor: guide.isEqualSpacing ? '#d946ef' : '#f43f5e',
            opacity: 0.6,
          }"
        ></div>
        <div
          v-if="guide.projectionTo"
          class="absolute h-px border-t border-dashed"
          :style="{
            bottom: '0px',
            left: `${mmToPx(guide.projectionTo.start) - mmToPx(guide.crossPos)}px`,
            width: `${Math.max(1, mmToPx(guide.projectionTo.end - guide.projectionTo.start))}px`,
            borderColor: guide.isEqualSpacing ? '#d946ef' : '#f43f5e',
            opacity: 0.6,
          }"
        ></div>

        <!-- Centered distance pill badge -->
        <div
          class="absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 rounded-full px-1.5 py-0.5 text-[9px] font-mono font-bold text-white flex items-center whitespace-nowrap leading-none tracking-tight shadow-sm"
          :class="guide.isEqualSpacing ? 'bg-fuchsia-600 ring-2 ring-fuchsia-300 shadow-md scale-105 font-extrabold' : 'bg-rose-500 ring-1 ring-white/30'"
        >
          <span v-if="guide.isEqualSpacing" class="mr-0.5 opacity-90 text-[8px] font-sans">=</span>
          <span>{{ guide.label || `${guide.distanceMm} mm` }}</span>
        </div>
      </div>
    </template>
  </div>
</template>

