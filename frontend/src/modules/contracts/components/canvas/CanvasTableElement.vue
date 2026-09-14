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

const props = defineProps<{
  element: TableCanvasElement
  isSelected: boolean
  isEditing: boolean
  zoomLevel: number
  variableValues?: Record<string, string>
}>()

const emit = defineEmits<{
  'update:element': [updates: Partial<TableCanvasElement>]
  'update:cell': [rowIndex: number, colIndex: number, content: string]
  'select-cell': [rowIndex: number, colIndex: number]
}>()

const activeCellCoord = ref<{ r: number; c: number } | null>(null)
const editingCellCoord = ref<{ r: number; c: number } | null>(null)

const MM_TO_PX_BASE = 3.779527559

function mmToPx(mm: number): number {
  return mm * MM_TO_PX_BASE * (props.zoomLevel / 100)
}

function pxToMm(px: number): number {
  return px / (MM_TO_PX_BASE * (props.zoomLevel / 100))
}

// Resizing Columns via Dragging Column Headers
function onColumnResizeStart(colIdx: number, e: PointerEvent) {
  e.preventDefault()
  e.stopPropagation()

  const startClientX = e.clientX
  const originalWidths = [...props.element.colWidths]
  const currentW = originalWidths[colIdx] || 20

  function onColMove(moveEvent: PointerEvent) {
    const deltaMm = pxToMm(moveEvent.clientX - startClientX)
    const newW = Math.max(10, currentW + deltaMm)
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
  }

  window.addEventListener('pointermove', onColMove)
  window.addEventListener('pointerup', onColUp)
}

// Cell Double Click -> In-place edit cell content
function onCellDoubleClick(r: number, c: number, e: MouseEvent) {
  e.stopPropagation()
  editingCellCoord.value = { r, c }
  activeCellCoord.value = { r, c }
  emit('select-cell', r, c)
}

function onCellClick(r: number, c: number, e: MouseEvent) {
  if (editingCellCoord.value?.r === r && editingCellCoord.value?.c === c) return
  activeCellCoord.value = { r, c }
  emit('select-cell', r, c)
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

// Row & Column Operations
function addColumnAfter(colIdx: number) {
  const newCols = props.element.cols + 1
  const avgW = props.element.width / newCols
  const newWidths = Array(newCols).fill(Math.round(avgW * 10) / 10)

  const newCells = props.element.cells.map(row => {
    const newRow = [...row]
    newRow.splice(colIdx + 1, 0, {
      id: `cell_${Date.now()}_${Math.random().toString(36).substring(2, 6)}`,
      content: '&nbsp;',
    })
    return newRow
  })

  emit('update:element', {
    cols: newCols,
    colWidths: newWidths,
    cells: newCells,
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
  const newRowHeights = [...props.element.rowHeights, 10]
  const newRowCells: TableCellModel[] = Array.from({ length: props.element.cols }, () => ({
    id: `cell_${Date.now()}_${Math.random().toString(36).substring(2, 6)}`,
    content: '&nbsp;',
  }))

  const newCells = [...props.element.cells]
  newCells.splice(rowIdx + 1, 0, newRowCells)

  emit('update:element', {
    rows: newRows,
    rowHeights: newRowHeights,
    cells: newCells,
    height: props.element.height + 10,
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
    height: Math.max(15, props.element.height - 10),
  })
}

// Variable replacement helper
function renderCellContent(content: string): string {
  let text = content || ''
  if (props.variableValues) {
    for (const [key, val] of Object.entries(props.variableValues)) {
      text = text.split(key).join(val)
    }
  }
  return text
}
</script>

<template>
  <div class="canvas-table-element w-full h-full relative font-serif select-none">
    <!-- Floating Table Quick Toolbar (when a cell or table is selected) -->
    <div
      v-if="isSelected && activeCellCoord"
      class="absolute -top-8 right-0 bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-700 shadow-xl rounded-xl px-1.5 py-0.5 flex items-center gap-1 z-50 text-[11px] pointer-events-auto opacity-100 ring-1 ring-black/5 dark:ring-white/10"
      @pointerdown.stop.prevent
    >
      <button
        type="button"
        @click="addColumnAfter(activeCellCoord.c)"
        class="px-1.5 py-0.5 rounded hover:bg-blue-50 hover:text-blue-600 dark:hover:bg-zinc-800 text-zinc-600 dark:text-zinc-300 font-semibold flex items-center gap-1"
        title="Add column right"
      >
        <Columns class="w-3 h-3 text-blue-500" />
        <span>+ Col</span>
      </button>

      <button
        type="button"
        @click="deleteColumnAt(activeCellCoord.c)"
        :disabled="element.cols <= 1"
        class="px-1.5 py-0.5 rounded hover:bg-rose-50 hover:text-rose-600 dark:hover:bg-zinc-800 text-zinc-500 disabled:opacity-30"
        title="Delete column"
      >
        <span>- Col</span>
      </button>

      <div class="w-px h-3 bg-zinc-200 dark:bg-zinc-700"></div>

      <button
        type="button"
        @click="addRowAfter(activeCellCoord.r)"
        class="px-1.5 py-0.5 rounded hover:bg-blue-50 hover:text-blue-600 dark:hover:bg-zinc-800 text-zinc-600 dark:text-zinc-300 font-semibold flex items-center gap-1"
        title="Add row below"
      >
        <Rows class="w-3 h-3 text-blue-500" />
        <span>+ Row</span>
      </button>

      <button
        type="button"
        @click="deleteRowAt(activeCellCoord.r)"
        :disabled="element.rows <= 1"
        class="px-1.5 py-0.5 rounded hover:bg-rose-50 hover:text-rose-600 dark:hover:bg-zinc-800 text-zinc-500 disabled:opacity-30"
        title="Delete row"
      >
        <span>- Row</span>
      </button>
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
          :style="{ minHeight: `${mmToPx(element.rowHeights[rIdx] || 10)}px` }"
        >
          <td
            v-for="(cell, cIdx) in row"
            :key="cell.id"
            class="relative transition-colors"
            :class="[
              activeCellCoord?.r === rIdx && activeCellCoord?.c === cIdx && isSelected
                ? 'ring-2 ring-blue-500 ring-inset bg-blue-50/20'
                : '',
              element.density === 'compact'
                ? 'p-1 text-[11px]'
                : element.density === 'spacious'
                ? 'p-3 text-sm'
                : 'p-1.5 text-xs'
            ]"
            :style="{
              border: `${element.borderWidth || '1px'} ${element.borderStyle || 'solid'} ${element.borderColor || '#94a3b8'}`,
              backgroundColor: cell.backgroundColor || 'transparent',
              textAlign: cell.textAlign || 'left',
              verticalAlign: cell.verticalAlign || 'top',
              color: cell.color || '#111827',
              fontFamily: `'Times New Roman', Times, serif`
            }"
            @click="onCellClick(rIdx, cIdx, $event)"
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

            <!-- Column Resize Handle on right edge of top-row cells -->
            <div
              v-if="rIdx === 0 && isSelected"
              class="absolute top-0 right-0 bottom-0 w-1.5 hover:w-2 bg-transparent hover:bg-blue-500/50 cursor-col-resize z-20 transition-all pointer-events-auto"
              @pointerdown="onColumnResizeStart(cIdx, $event)"
            ></div>
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
</style>
