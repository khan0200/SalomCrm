<script setup lang="ts">
import { ref, computed } from 'vue'
import type { PageGuide } from '../../types/contractCanvas'

const props = defineProps<{
  guide: PageGuide
  zoomLevel: number
  isSelected: boolean
  pageWidthMm: number
  pageHeightMm: number
}>()

const emit = defineEmits<{
  select: []
  'update:position': [positionMm: number, recordHistory: boolean]
  delete: []
}>()

const MM_TO_PX_BASE = 3.779527559

function mmToPx(mm: number): number {
  return mm * MM_TO_PX_BASE * (props.zoomLevel / 100)
}

function pxToMm(px: number): number {
  return px / (MM_TO_PX_BASE * (props.zoomLevel / 100))
}

const isDragging = ref(false)
const liveLabel = computed(() => {
  const pos = props.guide.position
  const rounded = Math.round(pos * 10) / 10
  const val = rounded % 1 === 0 ? rounded.toFixed(0) : rounded.toFixed(1)
  return props.guide.type === 'horizontal' ? `Y: ${val} mm` : `X: ${val} mm`
})

function onPointerDown(e: PointerEvent) {
  if (e.button !== 0) return
  e.preventDefault()
  e.stopPropagation()

  emit('select')
  // preventDefault() above suppresses the browser's default focus-on-click,
  // so Delete/Backspace (handled via @keydown on this element) would never
  // fire without explicitly focusing it here.
  ;(e.currentTarget as HTMLElement).focus()
  ;(e.currentTarget as HTMLElement).setPointerCapture(e.pointerId)

  const startClientX = e.clientX
  const startClientY = e.clientY
  const startPos = props.guide.position

  function onMove(moveEvent: PointerEvent) {
    isDragging.value = true
    const deltaMm = props.guide.type === 'horizontal'
      ? pxToMm(moveEvent.clientY - startClientY)
      : pxToMm(moveEvent.clientX - startClientX)
    const max = props.guide.type === 'horizontal' ? props.pageHeightMm : props.pageWidthMm
    const nextPos = Math.max(0, Math.min(max, startPos + deltaMm))
    emit('update:position', nextPos, false)
  }

  function onUp() {
    window.removeEventListener('pointermove', onMove)
    window.removeEventListener('pointerup', onUp)
    if (isDragging.value) {
      emit('update:position', props.guide.position, true)
    }
    isDragging.value = false
  }

  window.addEventListener('pointermove', onMove)
  window.addEventListener('pointerup', onUp)
}

function onKeydown(e: KeyboardEvent) {
  if (e.key === 'Delete' || e.key === 'Backspace') {
    e.preventDefault()
    e.stopPropagation()
    emit('delete')
  }
}
</script>

<template>
  <!-- Horizontal guide: full-width line at a fixed Y (mm) -->
  <div
    v-if="guide.type === 'horizontal'"
    class="canvas-guide-line canvas-guide-line--h absolute left-0 right-0 no-print"
    :class="{ 'is-selected': isSelected, 'is-dragging': isDragging }"
    :style="{ top: `${mmToPx(guide.position)}px` }"
    tabindex="0"
    role="separator"
    aria-label="Horizontal guide"
    @pointerdown="onPointerDown"
    @click.stop
    @keydown="onKeydown"
  >
    <div class="canvas-guide-hitbox canvas-guide-hitbox--h"></div>
    <div class="canvas-guide-visual canvas-guide-visual--h"></div>
    <span v-if="isDragging || isSelected" class="canvas-guide-label canvas-guide-label--h">
      {{ liveLabel }}
    </span>
  </div>

  <!-- Vertical guide: full-height line at a fixed X (mm) -->
  <div
    v-else
    class="canvas-guide-line canvas-guide-line--v absolute top-0 bottom-0 no-print"
    :class="{ 'is-selected': isSelected, 'is-dragging': isDragging }"
    :style="{ left: `${mmToPx(guide.position)}px` }"
    tabindex="0"
    role="separator"
    aria-label="Vertical guide"
    @pointerdown="onPointerDown"
    @click.stop
    @keydown="onKeydown"
  >
    <div class="canvas-guide-hitbox canvas-guide-hitbox--v"></div>
    <div class="canvas-guide-visual canvas-guide-visual--v"></div>
    <span v-if="isDragging || isSelected" class="canvas-guide-label canvas-guide-label--v">
      {{ liveLabel }}
    </span>
  </div>
</template>

<style scoped>
.canvas-guide-line {
  z-index: 45; /* above elements/selection (z<=40), below smart-guides (z-50) and toolbars */
  pointer-events: none;
}

/* Thin visual line — subtle at rest, brighter on hover/select/drag */
.canvas-guide-visual {
  position: absolute;
  background: rgba(6, 182, 212, 0.55); /* cyan-500 */
  pointer-events: none;
}
.canvas-guide-visual--h {
  left: 0;
  right: 0;
  top: 0;
  height: 1px;
}
.canvas-guide-visual--v {
  top: 0;
  bottom: 0;
  left: 0;
  width: 1px;
}

/* Invisible, generously-sized hitbox so the thin line is easy to grab */
.canvas-guide-hitbox {
  position: absolute;
  pointer-events: auto;
  cursor: default;
}
.canvas-guide-hitbox--h {
  left: 0;
  right: 0;
  top: -4px;
  height: 8px;
  cursor: ns-resize;
}
.canvas-guide-hitbox--v {
  top: 0;
  bottom: 0;
  left: -4px;
  width: 8px;
  cursor: ew-resize;
}

.canvas-guide-line:hover .canvas-guide-visual,
.canvas-guide-line.is-selected .canvas-guide-visual,
.canvas-guide-line.is-dragging .canvas-guide-visual {
  background: #06b6d4; /* solid cyan-500 */
}
.canvas-guide-line.is-selected .canvas-guide-visual,
.canvas-guide-line.is-dragging .canvas-guide-visual {
  box-shadow: 0 0 0 1px rgba(6, 182, 212, 0.25);
}

.canvas-guide-line:focus {
  outline: none;
}

/* Small, professional position label — only shown while dragging or selected */
.canvas-guide-label {
  position: absolute;
  background: #06b6d4;
  color: white;
  font-size: 9px;
  font-weight: 700;
  font-family: 'JetBrains Mono', 'Fira Code', ui-monospace, monospace;
  padding: 2px 6px;
  border-radius: 4px;
  white-space: nowrap;
  pointer-events: none;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.2);
  letter-spacing: 0.01em;
}
.canvas-guide-label--h {
  left: 6px;
  top: 3px;
}
.canvas-guide-label--v {
  top: 6px;
  left: 3px;
}

/* Never printed / exported — belt-and-suspenders alongside the fact that
   guides are structurally excluded from the PDF/HTML export path (which only
   ever reads page.elements, never document.guides). */
@media print {
  .canvas-guide-line {
    display: none !important;
  }
}
</style>
