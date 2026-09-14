<script setup lang="ts">
import { ref, computed } from 'vue'
import type {
  CanvasPageModel,
  CanvasElement,
  PageMargins,
  AlignmentGuide,
} from '../../types/contractCanvas'
import { Copy, Trash2 } from 'lucide-vue-next'
import CanvasRuler from './CanvasRuler.vue'
import CanvasSmartGuides from './CanvasSmartGuides.vue'
import CanvasMarqueeSelect from './CanvasMarqueeSelect.vue'
import CanvasElementWrapper from './CanvasElementWrapper.vue'
import CanvasTextElement from './CanvasTextElement.vue'
import CanvasTableElement from './CanvasTableElement.vue'
import CanvasSignatureElement from './CanvasSignatureElement.vue'
import CanvasLineElement from './CanvasLineElement.vue'
import CanvasCheckboxElement from './CanvasCheckboxElement.vue'

const props = withDefaults(
  defineProps<{
    page: CanvasPageModel
    pageIndex: number
    totalPages: number
    margins: PageMargins
    zoomLevel: number
    selectedElementIds: string[]
    editingElementId: string | null
    showMarginGuides: boolean
    showRulers: boolean
    showGrid: boolean
    activeGuides: AlignmentGuide[]
    readonly?: boolean
    variableValues?: Record<string, string>
    isActivePage?: boolean
    calculateSnapping?: (
      x: number,
      y: number,
      w: number,
      h: number,
      id: string
    ) => { x: number; y: number; guides: AlignmentGuide[] }
  }>(),
  {
    readonly: false,
  }
)

const emit = defineEmits<{
  'select-element': [id: string, multi: boolean]
  'select-elements': [ids: string[]]
  'set-active-page': [pageIndex: number]
  'clear-selection': []
  'double-click-element': [id: string]
  'update-element': [id: string, updates: Partial<CanvasElement>]
  'update-element-bounds': [id: string, bounds: { x: number; y: number; width: number; height: number; rotation?: number }]
  'duplicate-element': [id: string]
  'delete-element': [id: string]
  'toggle-lock': [id: string]
  'bring-forward': [id: string]
  'send-backward': [id: string]
  'set-guides': [guides: AlignmentGuide[]]
  'finish-edit': [id: string]
  'drag-end': []
  'resize-end': []
  'duplicate-page': [pageIndex: number]
  'delete-page': [pageIndex: number]
}>()

const MM_TO_PX_BASE = 3.779527559
const PAGE_WIDTH_MM = 210
const PAGE_HEIGHT_MM = 297

function mmToPx(mm: number): number {
  return mm * MM_TO_PX_BASE * (props.zoomLevel / 100)
}

function pxToMm(px: number): number {
  return px / (MM_TO_PX_BASE * (props.zoomLevel / 100))
}

const scaledPageWidthPx = computed(() => mmToPx(PAGE_WIDTH_MM))
const scaledPageHeightPx = computed(() => mmToPx(PAGE_HEIGHT_MM))

// Ref to the physical A4 sheet DOM element — needed for marquee coordinate math
const sheetRef = ref<HTMLElement | null>(null)

// ─── Marquee (Rubber-Band) Selection State ───────────────────────────────────
type MarqueeRect = { x: number; y: number; width: number; height: number }
const marqueeRect = ref<MarqueeRect | null>(null)
const marqueeActive = ref(false)

// Guard flag: when a marquee drag finishes the browser fires a 'click' event
// on the sheet which would immediately call onCanvasClick → clear-selection,
// wiping the freshly-made selection. We set this flag in onPointerUp when a
// real drag occurred, then check and reset it in onCanvasClick.
let marqueeJustFinished = false

/**
 * Left-mouse-button pointerdown on the A4 sheet background starts a marquee drag.
 * Only activates when the pointer lands on the bare sheet background — element
 * wrappers call e.stopPropagation() so their own pointerdown never reaches here.
 *
 * Edge cases handled:
 *  - button !== 0 guard: only left-click triggers marquee.
 *  - Extra target check: belt-and-suspenders guard for elements that may not
 *    stopPropagation (resize handles, contenteditable regions).
 *  - Text-edit guard: aborts if any element is in text-edit mode so the caret
 *    is never disrupted.
 *  - 4 px drag threshold: prevents a plain click from flickering the rect.
 *  - marqueeJustFinished flag: blocks the subsequent 'click' event from
 *    clearing the marquee selection in onCanvasClick.
 */
function onSheetPointerDown(e: PointerEvent) {
  // Abort if in readonly mode or not left mouse button
  if (props.readonly || e.button !== 0) return

  // Belt-and-suspenders: abort if the click actually landed on an element
  const target = e.target as HTMLElement
  if (
    target.closest('.canvas-element-wrapper') ||
    target.closest('.resize-handle') ||
    target.closest('[contenteditable="true"]')
  ) return

  // Abort while any element is in text-edit mode
  if (props.editingElementId !== null) return

  e.preventDefault()
  e.stopPropagation()
  emit('set-active-page', props.pageIndex)

  const sheet = sheetRef.value
  if (!sheet) return

  const sheetRect = sheet.getBoundingClientRect()
  const startX = e.clientX - sheetRect.left
  const startY = e.clientY - sheetRect.top

  let hasMoved = false
  const DRAG_THRESHOLD_PX = 4

  // Capture the pointer so pointermove/pointerup keep arriving even when
  // the cursor leaves the sheet or the browser window.
  sheet.setPointerCapture(e.pointerId)

  function onPointerMove(ev: PointerEvent) {
    const curX = ev.clientX - sheetRect.left
    const curY = ev.clientY - sheetRect.top

    if (!hasMoved) {
      const dx = Math.abs(curX - startX)
      const dy = Math.abs(curY - startY)
      if (dx < DRAG_THRESHOLD_PX && dy < DRAG_THRESHOLD_PX) return
      hasMoved = true
      marqueeActive.value = true
      // Clear existing selection when a fresh marquee drag starts
      emit('clear-selection')
    }

    // Build a normalised rect (always positive width/height)
    const x = Math.min(startX, curX)
    const y = Math.min(startY, curY)
    const width = Math.abs(curX - startX)
    const height = Math.abs(curY - startY)

    // Clamp to sheet bounds so the rect never overflows the page
    marqueeRect.value = {
      x: Math.max(0, x),
      y: Math.max(0, y),
      width: Math.min(width, scaledPageWidthPx.value - Math.max(0, x)),
      height: Math.min(height, scaledPageHeightPx.value - Math.max(0, y)),
    }
  }

  function onPointerUp() {
    sheet?.removeEventListener('pointermove', onPointerMove)
    sheet?.removeEventListener('pointerup', onPointerUp)

    if (hasMoved && marqueeRect.value) {
      selectElementsInMarquee(marqueeRect.value)
      // Set the guard so the imminent 'click' event does not clear the selection
      marqueeJustFinished = true
    }

    marqueeRect.value = null
    marqueeActive.value = false
  }

  sheet.addEventListener('pointermove', onPointerMove)
  sheet.addEventListener('pointerup', onPointerUp)
}

/**
 * Given a marquee rect (in sheet-relative px), find all page elements whose
 * bounding box overlaps the rect and emit a bulk selection event.
 *
 * Overlap test: two rects overlap iff neither is entirely to the side / above /
 * below the other.  We use the mm-domain to avoid repeated px↔mm round-trips.
 */
function selectElementsInMarquee(rect: MarqueeRect) {
  // Convert marquee from px to mm (sheet-relative)
  const mLeft   = pxToMm(rect.x)
  const mTop    = pxToMm(rect.y)
  const mRight  = pxToMm(rect.x + rect.width)
  const mBottom = pxToMm(rect.y + rect.height)

  const matched: string[] = []

  for (const el of props.page.elements) {
    if (el.hidden) continue

    const elRight  = el.x + el.width
    const elBottom = el.y + el.height

    // AABB overlap: not (left of | right of | above | below)
    const overlaps =
      mLeft   < elRight  &&
      mRight  > el.x     &&
      mTop    < elBottom &&
      mBottom > el.y

    if (overlaps) matched.push(el.id)
  }

  if (matched.length > 0) {
    emit('select-elements', matched)
  }
}

// Cursor tracking for rulers
const cursorXmm = ref<number>(-1)
const cursorYmm = ref<number>(-1)

function onCanvasPointerMove(e: PointerEvent) {
  const rect = (e.currentTarget as HTMLElement).getBoundingClientRect()
  const relXpx = e.clientX - rect.left
  const relYpx = e.clientY - rect.top
  cursorXmm.value = relXpx / (MM_TO_PX_BASE * (props.zoomLevel / 100))
  cursorYmm.value = relYpx / (MM_TO_PX_BASE * (props.zoomLevel / 100))
}

function onCanvasPointerLeave() {
  cursorXmm.value = -1
  cursorYmm.value = -1
}

function onCanvasClick(e: MouseEvent) {
  emit('set-active-page', props.pageIndex)
  // If clicked directly on the page background (not on an element)
  if ((e.target as HTMLElement).classList.contains('canvas-sheet-background')) {
    // Skip clear-selection if this click is the synthetic click event that
    // the browser fires at the end of a marquee drag — we just selected elements
    // and must NOT wipe them immediately.
    if (marqueeJustFinished) {
      marqueeJustFinished = false
      ;(e.target as HTMLElement).focus()
      return
    }
    emit('clear-selection')
    ;(e.target as HTMLElement).focus()
  }
}

function confirmDeletePage() {
  if (props.totalPages <= 1) return
  if (props.page.elements && props.page.elements.length > 0) {
    if (!window.confirm(`${props.page.pageNumber}-sahifani va undagi barcha ma'lumotlarni o'chirib yubormoqchimisiz?`)) {
      return
    }
  }
  emit('delete-page', props.pageIndex)
}
</script>

<template>
  <div
    class="canvas-a4-page-container flex flex-col items-center select-none my-6"
    :data-page-index="pageIndex"
    @pointerdown="emit('set-active-page', pageIndex)"
  >
    <!-- Page Header Label & Actions -->
    <div
      class="page-meta-header flex items-center justify-between pb-2 mb-2 text-zinc-400 font-sans text-[11px] select-none transition-colors"
      :style="{ width: `${scaledPageWidthPx + (showRulers ? 20 : 0)}px` }"
    >
      <!-- Left: Page Number -->
      <div class="flex items-center gap-2">
        <span
          class="w-2 h-2 rounded-full inline-block transition-all"
          :class="isActivePage ? 'bg-blue-600 ring-4 ring-blue-500/20 shadow-xs' : 'bg-zinc-400 dark:bg-zinc-600'"
        ></span>
        <span
          class="font-bold tracking-wider uppercase transition-colors"
          :class="isActivePage ? 'text-blue-600 dark:text-blue-400' : 'text-zinc-600 dark:text-zinc-400'"
        >
          PAGE {{ page.pageNumber }}/{{ totalPages }}
        </span>
      </div>

      <!-- Right: Duplicate & Delete Page Actions (Icon-only) -->
      <div v-if="!readonly" class="flex items-center gap-0.5 bg-white/95 dark:bg-zinc-800/95 backdrop-blur-xs border border-zinc-200/90 dark:border-zinc-700/80 rounded-xl p-0.5 shadow-2xs">
        <button
          type="button"
          class="w-6 h-6 rounded-lg flex items-center justify-center text-zinc-500 dark:text-zinc-400 hover:text-blue-600 dark:hover:text-blue-400 hover:bg-blue-50 dark:hover:bg-zinc-700 active:scale-95 transition-all cursor-pointer select-none"
          title="Sahifani nusxalash (Dublikat)"
          @click.stop="emit('duplicate-page', pageIndex)"
        >
          <Copy class="w-3.5 h-3.5 text-blue-500" />
        </button>

        <div class="w-px h-3 bg-zinc-200 dark:bg-zinc-700"></div>

        <button
          type="button"
          class="w-6 h-6 rounded-lg flex items-center justify-center text-zinc-500 dark:text-zinc-400 hover:text-rose-600 dark:hover:text-rose-400 hover:bg-rose-50 dark:hover:bg-zinc-700 active:scale-95 transition-all cursor-pointer select-none disabled:opacity-30 disabled:cursor-not-allowed"
          :disabled="totalPages <= 1"
          :title="totalPages <= 1 ? 'Kamida 1 ta sahifa bo\'lishi shart' : 'Sahifani o\'chirish'"
          @click.stop="confirmDeletePage"
        >
          <Trash2 class="w-3.5 h-3.5 text-rose-500" />
        </button>
      </div>
    </div>

    <!-- Sheet Wrapper with Rulers: [corner+vert] | [horiz+sheet] -->
    <div class="flex items-start">
      <!-- Left column: corner box + vertical ruler -->
      <div v-if="!readonly && showRulers" class="flex flex-col shrink-0">
        <!-- Corner box at ruler intersection -->
        <div class="ruler-corner" style="width:22px;height:22px" />
        <!-- Vertical ruler -->
        <CanvasRuler
          orientation="vertical"
          :length-mm="PAGE_HEIGHT_MM"
          :zoom-level="zoomLevel"
          :cursor-pos-mm="cursorYmm"
          :margin-start="margins.top"
          :margin-end="margins.bottom"
        />
      </div>

      <!-- Right column: horizontal ruler + A4 sheet -->
      <div class="flex flex-col">
        <!-- Top Ruler -->
        <CanvasRuler
          v-if="!readonly && showRulers"
          orientation="horizontal"
          :length-mm="PAGE_WIDTH_MM"
          :zoom-level="zoomLevel"
          :cursor-pos-mm="cursorXmm"
          :margin-start="margins.left"
          :margin-end="margins.right"
        />

        <!-- The Physical A4 Sheet -->
        <div
          ref="sheetRef"
          class="canvas-sheet-background relative bg-white text-zinc-900 shadow-2xl border border-zinc-300/80 dark:border-zinc-700/60 transition-shadow overflow-hidden outline-none focus:outline-none"
          tabindex="0"
          :style="{
            width: `${scaledPageWidthPx}px`,
            height: `${scaledPageHeightPx}px`,
            fontFamily: `'Times New Roman', Times, serif`,
            cursor: !readonly && marqueeActive ? 'crosshair' : 'default',
          }"
          @pointermove="onCanvasPointerMove"
          @pointerleave="onCanvasPointerLeave"
          @click="onCanvasClick"
          @pointerdown="onSheetPointerDown"
        >
          <!-- Grid Background (if enabled) -->
          <div
            v-if="!readonly && showGrid"
            class="absolute inset-0 pointer-events-none opacity-30"
            :style="{
              backgroundImage: 'radial-gradient(#3b82f6 0.75px, transparent 0.75px)',
              backgroundSize: `${mmToPx(5)}px ${mmToPx(5)}px`,
            }"
          ></div>

          <!-- Margin Guide Dashed Lines & Crop Corners (if enabled) -->
          <div
            v-if="!readonly && showMarginGuides"
            class="margin-guide-overlay pointer-events-none select-none absolute no-print"
            :style="{
              top: `${mmToPx(margins.top)}px`,
              left: `${mmToPx(margins.left)}px`,
              right: `${mmToPx(margins.right)}px`,
              bottom: `${mmToPx(margins.bottom)}px`,
            }"
            aria-hidden="true"
          >
            <!-- Corner Crop Marks -->
            <div class="absolute -top-2.5 -left-2.5 w-3 h-3 border-t-2 border-l-2 border-blue-500/80 z-20"></div>
            <div class="absolute -top-2.5 -right-2.5 w-3 h-3 border-t-2 border-r-2 border-blue-500/80 z-20"></div>
            <div class="absolute -bottom-2.5 -left-2.5 w-3 h-3 border-b-2 border-l-2 border-blue-500/80 z-20"></div>
            <div class="absolute -bottom-2.5 -right-2.5 w-3 h-3 border-b-2 border-r-2 border-blue-500/80 z-20"></div>

            <!-- Dashed Printable Boundary Rect -->
            <div class="absolute inset-0 border border-dashed border-blue-400/35 rounded-[1px] z-10"></div>
          </div>

          <!-- Smart Alignment Guides Overlay -->
          <CanvasSmartGuides v-if="!readonly" :guides="activeGuides" :zoom-level="zoomLevel" />

          <!-- Marquee Selection Overlay -->
          <CanvasMarqueeSelect
            v-if="!readonly && marqueeRect"
            :x="marqueeRect.x"
            :y="marqueeRect.y"
            :width="marqueeRect.width"
            :height="marqueeRect.height"
          />

          <!-- Render All Elements on this Page -->
          <CanvasElementWrapper
            v-for="el in page.elements"
            :key="el.id"
            :element="el"
            :readonly="readonly"
            :is-selected="!readonly && selectedElementIds.includes(el.id)"
            :is-editing="!readonly && editingElementId === el.id"
            :zoom-level="zoomLevel"
            :calculate-snapping="calculateSnapping"
            @select="emit('set-active-page', pageIndex); emit('select-element', el.id, $event.shiftKey)"
            @double-click="emit('double-click-element', el.id)"
            @update:bounds="emit('update-element-bounds', el.id, $event)"
            @duplicate="emit('duplicate-element', el.id)"
            @delete="emit('delete-element', el.id)"
            @toggle-lock="emit('toggle-lock', el.id)"
            @bring-forward="emit('bring-forward', el.id)"
            @send-backward="emit('send-backward', el.id)"
            @set-guides="emit('set-guides', $event)"
            @drag:end="emit('drag-end')"
            @resize:end="emit('resize-end')"
          >
            <!-- Text / Heading -->
            <CanvasTextElement
              v-if="el.type === 'text' || el.type === 'heading' || el.type === 'paragraph' || el.type === 'date' || el.type === 'variable'"
              :element="el as any"
              :is-editing="editingElementId === el.id"
              :zoom-level="zoomLevel"
              :variable-values="variableValues"
              @update:content="emit('update-element', el.id, { content: $event })"
              @finish-edit="emit('finish-edit', el.id)"
              @auto-resize-height="emit('update-element-bounds', el.id, { x: el.x, y: el.y, width: el.width, height: $event })"
            />

            <!-- Table -->
            <CanvasTableElement
              v-else-if="el.type === 'table'"
              :element="el as any"
              :is-selected="selectedElementIds.includes(el.id)"
              :is-editing="editingElementId === el.id"
              :zoom-level="zoomLevel"
              :variable-values="variableValues"
              @update:element="emit('update-element', el.id, $event)"
              @update:cell="(r, c, val) => {
                const cells = [...(el as any).cells]
                cells[r][c].content = val
                emit('update-element', el.id, { cells })
              }"
            />

            <!-- Signature -->
            <CanvasSignatureElement
              v-else-if="el.type === 'signature'"
              :element="el as any"
              :is-selected="selectedElementIds.includes(el.id)"
              :zoom-level="zoomLevel"
              :variable-values="variableValues"
            />

            <!-- Line -->
            <CanvasLineElement
              v-else-if="el.type === 'line'"
              :element="el as any"
              :zoom-level="zoomLevel"
            />

            <!-- Checkbox -->
            <CanvasCheckboxElement
              v-else-if="el.type === 'checkbox'"
              :element="el as any"
              :zoom-level="zoomLevel"
              @update:checked="emit('update-element', el.id, { checked: $event })"
            />
          </CanvasElementWrapper>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.canvas-sheet-background {
  font-family: 'Times New Roman', Times, Georgia, serif !important;
}

/* Corner box at the ruler intersection (top-left) */
.ruler-corner {
  background: #f0f1f4;
  border-right: 1px solid #e2e4e9;
  border-bottom: 1px solid #e2e4e9;
  flex-shrink: 0;
}
:global(.dark) .ruler-corner {
  background: #18181b;
  border-right-color: #27272a;
  border-bottom-color: #27272a;
}
</style>
