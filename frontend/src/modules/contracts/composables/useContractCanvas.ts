import { ref, computed, watch } from 'vue'
import type {
  ContractDocumentModel,
  CanvasPageModel,
  CanvasElement,
  TextCanvasElement,
  TableCanvasElement,
  TableCellModel,
  AlignmentGuide,
  PageMargins,
  ResizeHandle,
} from '../types/contractCanvas'
import { useCanvasHistory } from './useCanvasHistory'
import { CANVAS_ELEMENT_CLIPBOARD_KEY, CANVAS_ELEMENT_CLIPBOARD_VALUE } from '../utils/clipboardUtils'


const MM_TO_PX_BASE = 3.779527559 // 96 DPI standard: 1mm ≈ 3.7795px
const PAGE_WIDTH_MM = 210
const PAGE_HEIGHT_MM = 297
const SNAP_THRESHOLD_MM = 2.0 // Snap distance threshold

export function useContractCanvas(initialDoc?: ContractDocumentModel) {
  const document = ref<ContractDocumentModel>(
    initialDoc || {
      version: 2,
      type: 'canvas-contract',
      pageSize: { width: PAGE_WIDTH_MM, height: PAGE_HEIGHT_MM, unit: 'mm' },
      margins: { top: 20, right: 15, bottom: 20, left: 25 },
      pages: [
        {
          id: `page_${Date.now()}`,
          pageNumber: 1,
          elements: [],
        },
      ],
      defaultFontFamily: 'Times New Roman',
      defaultFontSize: 12,
    }
  )

  const activePageIndex = ref<number>(0)
  const selectedElementIds = ref<string[]>([])
  const editingElementId = ref<string | null>(null)

  // Viewport & Guides
  const zoomLevel = ref<number>(100)
  const showMarginGuides = ref<boolean>(false)
  const showRulers = ref<boolean>(false)
  const showGrid = ref<boolean>(false)
  const snapToGrid = ref<boolean>(true)
  const gridSizeMm = ref<number>(2) // 2mm grid

  // Interaction State
  const isDragging = ref<boolean>(false)
  const isResizing = ref<boolean>(false)
  const activeGuides = ref<AlignmentGuide[]>([])
  const clipboard = ref<CanvasElement[]>([])

  // Undo / Redo history
  const history = useCanvasHistory(50)

  // Record initial snapshot
  history.recordSnapshot(document.value)

  // Helper: Find element and its hosting page across the entire document
  function findElementAndPage(id: string): { element: CanvasElement; page: CanvasPageModel; pageIndex: number } | null {
    if (!id || !document.value?.pages) return null
    for (let i = 0; i < document.value.pages.length; i++) {
      const p = document.value.pages[i]
      const el = p.elements.find(e => e.id === id)
      if (el) return { element: el, page: p, pageIndex: i }
    }
    return null
  }

  function setActivePageIndex(index: number) {
    if (index >= 0 && index < document.value.pages.length) {
      activePageIndex.value = index
    }
  }

  // Active page
  const activePage = computed<CanvasPageModel>(() => {
    const idx = Math.max(0, Math.min(activePageIndex.value, document.value.pages.length - 1))
    return document.value.pages[idx] || document.value.pages[0]
  })

  // Selected element(s) — searches all pages so selection never breaks across pages
  const selectedElements = computed<CanvasElement[]>(() => {
    const set = new Set(selectedElementIds.value)
    if (set.size === 0) return []
    const results: CanvasElement[] = []
    document.value.pages.forEach(p => {
      p.elements.forEach(el => {
        if (set.has(el.id)) results.push(el)
      })
    })
    return results
  })

  const selectedElement = computed<CanvasElement | null>(() => {
    return selectedElements.value.length === 1 ? selectedElements.value[0] : null
  })

  // Conversion helpers between mm and scaled px
  function mmToPx(mm: number): number {
    return mm * MM_TO_PX_BASE * (zoomLevel.value / 100)
  }

  function pxToMm(px: number): number {
    return px / (MM_TO_PX_BASE * (zoomLevel.value / 100))
  }

  // Selection
  function selectElement(id: string, multi = false, pageIndexHint?: number) {
    if (pageIndexHint !== undefined && pageIndexHint >= 0 && pageIndexHint < document.value.pages.length) {
      activePageIndex.value = pageIndexHint
    } else {
      const found = findElementAndPage(id)
      if (found) {
        activePageIndex.value = found.pageIndex
      }
    }
    if (multi) {
      if (selectedElementIds.value.includes(id)) {
        selectedElementIds.value = selectedElementIds.value.filter(item => item !== id)
      } else {
        selectedElementIds.value.push(id)
      }
    } else {
      selectedElementIds.value = [id]
    }
    editingElementId.value = null
    try {
      window.getSelection()?.removeAllRanges()
    } catch {}
  }

  function selectAll(targetPageIndex?: number) {
    const pIdx = targetPageIndex !== undefined ? targetPageIndex : activePageIndex.value
    const page = document.value.pages[pIdx] || activePage.value
    if (page && page.elements.length > 0) {
      selectedElementIds.value = page.elements.map(el => el.id)
      activePageIndex.value = pIdx
    }
  }

  function clearSelection() {
    selectedElementIds.value = []
    editingElementId.value = null
    activeGuides.value = []
    try {
      window.getSelection()?.removeAllRanges()
    } catch {}
  }

  function isElementSelected(id: string): boolean {
    return selectedElementIds.value.includes(id)
  }

  // Page Operations
  function addPage(): number {
    const newNum = document.value.pages.length + 1
    const newPage: CanvasPageModel = {
      id: `page_${Date.now()}_${Math.random().toString(36).substring(2, 6)}`,
      pageNumber: newNum,
      elements: [],
    }
    document.value.pages.push(newPage)
    activePageIndex.value = document.value.pages.length - 1
    clearSelection()
    history.recordSnapshot(document.value)
    return activePageIndex.value
  }

  function duplicatePage(index: number) {
    const target = document.value.pages[index]
    if (!target) return
    const duplicatedElements: CanvasElement[] = JSON.parse(JSON.stringify(target.elements)).map(
      (el: CanvasElement) => ({
        ...el,
        id: `${el.type}_${Date.now()}_${Math.random().toString(36).substring(2, 6)}`,
      })
    )
    const newPage: CanvasPageModel = {
      id: `page_${Date.now()}_${Math.random().toString(36).substring(2, 6)}`,
      pageNumber: index + 2,
      elements: duplicatedElements,
    }
    document.value.pages.splice(index + 1, 0, newPage)
    // Renumber subsequent pages
    document.value.pages.forEach((p, i) => {
      p.pageNumber = i + 1
    })
    activePageIndex.value = index + 1
    clearSelection()
    history.recordSnapshot(document.value)
  }

  function deletePage(index: number) {
    if (document.value.pages.length <= 1) return // Keep at least one page
    document.value.pages.splice(index, 1)
    document.value.pages.forEach((p, i) => {
      p.pageNumber = i + 1
    })
    activePageIndex.value = Math.max(0, Math.min(index, document.value.pages.length - 1))
    clearSelection()
    history.recordSnapshot(document.value)
  }

  function movePage(fromIndex: number, toIndex: number) {
    if (fromIndex === toIndex || toIndex < 0 || toIndex >= document.value.pages.length) return
    const [moved] = document.value.pages.splice(fromIndex, 1)
    document.value.pages.splice(toIndex, 0, moved)
    document.value.pages.forEach((p, i) => {
      p.pageNumber = i + 1
    })
    activePageIndex.value = toIndex
    history.recordSnapshot(document.value)
  }

  // Element CRUD
  function addElement(element: CanvasElement, pageIdx = activePageIndex.value) {
    const page = document.value.pages[pageIdx]
    if (!page) return
    const maxZ = page.elements.reduce((max, el) => Math.max(max, el.zIndex || 1), 0)
    element.zIndex = maxZ + 1
    page.elements.push(element)
    selectedElementIds.value = [element.id]
    history.recordSnapshot(document.value)
  }

  function updateElement(id: string, updates: Partial<CanvasElement>, recordHistory = true) {
    const found = findElementAndPage(id)
    if (!found) return
    Object.assign(found.element, updates)
    activePageIndex.value = found.pageIndex
    if (recordHistory) {
      history.recordSnapshot(document.value)
    }
  }

  function deleteSelectedElements(specificId?: string) {
    const idsToDelete = new Set(selectedElementIds.value)
    if (specificId) idsToDelete.add(specificId)
    if (idsToDelete.size === 0) return
    let anyDeleted = false
    document.value.pages.forEach(page => {
      const prevCount = page.elements.length
      page.elements = page.elements.filter(el => !idsToDelete.has(el.id))
      if (page.elements.length !== prevCount) {
        anyDeleted = true
      }
    })
    if (anyDeleted) {
      selectedElementIds.value = selectedElementIds.value.filter(id => !idsToDelete.has(id))
      if (!specificId || editingElementId.value === specificId) {
        editingElementId.value = null
      }
      history.recordSnapshot(document.value)
    }
  }

  function duplicateSelectedElements(specificId?: string) {
    const targetIds = specificId ? [specificId] : selectedElementIds.value
    if (targetIds.length === 0) return
    const set = new Set(targetIds)
    const newSelectedIds: string[] = []
    let anyDuplicated = false

    document.value.pages.forEach(page => {
      const toClone = page.elements.filter(el => set.has(el.id))
      if (toClone.length > 0) {
        anyDuplicated = true
        toClone.forEach(el => {
          const cloned: CanvasElement = JSON.parse(JSON.stringify(el))
          cloned.id = `${el.type}_${Date.now()}_${Math.random().toString(36).substring(2, 6)}`
          cloned.x = Math.min(PAGE_WIDTH_MM - cloned.width, cloned.x + 5)
          cloned.y = Math.min(PAGE_HEIGHT_MM - cloned.height, cloned.y + 5)
          cloned.zIndex = page.elements.length + 1
          page.elements.push(cloned)
          newSelectedIds.push(cloned.id)
        })
      }
    })

    if (anyDuplicated) {
      selectedElementIds.value = newSelectedIds
      history.recordSnapshot(document.value)
    }
  }

  // Layer Ordering (Z-Index)
  function bringToFront(id: string) {
    const found = findElementAndPage(id)
    if (!found) return
    const { element, page } = found
    const maxZ = page.elements.reduce((max, e) => Math.max(max, e.zIndex || 1), 0)
    element.zIndex = maxZ + 1
    history.recordSnapshot(document.value)
  }

  function sendToBack(id: string) {
    const found = findElementAndPage(id)
    if (!found) return
    const { element, page } = found
    const minZ = page.elements.reduce((min, e) => Math.min(min, e.zIndex || 1), 1)
    element.zIndex = Math.max(1, minZ - 1)
    // Re-normalize all to keep positive
    page.elements
      .sort((a, b) => (a.zIndex || 1) - (b.zIndex || 1))
      .forEach((e, idx) => {
        e.zIndex = idx + 1
      })
    history.recordSnapshot(document.value)
  }

  function bringForward(id: string) {
    const found = findElementAndPage(id)
    if (!found) return
    found.element.zIndex = (found.element.zIndex || 1) + 1
    history.recordSnapshot(document.value)
  }

  function sendBackward(id: string) {
    const found = findElementAndPage(id)
    if (!found) return
    found.element.zIndex = Math.max(1, (found.element.zIndex || 1) - 1)
    history.recordSnapshot(document.value)
  }

  function toggleLock(id: string) {
    const found = findElementAndPage(id)
    if (!found) return
    found.element.locked = !found.element.locked
    history.recordSnapshot(document.value)
  }

  function toggleVisibility(id: string) {
    const found = findElementAndPage(id)
    if (!found) return
    found.element.hidden = !found.element.hidden
    history.recordSnapshot(document.value)
  }

  // Smart Snapping Engine
  function calculateSnapping(
    targetX: number,
    targetY: number,
    targetW: number,
    targetH: number,
    ignoreId: string
  ): { x: number; y: number; guides: AlignmentGuide[] } {
    let snappedX = targetX
    let snappedY = targetY
    const guides: AlignmentGuide[] = []

    const margins = document.value.margins || { top: 20, right: 15, bottom: 20, left: 25 }
    const pageCenterHoriz = PAGE_WIDTH_MM / 2 // 105mm
    const pageCenterVert = PAGE_HEIGHT_MM / 2 // 148.5mm

    const targetCenterX = targetX + targetW / 2
    const targetRight = targetX + targetW
    const targetCenterY = targetY + targetH / 2
    const targetBottom = targetY + targetH

    // 1. Page Bounds & Margin Snaps (X Axis)
    const xSnaps = [
      { pos: margins.left, label: 'Left Margin' },
      { pos: PAGE_WIDTH_MM - margins.right, label: 'Right Margin' },
      { pos: pageCenterHoriz, label: 'Center Page (X)' },
    ]

    for (const snap of xSnaps) {
      // Align Left edge
      if (Math.abs(targetX - snap.pos) < SNAP_THRESHOLD_MM) {
        snappedX = snap.pos
        guides.push({
          type: 'vertical',
          position: snap.pos,
          start: 0,
          end: PAGE_HEIGHT_MM,
          label: snap.label,
        })
        break
      }
      // Align Center
      if (Math.abs(targetCenterX - snap.pos) < SNAP_THRESHOLD_MM) {
        snappedX = snap.pos - targetW / 2
        guides.push({
          type: 'vertical',
          position: snap.pos,
          start: 0,
          end: PAGE_HEIGHT_MM,
          label: snap.label,
        })
        break
      }
      // Align Right edge
      if (Math.abs(targetRight - snap.pos) < SNAP_THRESHOLD_MM) {
        snappedX = snap.pos - targetW
        guides.push({
          type: 'vertical',
          position: snap.pos,
          start: 0,
          end: PAGE_HEIGHT_MM,
          label: snap.label,
        })
        break
      }
    }

    // 2. Page Bounds & Margin Snaps (Y Axis)
    const ySnaps = [
      { pos: margins.top, label: 'Top Margin' },
      { pos: PAGE_HEIGHT_MM - margins.bottom, label: 'Bottom Margin' },
      { pos: pageCenterVert, label: 'Center Page (Y)' },
    ]

    for (const snap of ySnaps) {
      // Align Top edge
      if (Math.abs(targetY - snap.pos) < SNAP_THRESHOLD_MM) {
        snappedY = snap.pos
        guides.push({
          type: 'horizontal',
          position: snap.pos,
          start: 0,
          end: PAGE_WIDTH_MM,
          label: snap.label,
        })
        break
      }
      // Align Center
      if (Math.abs(targetCenterY - snap.pos) < SNAP_THRESHOLD_MM) {
        snappedY = snap.pos - targetH / 2
        guides.push({
          type: 'horizontal',
          position: snap.pos,
          start: 0,
          end: PAGE_WIDTH_MM,
          label: snap.label,
        })
        break
      }
      // Align Bottom edge
      if (Math.abs(targetBottom - snap.pos) < SNAP_THRESHOLD_MM) {
        snappedY = snap.pos - targetH
        guides.push({
          type: 'horizontal',
          position: snap.pos,
          start: 0,
          end: PAGE_WIDTH_MM,
          label: snap.label,
        })
        break
      }
    }

    // 3. Other Elements on Page Snaps
    const pageIndex = findElementAndPage(ignoreId)?.pageIndex ?? activePageIndex.value
    const targetPage = document.value.pages[pageIndex] || activePage.value
    const otherElements = (targetPage?.elements || []).filter(
      el => el.id !== ignoreId && !el.hidden
    )

    for (const other of otherElements) {
      const otherCenterX = other.x + other.width / 2
      const otherRight = other.x + other.width
      const otherCenterY = other.y + other.height / 2
      const otherBottom = other.y + other.height

      // Horizontal element alignments
      if (Math.abs(targetX - other.x) < SNAP_THRESHOLD_MM) {
        snappedX = other.x
        guides.push({
          type: 'vertical',
          position: other.x,
          start: Math.min(targetY, other.y),
          end: Math.max(targetBottom, otherBottom),
        })
      } else if (Math.abs(targetCenterX - otherCenterX) < SNAP_THRESHOLD_MM) {
        snappedX = otherCenterX - targetW / 2
        guides.push({
          type: 'vertical',
          position: otherCenterX,
          start: Math.min(targetY, other.y),
          end: Math.max(targetBottom, otherBottom),
        })
      } else if (Math.abs(targetRight - otherRight) < SNAP_THRESHOLD_MM) {
        snappedX = otherRight - targetW
        guides.push({
          type: 'vertical',
          position: otherRight,
          start: Math.min(targetY, other.y),
          end: Math.max(targetBottom, otherBottom),
        })
      }

      // Vertical element alignments
      if (Math.abs(targetY - other.y) < SNAP_THRESHOLD_MM) {
        snappedY = other.y
        guides.push({
          type: 'horizontal',
          position: other.y,
          start: Math.min(targetX, other.x),
          end: Math.max(targetRight, otherRight),
        })
      } else if (Math.abs(targetCenterY - otherCenterY) < SNAP_THRESHOLD_MM) {
        snappedY = otherCenterY - targetH / 2
        guides.push({
          type: 'horizontal',
          position: otherCenterY,
          start: Math.min(targetX, other.x),
          end: Math.max(targetRight, otherRight),
        })
      } else if (Math.abs(targetBottom - otherBottom) < SNAP_THRESHOLD_MM) {
        snappedY = otherBottom - targetH
        guides.push({
          type: 'horizontal',
          position: otherBottom,
          start: Math.min(targetX, other.x),
          end: Math.max(targetRight, otherRight),
        })
      }
    }

    return { x: snappedX, y: snappedY, guides }
  }

  // Nudge selected with keyboard arrows
  function nudgeSelected(dxMm: number, dyMm: number) {
    if (selectedElements.value.length === 0) return
    selectedElements.value.forEach(el => {
      if (el.locked) return
      el.x = Math.max(0, Math.min(PAGE_WIDTH_MM - el.width, el.x + dxMm))
      el.y = Math.max(0, Math.min(PAGE_HEIGHT_MM - el.height, el.y + dyMm))
    })
    history.recordSnapshot(document.value)
  }

  // Keyboard shortcut listener
  function handleKeyDown(e: KeyboardEvent) {
    const activeEl = window.document.activeElement
    const isInTextEdit =
      activeEl &&
      (activeEl.tagName === 'INPUT' ||
        activeEl.tagName === 'TEXTAREA' ||
        (activeEl as HTMLElement).getAttribute('contenteditable') === 'true')

    // In text editing context: only handle Escape to exit
    if (isInTextEdit) {
      if (e.key === 'Escape') {
        editingElementId.value = null
        ;(activeEl as HTMLElement).blur()
      }
      return
    }

    const step = e.shiftKey ? 5 : 1 // 1mm or 5mm nudge

    // F2 or Enter → enter text-edit mode for selected element
    if (e.key === 'F2' || (e.key === 'Enter' && !(e.ctrlKey || e.metaKey))) {
      if (selectedElementIds.value.length === 1) {
        e.preventDefault()
        editingElementId.value = selectedElementIds.value[0]
      }
      return
    }

    // Arrow nudge
    if (e.key === 'ArrowUp') {
      e.preventDefault()
      nudgeSelected(0, -step)
    } else if (e.key === 'ArrowDown') {
      e.preventDefault()
      nudgeSelected(0, step)
    } else if (e.key === 'ArrowLeft') {
      e.preventDefault()
      nudgeSelected(-step, 0)
    } else if (e.key === 'ArrowRight') {
      e.preventDefault()
      nudgeSelected(step, 0)
    } else if (e.key === 'Delete' || e.key === 'Backspace') {
      if (selectedElementIds.value.length > 0) {
        e.preventDefault()
        deleteSelectedElements()
      }
    } else if (e.key === 'Escape') {
      clearSelection()
      editingElementId.value = null
    } else if (e.ctrlKey || e.metaKey) {
      // ── Zoom ──────────────────────────────────────
      if (e.key === '=' || e.key === '+') {
        e.preventDefault()
        zoomIn()
      } else if (e.key === '-' || e.key === '_') {
        e.preventDefault()
        zoomOut()
      } else if (e.key === '0') {
        e.preventDefault()
        setZoom(100)
      }
      // ── Layering ──────────────────────────────────
      else if (e.key === ']' && !e.shiftKey) {
        e.preventDefault()
        if (selectedElement.value) bringForward(selectedElement.value.id)
      } else if (e.key === '[' && !e.shiftKey) {
        e.preventDefault()
        if (selectedElement.value) sendBackward(selectedElement.value.id)
      } else if (e.key === ']' && e.shiftKey) {
        e.preventDefault()
        if (selectedElement.value) bringToFront(selectedElement.value.id)
      } else if (e.key === '[' && e.shiftKey) {
        e.preventDefault()
        if (selectedElement.value) sendToBack(selectedElement.value.id)
      }
      // ── Lock / Unlock: Ctrl+L ──────────────────────
      else if ((e.key === 'l' || e.key === 'L') && !e.shiftKey) {
        e.preventDefault()
        selectedElementIds.value.forEach(id => toggleLock(id))
      }
      // ── History ───────────────────────────────────
      else if (e.key === 'z' || e.key === 'Z') {
        e.preventDefault()
        if (e.shiftKey) {
          const redoState = history.redo()
          if (redoState) document.value = redoState
        } else {
          const undoState = history.undo()
          if (undoState) document.value = undoState
        }
      } else if (e.key === 'y' || e.key === 'Y') {
        e.preventDefault()
        const redoState = history.redo()
        if (redoState) document.value = redoState
      }
      // ── Duplicate ─────────────────────────────────
      else if ((e.key === 'd' || e.key === 'D') && !e.shiftKey) {
        e.preventDefault()
        duplicateSelectedElements()
      }
      // ── Select All ────────────────────────────────
      else if (e.key === 'a' || e.key === 'A') {
        e.preventDefault()
        selectAll()
      }
      // ── Copy ──────────────────────────────────────
      else if ((e.key === 'c' || e.key === 'C') && !e.shiftKey) {
        if (selectedElements.value.length > 0) {
          clipboard.value = JSON.parse(JSON.stringify(selectedElements.value))
          try {
            const payload = JSON.stringify({
              [CANVAS_ELEMENT_CLIPBOARD_KEY]: CANVAS_ELEMENT_CLIPBOARD_VALUE,
              elements: selectedElements.value,
            })
            navigator.clipboard.writeText(payload)
          } catch {}
        }
      }
      // ── Cut ───────────────────────────────────────
      else if ((e.key === 'x' || e.key === 'X') && !e.shiftKey) {
        if (selectedElements.value.length > 0) {
          clipboard.value = JSON.parse(JSON.stringify(selectedElements.value))
          try {
            const payload = JSON.stringify({
              [CANVAS_ELEMENT_CLIPBOARD_KEY]: CANVAS_ELEMENT_CLIPBOARD_VALUE,
              elements: selectedElements.value,
            })
            navigator.clipboard.writeText(payload)
          } catch {}
          deleteSelectedElements()
        }
      }
      // ── Paste ─────────────────────────────────────
      else if (e.key === 'v' || e.key === 'V') {
        // Do NOT preventDefault! Allow the native 'paste' event to fire so e.clipboardData
        // can be read synchronously by the document editor.
      }
    }
  }

  // Paste canvas elements (from internal copy or system clipboard JSON)
  function pasteElements(elementsToPaste?: CanvasElement[]): string[] {
    const list = elementsToPaste || clipboard.value
    if (!list || list.length === 0) return []
    const newIds: string[] = []
    const page = activePage.value
    list.forEach(item => {
      const pasted: CanvasElement = JSON.parse(JSON.stringify(item))
      pasted.id = `${item.type}_${Date.now()}_${Math.random().toString(36).substring(2, 6)}`
      pasted.x = Math.min(PAGE_WIDTH_MM - pasted.width, (pasted.x || 0) + 8)
      pasted.y = Math.min(PAGE_HEIGHT_MM - pasted.height, (pasted.y || 0) + 8)
      pasted.zIndex = page.elements.length + 1
      page.elements.push(pasted)
      newIds.push(pasted.id)
    })
    selectedElementIds.value = newIds
    history.recordSnapshot(document.value)
    return newIds
  }


  // Zoom helpers
  function zoomIn() {
    zoomLevel.value = Math.min(200, zoomLevel.value + 15)
  }

  function zoomOut() {
    zoomLevel.value = Math.max(25, zoomLevel.value - 15)
  }

  function setZoom(level: number) {
    zoomLevel.value = Math.max(25, Math.min(200, level))
  }

  return {
    document,
    activePageIndex,
    activePage,
    selectedElementIds,
    selectedElement,
    selectedElements,
    editingElementId,
    zoomLevel,
    showMarginGuides,
    showRulers,
    showGrid,
    snapToGrid,
    gridSizeMm,
    isDragging,
    isResizing,
    activeGuides,
    history,
    mmToPx,
    pxToMm,
    setActivePageIndex,
    findElementAndPage,
    selectElement,
    selectAll,
    clearSelection,
    isElementSelected,
    addPage,
    duplicatePage,
    deletePage,
    movePage,
    addElement,
    updateElement,
    deleteSelectedElements,
    duplicateSelectedElements,
    bringToFront,
    sendToBack,
    bringForward,
    sendBackward,
    toggleLock,
    toggleVisibility,
    calculateSnapping,
    nudgeSelected,
    handleKeyDown,
    clipboard,
    pasteElements,
    zoomIn,
    zoomOut,
    setZoom,
  }
}
