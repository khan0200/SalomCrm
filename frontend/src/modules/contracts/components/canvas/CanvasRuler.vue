<script setup lang="ts">
import { computed } from 'vue'

const props = withDefaults(
  defineProps<{
    orientation: 'horizontal' | 'vertical'
    lengthMm: number
    zoomLevel: number
    cursorPosMm?: number
    marginStart?: number   // left margin (horiz) or top margin (vert)
    marginEnd?: number     // right margin (horiz) or bottom margin (vert)
  }>(),
  {
    cursorPosMm: -1,
    marginStart: 0,
    marginEnd: 0,
  }
)

const MM_TO_PX_BASE = 3.779527559
const THICKNESS = 22 // ruler height (horiz) or width (vert) in px

function mmToPx(mm: number): number {
  return mm * MM_TO_PX_BASE * (props.zoomLevel / 100)
}

const scaledLengthPx = computed(() => mmToPx(props.lengthMm))
const marginStartPx = computed(() => mmToPx(props.marginStart))
const marginEndPx = computed(() => mmToPx(props.marginEnd))
const marginEndFromStartPx = computed(() => scaledLengthPx.value - marginEndPx.value)

interface Tick {
  posMm: number
  level: 1 | 2 | 3  // 1=minor(1mm), 2=medium(5mm), 3=major(10mm)
  label?: string
}

const ticks = computed<Tick[]>(() => {
  const list: Tick[] = []
  const pxPerMm = MM_TO_PX_BASE * (props.zoomLevel / 100)
  // Adaptive granularity based on zoom
  const showMm    = pxPerMm >= 3.0     // show 1mm only at ≥80% zoom
  const show5mm   = pxPerMm >= 0.8     // show 5mm at ≥21% zoom

  for (let mm = 0; mm <= props.lengthMm; mm++) {
    const isMajor  = mm % 10 === 0
    const isMedium = !isMajor && mm % 5 === 0
    const isMinor  = !isMajor && !isMedium

    if (isMinor  && !showMm)  continue
    if (isMedium && !show5mm) continue

    // Label spacing: every 10mm, but skip if too dense
    let label: string | undefined
    if (isMajor) {
      // At low zoom: only show every 20mm label
      const labelStep = pxPerMm < 1.5 ? 20 : 10
      if (mm % labelStep === 0 && mm > 0) label = String(mm)
    }

    list.push({
      posMm: mm,
      level: isMajor ? 3 : isMedium ? 2 : 1,
      label,
    })
  }
  return list
})

// Cursor indicator position
const cursorPx = computed(() => {
  if (props.cursorPosMm < 0 || props.cursorPosMm > props.lengthMm) return -1
  return mmToPx(props.cursorPosMm)
})

// Tick height/width based on level (from ruler edge)
function tickSize(level: 1 | 2 | 3): number {
  if (level === 3) return 11
  if (level === 2) return 7
  return 4
}
function tickColor(level: 1 | 2 | 3, isDark = false): string {
  if (level === 3) return isDark ? '#71717a' : '#9ca3af'
  if (level === 2) return isDark ? '#52525b' : '#c4c4cc'
  return isDark ? '#3f3f46' : '#e4e4e7'
}
</script>

<template>
  <!-- ═══ HORIZONTAL RULER ═══ -->
  <div
    v-if="orientation === 'horizontal'"
    class="ruler-h-container"
    :style="{ width: `${scaledLengthPx}px`, height: `${THICKNESS}px` }"
  >
    <svg
      :width="scaledLengthPx"
      :height="THICKNESS"
      class="ruler-svg"
      style="display:block;overflow:hidden"
    >
      <!-- Background -->
      <rect width="100%" height="100%" class="ruler-bg" />

      <!-- Left margin zone (subtle fill) -->
      <rect
        v-if="marginStart > 0"
        x="0" y="0"
        :width="marginStartPx"
        :height="THICKNESS"
        class="ruler-margin-zone"
      />

      <!-- Right margin zone -->
      <rect
        v-if="marginEnd > 0"
        :x="marginEndFromStartPx" y="0"
        :width="marginEndPx"
        :height="THICKNESS"
        class="ruler-margin-zone"
      />

      <!-- Tick marks -->
      <g v-for="tick in ticks" :key="tick.posMm">
        <line
          :x1="mmToPx(tick.posMm)"
          :x2="mmToPx(tick.posMm)"
          :y1="THICKNESS - tickSize(tick.level)"
          :y2="THICKNESS"
          class="ruler-tick"
          :class="`ruler-tick-${tick.level}`"
        />
        <text
          v-if="tick.label"
          :x="mmToPx(tick.posMm) + 2"
          :y="THICKNESS - tickSize(3) - 1"
          class="ruler-label"
        >
          {{ tick.label }}
        </text>
      </g>

      <!-- Bottom border line -->
      <line x1="0" :x2="scaledLengthPx" :y1="THICKNESS - 0.5" :y2="THICKNESS - 0.5" class="ruler-border-line" />

      <!-- Margin edge markers (vertical lines at margin boundaries) -->
      <line
        v-if="marginStart > 0"
        :x1="marginStartPx" :x2="marginStartPx"
        y1="0" :y2="THICKNESS"
        class="ruler-margin-edge"
      />
      <line
        v-if="marginEnd > 0"
        :x1="marginEndFromStartPx" :x2="marginEndFromStartPx"
        y1="0" :y2="THICKNESS"
        class="ruler-margin-edge"
      />

      <!-- Cursor indicator -->
      <line
        v-if="cursorPx >= 0"
        :x1="cursorPx" :x2="cursorPx"
        y1="0" :y2="THICKNESS"
        class="ruler-cursor"
      />
    </svg>
  </div>

  <!-- ═══ VERTICAL RULER ═══ -->
  <div
    v-else
    class="ruler-v-container"
    :style="{ width: `${THICKNESS}px`, height: `${scaledLengthPx}px` }"
  >
    <svg
      :width="THICKNESS"
      :height="scaledLengthPx"
      class="ruler-svg"
      style="display:block;overflow:hidden"
    >
      <!-- Background -->
      <rect width="100%" height="100%" class="ruler-bg" />

      <!-- Top margin zone -->
      <rect
        v-if="marginStart > 0"
        x="0" y="0"
        :width="THICKNESS"
        :height="marginStartPx"
        class="ruler-margin-zone"
      />

      <!-- Bottom margin zone -->
      <rect
        v-if="marginEnd > 0"
        x="0"
        :y="marginEndFromStartPx"
        :width="THICKNESS"
        :height="marginEndPx"
        class="ruler-margin-zone"
      />

      <!-- Tick marks -->
      <g v-for="tick in ticks" :key="tick.posMm">
        <line
          :y1="mmToPx(tick.posMm)"
          :y2="mmToPx(tick.posMm)"
          :x1="THICKNESS - tickSize(tick.level)"
          :x2="THICKNESS"
          class="ruler-tick"
          :class="`ruler-tick-${tick.level}`"
        />
        <text
          v-if="tick.label"
          :y="mmToPx(tick.posMm) - 2"
          :x="2"
          class="ruler-label ruler-label-vertical"
        >
          {{ tick.label }}
        </text>
      </g>

      <!-- Right border line -->
      <line :x1="THICKNESS - 0.5" :x2="THICKNESS - 0.5" y1="0" :y2="scaledLengthPx" class="ruler-border-line" />

      <!-- Margin edge markers (horizontal lines) -->
      <line
        v-if="marginStart > 0"
        x1="0" :x2="THICKNESS"
        :y1="marginStartPx" :y2="marginStartPx"
        class="ruler-margin-edge"
      />
      <line
        v-if="marginEnd > 0"
        x1="0" :x2="THICKNESS"
        :y1="marginEndFromStartPx" :y2="marginEndFromStartPx"
        class="ruler-margin-edge"
      />

      <!-- Cursor indicator -->
      <line
        v-if="cursorPx >= 0"
        x1="0" :x2="THICKNESS"
        :y1="cursorPx" :y2="cursorPx"
        class="ruler-cursor"
      />
    </svg>
  </div>
</template>

<style scoped>
/* ─── Container sizing ─── */
.ruler-h-container,
.ruler-v-container {
  flex-shrink: 0;
  overflow: hidden;
  user-select: none;
}

/* ─── SVG base elements ─── */
.ruler-svg {
  shape-rendering: crispEdges;
}

/* Background */
.ruler-bg {
  fill: #f7f8fa;
}
:global(.dark) .ruler-bg {
  fill: #18181b;
}

/* Margin zone fill */
.ruler-margin-zone {
  fill: rgba(0, 0, 0, 0.03);
}
:global(.dark) .ruler-margin-zone {
  fill: rgba(255, 255, 255, 0.025);
}

/* Ticks */
.ruler-tick {
  stroke-width: 0.75;
}
.ruler-tick-3 {
  stroke: #9ca3af;
  stroke-width: 1;
}
.ruler-tick-2 {
  stroke: #c4c4cc;
  stroke-width: 0.75;
}
.ruler-tick-1 {
  stroke: #e4e4e7;
  stroke-width: 0.5;
}
:global(.dark) .ruler-tick-3 { stroke: #71717a; }
:global(.dark) .ruler-tick-2 { stroke: #52525b; }
:global(.dark) .ruler-tick-1 { stroke: #3f3f46; }

/* Border line */
.ruler-border-line {
  stroke: #e2e4e9;
  stroke-width: 0.75;
}
:global(.dark) .ruler-border-line {
  stroke: #27272a;
}

/* Margin edge lines */
.ruler-margin-edge {
  stroke: #93c5fd;
  stroke-width: 0.75;
  stroke-dasharray: 2 2;
  opacity: 0.7;
}
:global(.dark) .ruler-margin-edge {
  stroke: #3b82f6;
  opacity: 0.4;
}

/* Labels */
.ruler-label {
  font-size: 7.5px;
  font-family: 'JetBrains Mono', 'Fira Code', ui-monospace, monospace;
  fill: #9ca3af;
  dominant-baseline: text-before-edge;
  letter-spacing: 0.02em;
}
:global(.dark) .ruler-label {
  fill: #52525b;
}
.ruler-label-vertical {
  writing-mode: vertical-rl;
  text-orientation: mixed;
  dominant-baseline: auto;
  font-size: 7px;
}

/* Cursor indicator */
.ruler-cursor {
  stroke: #3b82f6;
  stroke-width: 1;
  opacity: 0.85;
  pointer-events: none;
}
</style>
