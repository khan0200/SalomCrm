<script setup lang="ts">
import { ref, computed } from 'vue'
import {
  Plus,
  Trash2,
  Columns,
  Rows,
} from 'lucide-vue-next'
import type { TableCanvasElement, TableCellModel } from '../../types/contractCanvas'
import { cleanClipboardContent } from '../../utils/clipboardUtils'
import { replaceVariablesInHtml } from '../../utils/contractVariables'

const props = withDefaults(
  defineProps<{
    element: TableCanvasElement
    isSelected: boolean
    isEditing: boolean
    readonly?: boolean
    zoomLevel: number
    variableValues?: Record<string, string>
  }>(),
  {
    readonly: false,
  }
)

const emit = defineEmits<{
  'update:element': [updates: Partial<TableCanvasElement>]
  'update:cell': [rowIndex: number, colIndex: number, content: string]
  'select-cells': [r1: number, c1: number, r2: number, c2: number]
}>()

// Excel-style block selection: the anchor is where the drag/shift-click started,
// the focus is the cell under the pointer now. Everything between them is
// selected, so the pair is kept rather than a single coordinate.
const anchorCell = ref<{ r: number; c: number } | null>(null)
const focusCell = ref<{ r: number; c: number } | null>(null)
const editingCellCoord = ref<{ r: number; c: number } | null>(null)
const isDragSelecting = ref(false)

// Which handle is mid-drag. Hover styling alone left the grip invisible the
// moment the pointer moved off the 2px strip it was dragging, which is exactly
// when the user most needs to see what they are resizing.
const resizing = ref<{ axis: 'col' | 'row'; index: number } | null>(null)

const selectionRect = computed(() => {
  const a = anchorCell.value
  const f = focusCell.value
  if (!a || !f) return null
  return {
    r1: Math.min(a.r, f.r),
    c1: Math.min(a.c, f.c),
    r2: Math.max(a.r, f.r),
    c2: Math.max(a.c, f.c),
  }
})

const hasMultiSelection = computed(() => {
  const rect = selectionRect.value
  return Boolean(rect && (rect.r1 !== rect.r2 || rect.c1 !== rect.c2))
})

function isCellSelected(r: number, c: number): boolean {
  const rect = selectionRect.value
  if (!rect) return false
  return r >= rect.r1 && r <= rect.r2 && c >= rect.c1 && c <= rect.c2
}

function emitSelection() {
  const rect = selectionRect.value
  if (!rect) return
  emit('select-cells', rect.r1, rect.c1, rect.r2, rect.c2)
}

/**
 * Sit on the opposite side from the element wrapper's own action bar, which
 * uses the element's top unless it is within 16mm of the page edge. Sharing a
 * side made the two bars overlap and swallow each other's buttons.
 */
const toolbarPositionClass = computed(() =>
  props.element.y < 16 ? '-top-9 left-0' : 'top-[calc(100%+10px)] left-0'
)

const MM_TO_PX_BASE = 3.779527559
// Cell font sizes are authored in pt like the rest of the document; the canvas
// draws in px, and 1pt = 1/72in while 1px = 1/96in.
const PT_TO_PX = 96 / 72

function mmToPx(mm: number): number {
  return mm * MM_TO_PX_BASE
}

function pxToMm(px: number): number {
  return px / (MM_TO_PX_BASE * (props.zoomLevel / 100))
}

const cellFontSizePx = computed(() => {
  const base = props.element.density === 'compact' ? 11 : props.element.density === 'spacious' ? 14 : 12
  return base
})

const cellPaddingPx = computed(() => {
  const base = props.element.density === 'compact' ? 3 : props.element.density === 'spacious' ? 10 : 5
  return base
})

const MIN_COL_MM = 8
const MIN_ROW_MM = 5

/**
 * While a grip is dragged the pointer routinely leaves the thin strip it grabbed
 * (and passes over cells, whose own cursor would take over). Capturing the
 * pointer keeps the events coming, and locking the cursor on <body> keeps the
 * resize arrow on screen for the whole gesture instead of flicking back to the
 * default white arrow the moment the pointer crosses a cell.
 */
function beginHandleDrag(axis: 'col' | 'row', index: number, e: PointerEvent) {
  resizing.value = { axis, index }
  try {
    ;(e.currentTarget as HTMLElement).setPointerCapture(e.pointerId)
  } catch {
    /* capture is a nicety - dragging still works through the window listeners */
  }
  window.document.body.classList.add(axis === 'col' ? 'canvas-resizing-col' : 'canvas-resizing-row')
}

function endHandleDrag() {
  resizing.value = null
  window.document.body.classList.remove('canvas-resizing-col', 'canvas-resizing-row')
}

// Resizing Columns via Dragging Column Headers
function onColumnResizeStart(colIdx: number, e: PointerEvent) {
  e.preventDefault()
  e.stopPropagation()
  beginHandleDrag('col', colIdx, e)

  const startClientX = e.clientX
  const originalWidths = [...props.element.colWidths]
  const currentW = originalWidths[colIdx] || 20

  function onColMove(moveEvent: PointerEvent) {
    const deltaMm = pxToMm(moveEvent.clientX - startClientX)
    const newW = Math.max(MIN_COL_MM, currentW + deltaMm)
    const updatedWidths = [...originalWidths]
    updatedWidths[colIdx] = Math.round(newW * 10) / 10

    // Update total table width
    const totalW = updatedWidths.reduce((sum, w) => sum + w, 0)
    emit('update:element', {
      colWidths: updatedWidths,
      width: Math.round(totalW * 10) / 10,
    })
  }

  function onColUp() {
    window.removeEventListener('pointermove', onColMove)
    window.removeEventListener('pointerup', onColUp)
    endHandleDrag()
  }

  window.addEventListener('pointermove', onColMove)
  window.addEventListener('pointerup', onColUp)
}

// Resizing Rows via dragging the bottom edge of a row's first cell
function onRowResizeStart(rowIdx: number, e: PointerEvent) {
  e.preventDefault()
  e.stopPropagation()
  beginHandleDrag('row', rowIdx, e)

  const startClientY = e.clientY
  const originalHeights = [...props.element.rowHeights]
  const currentH = originalHeights[rowIdx] || 10

  function onRowMove(moveEvent: PointerEvent) {
    const deltaMm = pxToMm(moveEvent.clientY - startClientY)
    const newH = Math.max(MIN_ROW_MM, currentH + deltaMm)
    const updatedHeights = [...originalHeights]
    updatedHeights[rowIdx] = Math.round(newH * 10) / 10

    const totalH = updatedHeights.reduce((sum, h) => sum + h, 0)
    emit('update:element', {
      rowHeights: updatedHeights,
      height: Math.round(totalH * 10) / 10,
    })
  }

  function onRowUp() {
    window.removeEventListener('pointermove', onRowMove)
    window.removeEventListener('pointerup', onRowUp)
    endHandleDrag()
  }

  window.addEventListener('pointermove', onRowMove)
  window.addEventListener('pointerup', onRowUp)
}

// Cell Double Click -> In-place edit cell content
function onCellDoubleClick(r: number, c: number, e: MouseEvent) {
  e.stopPropagation()
  editingCellCoord.value = { r, c }
  anchorCell.value = { r, c }
  focusCell.value = { r, c }
  emitSelection()
}

function onCellPointerDown(r: number, c: number, e: PointerEvent) {
  if (props.readonly) return
  // Leave an in-progress cell edit alone: the pointer belongs to the caret then.
  if (editingCellCoord.value) return
  if (e.button !== 0) return

  e.stopPropagation()

  if (e.shiftKey && anchorCell.value) {
    focusCell.value = { r, c }
  } else {
    anchorCell.value = { r, c }
    focusCell.value = { r, c }
    isDragSelecting.value = true
    window.addEventListener('pointerup', onSelectionPointerUp, { once: true })
  }
  emitSelection()
}

function onCellPointerEnter(r: number, c: number) {
  if (!isDragSelecting.value) return
  const f = focusCell.value
  if (f && f.r === r && f.c === c) return
  focusCell.value = { r, c }
  emitSelection()
}

function onSelectionPointerUp() {
  isDragSelecting.value = false
}

function selectAllCells() {
  const lastRow = props.element.cells.length - 1
  if (lastRow < 0) return
  const lastCol = Math.max(0, (props.element.cells[lastRow]?.length ?? 1) - 1)
  anchorCell.value = { r: 0, c: 0 }
  focusCell.value = { r: lastRow, c: lastCol }
  emitSelection()
}

function onCellBlur(r: number, c: number, e: FocusEvent) {
  const target = e.target as HTMLElement
  emit('update:cell', r, c, target.innerHTML)
  editingCellCoord.value = null
}

function onCellPaste(r: number, c: number, e: ClipboardEvent) {
  e.preventDefault()
  const clipboardData = e.clipboardData
  if (!clipboardData) return

  const cleanHtml = cleanClipboardContent(clipboardData, props.element.cells[r]?.[c]?.color || '#000000')
  if (!cleanHtml) return

  const target = e.target as HTMLElement
  if (target) {
    const sel = window.getSelection()
    if (sel && sel.rangeCount > 0) {
      const range = sel.getRangeAt(0)
      range.deleteContents()
      const fragment = range.createContextualFragment(cleanHtml)
      const lastNode = fragment.lastChild
      range.insertNode(fragment)
      if (lastNode) {
        range.setStartAfter(lastNode)
        range.collapse(true)
        sel.removeAllRanges()
        sel.addRange(range)
      }
    } else {
      target.innerHTML = cleanHtml
    }
    emit('update:cell', r, c, target.innerHTML)
  }
}

function newCell(): TableCellModel {
  return {
    id: `cell_${Date.now()}_${Math.random().toString(36).substring(2, 6)}`,
    content: '&nbsp;',
  }
}

// Row & Column Operations
function addColumnAfter(colIdx: number) {
  const newCols = props.element.cols + 1

  // Split the source column in two rather than redistributing every column:
  // rebuilding all widths from an average silently discarded whatever column
  // sizing had been set up, which is never what adding one column should mean.
  const newWidths = [...props.element.colWidths]
  const sourceW = newWidths[colIdx] || 20
  const halfW = Math.max(MIN_COL_MM, Math.round((sourceW / 2) * 10) / 10)
  newWidths[colIdx] = halfW
  newWidths.splice(colIdx + 1, 0, halfW)

  const newCells = props.element.cells.map(row => {
    const newRow = [...row]
    newRow.splice(Math.min(colIdx + 1, newRow.length), 0, newCell())
    return newRow
  })

  emit('update:element', {
    cols: newCols,
    colWidths: newWidths,
    cells: newCells,
    width: Math.round(newWidths.reduce((sum, w) => sum + w, 0) * 10) / 10,
  })
}

function deleteColumnAt(colIdx: number) {
  if (props.element.cols <= 1) return
  const newCols = props.element.cols - 1
  const newWidths = props.element.colWidths.filter((_, idx) => idx !== colIdx)
  const newCells = props.element.cells.map(row => row.filter((_, idx) => idx !== colIdx))
  const newTotalW = newWidths.reduce((sum, w) => sum + w, 0)

  emit('update:element', {
    cols: newCols,
    colWidths: newWidths,
    cells: newCells,
    width: Math.round(newTotalW * 10) / 10,
  })
}

function addRowAfter(rowIdx: number) {
  const newRows = props.element.rows + 1

  // The height entry has to land beside its row: appending to the end left
  // every row below the insertion point wearing its neighbour's height.
  const newRowHeights = [...props.element.rowHeights]
  const sourceH = newRowHeights[rowIdx] || 10
  newRowHeights.splice(rowIdx + 1, 0, sourceH)

  const newRowCells: TableCellModel[] = Array.from({ length: props.element.cols }, newCell)

  const newCells = [...props.element.cells]
  newCells.splice(rowIdx + 1, 0, newRowCells)

  emit('update:element', {
    rows: newRows,
    rowHeights: newRowHeights,
    cells: newCells,
    height: Math.round(newRowHeights.reduce((sum, h) => sum + h, 0) * 10) / 10,
  })
}

function deleteRowAt(rowIdx: number) {
  if (props.element.rows <= 1) return
  const newRows = props.element.rows - 1
  const newRowHeights = props.element.rowHeights.filter((_, idx) => idx !== rowIdx)
  const newCells = props.element.cells.filter((_, idx) => idx !== rowIdx)

  emit('update:element', {
    rows: newRows,
    rowHeights: newRowHeights,
    cells: newCells,
    height: Math.max(MIN_ROW_MM, Math.round(newRowHeights.reduce((sum, h) => sum + h, 0) * 10) / 10),
  })
}

/** Deletes every column the selection spans, keeping at least one behind. */
function deleteSelectedColumns() {
  const rect = selectionRect.value
  if (!rect) return
  const count = Math.min(rect.c2 - rect.c1 + 1, props.element.cols - 1)
  if (count <= 0) return
  for (let i = 0; i < count; i++) deleteColumnAt(rect.c1)
  const lastCol = Math.max(0, props.element.cols - 1 - count)
  anchorCell.value = { r: rect.r1, c: Math.min(rect.c1, lastCol) }
  focusCell.value = { ...anchorCell.value }
  emitSelection()
}

/** Deletes every row the selection spans, keeping at least one behind. */
function deleteSelectedRows() {
  const rect = selectionRect.value
  if (!rect) return
  const count = Math.min(rect.r2 - rect.r1 + 1, props.element.rows - 1)
  if (count <= 0) return
  for (let i = 0; i < count; i++) deleteRowAt(rect.r1)
  const lastRow = Math.max(0, props.element.rows - 1 - count)
  anchorCell.value = { r: Math.min(rect.r1, lastRow), c: rect.c1 }
  focusCell.value = { ...anchorCell.value }
  emitSelection()
}

// Variable replacement helper
function renderCellContent(content: string): string {
  let text = content || ''
  if (props.readonly || (props.variableValues && Object.keys(props.variableValues).length > 0)) {
    text = replaceVariablesInHtml(text, props.variableValues || {}, { skipHeuristics: true })
  }
  return text
}
</script>

<template>
  <div class="canvas-table-element w-full h-full relative font-serif select-none">
    <!-- Floating Table Quick Toolbar (when a cell or table is selected) -->
    <div
      v-if="isSelected && !readonly && anchorCell"
      class="absolute bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-700 shadow-xl rounded-xl px-1.5 py-0.5 flex items-center gap-1 z-[90] text-[11px] pointer-events-auto opacity-100 ring-1 ring-black/5 dark:ring-white/10 whitespace-nowrap"
      :class="toolbarPositionClass"
      :style="{
        transform: `scale(${100 / Math.max(25, props.zoomLevel)})`,
        transformOrigin: props.element.y < 16 ? 'bottom left' : 'top left'
      }"
      @pointerdown.stop.prevent
    >
      <button
        type="button"
        @click="addColumnAfter(selectionRect!.c2)"
        class="px-1.5 py-0.5 rounded hover:bg-blue-50 hover:text-blue-600 dark:hover:bg-zinc-800 text-zinc-600 dark:text-zinc-300 font-semibold flex items-center gap-1"
        title="O'ngga ustun qo'shish"
      >
        <Columns class="w-3 h-3 text-blue-500" />
        <span>+ Ustun</span>
      </button>

      <button
        type="button"
        @click="deleteSelectedColumns()"
        :disabled="element.cols <= 1"
        class="px-1.5 py-0.5 rounded hover:bg-rose-50 hover:text-rose-600 dark:hover:bg-zinc-800 text-zinc-500 disabled:opacity-30"
        title="Tanlangan ustun(lar)ni o'chirish"
      >
        <span>− Ustun</span>
      </button>

      <div class="w-px h-3 bg-zinc-200 dark:bg-zinc-700"></div>

      <button
        type="button"
        @click="addRowAfter(selectionRect!.r2)"
        class="px-1.5 py-0.5 rounded hover:bg-blue-50 hover:text-blue-600 dark:hover:bg-zinc-800 text-zinc-600 dark:text-zinc-300 font-semibold flex items-center gap-1"
        title="Pastga qator qo'shish"
      >
        <Rows class="w-3 h-3 text-blue-500" />
        <span>+ Qator</span>
      </button>

      <button
        type="button"
        @click="deleteSelectedRows()"
        :disabled="element.rows <= 1"
        class="px-1.5 py-0.5 rounded hover:bg-rose-50 hover:text-rose-600 dark:hover:bg-zinc-800 text-zinc-500 disabled:opacity-30"
        title="Tanlangan qator(lar)ni o'chirish"
      >
        <span>− Qator</span>
      </button>

      <div class="w-px h-3 bg-zinc-200 dark:bg-zinc-700"></div>

      <button
        type="button"
        @click="selectAllCells()"
        class="px-1.5 py-0.5 rounded hover:bg-blue-50 hover:text-blue-600 dark:hover:bg-zinc-800 text-zinc-600 dark:text-zinc-300 font-semibold"
        title="Barcha kataklarni tanlash"
      >
        <span>Hammasi</span>
      </button>

      <span
        v-if="hasMultiSelection"
        class="px-1.5 py-0.5 rounded bg-blue-50 dark:bg-blue-950/50 text-blue-600 dark:text-blue-300 font-bold tabular-nums"
      >
        {{ (selectionRect!.r2 - selectionRect!.r1 + 1) }}×{{ (selectionRect!.c2 - selectionRect!.c1 + 1) }}
      </span>
    </div>

    <!-- Table Render -->
    <table
      class="w-full h-full border-collapse"
      :style="{
        tableLayout: 'fixed',
        border: `${element.borderWidth || '1px'} ${element.borderStyle || 'solid'} ${element.borderColor || '#94a3b8'}`
      }"
    >
      <colgroup>
        <col
          v-for="(w, colIdx) in element.colWidths"
          :key="colIdx"
          :style="{ width: `${mmToPx(w)}px` }"
        />
      </colgroup>
      <tbody>
        <tr
          v-for="(row, rIdx) in element.cells"
          :key="rIdx"
          :style="{ height: `${mmToPx(element.rowHeights[rIdx] || 10)}px` }"
        >
          <td
            v-for="(cell, cIdx) in row"
            :key="cell.id"
            class="relative transition-colors"
            :colspan="cell.colSpan && cell.colSpan > 1 ? cell.colSpan : undefined"
            :rowspan="cell.rowSpan && cell.rowSpan > 1 ? cell.rowSpan : undefined"
            :class="[
              isSelected && isCellSelected(rIdx, cIdx) ? 'canvas-cell-selected' : '',
              isSelected && anchorCell?.r === rIdx && anchorCell?.c === cIdx
                ? 'ring-2 ring-blue-500 ring-inset'
                : ''
            ]"
            :style="{
              border: `${element.borderWidth || '1px'} ${element.borderStyle || 'solid'} ${element.borderColor || '#94a3b8'}`,
              backgroundColor: cell.backgroundColor || 'transparent',
              textAlign: cell.textAlign || 'left',
              verticalAlign: cell.verticalAlign || 'top',
              color: cell.color || '#111827',
              fontFamily: `'Times New Roman', Times, serif`,
              fontSize: `${cell.fontSize ? cell.fontSize * PT_TO_PX : cellFontSizePx}px`,
              fontWeight: cell.fontWeight || 'normal',
              fontStyle: cell.fontStyle || 'normal',
              textDecoration: cell.textDecoration || 'none',
              padding: `${cellPaddingPx}px`
            }"
            @pointerdown="onCellPointerDown(rIdx, cIdx, $event)"
            @pointerenter="onCellPointerEnter(rIdx, cIdx)"
            @dblclick="onCellDoubleClick(rIdx, cIdx, $event)"
          >
            <!-- Cell Content (Editable when double clicked) -->
            <div
              v-if="editingCellCoord?.r === rIdx && editingCellCoord?.c === cIdx"
              contenteditable="true"
              class="w-full h-full min-h-[18px] outline-none select-text cursor-text bg-white dark:bg-zinc-800 p-0.5 rounded-xs"
              @blur="onCellBlur(rIdx, cIdx, $event)"
              @paste="onCellPaste(rIdx, cIdx, $event)"
              v-html="cell.content"
            ></div>
            <div
              v-else
              class="w-full h-full min-h-[18px] break-words"
              v-html="renderCellContent(cell.content)"
            ></div>

            <!-- Column Resize Handle on right edge of top-row cells.
                 Skipped on spanned cells: their cIdx no longer maps onto a
                 single column, so dragging one would resize the wrong column.
                 Stays lit for the whole drag (not just :hover) so the grip does
                 not vanish the moment the pointer runs ahead of it. -->
            <div
              v-if="rIdx === 0 && isSelected && !readonly && !(cell.colSpan && cell.colSpan > 1)"
              class="canvas-col-grip absolute -top-px right-0 bottom-0 w-2 cursor-col-resize z-30 pointer-events-auto"
              :class="resizing?.axis === 'col' && resizing.index === cIdx ? 'is-active' : ''"
              @pointerdown="onColumnResizeStart(cIdx, $event)"
            >
              <span class="grip-line"></span>
            </div>

            <!-- Row Resize Handle on the bottom edge of the first cell in a row -->
            <div
              v-if="cIdx === 0 && isSelected && !readonly && !(cell.rowSpan && cell.rowSpan > 1)"
              class="canvas-row-grip absolute left-0 -right-px bottom-0 h-2 cursor-row-resize z-30 pointer-events-auto"
              :class="resizing?.axis === 'row' && resizing.index === rIdx ? 'is-active' : ''"
              @pointerdown="onRowResizeStart(rIdx, $event)"
            >
              <span class="grip-line"></span>
            </div>
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<style>
.canvas-table-element,
.canvas-table-element table,
.canvas-table-element td,
.canvas-table-element th,
.canvas-table-element div,
.canvas-table-element span,
.canvas-table-element p {
  font-family: 'Times New Roman', Times, Georgia, serif !important;
}

/* Block selection tint. Painted with a box-shadow inset rather than
   background-color so a cell's own fill colour stays visible underneath. */
.canvas-table-element td.canvas-cell-selected {
  box-shadow: inset 0 0 0 9999px rgba(37, 99, 235, 0.13);
}

/* Resize grips: a hairline that thickens on hover and stays thick while the
   drag is in flight. */
.canvas-col-grip .grip-line,
.canvas-row-grip .grip-line {
  position: absolute;
  background: transparent;
  transition: background-color 0.12s ease;
}

.canvas-col-grip .grip-line {
  top: 0;
  bottom: 0;
  right: 0;
  width: 2px;
}

.canvas-row-grip .grip-line {
  left: 0;
  right: 0;
  bottom: 0;
  height: 2px;
}

.canvas-col-grip:hover .grip-line,
.canvas-row-grip:hover .grip-line,
.canvas-col-grip.is-active .grip-line,
.canvas-row-grip.is-active .grip-line {
  background: #2563eb;
}

/* Keep the resize cursor for the whole gesture. Without this the pointer
   crosses cells mid-drag and picks up their cursor instead. */
body.canvas-resizing-col,
body.canvas-resizing-col * {
  cursor: col-resize !important;
}

body.canvas-resizing-row,
body.canvas-resizing-row * {
  cursor: row-resize !important;
}

/* Dragging a block selection should not paint the browser's own text
   highlight over the cells. */
body.canvas-resizing-col,
body.canvas-resizing-row {
  user-select: none;
}
</style>
