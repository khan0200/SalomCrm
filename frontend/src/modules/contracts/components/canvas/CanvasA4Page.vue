<script setup lang="ts">
import { ref, computed } from 'vue'
import type {
  CanvasPageModel,
  CanvasElement,
  PageMargins,
  AlignmentGuide,
  DistanceGuide,
} from '../../types/contractCanvas'
import { Copy, Trash2 } from 'lucide-vue-next'
import CanvasRuler from './CanvasRuler.vue'
import CanvasSmartGuides from './CanvasSmartGuides.vue'
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
    activeDistanceGuides?: DistanceGuide[]
    readonly?: boolean
    variableValues?: Record<string, string>
    isActivePage?: boolean
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
    // Marquee (rubber-band) selection now lives at the workspace level (see
    // ContractDocumentEditor.vue) so a drag can start outside any single page
    // and span multiple pages. This callback lets this page's own background
    // click-to-clear-selection handler check "did a marquee drag just end?"
    // before wiping the selection the workspace just made.
    consumeMarqueeGuard?: () => boolean
  }>(),
  {
    readonly: false,
    isCopyStyleActive: false,
    copyStyleMode: null,
  }
)

const emit = defineEmits<{
  'select-element': [id: string, multi: boolean]
  'set-active-page': [pageIndex: number]
  'clear-selection': []
  'double-click-element': [id: string]
  'update-element': [id: string, updates: Partial<CanvasElement>, recordHistory?: boolean]
  'update-element-bounds': [id: string, bounds: { x: number; y: number; width: number; height: number; rotation?: number }]
  'duplicate-element': [id: string]
  'delete-element': [id: string]
  'toggle-lock': [id: string]
  'bring-forward': [id: string]
  'send-backward': [id: string]
  'set-guides': [guides: AlignmentGuide[], distanceGuides?: DistanceGuide[]]
  'finish-edit': [id: string]
  'drag-start': [id: string]
  'drag-end': []
  'resize-end': []
  'duplicate-page': [pageIndex: number]
  'delete-page': [pageIndex: number]
  'copy-style': [e: MouseEvent]
}>()

const MM_TO_PX_BASE = 3.779527559
const PAGE_WIDTH_MM = 210
const PAGE_HEIGHT_MM = 297

const BASE_PAGE_WIDTH_PX = PAGE_WIDTH_MM * MM_TO_PX_BASE
const BASE_PAGE_HEIGHT_PX = PAGE_HEIGHT_MM * MM_TO_PX_BASE

function mmToBasePx(mm: number): number {
  return mm * MM_TO_PX_BASE
}

const scaledPageWidthPx = computed(() => BASE_PAGE_WIDTH_PX * (props.zoomLevel / 100))
const scaledPageHeightPx = computed(() => BASE_PAGE_HEIGHT_PX * (props.zoomLevel / 100))

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
    // the browser fires at the end of a workspace-level marquee drag — we
    // just selected elements and must NOT wipe them immediately.
    if (props.consumeMarqueeGuard?.()) return
    emit('clear-selection')
    if (document.activeElement instanceof HTMLElement && document.activeElement !== document.body) {
      document.activeElement.blur()
    }
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

        <!-- Outer Viewport: reserves scaled layout space for scrollbars, centered layouts, and rulers -->
        <div
          class="canvas-sheet-viewport relative shrink-0"
          :style="{
            width: `${scaledPageWidthPx}px`,
            height: `${scaledPageHeightPx}px`,
          }"
        >
          <!-- The Physical A4 Sheet (Rendered at 100% scale, scaled via GPU transform) -->
          <!-- Note: identified by the `canvas-sheet-background` class (not a
               template ref) because the workspace-level marquee selection in
               ContractDocumentEditor.vue looks up every page's sheet via
               querySelector to hit-test elements against the drag rect. -->
          <div
            class="canvas-sheet-background absolute top-0 left-0 bg-white text-zinc-900 shadow-2xl border border-zinc-300/80 dark:border-zinc-700/60 transition-shadow overflow-hidden outline-none"
            :style="{
              width: `${BASE_PAGE_WIDTH_PX}px`,
              height: `${BASE_PAGE_HEIGHT_PX}px`,
              transform: `scale(${zoomLevel / 100})`,
              transformOrigin: 'top left',
              fontFamily: `'Times New Roman', Times, serif`,
            }"
            @pointermove="onCanvasPointerMove"
            @pointerleave="onCanvasPointerLeave"
            @click="onCanvasClick"
          >
            <!-- Grid Background (if enabled) -->
            <div
              v-if="!readonly && showGrid"
              class="absolute inset-0 pointer-events-none opacity-30"
              :style="{
                backgroundImage: 'radial-gradient(#3b82f6 0.75px, transparent 0.75px)',
                backgroundSize: `${mmToBasePx(5)}px ${mmToBasePx(5)}px`,
              }"
            ></div>

            <!-- Margin Guide Dashed Lines & Crop Corners (if enabled) -->
            <div
              v-if="!readonly && showMarginGuides"
              class="margin-guide-overlay pointer-events-none select-none absolute no-print"
              :style="{
                top: `${mmToBasePx(margins.top)}px`,
                left: `${mmToBasePx(margins.left)}px`,
                right: `${mmToBasePx(margins.right)}px`,
                bottom: `${mmToBasePx(margins.bottom)}px`,
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

          <!-- Smart Alignment & Distance Guides Overlay -->
          <CanvasSmartGuides
            v-if="!readonly"
            :guides="activeGuides"
            :distance-guides="activeDistanceGuides"
            :zoom-level="zoomLevel"
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
            :is-copy-style-active="isCopyStyleActive"
            :copy-style-mode="copyStyleMode"
            :calculate-snapping="calculateSnapping"
            @select="emit('set-active-page', pageIndex); emit('select-element', el.id, $event.shiftKey)"
            @copy-style="emit('copy-style', $event)"
            @double-click="emit('double-click-element', el.id)"
            @update:bounds="emit('update-element-bounds', el.id, $event)"
            @duplicate="emit('duplicate-element', el.id)"
            @delete="emit('delete-element', el.id)"
            @toggle-lock="emit('toggle-lock', el.id)"
            @bring-forward="emit('bring-forward', el.id)"
            @send-backward="emit('send-backward', el.id)"
            @set-guides="(guides, distGuides) => emit('set-guides', guides, distGuides)"
            @drag:start="emit('drag-start', el.id)"
            @drag:end="emit('drag-end')"
            @resize:end="emit('resize-end')"
          >
            <!-- Text / Heading -->
            <CanvasTextElement
              v-if="el.type === 'text' || el.type === 'heading' || el.type === 'paragraph' || el.type === 'date' || el.type === 'variable'"
              :element="el as any"
              :is-editing="editingElementId === el.id"
              :readonly="readonly"
              :zoom-level="zoomLevel"
              :variable-values="variableValues"
              @update:content="(html, record) => emit('update-element', el.id, { content: html }, record)"
              @finish-edit="emit('finish-edit', el.id)"
              @auto-resize-height="emit('update-element-bounds', el.id, { x: el.x, y: el.y, width: el.width, height: $event })"
            />

            <!-- Table -->
            <CanvasTableElement
              v-else-if="el.type === 'table'"
              :element="el as any"
              :is-selected="selectedElementIds.includes(el.id)"
              :is-editing="editingElementId === el.id"
              :readonly="readonly"
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
              :is-editing="!readonly && editingElementId === el.id"
              :readonly="readonly"
              :zoom-level="zoomLevel"
              @update:checked="emit('update-element', el.id, { checked: $event })"
              @update:label="emit('update-element', el.id, { label: $event })"
              @update:style="emit('update-element', el.id, { style: $event })"
              @finish-edit="emit('finish-edit', el.id)"
              @auto-resize-width="emit('update-element-bounds', el.id, { x: el.x, y: el.y, width: $event, height: el.height })"
            />
          </CanvasElementWrapper>
        </div>
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
