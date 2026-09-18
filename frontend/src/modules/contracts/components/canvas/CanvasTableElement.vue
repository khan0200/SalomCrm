<script setup lang="ts">
import { ref, computed, nextTick } from 'vue'
import {
  Copy,
  Scissors,
  Trash2,
  ClipboardPaste,
  Combine,
  Grid3x3,
} from 'lucide-vue-next'
import type { TableCanvasElement, TableCellModel } from '../../types/contractCanvas'
import { cleanClipboardContent } from '../../utils/clipboardUtils'
import { replaceVariablesInHtml } from '../../utils/contractVariables'
import * as Grid from '../../utils/tableGrid'
import type { Rect } from '../../utils/tableGrid'

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
  'select-cells': [r1: number, c1: number, r2: number, c2: number]
  /** Tells the parent to make this table the active canvas element - see the
   * big comment above tableRootEl for why the table has to do this itself. */
  'activate-element': []
}>()

// A table's own cells cover its whole box with pointer-events re-enabled (see
// the style block), so a click inside it never reaches the generic element
// wrapper's own "click to select" handler - that handler lives on an
// ancestor the click no longer bubbles to once a cell's own handler stops
// propagation. Every gesture that begins inside the table therefore has to
// ask the parent to select this element explicitly.
function activate() {
  emit('activate-element')
}

// ─── Cross-table clipboards (module scope: shared across every table on the
// page, like the OS clipboard) ───────────────────────────────────────────
let cellClipboard: TableCellModel[][] | null = null
let rowClipboard: TableCellModel[] | null = null
let colClipboard: TableCellModel[] | null = null

const tableRootEl = ref<HTMLElement | null>(null)

// Excel-style block selection: the anchor is where the drag/shift-click/
// keyboard selection started, the focus is the other end. Everything between
// them is selected. Both a plain cell click and a row/column header click set
// both to the same axis-spanning coordinates, so one rect model covers cell,
// row, column and "select all" selections without a separate mode flag.
const anchorCell = ref<{ r: number; c: number } | null>(null)
const focusCell = ref<{ r: number; c: number } | null>(null)
const editingCellCoord = ref<{ r: number; c: number } | null>(null)
const isDragSelecting = ref(false)

// Which resize handle is mid-drag - kept so the grip stays lit for the whole
// gesture instead of only while the pointer happens to hover its 2px strip.
const resizing = ref<{ axis: 'col' | 'row'; index: number } | null>(null)

// Row/column reorder-by-drag (see startRowHeaderDrag/startColHeaderDrag).
const rowDrag = ref<{ from: number; over: number } | null>(null)
const colDrag = ref<{ from: number; over: number } | null>(null)

const rows = computed(() => props.element.rows)
const cols = computed(() => props.element.cols)

/** Always grown to whole spans, so a selection never visually slices a merged cell in half. */
const selectionRect = computed<Rect | null>(() => {
  const a = anchorCell.value
  const f = focusCell.value
  if (!a || !f) return null
  const raw = Grid.normalizeRect(a.r, a.c, f.r, f.c)
  return Grid.expandRectToWholeSpans(props.element.cells, raw)
})

const isWholeRowSelection = computed(() => {
  const r = selectionRect.value
  return Boolean(r && r.c1 === 0 && r.c2 === cols.value - 1)
})
const isWholeColSelection = computed(() => {
  const r = selectionRect.value
  return Boolean(r && r.r1 === 0 && r.r2 === rows.value - 1)
})

const hasMultiSelection = computed(() => {
  const rect = selectionRect.value
  return Boolean(rect && (rect.r1 !== rect.r2 || rect.c1 !== rect.c2))
})

const canMerge = computed(() => hasMultiSelection.value)
const canSplit = computed(() => {
  const a = anchorCell.value
  if (!a) return false
  const master = props.element.cells[a.r]?.[a.c]
  if (!master) return false
  const m = Grid.resolveMaster(props.element.cells, a.r, a.c)
  const masterCell = props.element.cells[m.r][m.c]
  return (masterCell.rowSpan ?? 1) > 1 || (masterCell.colSpan ?? 1) > 1
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

function focusTableRoot() {
  nextTick(() => tableRootEl.value?.focus())
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
// Editor-only row/column gutters (never exported - the export path renders
// straight from element data, not this component).
const GUTTER_W_MM = 5.5
const GUTTER_H_MM = 4.5

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

const defaultBorderCss = computed(
  () => `${props.element.borderWidth || '1px'} ${props.element.borderStyle || 'solid'} ${props.element.borderColor || '#94a3b8'}`
)

/** Per-side border for one cell: its own override if set (including an explicit 'none'), else the table default. */
function cellBorderStyle(cell: TableCellModel) {
  const b = cell.borders
  return {
    borderTop: b?.top ?? defaultBorderCss.value,
    borderRight: b?.right ?? defaultBorderCss.value,
    borderBottom: b?.bottom ?? defaultBorderCss.value,
    borderLeft: b?.left ?? defaultBorderCss.value,
  }
}

/**
 * Effective background, highest precedence first: the cell's own explicit
 * fill, then the header-row treatment (row 0, if enabled), then zebra
 * striping on odd body rows (if enabled), then the table's base fill.
 */
function cellBackground(cell: TableCellModel, rIdx: number): string {
  if (cell.backgroundColor) return cell.backgroundColor
  if (props.element.headerRow && rIdx === 0) return props.element.headerColor || '#e5e7eb'
  if (props.element.zebra) {
    const bodyRow = props.element.headerRow ? rIdx - 1 : rIdx
    if (bodyRow >= 0 && bodyRow % 2 === 1) return props.element.zebraColor || '#f8fafc'
  }
  return props.element.tableBackground || 'transparent'
}

function cellFontWeight(cell: TableCellModel, rIdx: number): string | number {
  if (cell.fontWeight) return cell.fontWeight
  if (props.element.headerRow && rIdx === 0) return 'bold'
  return 'normal'
}

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

function onColumnResizeStart(colIdx: number, e: PointerEvent) {
  e.preventDefault()
  e.stopPropagation()
  activate()
  beginHandleDrag('col', colIdx, e)

  const startClientX = e.clientX
  const originalWidths = [...props.element.colWidths]
  const currentW = originalWidths[colIdx] || 20

  function onColMove(moveEvent: PointerEvent) {
    const deltaMm = pxToMm(moveEvent.clientX - startClientX)
    const newW = Math.max(MIN_COL_MM, currentW + deltaMm)
    const updatedWidths = [...originalWidths]
    updatedWidths[colIdx] = Math.round(newW * 10) / 10
    const totalW = updatedWidths.reduce((sum, w) => sum + w, 0)
    emit('update:element', { colWidths: updatedWidths, width: Math.round(totalW * 10) / 10 })
  }
  function onColUp() {
    window.removeEventListener('pointermove', onColMove)
    window.removeEventListener('pointerup', onColUp)
    endHandleDrag()
  }
  window.addEventListener('pointermove', onColMove)
  window.addEventListener('pointerup', onColUp)
}

function onRowResizeStart(rowIdx: number, e: PointerEvent) {
  e.preventDefault()
  e.stopPropagation()
  activate()
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
    emit('update:element', { rowHeights: updatedHeights, height: Math.round(totalH * 10) / 10 })
  }
  function onRowUp() {
    window.removeEventListener('pointermove', onRowMove)
    window.removeEventListener('pointerup', onRowUp)
    endHandleDrag()
  }
  window.addEventListener('pointermove', onRowMove)
  window.addEventListener('pointerup', onRowUp)
}

// ─── Cell selection & editing ───────────────────────────────────────────

function onCellDoubleClick(r: number, c: number, e: MouseEvent) {
  e.stopPropagation()
  activate()
  beginEdit(r, c)
}

function beginEdit(r: number, c: number) {
  const m = Grid.resolveMaster(props.element.cells, r, c)
  editingCellCoord.value = m
  anchorCell.value = m
  focusCell.value = m
  emitSelection()
  nextTick(() => {
    const el = tableRootEl.value?.querySelector<HTMLElement>('[data-cell-editor="true"]')
    el?.focus()
  })
}

function onCellPointerDown(r: number, c: number, e: PointerEvent) {
  if (props.readonly) return
  if (editingCellCoord.value) {
    const ec = editingCellCoord.value
    // A click INSIDE the cell currently being edited belongs to the caret -
    // let it place the text cursor instead of hijacking it into a selection
    // drag. A click on any OTHER cell, though, must first commit that edit;
    // otherwise this handler used to bail out entirely (leaving anchor/focus
    // pointed at the old cell), so the old cell kept showing as "selected"
    // and the click's own pointerdown fell through uncommitted, occasionally
    // still leaving the caret console mid-edit - the more the interaction
    // repeated, the more it looked like typing and clicking flickered the
    // selection between cells.
    if (ec.r === r && ec.c === c) return
    commitActiveEdit()
  }
  if (e.button !== 0) return

  e.stopPropagation()
  activate()

  if (e.shiftKey && anchorCell.value) {
    focusCell.value = { r, c }
  } else {
    anchorCell.value = { r, c }
    focusCell.value = { r, c }
    isDragSelecting.value = true
    window.addEventListener('pointerup', onSelectionPointerUp, { once: true })
  }
  emitSelection()
  focusTableRoot()
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
  if (rows.value < 1 || cols.value < 1) return
  anchorCell.value = { r: 0, c: 0 }
  focusCell.value = { r: rows.value - 1, c: cols.value - 1 }
  emitSelection()
  focusTableRoot()
}

function onCellBlur(r: number, c: number, e: FocusEvent) {
  const target = e.target as HTMLElement
  updateCell(r, c, target.innerHTML)
  editingCellCoord.value = null
}

/** Commits the currently-edited cell's live DOM content, if any is being edited. */
function commitActiveEdit() {
  if (!editingCellCoord.value) return
  const el = tableRootEl.value?.querySelector<HTMLElement>('[data-cell-editor="true"]')
  if (el) {
    updateCell(editingCellCoord.value.r, editingCellCoord.value.c, el.innerHTML)
  }
  editingCellCoord.value = null
}

function updateCell(r: number, c: number, html: string) {
  const next = Grid.cloneGridForWrite(props.element.cells)
  if (!next[r]?.[c]) return
  next[r][c].content = html
  emit('update:element', { cells: next })
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
    updateCell(r, c, target.innerHTML)
  }
}

/** Tab/Shift+Tab/Enter while editing a cell - commit and hop to the next cell, Excel-style. */
function onCellEditorKeyDown(r: number, c: number, e: KeyboardEvent) {
  if (e.key === 'Escape') {
    e.preventDefault()
    editingCellCoord.value = null
    focusTableRoot()
    return
  }
  if (e.key === 'Tab') {
    e.preventDefault()
    commitActiveEdit()
    const next = e.shiftKey ? stepCell(r, c, 0, -1) : stepCell(r, c, 0, 1)
    if (next) beginEdit(next.r, next.c)
    return
  }
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault()
    commitActiveEdit()
    const next = stepCell(r, c, 1, 0)
    if (next) {
      anchorCell.value = next
      focusCell.value = next
      emitSelection()
    }
    focusTableRoot()
  }
}

/** Next grid coordinate stepping by (dr, dc), wrapping columns and resolving onto whichever span it lands in. */
function stepCell(r: number, c: number, dr: number, dc: number): { r: number; c: number } | null {
  let nr = r, nc = c + dc
  if (nc >= cols.value) { nc = 0; nr += 1 }
  else if (nc < 0) { nc = cols.value - 1; nr -= 1 }
  nr += dr
  if (nr < 0 || nr >= rows.value) return null
  return Grid.resolveMaster(props.element.cells, nr, nc)
}

// ─── Keyboard: arrow nav, Shift+Arrow extend, Ctrl+A, Delete, Ctrl+C/X/V ──

function onTableKeyDown(e: KeyboardEvent) {
  if (editingCellCoord.value) return // contenteditable handles its own keys (see onCellEditorKeyDown)
  const a = anchorCell.value
  if (!a) return
  const isMod = e.ctrlKey || e.metaKey

  if (isMod && (e.key === 'a' || e.key === 'A')) {
    e.preventDefault(); e.stopPropagation()
    selectAllCells()
    return
  }
  if (isMod && (e.key === 'c' || e.key === 'C')) {
    const rect = selectionRect.value
    if (rect) {
      e.preventDefault(); e.stopPropagation()
      cellClipboard = Grid.extractBlock(props.element.cells, rect)
    }
    return
  }
  if (isMod && (e.key === 'x' || e.key === 'X')) {
    const rect = selectionRect.value
    if (rect) {
      e.preventDefault(); e.stopPropagation()
      cellClipboard = Grid.extractBlock(props.element.cells, rect)
      emit('update:element', { cells: Grid.clearBlockContent(props.element.cells, rect) })
    }
    return
  }
  if (isMod && (e.key === 'v' || e.key === 'V')) {
    if (cellClipboard) {
      e.preventDefault(); e.stopPropagation()
      emit('update:element', { cells: Grid.pasteBlock(props.element.cells, a.r, a.c, cellClipboard) })
    }
    return
  }
  if (e.key === 'Delete' || e.key === 'Backspace') {
    const rect = selectionRect.value
    if (rect) {
      e.preventDefault(); e.stopPropagation()
      emit('update:element', { cells: Grid.clearBlockContent(props.element.cells, rect) })
    }
    return
  }
  if (e.key === 'F2' || (e.key === 'Enter' && !isMod)) {
    e.preventDefault(); e.stopPropagation()
    beginEdit(a.r, a.c)
    return
  }
  if (e.key === 'ArrowUp' || e.key === 'ArrowDown' || e.key === 'ArrowLeft' || e.key === 'ArrowRight') {
    const dr = e.key === 'ArrowUp' ? -1 : e.key === 'ArrowDown' ? 1 : 0
    const dc = e.key === 'ArrowLeft' ? -1 : e.key === 'ArrowRight' ? 1 : 0
    e.preventDefault(); e.stopPropagation()
    if (e.shiftKey) {
      const f = focusCell.value || a
      const nr = Math.min(rows.value - 1, Math.max(0, f.r + dr))
      const nc = Math.min(cols.value - 1, Math.max(0, f.c + dc))
      focusCell.value = { r: nr, c: nc }
    } else {
      const nr = Math.min(rows.value - 1, Math.max(0, a.r + dr))
      const nc = Math.min(cols.value - 1, Math.max(0, a.c + dc))
      const resolved = Grid.resolveMaster(props.element.cells, nr, nc)
      anchorCell.value = resolved
      focusCell.value = resolved
    }
    emitSelection()
  }
}

// ─── Merge / split ───────────────────────────────────────────────────────

function mergeSelection() {
  const rect = selectionRect.value
  if (!rect || !canMerge.value) return
  emit('update:element', { cells: Grid.mergeCells(props.element.cells, rect) })
  anchorCell.value = { r: rect.r1, c: rect.c1 }
  focusCell.value = { r: rect.r1, c: rect.c1 }
  emitSelection()
}

function splitSelection() {
  const a = anchorCell.value
  if (!a || !canSplit.value) return
  emit('update:element', { cells: Grid.splitCell(props.element.cells, a.r, a.c) })
}

// ─── Row / column structural operations (quick toolbar) ─────────────────

function insertRowAfterSelection() {
  const rect = selectionRect.value
  const at = (rect ? rect.r2 : rows.value - 1) + 1
  const res = Grid.insertRow(props.element.cells, props.element.rowHeights, at, cols.value)
  emit('update:element', {
    rows: res.cells.length,
    rowHeights: res.rowHeights,
    cells: res.cells,
    height: Math.round(res.rowHeights.reduce((s, h) => s + h, 0) * 10) / 10,
  })
}

function insertColumnAfterSelection() {
  const rect = selectionRect.value
  const at = (rect ? rect.c2 : cols.value - 1) + 1
  const res = Grid.insertColumn(props.element.cells, props.element.colWidths, at, rows.value)
  emit('update:element', {
    cols: res.cells[0]?.length ?? cols.value + 1,
    colWidths: res.colWidths,
    cells: res.cells,
    width: Math.round(res.colWidths.reduce((s, w) => s + w, 0) * 10) / 10,
  })
}

function deleteSelectedRows() {
  const rect = selectionRect.value
  if (!rect) return
  const count = Math.min(rect.r2 - rect.r1 + 1, rows.value - 1)
  if (count <= 0) return
  let cells = props.element.cells
  let heights = props.element.rowHeights
  for (let i = 0; i < count; i++) {
    const res = Grid.deleteRow(cells, heights, rect.r1)
    cells = res.cells; heights = res.rowHeights
  }
  emit('update:element', {
    rows: cells.length,
    rowHeights: heights,
    cells,
    height: Math.round(heights.reduce((s, h) => s + h, 0) * 10) / 10,
  })
  const lastRow = Math.max(0, cells.length - 1)
  anchorCell.value = { r: Math.min(rect.r1, lastRow), c: rect.c1 }
  focusCell.value = { ...anchorCell.value }
  emitSelection()
}

function deleteSelectedColumns() {
  const rect = selectionRect.value
  if (!rect) return
  const count = Math.min(rect.c2 - rect.c1 + 1, cols.value - 1)
  if (count <= 0) return
  let cells = props.element.cells
  let widths = props.element.colWidths
  for (let i = 0; i < count; i++) {
    const res = Grid.deleteColumn(cells, widths, rect.c1)
    cells = res.cells; widths = res.colWidths
  }
  emit('update:element', {
    cols: cells[0]?.length ?? Math.max(1, cols.value - count),
    colWidths: widths,
    cells,
    width: Math.round(widths.reduce((s, w) => s + w, 0) * 10) / 10,
  })
  const lastCol = Math.max(0, (cells[0]?.length ?? 1) - 1)
  anchorCell.value = { r: rect.r1, c: Math.min(rect.c1, lastCol) }
  focusCell.value = { ...anchorCell.value }
  emitSelection()
}

// ─── Row / column headers: select, hover actions, drag reorder ──────────

function selectRow(r: number, shiftKey: boolean) {
  activate()
  if (shiftKey && anchorCell.value) {
    anchorCell.value = { r: anchorCell.value.r, c: 0 }
    focusCell.value = { r, c: cols.value - 1 }
  } else {
    anchorCell.value = { r, c: 0 }
    focusCell.value = { r, c: cols.value - 1 }
  }
  emitSelection()
  focusTableRoot()
}

function selectColumn(c: number, shiftKey: boolean) {
  activate()
  if (shiftKey && anchorCell.value) {
    anchorCell.value = { r: 0, c: anchorCell.value.c }
    focusCell.value = { r: rows.value - 1, c }
  } else {
    anchorCell.value = { r: 0, c }
    focusCell.value = { r: rows.value - 1, c }
  }
  emitSelection()
  focusTableRoot()
}

/**
 * A header click always selects first. Dragging from a header that is
 * ALREADY the sole selection reorders it instead of extending the selection -
 * the same two-step "select, then drag to move" convention spreadsheets use,
 * so a plain click-drag still means "select a range" the rest of the time.
 */
function startRowHeaderDrag(r: number, e: PointerEvent) {
  if (props.readonly) return
  if (e.button !== 0) return
  e.stopPropagation()

  const rect = selectionRect.value
  const alreadySoleSelected = Boolean(rect && rect.r1 === r && rect.r2 === r && rect.c1 === 0 && rect.c2 === cols.value - 1)

  if (!alreadySoleSelected) {
    selectRow(r, e.shiftKey)
    window.addEventListener('pointerup', onSelectionPointerUp, { once: true })
    isDragSelecting.value = true
    return
  }

  activate()
  rowDrag.value = { from: r, over: r }
  function onMove(moveEvent: PointerEvent) {
    const header = (moveEvent.target as HTMLElement)?.closest<HTMLElement>('[data-row-header]')
    if (header) {
      const idx = Number(header.dataset.rowHeader)
      if (!Number.isNaN(idx) && rowDrag.value) rowDrag.value = { ...rowDrag.value, over: idx }
    }
  }
  function onUp() {
    window.removeEventListener('pointermove', onMove)
    window.removeEventListener('pointerup', onUp)
    const drag = rowDrag.value
    rowDrag.value = null
    if (drag && drag.over !== drag.from) {
      const res = Grid.moveRow(props.element.cells, props.element.rowHeights, drag.from, drag.over)
      emit('update:element', { cells: res.cells, rowHeights: res.rowHeights })
      anchorCell.value = { r: drag.over, c: 0 }
      focusCell.value = { r: drag.over, c: cols.value - 1 }
      emitSelection()
    }
  }
  window.addEventListener('pointermove', onMove)
  window.addEventListener('pointerup', onUp)
}

function startColHeaderDrag(c: number, e: PointerEvent) {
  if (props.readonly) return
  if (e.button !== 0) return
  e.stopPropagation()

  const rect = selectionRect.value
  const alreadySoleSelected = Boolean(rect && rect.c1 === c && rect.c2 === c && rect.r1 === 0 && rect.r2 === rows.value - 1)

  if (!alreadySoleSelected) {
    selectColumn(c, e.shiftKey)
    window.addEventListener('pointerup', onSelectionPointerUp, { once: true })
    isDragSelecting.value = true
    return
  }

  activate()
  colDrag.value = { from: c, over: c }
  function onMove(moveEvent: PointerEvent) {
    const header = (moveEvent.target as HTMLElement)?.closest<HTMLElement>('[data-col-header]')
    if (header) {
      const idx = Number(header.dataset.colHeader)
      if (!Number.isNaN(idx) && colDrag.value) colDrag.value = { ...colDrag.value, over: idx }
    }
  }
  function onUp() {
    window.removeEventListener('pointermove', onMove)
    window.removeEventListener('pointerup', onUp)
    const drag = colDrag.value
    colDrag.value = null
    if (drag && drag.over !== drag.from) {
      const res = Grid.moveColumn(props.element.cells, props.element.colWidths, drag.from, drag.over)
      emit('update:element', { cells: res.cells, colWidths: res.colWidths })
      anchorCell.value = { r: 0, c: drag.over }
      focusCell.value = { r: rows.value - 1, c: drag.over }
      emitSelection()
    }
  }
  window.addEventListener('pointermove', onMove)
  window.addEventListener('pointerup', onUp)
}

const hoveredRow = ref<number | null>(null)
const hoveredCol = ref<number | null>(null)

function duplicateRowAt(r: number) {
  const res = Grid.duplicateRow(props.element.cells, props.element.rowHeights, r)
  emit('update:element', {
    rows: res.cells.length,
    rowHeights: res.rowHeights,
    cells: res.cells,
    height: Math.round(res.rowHeights.reduce((s, h) => s + h, 0) * 10) / 10,
  })
}

function cutRowAt(r: number) {
  if (rows.value <= 1) return
  rowClipboard = props.element.cells[r].map(cell => ({ ...cell, id: Grid.newCellId() }))
  const res = Grid.deleteRow(props.element.cells, props.element.rowHeights, r)
  emit('update:element', {
    rows: res.cells.length,
    rowHeights: res.rowHeights,
    cells: res.cells,
    height: Math.round(res.rowHeights.reduce((s, h) => s + h, 0) * 10) / 10,
  })
}

function deleteRowAtHeader(r: number) {
  if (rows.value <= 1) return
  const res = Grid.deleteRow(props.element.cells, props.element.rowHeights, r)
  emit('update:element', {
    rows: res.cells.length,
    rowHeights: res.rowHeights,
    cells: res.cells,
    height: Math.round(res.rowHeights.reduce((s, h) => s + h, 0) * 10) / 10,
  })
}

function pasteRowAt(r: number) {
  if (!rowClipboard) return
  const withSpace = Grid.insertRow(props.element.cells, props.element.rowHeights, r + 1, cols.value)
  const placed = withSpace.cells.map((row, idx) =>
    idx === r + 1 ? rowClipboard!.map(cell => ({ ...cell, id: Grid.newCellId() })) : row
  )
  emit('update:element', {
    rows: placed.length,
    rowHeights: withSpace.rowHeights,
    cells: placed,
    height: Math.round(withSpace.rowHeights.reduce((s, h) => s + h, 0) * 10) / 10,
  })
}

function duplicateColAt(c: number) {
  const res = Grid.duplicateColumn(props.element.cells, props.element.colWidths, c)
  emit('update:element', {
    cols: res.cells[0]?.length ?? cols.value + 1,
    colWidths: res.colWidths,
    cells: res.cells,
    width: Math.round(res.colWidths.reduce((s, w) => s + w, 0) * 10) / 10,
  })
}

function cutColAt(c: number) {
  if (cols.value <= 1) return
  colClipboard = props.element.cells.map(row => ({ ...row[c], id: Grid.newCellId() }))
  const res = Grid.deleteColumn(props.element.cells, props.element.colWidths, c)
  emit('update:element', {
    cols: res.cells[0]?.length ?? Math.max(1, cols.value - 1),
    colWidths: res.colWidths,
    cells: res.cells,
    width: Math.round(res.colWidths.reduce((s, w) => s + w, 0) * 10) / 10,
  })
}

function deleteColAtHeader(c: number) {
  if (cols.value <= 1) return
  const res = Grid.deleteColumn(props.element.cells, props.element.colWidths, c)
  emit('update:element', {
    cols: res.cells[0]?.length ?? Math.max(1, cols.value - 1),
    colWidths: res.colWidths,
    cells: res.cells,
    width: Math.round(res.colWidths.reduce((s, w) => s + w, 0) * 10) / 10,
  })
}

function pasteColAt(c: number) {
  if (!colClipboard) return
  const withSpace = Grid.insertColumn(props.element.cells, props.element.colWidths, c + 1, rows.value)
  const placed = withSpace.cells.map((row, r) => {
    const copy = [...row]
    copy[c + 1] = { ...colClipboard![r], id: Grid.newCellId() }
    return copy
  })
  emit('update:element', {
    cols: placed[0]?.length ?? cols.value + 1,
    colWidths: withSpace.colWidths,
    cells: placed,
    width: Math.round(withSpace.colWidths.reduce((s, w) => s + w, 0) * 10) / 10,
  })
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
  <div
    ref="tableRootEl"
    class="canvas-table-element w-full h-full relative font-serif select-none"
    tabindex="-1"
    @keydown="onTableKeyDown"
  >
    <!-- Floating Table Quick Toolbar -->
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
      <button type="button" @click="insertColumnAfterSelection()" class="px-1.5 py-0.5 rounded hover:bg-blue-50 hover:text-blue-600 dark:hover:bg-zinc-800 text-zinc-600 dark:text-zinc-300 font-semibold" title="Ustun qo'shish">
        + Ustun
      </button>
      <button type="button" @click="deleteSelectedColumns()" :disabled="element.cols <= 1" class="px-1.5 py-0.5 rounded hover:bg-rose-50 hover:text-rose-600 dark:hover:bg-zinc-800 text-zinc-500 disabled:opacity-30" title="Tanlangan ustun(lar)ni o'chirish">
        − Ustun
      </button>

      <div class="w-px h-3 bg-zinc-200 dark:bg-zinc-700"></div>

      <button type="button" @click="insertRowAfterSelection()" class="px-1.5 py-0.5 rounded hover:bg-blue-50 hover:text-blue-600 dark:hover:bg-zinc-800 text-zinc-600 dark:text-zinc-300 font-semibold" title="Qator qo'shish">
        + Qator
      </button>
      <button type="button" @click="deleteSelectedRows()" :disabled="element.rows <= 1" class="px-1.5 py-0.5 rounded hover:bg-rose-50 hover:text-rose-600 dark:hover:bg-zinc-800 text-zinc-500 disabled:opacity-30" title="Tanlangan qator(lar)ni o'chirish">
        − Qator
      </button>

      <div class="w-px h-3 bg-zinc-200 dark:bg-zinc-700"></div>

      <button
        type="button"
        @click="mergeSelection()"
        :disabled="!canMerge"
        class="p-1 rounded hover:bg-blue-50 hover:text-blue-600 dark:hover:bg-zinc-800 text-zinc-600 dark:text-zinc-300 disabled:opacity-30"
        title="Kataklarni birlashtirish"
      >
        <Combine class="w-3.5 h-3.5" />
      </button>
      <button
        type="button"
        @click="splitSelection()"
        :disabled="!canSplit"
        class="p-1 rounded hover:bg-blue-50 hover:text-blue-600 dark:hover:bg-zinc-800 text-zinc-600 dark:text-zinc-300 disabled:opacity-30"
        title="Katakni ajratish"
      >
        <Grid3x3 class="w-3.5 h-3.5" />
      </button>

      <div class="w-px h-3 bg-zinc-200 dark:bg-zinc-700"></div>

      <button type="button" @click="selectAllCells()" class="px-1.5 py-0.5 rounded hover:bg-blue-50 hover:text-blue-600 dark:hover:bg-zinc-800 text-zinc-600 dark:text-zinc-300 font-semibold" title="Barcha kataklarni tanlash (Ctrl+A)">
        Hammasi
      </button>

      <span v-if="hasMultiSelection" class="px-1.5 py-0.5 rounded bg-blue-50 dark:bg-blue-950/50 text-blue-600 dark:text-blue-300 font-bold tabular-nums">
        {{ (selectionRect!.r2 - selectionRect!.r1 + 1) }}×{{ (selectionRect!.c2 - selectionRect!.c1 + 1) }}
      </span>
    </div>

    <!-- Row / column header gutters (editor chrome only - never exported) -->
    <div
      v-if="isSelected && !readonly"
      class="absolute pointer-events-none z-40"
      :style="{
        left: `-${GUTTER_W_MM}mm`,
        top: `-${GUTTER_H_MM}mm`,
        width: `${GUTTER_W_MM}mm`,
        height: `${GUTTER_H_MM}mm`,
      }"
    >
      <button
        type="button"
        class="w-full h-full pointer-events-auto bg-zinc-100 dark:bg-zinc-800 border border-zinc-300 dark:border-zinc-600 hover:bg-blue-100 dark:hover:bg-blue-950/60 rounded-tl-md"
        title="Hammasini tanlash"
        @pointerdown.stop
        @click.stop="selectAllCells()"
      ></button>
    </div>

    <div
      v-if="isSelected && !readonly"
      class="absolute flex pointer-events-none z-40"
      :style="{ left: 0, top: `-${GUTTER_H_MM}mm`, width: `${element.width}mm`, height: `${GUTTER_H_MM}mm` }"
    >
      <div
        v-for="(w, cIdx) in element.colWidths"
        :key="'colhead_' + cIdx"
        :data-col-header="cIdx"
        class="relative shrink-0 flex items-center justify-center text-[8px] font-semibold text-zinc-500 dark:text-zinc-400 bg-zinc-100 dark:bg-zinc-800 border-t border-r border-b border-zinc-300 dark:border-zinc-600 pointer-events-auto cursor-pointer select-none"
        :class="[
          isWholeColSelection && isCellSelected(0, cIdx) ? 'bg-blue-200/70 dark:bg-blue-900/60 text-blue-700 dark:text-blue-300' : 'hover:bg-blue-50 dark:hover:bg-zinc-750',
          colDrag?.from === cIdx ? 'opacity-40' : '',
        ]"
        :style="{ width: `${mmToPx(w)}px` }"
        @pointerdown="startColHeaderDrag(cIdx, $event)"
      >
        <span v-if="colDrag?.over === cIdx && colDrag.from !== cIdx" class="absolute inset-y-0 left-0 w-0.5 bg-blue-600"></span>
        {{ cIdx + 1 }}

        <!-- Hover actions: duplicate / cut / delete / paste -->
        <div
          v-if="hoveredCol === cIdx && !colDrag"
          class="absolute top-full left-1/2 -translate-x-1/2 mt-0.5 flex items-center gap-0.5 bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-700 shadow-lg rounded-md p-0.5 z-50"
          @pointerdown.stop
        >
          <button type="button" class="p-0.5 rounded hover:bg-blue-50 dark:hover:bg-zinc-800 text-zinc-500" title="Ustunni nusxalash" @click.stop="duplicateColAt(cIdx)"><Copy class="w-3 h-3" /></button>
          <button type="button" class="p-0.5 rounded hover:bg-amber-50 dark:hover:bg-zinc-800 text-zinc-500" title="Ustunni kesish" @click.stop="cutColAt(cIdx)"><Scissors class="w-3 h-3" /></button>
          <button v-if="colClipboard" type="button" class="p-0.5 rounded hover:bg-emerald-50 dark:hover:bg-zinc-800 text-zinc-500" title="Bu yerga joylash" @click.stop="pasteColAt(cIdx)"><ClipboardPaste class="w-3 h-3" /></button>
          <button type="button" class="p-0.5 rounded hover:bg-rose-50 dark:hover:bg-zinc-800 text-rose-500 disabled:opacity-30" :disabled="element.cols <= 1" title="Ustunni o'chirish" @click.stop="deleteColAtHeader(cIdx)"><Trash2 class="w-3 h-3" /></button>
        </div>

        <div class="absolute inset-y-0 -right-1 w-2 pointer-events-auto" @pointerenter="hoveredCol = cIdx" @pointerleave="hoveredCol = null"></div>
      </div>
    </div>

    <div
      v-if="isSelected && !readonly"
      class="absolute flex flex-col pointer-events-none z-40"
      :style="{ left: `-${GUTTER_W_MM}mm`, top: 0, width: `${GUTTER_W_MM}mm`, height: `${element.height}mm` }"
    >
      <div
        v-for="(h, rIdx) in element.rowHeights"
        :key="'rowhead_' + rIdx"
        :data-row-header="rIdx"
        class="relative shrink-0 flex items-center justify-center text-[8px] font-semibold text-zinc-500 dark:text-zinc-400 bg-zinc-100 dark:bg-zinc-800 border-l border-t border-b border-zinc-300 dark:border-zinc-600 pointer-events-auto cursor-pointer select-none"
        :class="[
          isWholeRowSelection && isCellSelected(rIdx, 0) ? 'bg-blue-200/70 dark:bg-blue-900/60 text-blue-700 dark:text-blue-300' : 'hover:bg-blue-50 dark:hover:bg-zinc-750',
          rowDrag?.from === rIdx ? 'opacity-40' : '',
        ]"
        :style="{ height: `${mmToPx(h)}px` }"
        @pointerdown="startRowHeaderDrag(rIdx, $event)"
        @pointerenter="hoveredRow = rIdx"
        @pointerleave="hoveredRow = null"
      >
        <span v-if="rowDrag?.over === rIdx && rowDrag.from !== rIdx" class="absolute inset-x-0 top-0 h-0.5 bg-blue-600"></span>
        {{ rIdx + 1 }}

        <div
          v-if="hoveredRow === rIdx && !rowDrag"
          class="absolute left-full top-1/2 -translate-y-1/2 ml-0.5 flex items-center gap-0.5 bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-700 shadow-lg rounded-md p-0.5 z-50"
          @pointerdown.stop
        >
          <button type="button" class="p-0.5 rounded hover:bg-blue-50 dark:hover:bg-zinc-800 text-zinc-500" title="Qatorni nusxalash" @click.stop="duplicateRowAt(rIdx)"><Copy class="w-3 h-3" /></button>
          <button type="button" class="p-0.5 rounded hover:bg-amber-50 dark:hover:bg-zinc-800 text-zinc-500" title="Qatorni kesish" @click.stop="cutRowAt(rIdx)"><Scissors class="w-3 h-3" /></button>
          <button v-if="rowClipboard" type="button" class="p-0.5 rounded hover:bg-emerald-50 dark:hover:bg-zinc-800 text-zinc-500" title="Bu yerga joylash" @click.stop="pasteRowAt(rIdx)"><ClipboardPaste class="w-3 h-3" /></button>
          <button type="button" class="p-0.5 rounded hover:bg-rose-50 dark:hover:bg-zinc-800 text-rose-500 disabled:opacity-30" :disabled="element.rows <= 1" title="Qatorni o'chirish" @click.stop="deleteRowAtHeader(rIdx)"><Trash2 class="w-3 h-3" /></button>
        </div>
      </div>
    </div>

    <!-- Table Render -->
    <table
      class="w-full h-full border-collapse"
      :style="{ tableLayout: 'fixed' }"
    >
      <colgroup>
        <col v-for="(w, colIdx) in element.colWidths" :key="colIdx" :style="{ width: `${mmToPx(w)}px` }" />
      </colgroup>
      <tbody>
        <tr v-for="(row, rIdx) in element.cells" :key="rIdx" :style="{ height: `${mmToPx(element.rowHeights[rIdx] || 10)}px` }">
          <td
            v-for="(cell, cIdx) in row"
            v-show="!cell.coveredBy"
            :key="cell.id"
            class="relative transition-colors"
            :colspan="cell.colSpan && cell.colSpan > 1 ? cell.colSpan : undefined"
            :rowspan="cell.rowSpan && cell.rowSpan > 1 ? cell.rowSpan : undefined"
            :class="[
              isSelected && isCellSelected(rIdx, cIdx) ? 'canvas-cell-selected' : '',
              isSelected && anchorCell?.r === rIdx && anchorCell?.c === cIdx ? 'ring-2 ring-blue-500 ring-inset' : ''
            ]"
            :style="{
              ...cellBorderStyle(cell),
              backgroundColor: cellBackground(cell, rIdx),
              textAlign: cell.textAlign || 'left',
              verticalAlign: cell.verticalAlign || 'top',
              color: cell.color || '#111827',
              fontFamily: `'Times New Roman', Times, serif`,
              fontSize: `${cell.fontSize ? cell.fontSize * PT_TO_PX : cellFontSizePx}px`,
              fontWeight: cellFontWeight(cell, rIdx),
              fontStyle: cell.fontStyle || 'normal',
              textDecoration: cell.textDecoration || 'none',
              padding: `${cellPaddingPx}px`
            }"
            @pointerdown="onCellPointerDown(rIdx, cIdx, $event)"
            @pointerenter="onCellPointerEnter(rIdx, cIdx)"
            @dblclick="onCellDoubleClick(rIdx, cIdx, $event)"
          >
            <div
              v-if="editingCellCoord?.r === rIdx && editingCellCoord?.c === cIdx"
              data-cell-editor="true"
              contenteditable="true"
              class="w-full h-full min-h-[18px] outline-none select-text cursor-text bg-white dark:bg-zinc-800 p-0.5 rounded-xs"
              @blur="onCellBlur(rIdx, cIdx, $event)"
              @paste="onCellPaste(rIdx, cIdx, $event)"
              @keydown="onCellEditorKeyDown(rIdx, cIdx, $event)"
              @pointerdown.stop
              v-html="cell.content"
            ></div>
            <div v-else class="w-full h-full min-h-[18px] break-words" v-html="renderCellContent(cell.content)"></div>

            <div
              v-if="rIdx === 0 && isSelected && !readonly && !(cell.colSpan && cell.colSpan > 1)"
              class="canvas-col-grip absolute -top-px right-0 bottom-0 w-2 cursor-col-resize z-30 pointer-events-auto"
              :class="resizing?.axis === 'col' && resizing.index === cIdx ? 'is-active' : ''"
              @pointerdown="onColumnResizeStart(cIdx, $event)"
            ><span class="grip-line"></span></div>

            <div
              v-if="cIdx === 0 && isSelected && !readonly && !(cell.rowSpan && cell.rowSpan > 1)"
              class="canvas-row-grip absolute left-0 -right-px bottom-0 h-2 cursor-row-resize z-30 pointer-events-auto"
              :class="resizing?.axis === 'row' && resizing.index === rIdx ? 'is-active' : ''"
              @pointerdown="onRowResizeStart(rIdx, $event)"
            ><span class="grip-line"></span></div>
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

/* The ancestor element wrapper sets pointer-events:none on its content slot
   once selected-but-not-editing (so a merely-selected text/shape element can
   be dragged by its body without entering edit mode). A table has no such
   "body vs content" distinction - every pixel is an interactive cell - so it
   opts back into pointer events unconditionally. Without this, EVERY click
   on a table's cells was silently swallowed the moment the table became
   selected (which happens immediately on insert), only working again after
   an unrelated double-click happened to set edit mode first. */
.canvas-table-element {
  pointer-events: auto !important;
}

.canvas-table-element td.canvas-cell-selected {
  box-shadow: inset 0 0 0 9999px rgba(37, 99, 235, 0.13);
}

.canvas-col-grip .grip-line,
.canvas-row-grip .grip-line {
  position: absolute;
  background: transparent;
  transition: background-color 0.12s ease;
}
.canvas-col-grip .grip-line { top: 0; bottom: 0; right: 0; width: 2px; }
.canvas-row-grip .grip-line { left: 0; right: 0; bottom: 0; height: 2px; }

.canvas-col-grip:hover .grip-line,
.canvas-row-grip:hover .grip-line,
.canvas-col-grip.is-active .grip-line,
.canvas-row-grip.is-active .grip-line {
  background: #2563eb;
}

body.canvas-resizing-col,
body.canvas-resizing-col * { cursor: col-resize !important; }
body.canvas-resizing-row,
body.canvas-resizing-row * { cursor: row-resize !important; }
body.canvas-resizing-col,
body.canvas-resizing-row { user-select: none; }
</style>
