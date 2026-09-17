import { ref, computed, watch, nextTick } from 'vue'
import type {
  ContractDocumentModel,
  CanvasPageModel,
  CanvasElement,
  TextCanvasElement,
  TableCanvasElement,
  TableCellModel,
  AlignmentGuide,
  DistanceGuide,
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

  // Guide selection is tracked separately from element selection — a guide
  // is an editor-only layout aid, never a CanvasElement, so it must never be
  // able to enter selectedElementIds (which flows into element-only paths
  // like deleteSelectedElements, duplicateSelectedElements, PDF export, etc).
  const selectedGuideId = ref<string | null>(null)

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
  const activeDistanceGuides = ref<DistanceGuide[]>([])
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
    selectedGuideId.value = null
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
    selectedGuideId.value = null
    editingElementId.value = null
    activeGuides.value = []
    activeDistanceGuides.value = []
    try {
      window.getSelection()?.removeAllRanges()
    } catch {}
  }

  function isElementSelected(id: string): boolean {
    return selectedElementIds.value.includes(id)
  }

  // ─── Guides (editor-only layout aids, never contract content) ──────────
  // Stored document-wide as `document.guides` — GLOBAL, not per-page: one
  // guide created anywhere renders at the same mm position on every page,
  // and dragging/deleting it updates that single shared definition (per
  // explicit product requirement — a guide is not scoped to the page it was
  // created on). They still ride along with the document's existing
  // save/load/undo path for free (the whole `document` is snapshotted/
  // serialized as one JSON tree). Every export/render path (PDF, Preview,
  // HTML) only ever reads `page.elements`, so guides are structurally
  // invisible to them — no exclusion filtering needed there.
  function addGuide(type: 'horizontal' | 'vertical'): string {
    if (!document.value.guides) document.value.guides = []

    const id = `guide_${Date.now()}_${Math.random().toString(36).substring(2, 6)}`
    document.value.guides.push({
      id,
      type,
      position: type === 'horizontal' ? PAGE_HEIGHT_MM / 2 : PAGE_WIDTH_MM / 2,
      visible: true,
    })
    clearSelection()
    selectedGuideId.value = id
    history.recordSnapshot(document.value)
    return id
  }

  function updateGuidePosition(guideId: string, position: number, recordHistory = false) {
    const guide = document.value.guides?.find(g => g.id === guideId)
    if (!guide) return
    const max = guide.type === 'horizontal' ? PAGE_HEIGHT_MM : PAGE_WIDTH_MM
    guide.position = Math.round(Math.max(0, Math.min(max, position)) * 100) / 100
    if (recordHistory) history.recordSnapshot(document.value)
  }

  function deleteGuide(guideId: string) {
    if (!document.value.guides) return
    document.value.guides = document.value.guides.filter(g => g.id !== guideId)
    if (selectedGuideId.value === guideId) selectedGuideId.value = null
    history.recordSnapshot(document.value)
  }

  function selectGuide(guideId: string) {
    clearSelection()
    selectedGuideId.value = guideId
  }

  function deleteSelectedGuide() {
    if (!selectedGuideId.value) return
    deleteGuide(selectedGuideId.value)
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

  // ─── Multi-Element Drag Tracking ────────────────────────
  interface DragItemInitial {
    x: number
    y: number
    width: number
    height: number
  }
  const dragStartPositions = new Map<string, DragItemInitial>()

  function startDrag(primaryId?: string) {
    dragStartPositions.clear()
    selectedElements.value.forEach(el => {
      if (!el.locked) {
        dragStartPositions.set(el.id, { x: el.x, y: el.y, width: el.width, height: el.height })
      }
    })
    if (primaryId && !dragStartPositions.has(primaryId)) {
      const found = findElementAndPage(primaryId)
      if (found && !found.element.locked) {
        dragStartPositions.set(primaryId, { x: found.element.x, y: found.element.y, width: found.element.width, height: found.element.height })
      }
    }
  }

  function getGroupStartBounds(): { minX: number; minY: number; maxX: number; maxY: number; width: number; height: number } | null {
    if (dragStartPositions.size <= 1) return null
    let minX = Infinity
    let minY = Infinity
    let maxX = -Infinity
    let maxY = -Infinity
    for (const item of dragStartPositions.values()) {
      minX = Math.min(minX, item.x)
      minY = Math.min(minY, item.y)
      maxX = Math.max(maxX, item.x + item.width)
      maxY = Math.max(maxY, item.y + item.height)
    }
    return { minX, minY, maxX, maxY, width: maxX - minX, height: maxY - minY }
  }

  function updateElementBounds(
    primaryId: string,
    bounds: { x: number; y: number; width: number; height: number; rotation?: number }
  ) {
    if (dragStartPositions.size === 0 && selectedElements.value.length > 1) {
      startDrag(primaryId)
    }

    const isMultiDrag = dragStartPositions.size > 1 && dragStartPositions.has(primaryId)

    if (isMultiDrag) {
      const primaryStart = dragStartPositions.get(primaryId)!
      const dx = bounds.x - primaryStart.x
      const dy = bounds.y - primaryStart.y

      updateElement(primaryId, bounds, false)

      selectedElements.value.forEach(el => {
        if (el.id === primaryId || el.locked) return
        const startPos = dragStartPositions.get(el.id)
        if (startPos) {
          const newX = Math.max(0, Math.min(PAGE_WIDTH_MM - el.width, startPos.x + dx))
          const newY = Math.max(0, Math.min(PAGE_HEIGHT_MM - el.height, startPos.y + dy))
          el.x = Math.round(newX * 100) / 100
          el.y = Math.round(newY * 100) / 100
        }
      })
    } else {
      updateElement(primaryId, bounds, false)
    }
  }

  function endDrag() {
    dragStartPositions.clear()
    activeGuides.value = []
    activeDistanceGuides.value = []
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

  function formatDistanceMm(mm: number): string {
    const rounded = Math.round(mm * 10) / 10
    return rounded % 1 === 0 ? `${rounded.toFixed(0)} mm` : `${rounded.toFixed(1)} mm`
  }

  // Smart Snapping & Distance Guides Engine (Canva/Figma Style)
  function calculateSnapping(
    targetX: number,
    targetY: number,
    targetW: number,
    targetH: number,
    ignoreId: string | string[],
    isResize = false
  ): { x: number; y: number; guides: AlignmentGuide[]; distanceGuides: DistanceGuide[] } {
    const isMultiDrag = !isResize && typeof ignoreId === 'string' && dragStartPositions.size > 1 && dragStartPositions.has(ignoreId)
    const groupBounds = isMultiDrag ? getGroupStartBounds() : null

    // If multi-drag, we calculate snapping and distance guides for the entire group bounding box
    let calcX = targetX
    let calcY = targetY
    let calcW = targetW
    let calcH = targetH
    let offsetX = 0
    let offsetY = 0

    const ignoreSet = new Set<string>()
    if (isMultiDrag && groupBounds) {
      dragStartPositions.forEach((_, id) => ignoreSet.add(id))
      const primaryStart = dragStartPositions.get(ignoreId as string)!
      offsetX = primaryStart.x - groupBounds.minX
      offsetY = primaryStart.y - groupBounds.minY
      calcX = targetX - offsetX
      calcY = targetY - offsetY
      calcW = groupBounds.width
      calcH = groupBounds.height
    } else {
      if (Array.isArray(ignoreId)) {
        ignoreId.forEach(id => ignoreSet.add(id))
      } else if (ignoreId) {
        ignoreSet.add(ignoreId)
      }
    }

    let snappedX = calcX
    let snappedY = calcY
    const guides: AlignmentGuide[] = []
    const distanceGuides: DistanceGuide[] = []

    const margins = document.value.margins || { top: 20, right: 15, bottom: 20, left: 25 }
    const pageCenterHoriz = PAGE_WIDTH_MM / 2 // 105mm
    const pageCenterVert = PAGE_HEIGHT_MM / 2 // 148.5mm

    const targetCenterX = calcX + calcW / 2
    const targetRight = calcX + calcW
    const targetCenterY = calcY + calcH / 2
    const targetBottom = calcY + calcH

    const primaryIdStr = typeof ignoreId === 'string' ? ignoreId : (ignoreId[0] || '')
    const pageIndex = findElementAndPage(primaryIdStr)?.pageIndex ?? activePageIndex.value
    const targetPage = document.value.pages[pageIndex] || activePage.value
    const otherElements = (targetPage?.elements || []).filter(
      el => !ignoreSet.has(el.id) && !el.hidden
    )

    // ─── Unified Snap Resolution (Canva/Figma style: exactly ONE guide line
    // per axis, always the single closest candidate) ───────────────────────
    // Every possible snap target — page edges, margins, page center,
    // user-placed guides, and other elements' edges/centers — is collected
    // into one flat candidate list per axis, then reduced to whichever
    // candidate is numerically closest to the dragged/resized shape. This
    // replaces the old design where page-bounds, guides, and each element
    // were checked in separate sequential passes that each unconditionally
    // overwrote the previous match — that's what let a weaker/farther
    // element-edge match silently beat a closer margin or guide, and let
    // several elements each contribute their own line at once instead of
    // showing only the winning one.
    interface SnapCandidate {
      pos: number // fixed target position this candidate sits at, in mm
      guidePos: number // mm position where the guide LINE itself should be drawn (usually === pos)
      span: [number, number] // guide line's start/end extent along the cross axis, in mm
      label?: string
      priority: number // lower wins a tie (user guides > page/margin > other elements)
    }

    function pickBestCandidate(
      candidates: SnapCandidate[],
      calcPos: number,
      calcCenter: number,
      calcEnd: number,
      calcSize: number
    ): { snapped: number; guidePos: number; span: [number, number]; label?: string } | null {
      let best: { candidate: SnapCandidate; edge: 'start' | 'center' | 'end'; dist: number } | null = null

      for (const c of candidates) {
        const checks: Array<['start' | 'center' | 'end', number]> = [
          ['start', calcPos],
          ['center', calcCenter],
          ['end', calcEnd],
        ]
        for (const [edge, value] of checks) {
          const dist = Math.abs(value - c.pos)
          if (dist >= SNAP_THRESHOLD_MM) continue
          if (
            !best ||
            dist < best.dist - 1e-6 ||
            (Math.abs(dist - best.dist) <= 1e-6 && c.priority < best.candidate.priority)
          ) {
            best = { candidate: c, edge, dist }
          }
        }
      }

      if (!best) return null

      const snapped =
        best.edge === 'start' ? best.candidate.pos :
        best.edge === 'center' ? best.candidate.pos - calcSize / 2 :
        best.candidate.pos - calcSize

      return { snapped, guidePos: best.candidate.guidePos, span: best.candidate.span, label: best.candidate.label }
    }

    // Priority tiers: user guides win ties over page/margin, which win ties
    // over other elements — matching the old code's effective behavior
    // (guides were checked after page bounds but the "closest wins" rule
    // above is what actually matters; priority only breaks exact ties).
    const PRIORITY_GUIDE = 0
    const PRIORITY_PAGE_MARGIN = 1
    const PRIORITY_ELEMENT = 2

    // ─── X Axis Candidates ──────────────────────────────────────────────
    const xCandidates: SnapCandidate[] = [
      { pos: 0, guidePos: 0, span: [0, PAGE_HEIGHT_MM], label: 'Page Left', priority: PRIORITY_PAGE_MARGIN },
      { pos: margins.left, guidePos: margins.left, span: [0, PAGE_HEIGHT_MM], label: 'Left Margin', priority: PRIORITY_PAGE_MARGIN },
      { pos: pageCenterHoriz, guidePos: pageCenterHoriz, span: [0, PAGE_HEIGHT_MM], label: 'Center Page', priority: PRIORITY_PAGE_MARGIN },
      { pos: PAGE_WIDTH_MM - margins.right, guidePos: PAGE_WIDTH_MM - margins.right, span: [0, PAGE_HEIGHT_MM], label: 'Right Margin', priority: PRIORITY_PAGE_MARGIN },
      { pos: PAGE_WIDTH_MM, guidePos: PAGE_WIDTH_MM, span: [0, PAGE_HEIGHT_MM], label: 'Page Right', priority: PRIORITY_PAGE_MARGIN },
    ]

    const docGuides = (document.value.guides || []).filter(g => g.visible !== false)
    for (const guide of docGuides) {
      if (guide.type !== 'vertical') continue
      xCandidates.push({
        pos: guide.position,
        guidePos: guide.position,
        span: [0, PAGE_HEIGHT_MM],
        label: `X: ${formatDistanceMm(guide.position)}`,
        priority: PRIORITY_GUIDE,
      })
    }

    for (const other of otherElements) {
      const oRight = other.x + other.width
      const oCenter = other.x + other.width / 2
      const oSpan: [number, number] = [Math.min(calcY, other.y), Math.max(targetBottom, other.y + other.height)]
      xCandidates.push(
        { pos: other.x, guidePos: other.x, span: oSpan, priority: PRIORITY_ELEMENT },
        { pos: oCenter, guidePos: oCenter, span: oSpan, priority: PRIORITY_ELEMENT },
        { pos: oRight, guidePos: oRight, span: oSpan, priority: PRIORITY_ELEMENT },
      )
    }

    const xResult = pickBestCandidate(xCandidates, calcX, targetCenterX, targetRight, calcW)
    if (xResult) {
      snappedX = xResult.snapped
      guides.push({ type: 'vertical', position: xResult.guidePos, start: xResult.span[0], end: xResult.span[1], label: xResult.label })
    }

    // ─── Y Axis Candidates ──────────────────────────────────────────────
    const yCandidates: SnapCandidate[] = [
      { pos: 0, guidePos: 0, span: [0, PAGE_WIDTH_MM], label: 'Page Top', priority: PRIORITY_PAGE_MARGIN },
      { pos: margins.top, guidePos: margins.top, span: [0, PAGE_WIDTH_MM], label: 'Top Margin', priority: PRIORITY_PAGE_MARGIN },
      { pos: pageCenterVert, guidePos: pageCenterVert, span: [0, PAGE_WIDTH_MM], label: 'Center Page', priority: PRIORITY_PAGE_MARGIN },
      { pos: PAGE_HEIGHT_MM - margins.bottom, guidePos: PAGE_HEIGHT_MM - margins.bottom, span: [0, PAGE_WIDTH_MM], label: 'Bottom Margin', priority: PRIORITY_PAGE_MARGIN },
      { pos: PAGE_HEIGHT_MM, guidePos: PAGE_HEIGHT_MM, span: [0, PAGE_WIDTH_MM], label: 'Page Bottom', priority: PRIORITY_PAGE_MARGIN },
    ]

    for (const guide of docGuides) {
      if (guide.type !== 'horizontal') continue
      yCandidates.push({
        pos: guide.position,
        guidePos: guide.position,
        span: [0, PAGE_WIDTH_MM],
        label: `Y: ${formatDistanceMm(guide.position)}`,
        priority: PRIORITY_GUIDE,
      })
    }

    for (const other of otherElements) {
      const oBottom = other.y + other.height
      const oCenter = other.y + other.height / 2
      const oSpan: [number, number] = [Math.min(calcX, other.x), Math.max(targetRight, other.x + other.width)]
      yCandidates.push(
        { pos: other.y, guidePos: other.y, span: oSpan, priority: PRIORITY_ELEMENT },
        { pos: oCenter, guidePos: oCenter, span: oSpan, priority: PRIORITY_ELEMENT },
        { pos: oBottom, guidePos: oBottom, span: oSpan, priority: PRIORITY_ELEMENT },
      )
    }

    const yResult = pickBestCandidate(yCandidates, calcY, targetCenterY, targetBottom, calcH)
    if (yResult) {
      snappedY = yResult.snapped
      guides.push({ type: 'horizontal', position: yResult.guidePos, start: yResult.span[0], end: yResult.span[1], label: yResult.label })
    }

    // 4. Equal Spacing Snapping (during drag only).
    // Only allowed to override the alignment-snap result above (xResult/
    // yResult) when it's a genuinely closer match, not unconditionally —
    // otherwise equal-spacing could silently un-snap an element from a
    // margin/guide/edge it had already correctly locked onto.
    if (!isResize && otherElements.length >= 2) {
      // Horizontal Equal Spacing between Left and Right elements
      const leftCandidates = otherElements.filter(o => o.x + o.width <= calcX + SNAP_THRESHOLD_MM)
      const rightCandidates = otherElements.filter(o => o.x >= calcX + calcW - SNAP_THRESHOLD_MM)

      let bestEqualX: number | null = null
      let minEqualXDiff = xResult ? Math.abs(calcX - snappedX) : SNAP_THRESHOLD_MM

      for (const leftEl of leftCandidates) {
        const leftEdge = leftEl.x + leftEl.width
        for (const rightEl of rightCandidates) {
          const rightEdge = rightEl.x
          const totalGap = rightEdge - leftEdge
          const equalGap = (totalGap - calcW) / 2
          if (equalGap > 1) {
            const candidateEqualX = leftEdge + equalGap
            const diff = Math.abs(calcX - candidateEqualX)
            if (diff < minEqualXDiff) {
              minEqualXDiff = diff
              bestEqualX = candidateEqualX
            }
          }
        }
      }

      // Continuation rhythm Left1 -> Left2 -> Target
      for (let i = 0; i < leftCandidates.length; i++) {
        for (let j = 0; j < leftCandidates.length; j++) {
          if (i === j) continue
          const l1 = leftCandidates[i]
          const l2 = leftCandidates[j]
          if (l1.x + l1.width <= l2.x) {
            const gap = l2.x - (l1.x + l1.width)
            if (gap > 1) {
              const candidateEqualX = l2.x + l2.width + gap
              const diff = Math.abs(calcX - candidateEqualX)
              if (diff < minEqualXDiff) {
                minEqualXDiff = diff
                bestEqualX = candidateEqualX
              }
            }
          }
        }
      }

      if (bestEqualX !== null) {
        snappedX = bestEqualX
      }

      // Vertical Equal Spacing between Top and Bottom elements
      const topCandidates = otherElements.filter(o => o.y + o.height <= calcY + SNAP_THRESHOLD_MM)
      const bottomCandidates = otherElements.filter(o => o.y >= calcY + calcH - SNAP_THRESHOLD_MM)

      let bestEqualY: number | null = null
      let minEqualYDiff = yResult ? Math.abs(calcY - snappedY) : SNAP_THRESHOLD_MM

      for (const topEl of topCandidates) {
        const topEdge = topEl.y + topEl.height
        for (const bottomEl of bottomCandidates) {
          const bottomEdge = bottomEl.y
          const totalGap = bottomEdge - topEdge
          const equalGap = (totalGap - calcH) / 2
          if (equalGap > 1) {
            const candidateEqualY = topEdge + equalGap
            const diff = Math.abs(calcY - candidateEqualY)
            if (diff < minEqualYDiff) {
              minEqualYDiff = diff
              bestEqualY = candidateEqualY
            }
          }
        }
      }

      // Continuation rhythm Top1 -> Top2 -> Target
      for (let i = 0; i < topCandidates.length; i++) {
        for (let j = 0; j < topCandidates.length; j++) {
          if (i === j) continue
          const t1 = topCandidates[i]
          const t2 = topCandidates[j]
          if (t1.y + t1.height <= t2.y) {
            const gap = t2.y - (t1.y + t1.height)
            if (gap > 1) {
              const candidateEqualY = t2.y + t2.height + gap
              const diff = Math.abs(calcY - candidateEqualY)
              if (diff < minEqualYDiff) {
                minEqualYDiff = diff
                bestEqualY = candidateEqualY
              }
            }
          }
        }
      }

      if (bestEqualY !== null) {
        snappedY = bestEqualY
      }
    }

    // 5. Smart Distance Guides (calculated from FINAL snapped geometry)
    if (!isResize) {
      const geomLeft = snappedX
      const geomRight = snappedX + calcW
      const geomTop = snappedY
      const geomBottom = snappedY + calcH
      const geomCenterX = snappedX + calcW / 2
      const geomCenterY = snappedY + calcH / 2

      // ─── Horizontal Distance Guides ───
      const leftCandidates = otherElements.filter(o => o.x + o.width <= geomLeft + 0.1)
      let nearestLeft: CanvasElement | null = null
      let minLeftScore = Infinity

      for (const o of leftCandidates) {
        const gap = geomLeft - (o.x + o.width)
        const overlapY = Math.min(geomBottom, o.y + o.height) - Math.max(geomTop, o.y)
        const vertDist = overlapY > 0 ? 0 : Math.max(geomTop - (o.y + o.height), o.y - geomBottom)
        const score = (overlapY > 0 ? 0 : 500 + vertDist) + gap
        if (score < minLeftScore) {
          minLeftScore = score
          nearestLeft = o
        }
      }

      const rightCandidates = otherElements.filter(o => o.x >= geomRight - 0.1)
      let nearestRight: CanvasElement | null = null
      let minRightScore = Infinity

      for (const o of rightCandidates) {
        const gap = o.x - geomRight
        const overlapY = Math.min(geomBottom, o.y + o.height) - Math.max(geomTop, o.y)
        const vertDist = overlapY > 0 ? 0 : Math.max(geomTop - (o.y + o.height), o.y - geomBottom)
        const score = (overlapY > 0 ? 0 : 500 + vertDist) + gap
        if (score < minRightScore) {
          minRightScore = score
          nearestRight = o
        }
      }

      const leftGap = nearestLeft ? geomLeft - (nearestLeft.x + nearestLeft.width) : null
      const rightGap = nearestRight ? nearestRight.x - geomRight : null
      const isHorizontalEqual =
        leftGap !== null && rightGap !== null && leftGap >= 0.5 && rightGap >= 0.5 && Math.abs(leftGap - rightGap) < 0.35

      // Left Guide
      if (nearestLeft && leftGap !== null && leftGap >= 0.5) {
        const overlapY = Math.min(geomBottom, nearestLeft.y + nearestLeft.height) - Math.max(geomTop, nearestLeft.y)
        const crossY = overlapY > 0
          ? (Math.max(geomTop, nearestLeft.y) + Math.min(geomBottom, nearestLeft.y + nearestLeft.height)) / 2
          : geomCenterY

        const projFrom = overlapY <= 0 ? {
          start: Math.min(nearestLeft.y, nearestLeft.y + nearestLeft.height, crossY),
          end: Math.max(nearestLeft.y, nearestLeft.y + nearestLeft.height, crossY)
        } : undefined

        distanceGuides.push({
          id: 'dist-h-left',
          axis: 'horizontal',
          startPos: nearestLeft.x + nearestLeft.width,
          endPos: geomLeft,
          crossPos: crossY,
          distanceMm: Math.round(leftGap * 10) / 10,
          isEqualSpacing: isHorizontalEqual,
          targetType: 'element',
          label: formatDistanceMm(leftGap),
          projectionFrom: projFrom,
        })
      } else {
        const leftMarginDist = geomLeft - margins.left
        if (geomLeft >= margins.left && (leftMarginDist < 35 || !nearestRight)) {
          distanceGuides.push({
            id: 'dist-h-left-margin',
            axis: 'horizontal',
            startPos: margins.left,
            endPos: geomLeft,
            crossPos: geomCenterY,
            distanceMm: Math.round(leftMarginDist * 10) / 10,
            targetType: 'margin',
            label: formatDistanceMm(leftMarginDist),
          })
        } else if (geomLeft < margins.left || !nearestRight) {
          distanceGuides.push({
            id: 'dist-h-left-page',
            axis: 'horizontal',
            startPos: 0,
            endPos: geomLeft,
            crossPos: geomCenterY,
            distanceMm: Math.round(geomLeft * 10) / 10,
            targetType: 'page',
            label: formatDistanceMm(geomLeft),
          })
        }
      }

      // Right Guide
      if (nearestRight && rightGap !== null && rightGap >= 0.5) {
        const overlapY = Math.min(geomBottom, nearestRight.y + nearestRight.height) - Math.max(geomTop, nearestRight.y)
        const crossY = overlapY > 0
          ? (Math.max(geomTop, nearestRight.y) + Math.min(geomBottom, nearestRight.y + nearestRight.height)) / 2
          : geomCenterY

        const projTo = overlapY <= 0 ? {
          start: Math.min(nearestRight.y, nearestRight.y + nearestRight.height, crossY),
          end: Math.max(nearestRight.y, nearestRight.y + nearestRight.height, crossY)
        } : undefined

        distanceGuides.push({
          id: 'dist-h-right',
          axis: 'horizontal',
          startPos: geomRight,
          endPos: nearestRight.x,
          crossPos: crossY,
          distanceMm: Math.round(rightGap * 10) / 10,
          isEqualSpacing: isHorizontalEqual,
          targetType: 'element',
          label: formatDistanceMm(rightGap),
          projectionTo: projTo,
        })
      } else {
        const rightMarginPos = PAGE_WIDTH_MM - margins.right
        const rightMarginDist = rightMarginPos - geomRight
        const rightPageDist = PAGE_WIDTH_MM - geomRight

        if (rightMarginDist >= 0 && (rightMarginDist < 35 || !nearestLeft)) {
          distanceGuides.push({
            id: 'dist-h-right-margin',
            axis: 'horizontal',
            startPos: geomRight,
            endPos: rightMarginPos,
            crossPos: geomCenterY,
            distanceMm: Math.round(rightMarginDist * 10) / 10,
            targetType: 'margin',
            label: formatDistanceMm(rightMarginDist),
          })
        } else if (rightPageDist >= 0 && (geomRight > rightMarginPos || !nearestLeft)) {
          distanceGuides.push({
            id: 'dist-h-right-page',
            axis: 'horizontal',
            startPos: geomRight,
            endPos: PAGE_WIDTH_MM,
            crossPos: geomCenterY,
            distanceMm: Math.round(rightPageDist * 10) / 10,
            targetType: 'page',
            label: formatDistanceMm(rightPageDist),
          })
        }
      }

      // ─── Vertical Distance Guides ───
      const topCandidates = otherElements.filter(o => o.y + o.height <= geomTop + 0.1)
      let nearestTop: CanvasElement | null = null
      let minTopScore = Infinity

      for (const o of topCandidates) {
        const gap = geomTop - (o.y + o.height)
        const overlapX = Math.min(geomRight, o.x + o.width) - Math.max(geomLeft, o.x)
        const horizDist = overlapX > 0 ? 0 : Math.max(geomLeft - (o.x + o.width), o.x - geomRight)
        const score = (overlapX > 0 ? 0 : 500 + horizDist) + gap
        if (score < minTopScore) {
          minTopScore = score
          nearestTop = o
        }
      }

      const bottomCandidates = otherElements.filter(o => o.y >= geomBottom - 0.1)
      let nearestBottom: CanvasElement | null = null
      let minBottomScore = Infinity

      for (const o of bottomCandidates) {
        const gap = o.y - geomBottom
        const overlapX = Math.min(geomRight, o.x + o.width) - Math.max(geomLeft, o.x)
        const horizDist = overlapX > 0 ? 0 : Math.max(geomLeft - (o.x + o.width), o.x - geomRight)
        const score = (overlapX > 0 ? 0 : 500 + horizDist) + gap
        if (score < minBottomScore) {
          minBottomScore = score
          nearestBottom = o
        }
      }

      const topGap = nearestTop ? geomTop - (nearestTop.y + nearestTop.height) : null
      const bottomGap = nearestBottom ? nearestBottom.y - geomBottom : null
      const isVerticalEqual =
        topGap !== null && bottomGap !== null && topGap >= 0.5 && bottomGap >= 0.5 && Math.abs(topGap - bottomGap) < 0.35

      // Top Guide
      if (nearestTop && topGap !== null && topGap >= 0.5) {
        const overlapX = Math.min(geomRight, nearestTop.x + nearestTop.width) - Math.max(geomLeft, nearestTop.x)
        const crossX = overlapX > 0
          ? (Math.max(geomLeft, nearestTop.x) + Math.min(geomRight, nearestTop.x + nearestTop.width)) / 2
          : geomCenterX

        const projFrom = overlapX <= 0 ? {
          start: Math.min(nearestTop.x, nearestTop.x + nearestTop.width, crossX),
          end: Math.max(nearestTop.x, nearestTop.x + nearestTop.width, crossX)
        } : undefined

        distanceGuides.push({
          id: 'dist-v-top',
          axis: 'vertical',
          startPos: nearestTop.y + nearestTop.height,
          endPos: geomTop,
          crossPos: crossX,
          distanceMm: Math.round(topGap * 10) / 10,
          isEqualSpacing: isVerticalEqual,
          targetType: 'element',
          label: formatDistanceMm(topGap),
          projectionFrom: projFrom,
        })
      } else {
        const topMarginDist = geomTop - margins.top
        if (geomTop >= margins.top && (topMarginDist < 35 || !nearestBottom)) {
          distanceGuides.push({
            id: 'dist-v-top-margin',
            axis: 'vertical',
            startPos: margins.top,
            endPos: geomTop,
            crossPos: geomCenterX,
            distanceMm: Math.round(topMarginDist * 10) / 10,
            targetType: 'margin',
            label: formatDistanceMm(topMarginDist),
          })
        } else if (geomTop < margins.top || !nearestBottom) {
          distanceGuides.push({
            id: 'dist-v-top-page',
            axis: 'vertical',
            startPos: 0,
            endPos: geomTop,
            crossPos: geomCenterX,
            distanceMm: Math.round(geomTop * 10) / 10,
            targetType: 'page',
            label: formatDistanceMm(geomTop),
          })
        }
      }

      // Bottom Guide
      if (nearestBottom && bottomGap !== null && bottomGap >= 0.5) {
        const overlapX = Math.min(geomRight, nearestBottom.x + nearestBottom.width) - Math.max(geomLeft, nearestBottom.x)
        const crossX = overlapX > 0
          ? (Math.max(geomLeft, nearestBottom.x) + Math.min(geomRight, nearestBottom.x + nearestBottom.width)) / 2
          : geomCenterX

        const projTo = overlapX <= 0 ? {
          start: Math.min(nearestBottom.x, nearestBottom.x + nearestBottom.width, crossX),
          end: Math.max(nearestBottom.x, nearestBottom.x + nearestBottom.width, crossX)
        } : undefined

        distanceGuides.push({
          id: 'dist-v-bottom',
          axis: 'vertical',
          startPos: geomBottom,
          endPos: nearestBottom.y,
          crossPos: crossX,
          distanceMm: Math.round(bottomGap * 10) / 10,
          isEqualSpacing: isVerticalEqual,
          targetType: 'element',
          label: formatDistanceMm(bottomGap),
          projectionTo: projTo,
        })
      } else {
        const bottomMarginPos = PAGE_HEIGHT_MM - margins.bottom
        const bottomMarginDist = bottomMarginPos - geomBottom
        const bottomPageDist = PAGE_HEIGHT_MM - geomBottom

        if (bottomMarginDist >= 0 && (bottomMarginDist < 35 || !nearestTop)) {
          distanceGuides.push({
            id: 'dist-v-bottom-margin',
            axis: 'vertical',
            startPos: geomBottom,
            endPos: bottomMarginPos,
            crossPos: geomCenterX,
            distanceMm: Math.round(bottomMarginDist * 10) / 10,
            targetType: 'margin',
            label: formatDistanceMm(bottomMarginDist),
          })
        } else if (bottomPageDist >= 0 && (geomBottom > bottomMarginPos || !nearestTop)) {
          distanceGuides.push({
            id: 'dist-v-bottom-page',
            axis: 'vertical',
            startPos: geomBottom,
            endPos: PAGE_HEIGHT_MM,
            crossPos: geomCenterX,
            distanceMm: Math.round(bottomPageDist * 10) / 10,
            targetType: 'page',
            label: formatDistanceMm(bottomPageDist),
          })
        }
      }
    }

    const finalResultX = isMultiDrag ? snappedX + offsetX : snappedX
    const finalResultY = isMultiDrag ? snappedY + offsetY : snappedY

    return { x: finalResultX, y: finalResultY, guides, distanceGuides }
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
      } else if (selectedGuideId.value) {
        e.preventDefault()
        deleteSelectedGuide()
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
          if (redoState) {
            document.value = redoState
            nextTick(() => history.settleHistoryUpdate())
          }
        } else {
          const undoState = history.undo()
          if (undoState) {
            document.value = undoState
            nextTick(() => history.settleHistoryUpdate())
          }
        }
      } else if (e.key === 'y' || e.key === 'Y') {
        e.preventDefault()
        const redoState = history.redo()
        if (redoState) {
          document.value = redoState
          nextTick(() => history.settleHistoryUpdate())
        }
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
    zoomLevel.value = Math.min(500, zoomLevel.value + 15)
  }

  function zoomOut() {
    zoomLevel.value = Math.max(25, zoomLevel.value - 15)
  }

  function setZoom(level: number) {
    zoomLevel.value = Math.max(25, Math.min(500, level))
  }

  return {
    document,
    activePageIndex,
    activePage,
    selectedElementIds,
    selectedElement,
    selectedElements,
    selectedGuideId,
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
    activeDistanceGuides,
    history,
    mmToPx,
    pxToMm,
    setActivePageIndex,
    findElementAndPage,
    selectElement,
    selectAll,
    clearSelection,
    isElementSelected,
    addGuide,
    updateGuidePosition,
    deleteGuide,
    selectGuide,
    deleteSelectedGuide,
    addPage,
    duplicatePage,
    deletePage,
    movePage,
    addElement,
    updateElement,
    startDrag,
    updateElementBounds,
    endDrag,
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
