/**
 * Pure grid algebra for canvas tables: merge/split, row/column insert, delete,
 * duplicate, move, and block copy/paste. No Vue, no DOM - every function takes
 * a grid and returns a new one, so this is unit-testable in plain Node and the
 * Vue layer only wires user gestures to these calls.
 *
 * Grid model: `cells` is always a dense rows×cols array - every slot has an
 * entry. A merged region's top-left slot (the "master") carries the real
 * content plus colSpan/rowSpan; every other slot the merge covers carries
 * `coveredBy: {r, c}` pointing at the master, empty content, and no span of
 * its own. This mirrors how a real `<table>` needs its `<tr>`/`<td>` laid out
 * (a covered slot renders no `<td>` at all - the master's span consumes that
 * grid space), so render code just needs to skip covered slots, and every
 * other piece of code (selection, arrow-key nav, insert/delete) can treat
 * `cells[r][c]` as a literal, always-valid grid coordinate.
 *
 * Row/column insert, delete, duplicate and move never grow or shrink an
 * existing merge: any span the operation would cross is split back to plain
 * cells first. This trades away "inserting a row inside a merge grows it"
 * for code where a structural edit can never leave a dangling or
 * out-of-bounds span - the right trade for a contract editor, not a
 * spreadsheet.
 */
import type { TableCellModel } from '../types/contractCanvas'

export interface Rect {
  r1: number
  c1: number
  r2: number
  c2: number
}

let idCounter = 0
export function newCellId(): string {
  idCounter += 1
  return `cell_${Date.now().toString(36)}_${idCounter.toString(36)}_${Math.random().toString(36).slice(2, 6)}`
}

export function makeCell(overrides: Partial<TableCellModel> = {}): TableCellModel {
  return { id: newCellId(), content: '&nbsp;', ...overrides }
}

export function createGrid(rows: number, cols: number): TableCellModel[][] {
  return Array.from({ length: rows }, () => Array.from({ length: cols }, () => makeCell()))
}

export function normalizeRect(r1: number, c1: number, r2: number, c2: number): Rect {
  return { r1: Math.min(r1, r2), c1: Math.min(c1, c2), r2: Math.max(r1, r2), c2: Math.max(c1, c2) }
}

export function isCovered(cell: TableCellModel): boolean {
  return Boolean(cell.coveredBy)
}

function inBounds(cells: TableCellModel[][], r: number, c: number): boolean {
  return r >= 0 && r < cells.length && c >= 0 && c < (cells[0]?.length ?? 0)
}

/** Resolves a possibly-covered slot to the grid coordinate of its span's master. */
export function resolveMaster(cells: TableCellModel[][], r: number, c: number): { r: number; c: number } {
  const cell = cells[r]?.[c]
  if (cell?.coveredBy) return { r: cell.coveredBy.r, c: cell.coveredBy.c }
  return { r, c }
}

/** The full rectangle a span occupies, given any coordinate inside it (covered or master). */
export function spanRect(cells: TableCellModel[][], r: number, c: number): Rect {
  const m = resolveMaster(cells, r, c)
  const master = cells[m.r]?.[m.c]
  const rowSpan = master?.rowSpan ?? 1
  const colSpan = master?.colSpan ?? 1
  return { r1: m.r, c1: m.c, r2: m.r + rowSpan - 1, c2: m.c + colSpan - 1 }
}

/** Grows `rect` until it contains every span it partially overlaps (fixed point). */
export function expandRectToWholeSpans(cells: TableCellModel[][], rect: Rect): Rect {
  let { r1, c1, r2, c2 } = rect
  let changed = true
  while (changed) {
    changed = false
    for (let r = r1; r <= r2; r++) {
      for (let c = c1; c <= c2; c++) {
        if (!inBounds(cells, r, c)) continue
        const s = spanRect(cells, r, c)
        if (s.r1 < r1) { r1 = s.r1; changed = true }
        if (s.c1 < c1) { c1 = s.c1; changed = true }
        if (s.r2 > r2) { r2 = s.r2; changed = true }
        if (s.c2 > c2) { c2 = s.c2; changed = true }
      }
    }
  }
  return { r1, c1, r2, c2 }
}

/** Deep-clones a grid for a safe, isolated mutation (ids kept - this is not a duplicate). */
export function cloneGridForWrite(cells: TableCellModel[][]): TableCellModel[][] {
  return cloneGrid(cells)
}

function cloneGrid(cells: TableCellModel[][]): TableCellModel[][] {
  return cells.map(row => row.map(cell => ({ ...cell, borders: cell.borders ? { ...cell.borders } : undefined, coveredBy: cell.coveredBy ? { ...cell.coveredBy } : undefined })))
}

/** Resets every span whose footprint overlaps `rect` back to plain 1x1 cells. */
function splitSpansOverlapping(cells: TableCellModel[][], rect: Rect): TableCellModel[][] {
  const next = cloneGrid(cells)
  const masters = new Set<string>()
  for (let r = rect.r1; r <= rect.r2; r++) {
    for (let c = rect.c1; c <= rect.c2; c++) {
      if (!inBounds(next, r, c)) continue
      const m = resolveMaster(next, r, c)
      const master = next[m.r][m.c]
      if ((master.rowSpan ?? 1) > 1 || (master.colSpan ?? 1) > 1) masters.add(`${m.r},${m.c}`)
    }
  }
  masters.forEach(key => {
    const [mr, mc] = key.split(',').map(Number)
    splitAt(next, mr, mc)
  })
  return next
}

/** In-place split of the span at (r,c) - internal helper, operates on an already-cloned grid. */
function splitAt(cells: TableCellModel[][], r: number, c: number) {
  const m = resolveMaster(cells, r, c)
  const master = cells[m.r][m.c]
  const rowSpan = master.rowSpan ?? 1
  const colSpan = master.colSpan ?? 1
  if (rowSpan <= 1 && colSpan <= 1) return
  master.rowSpan = undefined
  master.colSpan = undefined
  for (let rr = m.r; rr < m.r + rowSpan; rr++) {
    for (let cc = m.c; cc < m.c + colSpan; cc++) {
      if (rr === m.r && cc === m.c) continue
      if (!inBounds(cells, rr, cc)) continue
      cells[rr][cc] = makeCell()
    }
  }
}

/** Merges the rectangle (expanded to whole-span boundaries) into one cell. */
export function mergeCells(cells: TableCellModel[][], rect: Rect): TableCellModel[][] {
  const full = expandRectToWholeSpans(cells, rect)
  const next = splitSpansOverlapping(cells, full)
  const master = next[full.r1][full.c1]
  master.rowSpan = full.r2 - full.r1 + 1 > 1 ? full.r2 - full.r1 + 1 : undefined
  master.colSpan = full.c2 - full.c1 + 1 > 1 ? full.c2 - full.c1 + 1 : undefined
  for (let r = full.r1; r <= full.r2; r++) {
    for (let c = full.c1; c <= full.c2; c++) {
      if (r === full.r1 && c === full.c1) continue
      next[r][c] = makeCell({ content: '', coveredBy: { r: full.r1, c: full.c1 } })
    }
  }
  return next
}

/** Splits whatever span the given coordinate belongs to, if any. */
export function splitCell(cells: TableCellModel[][], r: number, c: number): TableCellModel[][] {
  const next = cloneGrid(cells)
  splitAt(next, r, c)
  return next
}

// ─── Row operations ──────────────────────────────────────────────────────

/** Splits every span whose vertical extent strictly contains any of `boundaries`. */
function splitRowSpansCrossing(cells: TableCellModel[][], boundaries: number[]): TableCellModel[][] {
  let next = cells
  for (const b of boundaries) {
    const masters = new Set<string>()
    for (let r = 0; r < next.length; r++) {
      for (let c = 0; c < (next[0]?.length ?? 0); c++) {
        const s = spanRect(next, r, c)
        if (s.r1 < b && s.r2 >= b) masters.add(`${s.r1},${s.c1}`)
      }
    }
    if (masters.size === 0) continue
    next = cloneGrid(next)
    masters.forEach(key => {
      const [mr, mc] = key.split(',').map(Number)
      splitAt(next, mr, mc)
    })
  }
  return next
}

export function insertRow(
  cells: TableCellModel[][],
  rowHeights: number[],
  atIndex: number,
  cols: number
): { cells: TableCellModel[][]; rowHeights: number[] } {
  const safe = splitRowSpansCrossing(cells, [atIndex])
  const next = cloneGrid(safe)
  next.splice(atIndex, 0, Array.from({ length: cols }, () => makeCell()))
  const heights = [...rowHeights]
  heights.splice(atIndex, 0, rowHeights[Math.min(atIndex, rowHeights.length - 1)] ?? 10)
  return { cells: next, rowHeights: heights }
}

export function deleteRow(
  cells: TableCellModel[][],
  rowHeights: number[],
  atIndex: number
): { cells: TableCellModel[][]; rowHeights: number[] } {
  if (cells.length <= 1) return { cells, rowHeights }
  const safe = splitRowSpansCrossing(cells, [atIndex, atIndex + 1])
  const next = cloneGrid(safe)
  next.splice(atIndex, 1)
  next.forEach(row => row.forEach(cell => {
    if (cell.coveredBy && cell.coveredBy.r > atIndex) cell.coveredBy = { ...cell.coveredBy, r: cell.coveredBy.r - 1 }
  }))
  const heights = [...rowHeights]
  heights.splice(atIndex, 1)
  return { cells: next, rowHeights: heights }
}

export function duplicateRow(
  cells: TableCellModel[][],
  rowHeights: number[],
  atIndex: number
): { cells: TableCellModel[][]; rowHeights: number[] } {
  const safe = splitRowSpansCrossing(cells, [atIndex + 1])
  const next = cloneGrid(safe)
  const source = next[atIndex] ?? []
  const copy = source.map(cell => makeCell({
    content: cell.coveredBy ? '' : cell.content,
    backgroundColor: cell.backgroundColor,
    color: cell.color,
    textAlign: cell.textAlign,
    verticalAlign: cell.verticalAlign,
    fontWeight: cell.fontWeight,
    fontStyle: cell.fontStyle,
    textDecoration: cell.textDecoration,
    fontSize: cell.fontSize,
    borders: cell.borders ? { ...cell.borders } : undefined,
  }))
  next.splice(atIndex + 1, 0, copy)
  const heights = [...rowHeights]
  heights.splice(atIndex + 1, 0, rowHeights[atIndex] ?? 10)
  return { cells: next, rowHeights: heights }
}

export function moveRow(
  cells: TableCellModel[][],
  rowHeights: number[],
  from: number,
  to: number
): { cells: TableCellModel[][]; rowHeights: number[] } {
  if (from === to) return { cells, rowHeights }
  const boundaries = [from, from + 1, to, to + 1]
  const safe = splitRowSpansCrossing(cells, boundaries)
  const next = cloneGrid(safe)
  const heights = [...rowHeights]
  // `to` is the row's target index in the FINAL array, so no off-by-one
  // correction is needed: splicing the removed element back in at `to` lands
  // it there directly, including "append" when to >= the shortened length.
  const [row] = next.splice(from, 1)
  const [h] = heights.splice(from, 1)
  next.splice(to, 0, row)
  heights.splice(to, 0, h)
  return { cells: next, rowHeights: heights }
}

// ─── Column operations (mirror of the row operations above) ────────────────

function splitColSpansCrossing(cells: TableCellModel[][], boundaries: number[]): TableCellModel[][] {
  let next = cells
  for (const b of boundaries) {
    const masters = new Set<string>()
    for (let r = 0; r < next.length; r++) {
      for (let c = 0; c < (next[0]?.length ?? 0); c++) {
        const s = spanRect(next, r, c)
        if (s.c1 < b && s.c2 >= b) masters.add(`${s.r1},${s.c1}`)
      }
    }
    if (masters.size === 0) continue
    next = cloneGrid(next)
    masters.forEach(key => {
      const [mr, mc] = key.split(',').map(Number)
      splitAt(next, mr, mc)
    })
  }
  return next
}

export function insertColumn(
  cells: TableCellModel[][],
  colWidths: number[],
  atIndex: number,
  rows: number
): { cells: TableCellModel[][]; colWidths: number[] } {
  const safe = splitColSpansCrossing(cells, [atIndex])
  const next = cloneGrid(safe)
  for (let r = 0; r < rows; r++) {
    if (!next[r]) next[r] = []
    next[r].splice(atIndex, 0, makeCell())
  }
  const widths = [...colWidths]
  widths.splice(atIndex, 0, colWidths[Math.min(atIndex, colWidths.length - 1)] ?? 20)
  return { cells: next, colWidths: widths }
}

export function deleteColumn(
  cells: TableCellModel[][],
  colWidths: number[],
  atIndex: number
): { cells: TableCellModel[][]; colWidths: number[] } {
  if ((cells[0]?.length ?? 0) <= 1) return { cells, colWidths }
  const safe = splitColSpansCrossing(cells, [atIndex, atIndex + 1])
  const next = cloneGrid(safe)
  next.forEach(row => {
    row.splice(atIndex, 1)
    row.forEach(cell => {
      if (cell.coveredBy && cell.coveredBy.c > atIndex) cell.coveredBy = { ...cell.coveredBy, c: cell.coveredBy.c - 1 }
    })
  })
  const widths = [...colWidths]
  widths.splice(atIndex, 1)
  return { cells: next, colWidths: widths }
}

export function duplicateColumn(
  cells: TableCellModel[][],
  colWidths: number[],
  atIndex: number
): { cells: TableCellModel[][]; colWidths: number[] } {
  const safe = splitColSpansCrossing(cells, [atIndex + 1])
  const next = cloneGrid(safe)
  next.forEach(row => {
    const source = row[atIndex]
    const copy = makeCell({
      content: source?.coveredBy ? '' : source?.content,
      backgroundColor: source?.backgroundColor,
      color: source?.color,
      textAlign: source?.textAlign,
      verticalAlign: source?.verticalAlign,
      fontWeight: source?.fontWeight,
      fontStyle: source?.fontStyle,
      textDecoration: source?.textDecoration,
      fontSize: source?.fontSize,
      borders: source?.borders ? { ...source.borders } : undefined,
    })
    row.splice(atIndex + 1, 0, copy)
  })
  const widths = [...colWidths]
  widths.splice(atIndex + 1, 0, colWidths[atIndex] ?? 20)
  return { cells: next, colWidths: widths }
}

export function moveColumn(
  cells: TableCellModel[][],
  colWidths: number[],
  from: number,
  to: number
): { cells: TableCellModel[][]; colWidths: number[] } {
  if (from === to) return { cells, colWidths }
  const boundaries = [from, from + 1, to, to + 1]
  const safe = splitColSpansCrossing(cells, boundaries)
  const next = cloneGrid(safe)
  const widths = [...colWidths]
  next.forEach(row => {
    const [cell] = row.splice(from, 1)
    row.splice(to, 0, cell)
  })
  const [w] = widths.splice(from, 1)
  widths.splice(to, 0, w)
  return { cells: next, colWidths: widths }
}

// ─── Block copy / paste / clear (Ctrl+C / Ctrl+X / Ctrl+V / Delete) ────────

/** Deep-copies the rectangle (expanded to whole spans) with coordinates rebased to (0,0). */
export function extractBlock(cells: TableCellModel[][], rect: Rect): TableCellModel[][] {
  const full = expandRectToWholeSpans(cells, rect)
  const block: TableCellModel[][] = []
  for (let r = full.r1; r <= full.r2; r++) {
    const row: TableCellModel[] = []
    for (let c = full.c1; c <= full.c2; c++) {
      const cell = cells[r][c]
      row.push({
        ...cell,
        id: newCellId(),
        coveredBy: cell.coveredBy ? { r: cell.coveredBy.r - full.r1, c: cell.coveredBy.c - full.c1 } : undefined,
        borders: cell.borders ? { ...cell.borders } : undefined,
      })
    }
    block.push(row)
  }
  return block
}

/** Pastes `block` with its top-left at (atR, atC), clipped to grid bounds. Splits any destination span it would partially overwrite first. */
export function pasteBlock(
  cells: TableCellModel[][],
  atR: number,
  atC: number,
  block: TableCellModel[][]
): TableCellModel[][] {
  const rows = cells.length
  const cols = cells[0]?.length ?? 0
  const blockRows = block.length
  const blockCols = block[0]?.length ?? 0
  const destRect: Rect = {
    r1: atR,
    c1: atC,
    r2: Math.min(rows - 1, atR + blockRows - 1),
    c2: Math.min(cols - 1, atC + blockCols - 1),
  }
  const next = splitSpansOverlapping(cells, destRect)
  for (let r = destRect.r1; r <= destRect.r2; r++) {
    for (let c = destRect.c1; c <= destRect.c2; c++) {
      const src = block[r - atR][c - atC]
      if (src.coveredBy) continue // covered slots inside the pasted block are placed via their master below
      next[r][c] = { ...src, id: newCellId(), borders: src.borders ? { ...src.borders } : undefined, coveredBy: undefined }
    }
  }
  // Re-lay any spans the block itself carried, clipped to the destination bounds.
  for (let r = destRect.r1; r <= destRect.r2; r++) {
    for (let c = destRect.c1; c <= destRect.c2; c++) {
      const src = block[r - atR][c - atC]
      if (src.coveredBy) {
        const mr = atR + src.coveredBy.r
        const mc = atC + src.coveredBy.c
        if (mr >= destRect.r1 && mr <= destRect.r2 && mc >= destRect.c1 && mc <= destRect.c2) {
          next[r][c] = { ...src, id: newCellId(), content: '', coveredBy: { r: mr, c: mc } }
        } else {
          // the master fell outside the paste area - treat this slot as plain
          next[r][c] = makeCell()
        }
      }
    }
  }
  return next
}

/** Blanks the content of every non-covered cell in the rectangle; formatting is left alone. */
export function clearBlockContent(cells: TableCellModel[][], rect: Rect): TableCellModel[][] {
  const next = cloneGrid(cells)
  for (let r = rect.r1; r <= rect.r2; r++) {
    for (let c = rect.c1; c <= rect.c2; c++) {
      if (!inBounds(next, r, c)) continue
      if (next[r][c].coveredBy) continue
      next[r][c].content = ''
    }
  }
  return next
}
