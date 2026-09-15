<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import {
  Copy,
  Trash2,
  Lock,
  Unlock,
  ArrowUp,
  ArrowDown,
  RotateCw,
  Type,
  PaintRoller,
} from 'lucide-vue-next'
import type { CanvasElement, ResizeHandle, AlignmentGuide, DistanceGuide } from '../../types/contractCanvas'

const props = withDefaults(
  defineProps<{
    element: CanvasElement
    isSelected: boolean
    isEditing: boolean
    zoomLevel: number
    readonly?: boolean
    isCopyStyleActive?: boolean
    copyStyleMode?: 'single' | 'persistent' | null
    calculateSnapping?: (
      x: number,
      y: number,
      w: number,
      h: number,
      id: string,
      isResize?: boolean
    ) => { x: number; y: number; guides: AlignmentGuide[]; distanceGuides?: DistanceGuide[] }
  }>(),
  {
    readonly: false,
    isCopyStyleActive: false,
    copyStyleMode: null,
  }
)

const emit = defineEmits<{
  select: [e: MouseEvent]
  'double-click': []
  'update:bounds': [bounds: { x: number; y: number; width: number; height: number; rotation?: number }]
  'drag:start': []
  'drag:end': []
  'resize:start': []
  'resize:end': []
  'set-guides': [guides: AlignmentGuide[], distanceGuides?: DistanceGuide[]]
  duplicate: []
  delete: []
  'copy-style': [e: MouseEvent]
  'toggle-lock': []
  'bring-forward': []
  'send-backward': []
}>()

const MM_TO_PX_BASE = 3.779527559

function mmToBasePx(mm: number): number {
  return mm * MM_TO_PX_BASE
}

function pxToMm(px: number): number {
  return px / (MM_TO_PX_BASE * (props.zoomLevel / 100))
}

const counterScale = computed(() => Math.max(0.65, Math.min(1.4, 100 / (props.zoomLevel || 100))))
const handleScale = computed(() => Math.max(0.75, Math.min(1.5, 100 / (props.zoomLevel || 100))))

const isTextType = computed(() => {
  const t = props.element.type
  return t === 'text' || t === 'heading' || t === 'paragraph' || t === 'date' || t === 'variable' || t === 'checkbox'
})

const isNearTop = computed(() => {
  return props.element.y < 16
})

const toolbarPositionClass = computed(() => {
  // If element is near top edge (< 16mm), place toolbar below to avoid being clipped by sheet boundaries
  const vClass = isNearTop.value ? 'top-[calc(100%+12px)]' : '-top-12'

  return `${vClass} left-1/2 -translate-x-1/2`
})

const wrapperStyle = computed(() => {
  const leftPx = mmToBasePx(props.element.x)
  const topPx = mmToBasePx(props.element.y)
  const widthPx = mmToBasePx(props.element.width)
  const heightPx = mmToBasePx(props.element.height)
  const rot = props.element.rotation || 0

  return {
    transform: `translate3d(${leftPx}px, ${topPx}px, 0) rotate(${rot}deg)`,
    width: `${widthPx}px`,
    // Text elements use exact height (auto-resized to fit content),
    // other elements use minHeight so content can expand them
    ...(isTextType.value
      ? { height: `${heightPx}px` }
      : { minHeight: `${heightPx}px` }),
    // Elevate z-index when selected or editing so toolbar and selection handles
    // are ALWAYS on top of all other elements and guides
    zIndex: (props.isSelected || props.isEditing) ? 900 + (props.element.zIndex || 1) : (props.element.zIndex || 1),
  }
})

// --- Spacing Popover (Line Spacing & Letter Spacing — Canva Style) ---
const showSpacingPopover = ref(false)

watch(() => props.isSelected, (val) => {
  if (!val) showSpacingPopover.value = false
})

const currentLineHeight = computed(() => {
  return (props.element as any)?.style?.lineHeight ?? 1.5
})

const currentLetterSpacing = computed(() => {
  return (props.element as any)?.style?.letterSpacing ?? 0
})

function setLineHeight(val: number | string) {
  const num = typeof val === 'string' ? parseFloat(val) : val
  if (isNaN(num)) return
  const el = props.element as any
  if (!el.style) el.style = {}
  el.style.lineHeight = Math.max(0.5, Math.min(3.5, Math.round(num * 100) / 100))
}

function setLetterSpacing(val: number | string) {
  const num = typeof val === 'string' ? parseFloat(val) : val
  if (isNaN(num)) return
  const el = props.element as any
  if (!el.style) el.style = {}
  el.style.letterSpacing = Math.max(-5, Math.min(30, Math.round(num * 10) / 10))
}

// --- Drag & Move Logic ---
const isDraggingLocal = ref(false)
const hasDragged = ref(false)

function onPointerDown(e: PointerEvent) {
  // Ignore when in readonly mode, right clicks, or events when in text-edit mode
  if (props.readonly || props.isEditing || e.button !== 0) return

  // Prevent default (text selection) and stop propagation so the scroll
  // workspace does NOT steal pointer capture away from us.
  e.preventDefault()
  e.stopPropagation()

  if (props.isCopyStyleActive) {
    emit('select', e)
    return
  }

  if (props.element.locked) {
    emit('select', e)
    return
  }

  const wasAlreadySelected = props.isSelected

  // If this element is NOT already selected, or if Shift key is pressed (multi-toggle mode),
  // select it immediately.
  // If it IS already selected and Shift is not pressed, DO NOT deselect other elements yet,
  // so that multi-element dragging works seamlessly!
  if (!wasAlreadySelected || e.shiftKey) {
    emit('select', e)
  }

  // Capture the pointer so pointermove events keep coming even when the
  // cursor moves outside the element or the browser window.
  ;(e.currentTarget as HTMLElement).setPointerCapture(e.pointerId)

  hasDragged.value = false

  const startClientX = e.clientX
  const startClientY = e.clientY
  const startX = props.element.x
  const startY = props.element.y
  const elW = props.element.width
  const elH = props.element.height

  // Small threshold so a simple click doesn't count as a drag
  const DRAG_THRESHOLD_PX = 3

  function onPointerMove(moveEvent: PointerEvent) {
    const deltaXpx = moveEvent.clientX - startClientX
    const deltaYpx = moveEvent.clientY - startClientY

    if (!hasDragged.value) {
      if (Math.abs(deltaXpx) < DRAG_THRESHOLD_PX && Math.abs(deltaYpx) < DRAG_THRESHOLD_PX) return
      hasDragged.value = true
      isDraggingLocal.value = true
      emit('drag:start')
    }

    const rawXmm = startX + pxToMm(deltaXpx)
    const rawYmm = startY + pxToMm(deltaYpx)

    let finalX = Math.max(0, Math.min(210 - elW, rawXmm))
    let finalY = Math.max(0, Math.min(297 - elH, rawYmm))

    if (props.calculateSnapping) {
      const snapped = props.calculateSnapping(finalX, finalY, elW, elH, props.element.id, false)
      finalX = snapped.x
      finalY = snapped.y
      emit('set-guides', snapped.guides, snapped.distanceGuides || [])
    }

    emit('update:bounds', {
      x: Math.round(finalX * 100) / 100,
      y: Math.round(finalY * 100) / 100,
      width: props.element.width,
      height: props.element.height,
      rotation: props.element.rotation,
    })
  }

  function onPointerUp(upEvent: PointerEvent) {
    window.removeEventListener('pointermove', onPointerMove)
    window.removeEventListener('pointerup', onPointerUp)
    if (hasDragged.value) {
      emit('set-guides', [], [])
      emit('drag:end')
    } else {
      // If was already selected and clicked without dragging, isolate selection to this element
      if (wasAlreadySelected && !upEvent.shiftKey) {
        emit('select', upEvent)
      }
    }
    isDraggingLocal.value = false
    hasDragged.value = false
  }

  window.addEventListener('pointermove', onPointerMove)
  window.addEventListener('pointerup', onPointerUp)
}

// --- Resize Logic with 8 Handles ---
function onResizePointerDown(handle: ResizeHandle, e: PointerEvent) {
  e.preventDefault()
  e.stopPropagation()

  if (props.element.locked) return

  // Capture the pointer so resize stays smooth even when cursor moves fast
  ;(e.currentTarget as HTMLElement).setPointerCapture(e.pointerId)

  emit('resize:start')

  const startClientX = e.clientX
  const startClientY = e.clientY
  const startX = props.element.x
  const startY = props.element.y
  const startW = props.element.width
  const startH = props.element.height
  const aspectRatio = startW / startH

  function onResizeMove(moveEvent: PointerEvent) {
    const deltaXmm = pxToMm(moveEvent.clientX - startClientX)
    const deltaYmm = pxToMm(moveEvent.clientY - startClientY)

    let newX = startX
    let newY = startY
    let newW = startW
    let newH = startH

    const MIN_SIZE_MM = 5

    if (handle.includes('e')) newW = Math.max(MIN_SIZE_MM, startW + deltaXmm)
    if (handle.includes('w')) {
      const candidateW = startW - deltaXmm
      if (candidateW >= MIN_SIZE_MM) { newW = candidateW; newX = startX + deltaXmm }
    }

    // Only non-text elements (tables, signatures, lines) allow manual height stretching.
    // Text elements automatically hug text height; width changes reflow text and update height dynamically.
    if (!isTextType.value) {
      if (handle.includes('s')) newH = Math.max(MIN_SIZE_MM, startH + deltaYmm)
      if (handle.includes('n')) {
        const candidateH = startH - deltaYmm
        if (candidateH >= MIN_SIZE_MM) { newH = candidateH; newY = startY + deltaYmm }
      }

      // Proportional resize when Shift held on corner handles
      if (moveEvent.shiftKey && (handle === 'nw' || handle === 'ne' || handle === 'se' || handle === 'sw')) {
        newH = newW / aspectRatio
      }
    }

    // --- Resize Snapping ---
    // Each handle moves a specific edge. We probe that edge's position with a
    // near-zero-size element so calculateSnapping only fires for that edge.
    // PROBE = tiny width/height so all three checks (left, center, right) in
    // calculateSnapping converge to essentially the same point.
    if (props.calculateSnapping) {
      const snapGuides: AlignmentGuide[] = []
      const id = props.element.id
      const PROBE = 0.001 // mm — effectively a point probe

      // East handle: snap right edge → adjust width (x stays fixed)
      // Pass actual height (not PROBE) so the guide spans the full element height.
      if (handle.includes('e') && !handle.includes('w')) {
        const r = props.calculateSnapping(newX + newW, newY, PROBE, newH, id, true)
        newW = Math.max(MIN_SIZE_MM, r.x - newX)
        snapGuides.push(...r.guides)
      }

      // West handle: snap left edge → adjust x and width (right edge stays fixed)
      if (handle.includes('w') && !handle.includes('e')) {
        const r = props.calculateSnapping(newX, newY, PROBE, newH, id, true)
        newX = r.x
        newW = Math.max(MIN_SIZE_MM, (startX + startW) - r.x)
        snapGuides.push(...r.guides)
      }

      // South handle: snap bottom edge → adjust height (y stays fixed)
      if (!isTextType.value && handle.includes('s') && !handle.includes('n')) {
        const r = props.calculateSnapping(newX, newY + newH, newW, PROBE, id, true)
        newH = Math.max(MIN_SIZE_MM, r.y - newY)
        snapGuides.push(...r.guides)
      }

      // North handle: snap top edge → adjust y and height (bottom edge stays fixed)
      if (!isTextType.value && handle.includes('n') && !handle.includes('s')) {
        const r = props.calculateSnapping(newX, newY, newW, PROBE, id, true)
        newY = r.y
        newH = Math.max(MIN_SIZE_MM, (startY + startH) - r.y)
        snapGuides.push(...r.guides)
      }

      emit('set-guides', snapGuides, [])
    }

    emit('update:bounds', {
      x: Math.round(newX * 100) / 100,
      y: Math.round(newY * 100) / 100,
      width: Math.round(newW * 100) / 100,
      height: Math.round(newH * 100) / 100,
      rotation: props.element.rotation,
    })
  }

  function onResizeUp() {
    window.removeEventListener('pointermove', onResizeMove)
    window.removeEventListener('pointerup', onResizeUp)
    emit('set-guides', [], []) // clear snap guides on release
    emit('resize:end')
  }

  window.addEventListener('pointermove', onResizeMove)
  window.addEventListener('pointerup', onResizeUp)
}

function onDoubleClick(e: MouseEvent) {
  if (props.readonly || props.element.locked) return
  e.stopPropagation()
  emit('double-click')
}
</script>

<template>
  <div
    class="canvas-element-wrapper absolute top-0 left-0 select-none group"
    :class="[
      readonly ? 'cursor-default' : isEditing ? 'cursor-text' : element.locked ? 'cursor-not-allowed' : 'cursor-move',
      !readonly && !isSelected && !isEditing ? 'hover:outline hover:outline-1 hover:outline-[#7c3aed]/40' : ''
    ]"
    :style="wrapperStyle"
    @pointerdown="onPointerDown"
    @dblclick="onDoubleClick"
    @click.stop
  >
    <!-- Element Body Content Slot -->
    <div
      class="canvas-element-content w-full h-full relative"
      :class="{ 'pointer-events-auto': isEditing, 'pointer-events-none': !readonly && !isEditing && isSelected }"
    >
      <slot />
    </div>

    <!-- Canva Single Bounding Box & Handles (Only ONE transform box, matching Canva 1-to-1) -->
    <template v-if="!readonly && (isSelected || isEditing)">
      <!-- Canva Signature Single Bounding Line (#7c3aed) -->
      <div
        class="absolute -inset-0.5 border-[1.5px] border-[#7c3aed] pointer-events-none rounded-[1px] z-30"
        :class="{ 'border-dashed border-amber-500': element.locked }"
      ></div>

      <!-- Quick Floating Action Bar (Always visible when selected or editing) -->
      <div
        class="absolute bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-700 shadow-xl rounded-xl px-1.5 py-0.5 flex items-center gap-0.5 z-[100] text-zinc-600 dark:text-zinc-300 text-xs pointer-events-auto whitespace-nowrap opacity-100 select-none ring-1 ring-black/5 dark:ring-white/10"
        :class="toolbarPositionClass"
        :style="{
          transform: `scale(${counterScale})`,
          transformOrigin: isNearTop ? 'top center' : 'bottom center',
        }"
        @pointerdown.stop.prevent
      >
        <!-- Coordinates & Dimensions Badge -->
        <span class="px-1.5 py-0.5 font-mono text-[10px] text-zinc-400 font-bold border-r border-zinc-200 dark:border-zinc-700 mr-0.5">
          {{ Math.round(element.x) }}×{{ Math.round(element.y) }}mm
        </span>

        <!-- Edit Text / Label (for Text and Checkbox) -->
        <button
          v-if="element.type === 'text' || element.type === 'checkbox'"
          type="button"
          @click.stop="emit('double-click')"
          class="p-1 rounded-lg text-xs transition-colors"
          :class="isEditing ? 'bg-blue-600 text-white shadow-xs' : 'hover:bg-blue-50 dark:hover:bg-blue-950/60 text-blue-600 dark:text-blue-400'"
          :title="isEditing ? 'Tahrirlashni yakunlash (Double-click)' : 'Matnni tahrirlash (Double-click)'"
        >
          <Type class="w-3.5 h-3.5" />
        </button>

        <!-- Canva Copy Style Button -->
        <button
          v-if="isTextType"
          type="button"
          @click.stop="emit('copy-style', $event)"
          class="p-1 rounded-lg text-xs transition-colors relative"
          :class="isCopyStyleActive ? 'bg-blue-600 text-white shadow-xs' : 'hover:bg-zinc-100 dark:hover:bg-zinc-800 text-zinc-600 dark:text-zinc-300'"
          title="Uslubdan nusxa olish (Copy Style) — 1 marta bosish (bitta uchun) yoki 2 marta bosish (ko'p martalik) • Ctrl+Alt+C"
        >
          <PaintRoller class="w-3.5 h-3.5" />
          <span v-if="copyStyleMode === 'persistent'" class="absolute -top-0.5 -right-0.5 w-1.5 h-1.5 rounded-full bg-amber-400"></span>
        </button>

        <!-- Canva Spacing Button & Popover (Letter Spacing & Line Spacing) -->
        <div v-if="isTextType" class="relative">
          <button
            type="button"
            @click.stop="showSpacingPopover = !showSpacingPopover"
            class="p-1 rounded-lg text-xs transition-colors"
            :class="showSpacingPopover ? 'bg-blue-100 dark:bg-blue-950/60 text-blue-600 dark:text-blue-400' : 'hover:bg-zinc-100 dark:hover:bg-zinc-800 text-zinc-600 dark:text-zinc-300'"
            title="Oraliqlar: Qatorlar va Harflar oralig'i (Canva Spacing)"
          >
            <!-- Canva Spacing Icon -->
            <svg class="w-3.5 h-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M4 6h11" />
              <path d="M4 12h11" />
              <path d="M4 18h11" />
              <path d="M19 6v12" />
              <path d="m16.5 8.5 2.5-2.5 2.5 2.5" />
              <path d="m16.5 15.5 2.5 2.5 2.5 2.5" />
            </svg>
          </button>

          <!-- Floating Spacing Popover -->
          <div
            v-if="showSpacingPopover"
            class="absolute top-full left-1/2 -translate-x-1/2 mt-2 w-64 bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-700 shadow-2xl rounded-2xl p-3.5 z-[150] space-y-3.5 select-none ring-1 ring-black/5 dark:ring-white/10"
            @pointerdown.stop.prevent
            @click.stop
          >
            <div class="flex items-center justify-between pb-1.5 border-b border-zinc-100 dark:border-zinc-800">
              <span class="text-xs font-bold text-zinc-800 dark:text-zinc-100">Oraliqlar (Spacing)</span>
              <span class="text-[10px] text-zinc-400 font-mono font-semibold">Canva</span>
            </div>

            <!-- Letter Spacing -->
            <div class="space-y-1.5">
              <div class="flex items-center justify-between text-xs">
                <span class="font-medium text-zinc-700 dark:text-zinc-300">Harflar oralig'i</span>
                <div class="flex items-center gap-1">
                  <input
                    type="number"
                    step="0.5"
                    min="-3"
                    max="25"
                    :value="currentLetterSpacing"
                    @input="setLetterSpacing(($event.target as HTMLInputElement).value)"
                    class="w-14 h-6 px-1 text-right text-xs font-mono font-bold bg-zinc-100 dark:bg-zinc-800 border border-zinc-200 dark:border-zinc-700 rounded-md focus:outline-none focus:ring-1 focus:ring-blue-500"
                  />
                  <span class="text-[10px] text-zinc-400">px</span>
                </div>
              </div>
              <input
                type="range"
                min="-2"
                max="20"
                step="0.5"
                :value="currentLetterSpacing"
                @input="setLetterSpacing(($event.target as HTMLInputElement).value)"
                class="w-full accent-blue-600 h-1.5 bg-zinc-200 dark:bg-zinc-700 rounded-lg cursor-pointer"
              />
            </div>

            <!-- Line Spacing -->
            <div class="space-y-1.5">
              <div class="flex items-center justify-between text-xs">
                <span class="font-medium text-zinc-700 dark:text-zinc-300">Qatorlar oralig'i</span>
                <div class="flex items-center gap-1">
                  <input
                    type="number"
                    step="0.05"
                    min="0.8"
                    max="3.0"
                    :value="currentLineHeight"
                    @input="setLineHeight(($event.target as HTMLInputElement).value)"
                    class="w-14 h-6 px-1 text-right text-xs font-mono font-bold bg-zinc-100 dark:bg-zinc-800 border border-zinc-200 dark:border-zinc-700 rounded-md focus:outline-none focus:ring-1 focus:ring-blue-500"
                  />
                </div>
              </div>
              <input
                type="range"
                min="0.8"
                max="2.8"
                step="0.05"
                :value="currentLineHeight"
                @input="setLineHeight(($event.target as HTMLInputElement).value)"
                class="w-full accent-blue-600 h-1.5 bg-zinc-200 dark:bg-zinc-700 rounded-lg cursor-pointer"
              />
            </div>

            <!-- Presets -->
            <div class="pt-2 border-t border-zinc-100 dark:border-zinc-800 flex items-center justify-between text-[10px]">
              <span class="text-zinc-400">Shablon:</span>
              <div class="flex items-center gap-1">
                <button
                  type="button"
                  @click="setLineHeight(1.15); setLetterSpacing(0)"
                  class="px-1.5 py-0.5 rounded bg-zinc-100 dark:bg-zinc-800 hover:bg-zinc-200 dark:hover:bg-zinc-700 text-zinc-600 dark:text-zinc-300 font-medium"
                >
                  Zich (1.15)
                </button>
                <button
                  type="button"
                  @click="setLineHeight(1.5); setLetterSpacing(0)"
                  class="px-1.5 py-0.5 rounded bg-zinc-100 dark:bg-zinc-800 hover:bg-zinc-200 dark:hover:bg-zinc-700 text-zinc-600 dark:text-zinc-300 font-medium"
                >
                  Standart (1.5)
                </button>
                <button
                  type="button"
                  @click="setLineHeight(1.8); setLetterSpacing(0.5)"
                  class="px-1.5 py-0.5 rounded bg-zinc-100 dark:bg-zinc-800 hover:bg-zinc-200 dark:hover:bg-zinc-700 text-zinc-600 dark:text-zinc-300 font-medium"
                >
                  Keng (1.8)
                </button>
              </div>
            </div>
          </div>
        </div>

        <!-- Duplicate -->
        <button
          type="button"
          @click.stop="emit('duplicate')"
          class="p-1 hover:bg-zinc-100 dark:hover:bg-zinc-800 rounded-lg text-zinc-600 dark:text-zinc-300"
          title="Duplicate (Ctrl+D)"
        >
          <Copy class="w-3.5 h-3.5" />
        </button>

        <!-- Bring Forward -->
        <button
          type="button"
          @click.stop="emit('bring-forward')"
          class="p-1 hover:bg-zinc-100 dark:hover:bg-zinc-800 rounded-lg text-zinc-600 dark:text-zinc-300"
          title="Bring Forward"
        >
          <ArrowUp class="w-3.5 h-3.5" />
        </button>

        <!-- Send Backward -->
        <button
          type="button"
          @click.stop="emit('send-backward')"
          class="p-1 hover:bg-zinc-100 dark:hover:bg-zinc-800 rounded-lg text-zinc-600 dark:text-zinc-300"
          title="Send Backward"
        >
          <ArrowDown class="w-3.5 h-3.5" />
        </button>

        <!-- Lock / Unlock -->
        <button
          type="button"
          @click.stop="emit('toggle-lock')"
          class="p-1 hover:bg-zinc-100 dark:hover:bg-zinc-800 rounded-lg"
          :class="element.locked ? 'text-amber-500 font-bold' : 'text-zinc-600 dark:text-zinc-300'"
          :title="element.locked ? 'Unlock element' : 'Lock element'"
        >
          <Lock v-if="element.locked" class="w-3.5 h-3.5" />
          <Unlock v-else class="w-3.5 h-3.5" />
        </button>

        <!-- Delete -->
        <button
          type="button"
          @click.stop="emit('delete')"
          class="p-1 hover:bg-rose-50 text-rose-600 rounded-lg"
          title="Delete (Del)"
        >
          <Trash2 class="w-3.5 h-3.5" />
        </button>
      </div>

      <!-- Canva Resize Handles (Circles on 4 corners, Pills on left/right edges) -->
      <template v-if="!element.locked">
        <!-- NW Corner Circle -->
        <div
          class="resize-handle nw absolute -top-1.5 -left-1.5 w-2.5 h-2.5 bg-white border-[1.5px] border-[#7c3aed] rounded-full shadow-xs cursor-nwse-resize z-40 hover:scale-125 transition-transform"
          :style="{ transform: `scale(${handleScale})` }"
          @pointerdown="onResizePointerDown('nw', $event)"
        ></div>

        <!-- NE Corner Circle -->
        <div
          class="resize-handle ne absolute -top-1.5 -right-1.5 w-2.5 h-2.5 bg-white border-[1.5px] border-[#7c3aed] rounded-full shadow-xs cursor-nesw-resize z-40 hover:scale-125 transition-transform"
          :style="{ transform: `scale(${handleScale})` }"
          @pointerdown="onResizePointerDown('ne', $event)"
        ></div>

        <!-- SE Corner Circle -->
        <div
          class="resize-handle se absolute -bottom-1.5 -right-1.5 w-2.5 h-2.5 bg-white border-[1.5px] border-[#7c3aed] rounded-full shadow-xs cursor-nwse-resize z-40 hover:scale-125 transition-transform"
          :style="{ transform: `scale(${handleScale})` }"
          @pointerdown="onResizePointerDown('se', $event)"
        ></div>

        <!-- SW Corner Circle -->
        <div
          class="resize-handle sw absolute -bottom-1.5 -left-1.5 w-2.5 h-2.5 bg-white border-[1.5px] border-[#7c3aed] rounded-full shadow-xs cursor-nesw-resize z-40 hover:scale-125 transition-transform"
          :style="{ transform: `scale(${handleScale})` }"
          @pointerdown="onResizePointerDown('sw', $event)"
        ></div>

        <!-- Left Edge Vertical Pill Handle -->
        <div
          class="resize-handle w absolute top-1/2 -left-1 -translate-y-1/2 w-1.5 h-4 bg-white border-[1.5px] border-[#7c3aed] rounded-full shadow-xs cursor-ew-resize z-40 hover:scale-110 transition-transform"
          :style="{ transform: `scale(${handleScale})` }"
          @pointerdown="onResizePointerDown('w', $event)"
        ></div>

        <!-- Right Edge Vertical Pill Handle -->
        <div
          class="resize-handle e absolute top-1/2 -right-1 -translate-y-1/2 w-1.5 h-4 bg-white border-[1.5px] border-[#7c3aed] rounded-full shadow-xs cursor-ew-resize z-40 hover:scale-110 transition-transform"
          :style="{ transform: `scale(${handleScale})` }"
          @pointerdown="onResizePointerDown('e', $event)"
        ></div>

        <!-- Top & Bottom Pills (for non-text elements e.g. table) -->
        <template v-if="!isTextType">
          <div
            class="resize-handle n absolute -top-1 left-1/2 -translate-x-1/2 w-4 h-1.5 bg-white border-[1.5px] border-[#7c3aed] rounded-full shadow-xs cursor-ns-resize z-40 hover:scale-110 transition-transform"
            :style="{ transform: `scale(${handleScale})` }"
            @pointerdown="onResizePointerDown('n', $event)"
          ></div>
          <div
            class="resize-handle s absolute -bottom-1 left-1/2 -translate-x-1/2 w-4 h-1.5 bg-white border-[1.5px] border-[#7c3aed] rounded-full shadow-xs cursor-ns-resize z-40 hover:scale-110 transition-transform"
            :style="{ transform: `scale(${handleScale})` }"
            @pointerdown="onResizePointerDown('s', $event)"
          ></div>
        </template>
      </template>
    </template>
  </div>
</template>

<style scoped>
.animate-scale-in {
  animation: scaleIn 0.12s ease-out;
}
@keyframes scaleIn {
  from {
    opacity: 0;
    transform: translate(-50%, 4px) scale(0.95);
  }
  to {
    opacity: 1;
    transform: translate(-50%, 0) scale(1);
  }
}
</style>
