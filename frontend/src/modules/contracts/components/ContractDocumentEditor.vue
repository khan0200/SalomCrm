<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount, watch, computed, nextTick } from 'vue'
import {
  Bold,
  Italic,
  Underline as UnderlineIcon,
  Strikethrough,
  AlignLeft,
  AlignCenter,
  AlignRight,
  AlignJustify,
  List,
  ListOrdered,
  Heading1,
  Heading2,
  Heading3,
  Table as TableIcon,
  Undo2,
  Redo2,
  Minus,
  Sparkles,
  Trash2,
  Highlighter,
  CheckSquare,
  Square,
  Variable,
  Download,
  Eye,
  CheckCircle2,
  Loader2,
  AlertCircle,
  Save,
  Check,
  ChevronDown,
  FilePlus,
  FileText,
  ZoomIn,
  ZoomOut,
  Columns,
  Rows,
  Split,
  Combine,
  Grid,
  PaintBucket,
  ArrowUpDown,
  IndentIncrease,
  IndentDecrease,
  Ruler,
  SlidersHorizontal,
  Plus,
  Layers,
  Copy,
  Lock,
  Unlock,
  PaintRoller,
  X,
  Building2,
  UserCheck,
} from 'lucide-vue-next'
import { CONTRACT_VARIABLES, type ContractVariableDef, buildVariableValues, resolveTenantRequisites, buildCompanyRequisitesHtml, buildClientRequisitesHtml } from '../utils/contractVariables'
import { useUiStore } from '@/stores/ui'
import { downloadContractAsPdf, printContractAsPdf } from '../utils/contractPdf'
import type {
  ContractDocumentModel,
  CanvasPageModel,
  CanvasElement,
  TextCanvasElement,
  TableCanvasElement,
  PageMargins,
  AlignmentGuide,
  TextStyleProps,
} from '../types/contractCanvas'
import {
  convertHtmlToCanvasDocument,
  serializeCanvasDocument,
  deserializeCanvasDocument,
  isCanvasDocumentJson,
} from '../utils/contractCanvasConverter'
import {
  cleanClipboardContent,
  formatPlainTextToHtml,
  estimateTextHeightMm,
  CANVAS_ELEMENT_CLIPBOARD_KEY,
  CANVAS_ELEMENT_CLIPBOARD_VALUE,
} from '../utils/clipboardUtils'
import { useContractCanvas } from '../composables/useContractCanvas'
import CanvasA4Page from './canvas/CanvasA4Page.vue'

const props = withDefaults(
  defineProps<{
    content?: string
    initialContent?: string
    readonly?: boolean
    contractNumber?: string
    title?: string
    studentName?: string
    studentData?: any
    saveStatus?: 'idle' | 'saving' | 'saved' | 'error'
    lastSavedAt?: Date | string | null
    backLabel?: string
    hideTopBar?: boolean
  }>(),
  {
    content: '',
    initialContent: '',
    readonly: false,
    saveStatus: 'idle',
    backLabel: 'Contracts',
    hideTopBar: false,
  }
)

const emit = defineEmits<{
  'update:content': [val: string]
  save: []
  preview: []
  finalize: []
  back: []
}>()

// --- Initialize Canvas State ---
const initialRaw = props.content || props.initialContent || ''
const initialCanvasDoc = convertHtmlToCanvasDocument(initialRaw)
const canvas = useContractCanvas(initialCanvasDoc)
const uiStore = useUiStore()

// Compute dynamic variable replacements from studentData or contract metadata
const variableValues = computed(() => {
  const student = props.studentData || (props.studentName ? { full_name: props.studentName } : undefined)
  if (!student && !props.readonly) return undefined
  return buildVariableValues(student, {
    contractNumber: props.contractNumber,
    templateName: props.title,
  })
})

// UI Menus & Popovers
const showColorPicker = ref(false)
const showHighlightPicker = ref(false)
const showTableInsertMenu = ref(false)
const showMarginMenu = ref(false)
const showSpacingMenu = ref(false)
const showListMenu = ref(false)
const activeListType = ref<'ordered' | 'unordered' | null>(null)
const showVariablePicker = ref(false)
const showEditorDownloadMenu = ref(false)
const showShortcutHelp = ref(false)
const isDownloadingPdf = ref(false)

// Custom Table builder rows & cols
const customTableRows = ref(3)
const customTableCols = ref(3)

// Available font sizes (pt)
const fontSizes = [6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 18, 20, 22, 24, 28, 32]
const currentFontSize = computed(() => {
  const el = canvas.selectedElement.value as any
  if (el?.type === 'checkbox') return el?.style?.fontSize || el?.fontSize || 12
  return el?.style?.fontSize || 14
})

// Current font color
const currentFontColor = computed(() => {
  const el = canvas.selectedElement.value as any
  if (el?.type === 'checkbox') return el?.style?.color || el?.color || '#000000'
  return el?.style?.color || '#000000'
})

// Current text highlight
const currentHighlightColor = computed(() => {
  const el = canvas.selectedElement.value as any
  return el?.style?.backgroundColor || '#ffffff'
})

// 20 Curated Rich Text Colors
const TEXT_COLORS = [
  { name: 'Dark Slate', value: '#0f172a' },
  { name: 'Pure Black', value: '#000000' },
  { name: 'Charcoal', value: '#334155' },
  { name: 'Cool Gray', value: '#475569' },
  { name: 'Royal Blue', value: '#1d4ed8' },
  { name: 'Deep Navy', value: '#1e3a8a' },
  { name: 'Electric Indigo', value: '#4338ca' },
  { name: 'Deep Purple', value: '#6b21a8' },
  { name: 'Wine / Plum', value: '#831843' },
  { name: 'Crimson Red', value: '#b91c1c' },
  { name: 'Ruby / Rose', value: '#be123c' },
  { name: 'Rust / Brick', value: '#c2410c' },
  { name: 'Amber Gold', value: '#b45309' },
  { name: 'Deep Bronze', value: '#78350f' },
  { name: 'Forest Green', value: '#15803d' },
  { name: 'Deep Emerald', value: '#065f46' },
  { name: 'Teal Blue', value: '#0f766e' },
  { name: 'Ocean Cyan', value: '#0369a1' },
  { name: 'Olive Green', value: '#3f6212' },
  { name: 'Medium Slate', value: '#64748b' },
]

// 20 Curated Rich Background / Fill Colors
const CELL_BG_COLORS = [
  { name: 'Clear / White', value: '#ffffff' },
  { name: 'Slate Gray', value: '#475569' },
  { name: 'Dark Slate', value: '#1e293b' },
  { name: 'Medium Gray', value: '#64748b' },
  { name: 'Silver Slate', value: '#94a3b8' },
  { name: 'Royal Blue', value: '#2563eb' },
  { name: 'Deep Navy', value: '#1e3a8a' },
  { name: 'Ocean Blue', value: '#0284c7' },
  { name: 'Cyan Blue', value: '#0891b2' },
  { name: 'Deep Teal', value: '#0f766e' },
  { name: 'Emerald Green', value: '#059669' },
  { name: 'Forest Green', value: '#15803d' },
  { name: 'Olive Green', value: '#4d7c0f' },
  { name: 'Amber Gold', value: '#d97706' },
  { name: 'Warm Orange', value: '#ea580c' },
  { name: 'Crimson Red', value: '#dc2626' },
  { name: 'Deep Rose', value: '#e11d48' },
  { name: 'Vibrant Purple', value: '#7c3aed' },
  { name: 'Deep Violet', value: '#5b21b6' },
  { name: 'Plum / Wine', value: '#831843' },
]

// Page Margin presets
const marginPresets = [
  { name: 'Standard', top: 20, right: 15, bottom: 20, left: 25 },
  { name: 'Normal', top: 20, right: 20, bottom: 20, left: 20 },
  { name: 'Narrow', top: 12.7, right: 12.7, bottom: 12.7, left: 12.7 },
  { name: 'Wide', top: 25.4, right: 31.8, bottom: 25.4, left: 31.8 },
]

const currentMarginPresetName = computed(() => {
  const m = canvas.document.value.margins
  if (!m) return 'Standard'
  const match = marginPresets.find(
    p => p.top === m.top && p.right === m.right && p.bottom === m.bottom && p.left === m.left
  )
  return match ? match.name : 'Custom'
})

const printableContentWidthMm = computed(() => {
  const m = canvas.document.value.margins || { left: 25, right: 15 }
  return 210 - m.left - m.right
})

function applyMarginPreset(preset: typeof marginPresets[0]) {
  canvas.document.value.margins = {
    top: preset.top,
    right: preset.right,
    bottom: preset.bottom,
    left: preset.left,
  }
  showMarginMenu.value = false
}

function updateCustomMargin(key: keyof PageMargins, delta: number) {
  const m = canvas.document.value.margins
  const val = Math.max(5, Math.min(50, (m[key] || 20) + delta))
  m[key] = val
}

// Watch canvas changes and emit update:content
watch(
  () => canvas.document.value,
  newDoc => {
    emit('update:content', serializeCanvasDocument(newDoc))
  },
  { deep: true }
)

// Watch incoming props.content for switching contracts
watch(
  () => props.content,
  newContent => {
    if (!newContent) return
    const currentSerialized = serializeCanvasDocument(canvas.document.value)
    if (newContent !== currentSerialized) {
      const parsed = convertHtmlToCanvasDocument(newContent)
      canvas.document.value = parsed
      canvas.clearSelection()
    }
  }
)

// Global keyboard listeners — centralized shortcut system
function onKeyDown(e: KeyboardEvent) {
  const isMod = e.ctrlKey || e.metaKey
  const activeEl = window.document.activeElement as HTMLElement | null
  // Canvas text elements are contenteditable too, but - unlike a plain
  // <input>/<textarea> or a table cell - Ctrl+B/I/U should keep working
  // inside them (to format the highlighted selection; see applyInlineFormat).
  const isInCanvasTextEdit = Boolean(activeEl?.closest('.canvas-text-element'))
  const isInOtherTextField =
    !isInCanvasTextEdit &&
    Boolean(
      activeEl &&
        (activeEl.tagName === 'INPUT' ||
          activeEl.tagName === 'TEXTAREA' ||
          activeEl.getAttribute('contenteditable') === 'true' ||
          activeEl.closest('[contenteditable="true"]'))
    )
  const isInTextEdit = isInCanvasTextEdit || isInOtherTextField

  // ── Ctrl+S → Save (always, even in text edit) ────────────────
  if (isMod && (e.key === 's' || e.key === 'S') && !e.shiftKey) {
    e.preventDefault()
    emit('save')
    return
  }

  // ── Ctrl+/ or ? → Shortcut help modal ───────────────────────
  if ((isMod && e.key === '/') || (e.key === '?' && !isInTextEdit)) {
    e.preventDefault()
    showShortcutHelp.value = !showShortcutHelp.value
    return
  }

  // ── Escape → exit copy style mode or close help modal ─────────
  if (e.key === 'Escape') {
    if (copyStyleMode.value) {
      e.preventDefault()
      deactivateCopyStyle()
      return
    }
    if (showShortcutHelp.value) {
      showShortcutHelp.value = false
      return
    }
  }

  // ── Canva Copy Style: Ctrl+Alt+C / Cmd+Option+C ────────────
  if (isMod && e.altKey && (e.key === 'c' || e.key === 'C')) {
    e.preventDefault()
    if (isTextSelected.value) {
      activateCopyStyle('single')
    }
    return
  }

  // ── Canva Paste Style: Ctrl+Alt+V / Cmd+Option+V ───────────
  if (isMod && e.altKey && (e.key === 'v' || e.key === 'V')) {
    e.preventDefault()
    pasteCopiedStyleToSelected()
    return
  }

  // ── Spacebar for Canvas Pan (Hand tool) ────────────────────
  if (e.code === 'Space' && !isInTextEdit && !isSpacePressed.value) {
    e.preventDefault()
    isSpacePressed.value = true
    return
  }

  // ── Text formatting: works both when an element is merely selected AND
  //    while actively editing its text (applyInlineFormat then targets the
  //    highlighted selection instead of the whole block). Only truly
  //    unrelated text fields (inputs, table cells) are excluded. ──
  if (isMod && !isInOtherTextField && canvas.selectedElement.value) {
    // Ctrl+B → Bold
    if ((e.key === 'b' || e.key === 'B') && !e.shiftKey) {
      e.preventDefault()
      toggleBold()
      return
    }
    // Ctrl+I → Italic
    if ((e.key === 'i' || e.key === 'I') && !e.shiftKey) {
      e.preventDefault()
      toggleItalic()
      return
    }
    // Ctrl+U → Underline
    if ((e.key === 'u' || e.key === 'U') && !e.shiftKey) {
      e.preventDefault()
      toggleUnderline()
      return
    }
    // Alignment: Ctrl+Shift+L/E/R/J
    if (e.shiftKey) {
      if (e.key === 'L') { e.preventDefault(); setTextAlign('left'); return }
      if (e.key === 'E') { e.preventDefault(); setTextAlign('center'); return }
      if (e.key === 'R') { e.preventDefault(); setTextAlign('right'); return }
      if (e.key === 'J') { e.preventDefault(); setTextAlign('justify'); return }
      // Ctrl+Shift+X → Strikethrough
      if (e.key === 'X') { e.preventDefault(); toggleStrike(); return }
      // Ctrl+Shift+> or . → Font size increase
      if (e.key === '>' || e.key === '.') {
        e.preventDefault()
        const cur = currentFontSize.value
        const idx = fontSizes.indexOf(cur)
        if (idx < fontSizes.length - 1) setFontSize(fontSizes[idx + 1])
        return
      }
      // Ctrl+Shift+< or , → Font size decrease
      if (e.key === '<' || e.key === ',') {
        e.preventDefault()
        const cur = currentFontSize.value
        const idx = fontSizes.indexOf(cur)
        if (idx > 0) setFontSize(fontSizes[idx - 1])
        return
      }
    }
  }

  // ── Document Zoom: Ctrl+= / Ctrl+- / Ctrl+0 ──────────────────
  if (isMod && !isInTextEdit) {
    if (e.key === '=' || e.key === '+') {
      e.preventDefault()
      zoomInAroundCenter()
      return
    }
    if (e.key === '-' || e.key === '_') {
      e.preventDefault()
      zoomOutAroundCenter()
      return
    }
    if (e.key === '0') {
      e.preventDefault()
      zoomResetAroundCenter()
      return
    }
  }

  // ── Delegate remaining shortcuts to canvas handler ──────────
  canvas.handleKeyDown(e)
}

// Canvas workspace ref for wheel events, scrolling, and anchoring
const canvasWorkspaceRef = ref<HTMLElement | null>(null)

// Physical mm-to-px factor (zoom-independent base)
const MM_TO_PX_BASE = 3.779527559

// Re-entrancy guard & queue for zoom animations (avoids race conditions on rapid wheel/slider)
let isZooming = false
let pendingZoomAction: { zoom: number; anchor?: { x: number; y: number } } | null = null

/**
 * Core zoom engine: zooms the document while preserving the exact viewport position
 * of the document anchor point.
 *
 * @param newZoom Target zoom percentage (25-500)
 * @param viewportAnchor Optional pixel offset { x, y } inside the scroll container.
 *                       If omitted, anchors around the VISIBLE CENTER of the viewport.
 */
async function performZoom(newZoom: number, viewportAnchor?: { x: number; y: number }) {
  const ws = canvasWorkspaceRef.value
  if (!ws) {
    canvas.setZoom(newZoom)
    return
  }

  const oldZoom = canvas.zoomLevel.value
  if (oldZoom === newZoom) return

  const wsRect = ws.getBoundingClientRect()
  // Determine anchor in viewport pixels relative to scroll container viewport
  const vAnchorX = viewportAnchor !== undefined ? viewportAnchor.x : ws.clientWidth / 2
  const vAnchorY = viewportAnchor !== undefined ? viewportAnchor.y : ws.clientHeight / 2

  const anchorClientX = wsRect.left + vAnchorX
  const anchorClientY = wsRect.top + vAnchorY

  // Find the page sheet closest to the anchor point (supports multi-page seamlessly)
  const sheets = Array.from(ws.querySelectorAll<HTMLElement>('.canvas-sheet-background'))
  let targetPageIndex = 0
  let chosenSheet = sheets[0]

  if (sheets.length > 1) {
    let minDistance = Infinity
    sheets.forEach((sheet, idx) => {
      const rect = sheet.getBoundingClientRect()
      const cx = rect.left + rect.width / 2
      const cy = rect.top + rect.height / 2
      const dist = Math.hypot(anchorClientX - cx, anchorClientY - cy)
      if (dist < minDistance) {
        minDistance = dist
        targetPageIndex = idx
        chosenSheet = sheet
      }
    })
  }

  const oldScale = oldZoom / 100
  let anchorMmX = 105 // default center of A4 width
  let anchorMmY = 148.5 // default center of A4 height

  if (chosenSheet) {
    const sheetRect = chosenSheet.getBoundingClientRect()
    const relX = anchorClientX - sheetRect.left
    const relY = anchorClientY - sheetRect.top
    anchorMmX = relX / (MM_TO_PX_BASE * oldScale)
    anchorMmY = relY / (MM_TO_PX_BASE * oldScale)
  }

  // Update zoom reactive state
  canvas.setZoom(newZoom)

  // Wait for DOM to re-render with new layout dimensions
  await nextTick()

  const currentWs = canvasWorkspaceRef.value
  if (!currentWs) return

  const currentWsRect = currentWs.getBoundingClientRect()
  const sheetsAfter = currentWs.querySelectorAll<HTMLElement>('.canvas-sheet-background')
  const newSheet = sheetsAfter[targetPageIndex] || sheetsAfter[0]

  if (newSheet) {
    const newSheetRect = newSheet.getBoundingClientRect()
    const sheetContentLeft = newSheetRect.left - currentWsRect.left + currentWs.scrollLeft
    const sheetContentTop = newSheetRect.top - currentWsRect.top + currentWs.scrollTop

    const newScale = newZoom / 100
    const newAnchorContentX = sheetContentLeft + anchorMmX * (MM_TO_PX_BASE * newScale)
    const newAnchorContentY = sheetContentTop + anchorMmY * (MM_TO_PX_BASE * newScale)

    const targetScrollLeft = newAnchorContentX - vAnchorX
    const targetScrollTop = newAnchorContentY - vAnchorY

    currentWs.scrollLeft = Math.max(0, targetScrollLeft)
    currentWs.scrollTop = Math.max(0, targetScrollTop)
  }
}

/**
 * Public anchor zoom entry point with queue protection against rapid events.
 */
async function zoomWithAnchor(newZoom: number, viewportAnchor?: { x: number; y: number }) {
  const clampedZoom = Math.max(25, Math.min(500, newZoom))
  if (isZooming) {
    pendingZoomAction = { zoom: clampedZoom, anchor: viewportAnchor }
    return
  }
  isZooming = true
  try {
    await performZoom(clampedZoom, viewportAnchor)
    while (pendingZoomAction) {
      const next = pendingZoomAction
      pendingZoomAction = null
      await performZoom(next.zoom, next.anchor)
    }
  } finally {
    isZooming = false
  }
}

function zoomInAroundCenter() {
  const cur = canvas.zoomLevel.value
  zoomWithAnchor(Math.min(500, cur + 15))
}

function zoomOutAroundCenter() {
  const cur = canvas.zoomLevel.value
  zoomWithAnchor(Math.max(25, cur - 15))
}

function zoomResetAroundCenter() {
  canvas.setZoom(100)
  nextTick(() => {
    const ws = canvasWorkspaceRef.value
    if (!ws) return
    ws.scrollLeft = 0
    const activePageEl = ws.querySelector<HTMLElement>(`[data-page-index="${canvas.activePageIndex.value}"]`)
    if (activePageEl) {
      const wsRect = ws.getBoundingClientRect()
      const elRect = activePageEl.getBoundingClientRect()
      const offsetTop = elRect.top - wsRect.top + ws.scrollTop - 24
      ws.scrollTop = Math.max(0, offsetTop)
    }
  })
}

// ─── Custom Vertical Zoom Slider (Pointer-captured, direct clientY) ───
const zoomSliderTrackRef = ref<HTMLElement | null>(null)
let isDraggingSlider = false

const sliderPercent = computed(() => {
  const cur = canvas.zoomLevel.value
  const clamped = Math.max(25, Math.min(500, cur))
  return (((clamped - 25) / 475) * 100).toFixed(1)
})

function updateZoomFromPointer(clientY: number) {
  const track = zoomSliderTrackRef.value
  if (!track) return
  const rect = track.getBoundingClientRect()
  // Bottom of track is min (25%), top is max (500%)
  const ratio = Math.max(0, Math.min(1, (rect.bottom - clientY) / rect.height))
  let target = Math.round(25 + ratio * 475)
  // Step in 5s
  target = Math.round(target / 5) * 5
  // Magnetic notch: cleanly snap to 100% when near it
  if (target >= 92 && target <= 108) {
    target = 100
  }
  target = Math.max(25, Math.min(500, target))
  zoomWithAnchor(target)
}

function onSliderPointerDown(e: PointerEvent) {
  if (e.button !== 0) return
  e.preventDefault()
  e.stopPropagation()
  isDraggingSlider = true
  try {
    ;(e.currentTarget as HTMLElement).setPointerCapture(e.pointerId)
  } catch {
    // ignore
  }
  updateZoomFromPointer(e.clientY)
}

function onSliderPointerMove(e: PointerEvent) {
  if (!isDraggingSlider) return
  e.preventDefault()
  updateZoomFromPointer(e.clientY)
}

function onSliderPointerUp(e: PointerEvent) {
  if (isDraggingSlider) {
    isDraggingSlider = false
    try {
      ;(e.currentTarget as HTMLElement).releasePointerCapture(e.pointerId)
    } catch {
      // ignore
    }
  }
}

// ─── Canvas Panning (Spacebar + Drag / Middle Mouse Button) ───
const isSpacePressed = ref(false)
const isPanning = ref(false)
let panStartX = 0
let panStartY = 0
let panStartScrollLeft = 0
let panStartScrollTop = 0

function onKeyUp(e: KeyboardEvent) {
  if (e.code === 'Space') {
    isSpacePressed.value = false
    if (isPanning.value) {
      onWorkspacePointerUp()
    }
  }
}

function onWindowBlur() {
  isSpacePressed.value = false
  if (isPanning.value) {
    onWorkspacePointerUp()
  }
}

function onGlobalPointerDown(e: PointerEvent) {
  // Middle click (button 1) OR Left click (button 0) when Spacebar is held
  if (e.button === 1 || (e.button === 0 && isSpacePressed.value)) {
    const ws = canvasWorkspaceRef.value
    if (!ws || !ws.contains(e.target as Node)) return

    e.preventDefault()
    e.stopPropagation()

    isPanning.value = true
    panStartX = e.clientX
    panStartY = e.clientY
    panStartScrollLeft = ws.scrollLeft
    panStartScrollTop = ws.scrollTop

    window.addEventListener('pointermove', onWorkspacePointerMove, { passive: false })
    window.addEventListener('pointerup', onWorkspacePointerUp, { passive: false })
  }
}

function onWorkspacePointerMove(e: PointerEvent) {
  if (!isPanning.value) return
  const ws = canvasWorkspaceRef.value
  if (!ws) return

  e.preventDefault()
  const dx = e.clientX - panStartX
  const dy = e.clientY - panStartY

  ws.scrollLeft = panStartScrollLeft - dx
  ws.scrollTop = panStartScrollTop - dy
}

function onWorkspacePointerUp(e?: PointerEvent) {
  if (isPanning.value) {
    isPanning.value = false
    window.removeEventListener('pointermove', onWorkspacePointerMove)
    window.removeEventListener('pointerup', onWorkspacePointerUp)
  }
}

/**
 * MouseWheel handler:
 * - Ctrl + Wheel or Trackpad Pinch = zoom anchored to mouse cursor (Figma/Canva style)
 * - Shift + Wheel = smooth horizontal scroll
 */
function onCanvasWheel(e: WheelEvent) {
  const ws = canvasWorkspaceRef.value
  if (!ws) return

  // 1. Ctrl + Wheel = Zoom
  if (e.ctrlKey || e.metaKey) {
    e.preventDefault()
    e.stopPropagation()

    const wsRect = ws.getBoundingClientRect()
    const mouseViewX = e.clientX - wsRect.left
    const mouseViewY = e.clientY - wsRect.top

    // Calculate delta: positive deltaY means zoom out, negative means zoom in
    const delta = e.deltaY < 0 ? 10 : -10
    const currentZoom = canvas.zoomLevel.value
    const targetZoom = Math.max(25, Math.min(500, currentZoom + delta))

    if (targetZoom !== currentZoom) {
      zoomWithAnchor(targetZoom, { x: mouseViewX, y: mouseViewY })
    }
    return
  }

  // 2. Shift + Wheel = Horizontal Scroll
  if (e.shiftKey) {
    e.preventDefault()
    ws.scrollLeft += e.deltaY
    return
  }
}

// Track active page as user scrolls through the multi-page canvas
let scrollRafId: number | null = null
function onWorkspaceScroll() {
  if (scrollRafId) return
  scrollRafId = requestAnimationFrame(() => {
    scrollRafId = null
    if (!canvasWorkspaceRef.value) return
    // If elements are already selected on a page, keep that page active
    if (canvas.selectedElementIds.value.length > 0) return

    const workspaceRect = canvasWorkspaceRef.value.getBoundingClientRect()
    const workspaceTargetY = workspaceRect.top + workspaceRect.height / 3

    const pageContainers = canvasWorkspaceRef.value.querySelectorAll<HTMLElement>('.canvas-a4-page-container')
    let closestIdx = -1
    let minDistance = Infinity

    pageContainers.forEach((el) => {
      const rect = el.getBoundingClientRect()
      const pageCenterY = rect.top + rect.height / 2
      const dist = Math.abs(pageCenterY - workspaceTargetY)
      if (dist < minDistance) {
        minDistance = dist
        const pIdx = parseInt(el.getAttribute('data-page-index') || '0', 10)
        closestIdx = pIdx
      }
    })

    if (closestIdx >= 0 && closestIdx !== canvas.activePageIndex.value) {
      canvas.setActivePageIndex(closestIdx)
    }
  })
}

// Close all dropdown menus (click-outside support)
function closeAllDropdowns() {
  showTableInsertMenu.value = false
  showVariablePicker.value = false
  showColorPicker.value = false
  showHighlightPicker.value = false
  showMarginMenu.value = false
  showSpacingMenu.value = false
  showListMenu.value = false
  showEditorDownloadMenu.value = false
}

// Undo / Redo helpers (called once per action — buttons previously called undo() twice!)
function performUndo() {
  const state = canvas.history.undo()
  if (state) {
    canvas.document.value = state
    nextTick(() => canvas.history.settleHistoryUpdate())
  }
}

function performRedo() {
  const state = canvas.history.redo()
  if (state) {
    canvas.document.value = state
    nextTick(() => canvas.history.settleHistoryUpdate())
  }
}

// Called when drag or resize finishes — records a history snapshot so Ctrl+Z works
function onDragResizeEnd() {
  canvas.history.recordSnapshot(canvas.document.value)
}

onMounted(() => {
  window.addEventListener('keydown', onKeyDown)
  window.addEventListener('keyup', onKeyUp)
  window.addEventListener('blur', onWindowBlur)
  window.addEventListener('paste', onGlobalPaste)
  window.addEventListener('pointerdown', onGlobalPointerDown, { capture: true })
  // Document-level click → close all open dropdowns
  document.addEventListener('click', closeAllDropdowns)
  document.addEventListener('selectionchange', updateActiveListState)
  // Use passive:false so we can preventDefault on Ctrl+Wheel and Shift+Wheel
  canvasWorkspaceRef.value?.addEventListener('wheel', onCanvasWheel, { passive: false })
  canvasWorkspaceRef.value?.addEventListener('scroll', onWorkspaceScroll, { passive: true })
})

onBeforeUnmount(() => {
  window.removeEventListener('keydown', onKeyDown)
  window.removeEventListener('keyup', onKeyUp)
  window.removeEventListener('blur', onWindowBlur)
  window.removeEventListener('paste', onGlobalPaste)
  window.removeEventListener('pointerdown', onGlobalPointerDown, { capture: true })
  onWorkspacePointerUp()
  document.removeEventListener('click', closeAllDropdowns)
  document.removeEventListener('selectionchange', updateActiveListState)
  canvasWorkspaceRef.value?.removeEventListener('wheel', onCanvasWheel)
  canvasWorkspaceRef.value?.removeEventListener('scroll', onWorkspaceScroll)
  if (scrollRafId) cancelAnimationFrame(scrollRafId)
})

// --- Toolbar Element Styling Helpers ---
function setFontSize(sizePt: number | string) {
  const num = typeof sizePt === 'string' ? parseInt(sizePt, 10) : sizePt
  const el = canvas.selectedElement.value as any
  if (!el) return
  if (!el.style) el.style = {}
  el.style.fontSize = num
  canvas.history.recordSnapshot(canvas.document.value)
}

/**
 * Bold/Italic/Underline/Strikethrough need two different behaviors depending
 * on context, same as a real word processor:
 *  - Actively editing with an actual text selection highlighted: format just
 *    that run via execCommand (same technique already used by
 *    applyListFormat/increaseIndent/decreaseIndent below), so a single word
 *    can be bolded inside a paragraph instead of the whole block.
 *  - Otherwise (element merely selected, or a caret with nothing
 *    highlighted): toggle the whole block's base style, as before.
 * Either path now always records a history snapshot - previously this only
 * happened for checkbox elements, so bolding a paragraph was silently
 * unrecoverable with Ctrl+Z.
 */
function applyInlineFormat(command: 'bold' | 'italic' | 'underline' | 'strikeThrough', toggleWholeElement: (el: any) => void) {
  const el = canvas.selectedElement.value as any
  if (!el) return

  const activeEl = window.document.activeElement as HTMLElement | null
  const isInsideEditable = Boolean(
    activeEl && (activeEl.getAttribute('contenteditable') === 'true' || activeEl.closest('.canvas-text-element'))
  )
  const sel = window.getSelection()
  const hasHighlightedText = Boolean(sel && sel.rangeCount > 0 && !sel.isCollapsed)

  if (isInsideEditable && hasHighlightedText) {
    window.document.execCommand(command, false)
    const container = (activeEl!.closest('.canvas-text-element') || activeEl) as HTMLElement
    if (container) el.content = container.innerHTML
  } else {
    if (!el.style) el.style = {}
    toggleWholeElement(el)
  }

  nextTick(() => canvas.history.recordSnapshot(canvas.document.value))
}

function toggleBold() {
  applyInlineFormat('bold', el => {
    el.style.fontWeight = (el.style.fontWeight === 'bold' || el.style.fontWeight === 700) ? 'normal' : 'bold'
  })
}

function toggleItalic() {
  applyInlineFormat('italic', el => {
    el.style.fontStyle = el.style.fontStyle === 'italic' ? 'normal' : 'italic'
  })
}

function toggleUnderline() {
  applyInlineFormat('underline', el => {
    const current = el.style.textDecoration || ''
    el.style.textDecoration = current.includes('underline')
      ? (current.replace('underline', '').trim() || 'none')
      : (current === 'none' || !current ? 'underline' : `${current} underline`)
  })
}

function toggleStrike() {
  applyInlineFormat('strikeThrough', el => {
    const current = el.style.textDecoration || ''
    el.style.textDecoration = current.includes('line-through')
      ? (current.replace('line-through', '').trim() || 'none')
      : (current === 'none' || !current ? 'line-through' : `${current} line-through`)
  })
}

function setTextAlign(align: 'left' | 'center' | 'right' | 'justify') {
  const el = canvas.selectedElement.value as TextCanvasElement
  if (!el) return
  if (!el.style) el.style = {}
  el.style.textAlign = align
  canvas.history.recordSnapshot(canvas.document.value)
}

// Alignment cycle: Left → Center → Right → Justify → Left
const ALIGN_CYCLE: ('left' | 'center' | 'right' | 'justify')[] = ['left', 'center', 'right', 'justify']

const currentTextAlign = computed(() => {
  const el = canvas.selectedElement.value as TextCanvasElement
  return (el?.style?.textAlign as 'left' | 'center' | 'right' | 'justify') || 'left'
})

function cycleTextAlign() {
  if (!canvas.selectedElement.value) return
  const idx = ALIGN_CYCLE.indexOf(currentTextAlign.value)
  setTextAlign(ALIGN_CYCLE[(idx + 1) % ALIGN_CYCLE.length])
}

// Dropdown toggles (with clean mutual exclusivity)
function toggleColorPicker() {
  const next = !showColorPicker.value
  closeAllDropdowns()
  showColorPicker.value = next
}

function toggleHighlightPicker() {
  const next = !showHighlightPicker.value
  closeAllDropdowns()
  showHighlightPicker.value = next
}

// Margins dropdown toggle
function toggleMarginMenu() {
  const next = !showMarginMenu.value
  closeAllDropdowns()
  showMarginMenu.value = next
}

// Spacing dropdown toggle (Canva style)
function toggleSpacingMenu() {
  const next = !showSpacingMenu.value
  closeAllDropdowns()
  showSpacingMenu.value = next
}

// List dropdown toggle & active state (Canva / Word Style)
function toggleListMenu() {
  const next = !showListMenu.value
  closeAllDropdowns()
  showListMenu.value = next
  if (next) updateActiveListState()
}

function updateActiveListState() {
  const sel = window.document.getSelection()
  if (sel && sel.rangeCount > 0) {
    let node: Node | null = sel.anchorNode
    if (node && node.nodeType === Node.TEXT_NODE) node = node.parentNode
    const li = (node as HTMLElement)?.closest?.('li')
    if (li) {
      const list = li.closest('ol, ul')
      if (list) {
        activeListType.value = list.tagName.toLowerCase() === 'ol' ? 'ordered' : 'unordered'
        return
      }
    }
  }

  // Fallback: check selected canvas element content
  const el = canvas.selectedElement.value as TextCanvasElement | null
  if (el && el.content) {
    const trimmed = el.content.trim().toLowerCase()
    if (trimmed.startsWith('<ol') || trimmed.includes('<ol>') || trimmed.includes('<ol ')) {
      activeListType.value = 'ordered'
      return
    }
    if (trimmed.startsWith('<ul') || trimmed.includes('<ul>') || trimmed.includes('<ul ')) {
      activeListType.value = 'unordered'
      return
    }
  }
  activeListType.value = null
}

function formatHtmlAsList(html: string, type: 'ordered' | 'unordered'): string {
  const parser = new DOMParser()
  const doc = parser.parseFromString(`<body>${html}</body>`, 'text/html')
  const body = doc.body

  const targetTag = type === 'ordered' ? 'ol' : 'ul'
  const otherTag = type === 'ordered' ? 'ul' : 'ol'

  // 1. If body already contains exclusively the TARGET list type -> unwrap back to <p>
  if (body.children.length === 1 && body.firstElementChild?.tagName.toLowerCase() === targetTag) {
    const list = body.firstElementChild
    const items: string[] = []
    Array.from(list.children).forEach(li => {
      items.push(`<p>${li.innerHTML || '<br>'}</p>`)
    })
    return items.join('') || '<p><br></p>'
  }

  // 2. If body contains the OPPOSITE list type -> switch tag (<ol> <-> <ul>)
  if (body.children.length === 1 && body.firstElementChild?.tagName.toLowerCase() === otherTag) {
    const list = body.firstElementChild
    const newList = doc.createElement(targetTag)
    newList.innerHTML = list.innerHTML
    return newList.outerHTML
  }

  // 3. Convert paragraphs or raw text lines into list items
  const list = doc.createElement(targetTag)
  if (body.children.length > 0) {
    Array.from(body.children).forEach(child => {
      const tag = child.tagName.toLowerCase()
      if (tag === 'p' || tag === 'div') {
        const li = doc.createElement('li')
        li.innerHTML = child.innerHTML || '<br>'
        list.appendChild(li)
      } else if (tag === 'ol' || tag === 'ul') {
        Array.from(child.children).forEach(li => list.appendChild(li.cloneNode(true)))
      } else {
        const li = doc.createElement('li')
        li.innerHTML = child.outerHTML
        list.appendChild(li)
      }
    })
  } else {
    const raw = body.textContent || ''
    const lines = raw.split('\n').map(l => l.trim()).filter(Boolean)
    if (lines.length > 0) {
      lines.forEach(line => {
        const li = doc.createElement('li')
        li.textContent = line
        list.appendChild(li)
      })
    } else {
      const li = doc.createElement('li')
      li.innerHTML = '<br>'
      list.appendChild(li)
    }
  }

  return list.outerHTML
}

function applyListFormat(type: 'ordered' | 'unordered') {
  closeAllDropdowns()
  const selected = canvas.selectedElement.value as TextCanvasElement | null
  if (!selected || !isTextSelected.value) return

  const activeEl = window.document.activeElement as HTMLElement | null
  const isInsideEditable = activeEl && (
    activeEl.getAttribute('contenteditable') === 'true' ||
    Boolean(activeEl.closest('.canvas-text-element')) ||
    Boolean(activeEl.closest('[contenteditable="true"]'))
  )

  if (isInsideEditable) {
    const cmd = type === 'ordered' ? 'insertOrderedList' : 'insertUnorderedList'
    window.document.execCommand(cmd, false)
    const container = (activeEl.closest('.canvas-text-element') || activeEl) as HTMLElement
    if (container) {
      selected.content = container.innerHTML
    }
  } else {
    selected.content = formatHtmlAsList(selected.content || '', type)
  }

  nextTick(() => {
    updateActiveListState()
    canvas.history.recordSnapshot(canvas.document.value)
  })
}

function increaseIndent() {
  const selected = canvas.selectedElement.value as TextCanvasElement | null
  if (!selected || !isTextSelected.value) return

  const activeEl = window.document.activeElement as HTMLElement | null
  const isInsideEditable = activeEl && (
    activeEl.getAttribute('contenteditable') === 'true' ||
    Boolean(activeEl.closest('.canvas-text-element'))
  )

  if (isInsideEditable) {
    window.document.execCommand('indent', false)
    const container = (activeEl.closest('.canvas-text-element') || activeEl) as HTMLElement
    if (container) {
      selected.content = container.innerHTML
    }
  }
  nextTick(() => {
    updateActiveListState()
    canvas.history.recordSnapshot(canvas.document.value)
  })
}

function decreaseIndent() {
  const selected = canvas.selectedElement.value as TextCanvasElement | null
  if (!selected || !isTextSelected.value) return

  const activeEl = window.document.activeElement as HTMLElement | null
  const isInsideEditable = activeEl && (
    activeEl.getAttribute('contenteditable') === 'true' ||
    Boolean(activeEl.closest('.canvas-text-element'))
  )

  if (isInsideEditable) {
    window.document.execCommand('outdent', false)
    const container = (activeEl.closest('.canvas-text-element') || activeEl) as HTMLElement
    if (container) {
      selected.content = container.innerHTML
    }
  }
  nextTick(() => {
    updateActiveListState()
    canvas.history.recordSnapshot(canvas.document.value)
  })
}

function toggleTableInsertMenu() {
  const next = !showTableInsertMenu.value
  closeAllDropdowns()
  showTableInsertMenu.value = next
}

function toggleVariablePicker() {
  const next = !showVariablePicker.value
  closeAllDropdowns()
  showVariablePicker.value = next
}

const isTextSelected = computed(() => {
  const el = canvas.selectedElement.value
  if (!el) return false
  return (
    el.type === 'text' ||
    el.type === 'heading' ||
    el.type === 'paragraph' ||
    el.type === 'date' ||
    el.type === 'variable' ||
    el.type === 'checkbox'
  )
})

const currentLineHeight = computed(() => {
  const el = canvas.selectedElement.value as any
  return el?.style?.lineHeight ?? 1.5
})

const currentLetterSpacing = computed(() => {
  const el = canvas.selectedElement.value as any
  return el?.style?.letterSpacing ?? 0
})

function setLineHeight(val: number | string) {
  const num = typeof val === 'string' ? parseFloat(val) : val
  if (isNaN(num)) return
  const el = canvas.selectedElement.value as any
  if (!el) return
  if (!el.style) el.style = {}
  el.style.lineHeight = Math.max(0.5, Math.min(3.5, Math.round(num * 100) / 100))
  if (el.type === 'checkbox') {
    canvas.updateElement(el.id, { style: { ...el.style } })
  }
}

function setLetterSpacing(val: number | string) {
  const num = typeof val === 'string' ? parseFloat(val) : val
  if (isNaN(num)) return
  const el = canvas.selectedElement.value as any
  if (!el) return
  if (!el.style) el.style = {}
  el.style.letterSpacing = Math.max(-5, Math.min(30, Math.round(num * 10) / 10))
  if (el.type === 'checkbox') {
    canvas.updateElement(el.id, { style: { ...el.style } })
  }
}

function commitSpacingChange() {
  canvas.history.recordSnapshot(canvas.document.value)
}

function setFontColor(color: string) {
  const el = canvas.selectedElement.value as any
  if (!el) return
  if (!el.style) el.style = {}
  el.style.color = color
  canvas.history.recordSnapshot(canvas.document.value)
  showColorPicker.value = false
}

function setHighlightColor(color: string) {
  const el = canvas.selectedElement.value as any
  if (!el) return
  if (el.type === 'table') {
    // Apply fill to all cells in table
    const table = el as TableCanvasElement
    table.cells.forEach(row => {
      row.forEach(c => {
        c.backgroundColor = color === '#ffffff' ? undefined : color
      })
    })
  } else if (el.type === 'checkbox') {
    if (!el.style) el.style = {}
    const bg = color === '#ffffff' ? 'transparent' : color
    el.style.backgroundColor = bg
  } else {
    const textEl = el as TextCanvasElement
    if (!textEl.style) textEl.style = {}
    textEl.style.backgroundColor = color === '#ffffff' ? 'transparent' : color
  }
  canvas.history.recordSnapshot(canvas.document.value)
  showHighlightPicker.value = false
}

// --- Canva-Style "Copy Style" (Format Painter) ---
const copyStyleMode = ref<'single' | 'persistent' | null>(null)
const copiedTextStyle = ref<TextStyleProps | null>(null)

function extractElementStyle(el: any): TextStyleProps {
  const st = el.style || {}
  return {
    fontFamily: st.fontFamily,
    fontSize: st.fontSize || el.fontSize,
    fontWeight: st.fontWeight,
    fontStyle: st.fontStyle,
    textDecoration: st.textDecoration,
    color: st.color || el.color,
    backgroundColor: st.backgroundColor,
    textAlign: st.textAlign,
    lineHeight: st.lineHeight,
    letterSpacing: st.letterSpacing,
    textTransform: st.textTransform,
  }
}

function activateCopyStyle(mode: 'single' | 'persistent' = 'single') {
  const selected = canvas.selectedElement.value as any
  if (!selected || !isTextSelected.value) return
  closeAllDropdowns()
  copiedTextStyle.value = extractElementStyle(selected)
  copyStyleMode.value = mode
}

function deactivateCopyStyle() {
  copyStyleMode.value = null
  copiedTextStyle.value = null
}

function handleCopyStyleButtonClick(e: MouseEvent) {
  if (e.detail >= 2) {
    // Double click: persistent/locked mode
    activateCopyStyle('persistent')
    return
  }
  if (copyStyleMode.value) {
    // Click while active -> turn off
    deactivateCopyStyle()
    return
  }
  // Single click: single target mode
  activateCopyStyle('single')
}

function applyCopiedStyleToElement(targetId: string) {
  if (!copiedTextStyle.value || !copyStyleMode.value) return
  const found = canvas.findElementAndPage(targetId)
  if (!found) return
  const el = found.element as any

  // Only apply to text elements and checkboxes
  const isText =
    el.type === 'text' ||
    el.type === 'heading' ||
    el.type === 'paragraph' ||
    el.type === 'date' ||
    el.type === 'variable' ||
    el.type === 'checkbox'
  if (!isText) return

  // Apply copied style ONLY — CONTENT IS NEVER CHANGED!
  // Position, Dimensions, ID, and element metadata are NEVER CHANGED!
  const st = copiedTextStyle.value
  if (!el.style) el.style = {}

  if (st.fontFamily !== undefined) el.style.fontFamily = st.fontFamily
  if (st.fontSize !== undefined) {
    el.style.fontSize = st.fontSize
    if (el.type === 'checkbox') el.fontSize = st.fontSize
  }
  if (st.fontWeight !== undefined) el.style.fontWeight = st.fontWeight
  if (st.fontStyle !== undefined) el.style.fontStyle = st.fontStyle
  if (st.textDecoration !== undefined) el.style.textDecoration = st.textDecoration
  if (st.color !== undefined) {
    el.style.color = st.color
    if (el.type === 'checkbox') el.color = st.color
  }
  if (st.backgroundColor !== undefined) el.style.backgroundColor = st.backgroundColor
  if (st.textAlign !== undefined && el.type !== 'checkbox') el.style.textAlign = st.textAlign
  if (st.lineHeight !== undefined) el.style.lineHeight = st.lineHeight
  if (st.letterSpacing !== undefined) el.style.letterSpacing = st.letterSpacing
  if (st.textTransform !== undefined) el.style.textTransform = st.textTransform

  if (el.type === 'checkbox') {
    canvas.updateElement(el.id, {
      style: { ...el.style },
      fontSize: el.fontSize,
      color: el.color,
    })
  }

  // Select target element so user sees it highlighted with new style
  canvas.selectElement(targetId, false, found.pageIndex)

  // Record history snapshot for undo/redo
  canvas.history.recordSnapshot(canvas.document.value)

  // In single-use mode, deactivate automatically after applying once
  if (copyStyleMode.value === 'single') {
    deactivateCopyStyle()
  }
}

function pasteCopiedStyleToSelected() {
  if (!copiedTextStyle.value) return
  const sel = canvas.selectedElement.value
  if (sel && isTextSelected.value) {
    applyCopiedStyleToElement(sel.id)
  }
}

function handleSelectElement(id: string, multi: boolean, pageIdx?: number) {
  if (copyStyleMode.value) {
    applyCopiedStyleToElement(id)
    return
  }
  canvas.selectElement(id, multi, pageIdx)
}

// Automatically create and paste a new Text element from system clipboard (Times New Roman, 14pt, black)
function handlePasteNewText(clipboardData: DataTransfer) {
  closeAllDropdowns()
  const contentWidth = printableContentWidthMm.value || (210 - canvas.document.value.margins.left - canvas.document.value.margins.right)
  const page = canvas.activePage.value
  let targetY = canvas.document.value.margins.top + 5

  if (page && page.elements.length > 0) {
    const maxY = page.elements.reduce((max, el) => Math.max(max, (el.y || 0) + (el.height || 0)), 0)
    if (maxY + 15 < (297 - canvas.document.value.margins.bottom)) {
      targetY = maxY + 4
    }
  }

  // Clean HTML/text, stripping Telegram white fonts and dark backgrounds
  const cleanHtml = cleanClipboardContent(clipboardData, '#000000')
  if (!cleanHtml || !cleanHtml.trim()) return

  // Calculate dynamic element height so bounding box fits the pasted text
  const calculatedHeight = estimateTextHeightMm(cleanHtml, contentWidth, 14)

  const newElement: TextCanvasElement = {
    id: `text_${Date.now()}_${Math.random().toString(36).substring(2, 6)}`,
    type: 'text',
    x: canvas.document.value.margins.left,
    y: targetY,
    width: contentWidth,
    height: calculatedHeight,
    zIndex: (page?.elements.length || 0) + 1,
    content: cleanHtml,
    style: {
      fontFamily: 'Times New Roman',
      fontSize: 14,
      fontWeight: 'normal',
      fontStyle: 'normal',
      textAlign: 'justify',
      color: '#000000',
      lineHeight: 1.5,
      backgroundColor: 'transparent',
    },
  }

  canvas.addElement(newElement)
  canvas.selectedElementIds.value = [newElement.id]
  canvas.history.recordSnapshot(canvas.document.value)
}

function onGlobalPaste(e: ClipboardEvent) {
  const activeEl = window.document.activeElement
  const isInTextEdit =
    activeEl &&
    (activeEl.tagName === 'INPUT' ||
      activeEl.tagName === 'TEXTAREA' ||
      (activeEl as HTMLElement).getAttribute('contenteditable') === 'true' ||
      Boolean((activeEl as HTMLElement).closest('.canvas-text-element')) ||
      Boolean((activeEl as HTMLElement).closest('[contenteditable="true"]')))

  // If user is actively typing in an input, textarea, or contenteditable, let it handle paste
  if (isInTextEdit) return

  const clipboardData = e.clipboardData
  if (!clipboardData) return

  e.preventDefault()

  const plainText = clipboardData.getData('text/plain') || ''

  // 1. Check if user copied canvas elements (internal canvas elements)
  if (plainText.includes(CANVAS_ELEMENT_CLIPBOARD_KEY) && plainText.includes(CANVAS_ELEMENT_CLIPBOARD_VALUE)) {
    try {
      const data = JSON.parse(plainText)
      if (data[CANVAS_ELEMENT_CLIPBOARD_KEY] === CANVAS_ELEMENT_CLIPBOARD_VALUE && Array.isArray(data.elements) && data.elements.length > 0) {
        canvas.pasteElements(data.elements)
        return
      }
    } catch {}
  }

  // 2. If system clipboard has text or HTML (e.g. copied from Telegram, Word, Web):
  if (plainText.trim().length > 0 || clipboardData.getData('text/html').trim().length > 0) {
    handlePasteNewText(clipboardData)
    return
  }

  // 3. Fallback: if internal clipboard has elements and OS clipboard has no text
  if (canvas.clipboard.value && canvas.clipboard.value.length > 0) {
    canvas.pasteElements()
  }
}

// Insert Company / Contractor Requisites block (BAJARUVCHI) matching official layout
function insertCompanyRequisites() {
  closeAllDropdowns()
  const page = canvas.activePage.value
  const margins = canvas.document.value.margins
  const contentWidth = printableContentWidthMm.value || (210 - margins.left - margins.right)
  const blockWidth = Math.min(88, Math.floor(contentWidth / 2) - 2)
  let targetX = margins.left
  let targetY = margins.top + 10

  // Check if MIJOZ block already exists on current page to place BAJARUVCHI side-by-side at same Y
  const clientBlock = page?.elements.find(el => el.type === 'text' && el.content && el.content.includes('MIJOZ'))
  if (clientBlock) {
    targetY = clientBlock.y || targetY
    targetX = margins.left
  } else if (page && page.elements.length > 0) {
    const maxY = page.elements.reduce((max, el) => Math.max(max, (el.y || 0) + (el.height || 0)), 0)
    if (maxY + 75 < (297 - margins.bottom)) {
      targetY = maxY + 6
    } else {
      targetY = Math.max(margins.top + 5, 297 - margins.bottom - 75)
    }
  }

  const req = resolveTenantRequisites()
  const htmlContent = buildCompanyRequisitesHtml(req)

  const newElement: TextCanvasElement = {
    id: `req_${Date.now()}_${Math.random().toString(36).substring(2, 6)}`,
    type: 'text',
    x: targetX,
    y: targetY,
    width: blockWidth,
    height: 72,
    zIndex: 1,
    content: htmlContent,
    style: {
      fontFamily: 'Times New Roman',
      fontSize: 11,
      fontWeight: 'bold',
      fontStyle: 'normal',
      textAlign: 'left',
      color: '#000000',
      lineHeight: 1.35,
    },
  }

  canvas.addElement(newElement)
  canvas.selectedElementIds.value = [newElement.id]
  canvas.editingElementId.value = newElement.id

  uiStore.addToast({
    type: 'success',
    message: 'Bajaruvchi rekvizitlari sahifaga joylandi',
    duration: 3000,
  })
}

// Insert Client Requisites block (MIJOZ) matching official layout
function insertClientRequisites() {
  closeAllDropdowns()
  const page = canvas.activePage.value
  const margins = canvas.document.value.margins
  const contentWidth = printableContentWidthMm.value || (210 - margins.left - margins.right)
  const blockWidth = Math.min(88, Math.floor(contentWidth / 2) - 2)

  let targetX = 210 - margins.right - blockWidth
  let targetY = margins.top + 10

  // Check if BAJARUVCHI block already exists on current page to place MIJOZ side-by-side at same Y!
  const contractorBlock = page?.elements.find(el => el.type === 'text' && el.content && el.content.includes('BAJARUVCHI'))
  if (contractorBlock) {
    targetY = contractorBlock.y || targetY
    targetX = Math.max(contractorBlock.x + contractorBlock.width + 4, 210 - margins.right - blockWidth)
  } else if (page && page.elements.length > 0) {
    const maxY = page.elements.reduce((max, el) => Math.max(max, (el.y || 0) + (el.height || 0)), 0)
    if (maxY + 75 < (297 - margins.bottom)) {
      targetY = maxY + 6
    } else {
      targetY = Math.max(margins.top + 5, 297 - margins.bottom - 75)
    }
  }

  const htmlContent = buildClientRequisitesHtml()

  const newElement: TextCanvasElement = {
    id: `client_req_${Date.now()}_${Math.random().toString(36).substring(2, 6)}`,
    type: 'text',
    x: targetX,
    y: targetY,
    width: blockWidth,
    height: 72,
    zIndex: 1,
    content: htmlContent,
    style: {
      fontFamily: 'Times New Roman',
      fontSize: 11,
      fontWeight: 'bold',
      fontStyle: 'normal',
      textAlign: 'left',
      color: '#000000',
      lineHeight: 1.35,
    },
  }

  canvas.addElement(newElement)
  canvas.selectedElementIds.value = [newElement.id]
  canvas.editingElementId.value = newElement.id

  uiStore.addToast({
    type: 'success',
    message: 'Mijoz rekvizitlari sahifaga joylandi',
    duration: 3000,
  })
}

// Insert directly a new Text block (Times New Roman, 14pt)
function handleAddText() {
  closeAllDropdowns()
  const contentWidth = printableContentWidthMm.value || (210 - canvas.document.value.margins.left - canvas.document.value.margins.right)
  const page = canvas.activePage.value
  let targetY = canvas.document.value.margins.top + 5

  if (page && page.elements.length > 0) {
    const maxY = page.elements.reduce((max, el) => Math.max(max, (el.y || 0) + (el.height || 0)), 0)
    if (maxY + 15 < (297 - canvas.document.value.margins.bottom)) {
      targetY = maxY + 4
    }
  }

  const newElement: TextCanvasElement = {
    id: `text_${Date.now()}_${Math.random().toString(36).substring(2, 6)}`,
    type: 'text',
    x: canvas.document.value.margins.left,
    y: targetY,
    width: contentWidth,
    height: 8,
    zIndex: 1,
    content: '<p>Yangi matn bloki...</p>',
    style: {
      fontFamily: 'Times New Roman',
      fontSize: 14,
      fontWeight: 'normal',
      fontStyle: 'normal',
      textAlign: 'justify',
      color: '#000000',
      lineHeight: 1.5,
    },
  }

  canvas.addElement(newElement)
  canvas.editingElementId.value = newElement.id
}

// Table preset insertion
function insertPresetTable(rows: number, cols: number, borderStyle = 'solid') {
  const contentWidth = printableContentWidthMm.value
  const colW = Math.round((contentWidth / cols) * 10) / 10
  const colWidths = Array(cols).fill(colW)
  const rowHeights = Array(rows).fill(10)

  const cells = Array.from({ length: rows }, () =>
    Array.from({ length: cols }, () => ({
      id: `cell_${Date.now()}_${Math.random().toString(36).substring(2, 6)}`,
      content: '&nbsp;',
    }))
  )

  canvas.addElement({
    id: `table_${Date.now()}`,
    type: 'table',
    x: canvas.document.value.margins.left,
    y: canvas.document.value.margins.top + 10,
    width: contentWidth,
    height: Math.max(20, rows * 10),
    zIndex: 1,
    rows,
    cols,
    colWidths,
    rowHeights,
    cells,
    borderWidth: borderStyle === 'none' ? '0px' : '1px',
    borderColor: '#94a3b8',
    borderStyle: borderStyle === 'none' ? 'none' : 'solid',
    density: 'normal',
  })
  showTableInsertMenu.value = false
}

// Variable insertion
function insertVariable(vKey: string) {
  const cleanKey = vKey.replace(/^\{\{|\}\}$/g, '').trim()
  const token = `{{${cleanKey}}}`
  const el = canvas.selectedElement.value as any

  if (el && (el.type === 'text' || el.type === 'heading' || el.type === 'paragraph' || el.type === 'date' || el.type === 'variable')) {
    let insertedAtCaret = false
    const sel = window.getSelection()
    const activeEl = document.activeElement
    if (activeEl && (activeEl.closest('.canvas-text-element') || activeEl.closest('.canvas-table-element')) && sel && sel.rangeCount > 0) {
      try {
        document.execCommand('insertText', false, ` ${token} `)
        insertedAtCaret = true
      } catch {}
    }
    if (!insertedAtCaret) {
      let raw = el.content || ''
      let updatedContent = ''
      if (raw.endsWith('</p>')) {
        updatedContent = raw.slice(0, -4) + `&nbsp;${token}</p>`
      } else if (raw.endsWith('</div>')) {
        updatedContent = raw.slice(0, -6) + `&nbsp;${token}</div>`
      } else {
        updatedContent = (raw ? `${raw} ` : '') + token
      }
      canvas.updateElement(el.id, { content: updatedContent })
    }
  } else if (el && el.type === 'table') {
    let insertedAtCaret = false
    const sel = window.getSelection()
    const activeEl = document.activeElement
    if (activeEl && activeEl.closest('.canvas-table-element') && sel && sel.rangeCount > 0) {
      try {
        document.execCommand('insertText', false, ` ${token} `)
        insertedAtCaret = true
      } catch {}
    }
    if (!insertedAtCaret) {
      const newId = `var_${Date.now()}`
      canvas.addElement({
        id: newId,
        type: 'text',
        x: canvas.document.value.margins.left,
        y: canvas.document.value.margins.top + 10,
        width: 60,
        height: 10,
        zIndex: 1,
        content: `<p style="color: #2563eb; font-weight: bold;">${token}</p>`,
        variableKey: cleanKey,
        style: {
          fontFamily: 'Times New Roman',
          fontSize: 12,
          color: '#2563eb',
        },
      })
      canvas.selectedElementIds.value = [newId]
    }
  } else {
    const newId = `var_${Date.now()}`
    canvas.addElement({
      id: newId,
      type: 'text',
      x: canvas.document.value.margins.left,
      y: canvas.document.value.margins.top + 10,
      width: 60,
      height: 10,
      zIndex: 1,
      content: `<p style="color: #2563eb; font-weight: bold;">${token}</p>`,
      variableKey: cleanKey,
      style: {
        fontFamily: 'Times New Roman',
        fontSize: 12,
        color: '#2563eb',
      },
    })
    canvas.selectedElementIds.value = [newId]
  }
  showVariablePicker.value = false
}

// Checkbox insertion & management
function insertCheckboxElement(checked: boolean) {
  const newId = `checkbox_${Date.now()}`
  canvas.addElement({
    id: newId,
    type: 'checkbox',
    checked,
    label: 'Tanlov varianti',
    x: canvas.document.value.margins.left,
    y: canvas.document.value.margins.top + 10,
    width: 65,
    height: 7,
    zIndex: 1,
    fontSize: 12,
    style: {
      fontFamily: 'Times New Roman',
      fontSize: 12,
      fontWeight: 'normal',
      fontStyle: 'normal',
      textDecoration: 'none',
      color: '#111827',
    },
  })
  canvas.editingElementId.value = newId
}

function updateSelectedCheckboxLabel(newLabel: string) {
  const el = canvas.selectedElement.value as any
  if (el && el.type === 'checkbox') {
    const fontSize = el.style?.fontSize || el.fontSize || 12
    const isBold = el.style?.fontWeight === 'bold' || el.style?.fontWeight === 700
    const charWidthMm = (fontSize / 12) * (isBold ? 2.6 : 2.3)
    const neededWidthMm = Math.max(30, Math.ceil(newLabel.length * charWidthMm + 14))
    const finalWidth = neededWidthMm > el.width ? Math.min(printableContentWidthMm.value, neededWidthMm) : el.width
    canvas.updateElement(el.id, { label: newLabel, width: finalWidth })
  }
}

function toggleSelectedCheckboxState() {
  const el = canvas.selectedElement.value as any
  if (el && el.type === 'checkbox') {
    canvas.updateElement(el.id, { checked: !el.checked })
  }
}

// Downloads
async function downloadDocument(format: 'pdf' | 'doc' | 'print' = 'pdf') {
  const safeTitle = (props.title || props.contractNumber || 'shartnoma').replace(/[/\\?%*:|"<>]/g, '_')
  const serialized = serializeCanvasDocument(canvas.document.value)

  if (format === 'print') {
    printContractAsPdf(safeTitle, serialized, canvas.document.value.margins, variableValues.value)
    return
  }

  isDownloadingPdf.value = true
  try {
    await downloadContractAsPdf(safeTitle, serialized, canvas.document.value.margins, variableValues.value)
  } catch (err) {
    console.error('Failed to export PDF:', err)
  } finally {
    isDownloadingPdf.value = false
  }
}

const formattedLastSaved = computed(() => {
  if (!props.lastSavedAt) return null
  const d = new Date(props.lastSavedAt)
  return `${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}:${String(d.getSeconds()).padStart(2, '0')}`
})

// Detect Mac for shortcut display
const isMac = typeof navigator !== 'undefined' && /Mac|iPhone|iPad/.test(navigator.platform)
const mod = isMac ? '⌘' : 'Ctrl'

const shortcutCategories = computed(() => ({
  general: [
    { label: 'Save', keys: `${mod}+S` },
    { label: 'Undo', keys: `${mod}+Z` },
    { label: 'Redo', keys: `${mod}+Y / ${mod}+Shift+Z` },
    { label: 'Copy', keys: `${mod}+C` },
    { label: 'Cut', keys: `${mod}+X` },
    { label: 'Paste', keys: `${mod}+V` },
    { label: 'Duplicate', keys: `${mod}+D` },
    { label: 'Delete', keys: 'Delete / Backspace' },
    { label: 'Select All', keys: `${mod}+A` },
    { label: 'Escape / Cancel', keys: 'Escape' },
    { label: 'Shortcut Help', keys: `${mod}+/ or ?` },
  ],
  text: [
    { label: 'Bold', keys: `${mod}+B` },
    { label: 'Italic', keys: `${mod}+I` },
    { label: 'Underline', keys: `${mod}+U` },
    { label: 'Strikethrough', keys: `${mod}+Shift+X` },
    { label: 'Align Left', keys: `${mod}+Shift+L` },
    { label: 'Align Center', keys: `${mod}+Shift+E` },
    { label: 'Align Right', keys: `${mod}+Shift+R` },
    { label: 'Justify', keys: `${mod}+Shift+J` },
    { label: 'Font Size +', keys: `${mod}+Shift+.` },
    { label: 'Font Size -', keys: `${mod}+Shift+,` },
    { label: 'Copy Style', keys: `${mod}+Alt+C` },
    { label: 'Paste Style', keys: `${mod}+Alt+V` },
    { label: 'Numbered List', keys: 'Toolbar / 1. 2. 3.' },
    { label: 'Bulleted List', keys: 'Toolbar / • • •' },
    { label: 'Indent (List)', keys: 'Tab' },
    { label: 'Outdent (List)', keys: 'Shift+Tab' },
    { label: 'Edit Text (Enter)', keys: 'F2 / Enter' },
  ],
  elements: [
    { label: 'Move (1mm)', keys: 'Arrow keys' },
    { label: 'Move (5mm)', keys: 'Shift + Arrow' },
    { label: 'Bring Forward', keys: `${mod}+]` },
    { label: 'Send Backward', keys: `${mod}+[` },
    { label: 'Bring to Front', keys: `${mod}+Shift+]` },
    { label: 'Send to Back', keys: `${mod}+Shift+[` },
    { label: 'Lock / Unlock', keys: `${mod}+L` },
  ],
  zoom: [
    { label: 'Zoom In', keys: `${mod}++` },
    { label: 'Zoom Out', keys: `${mod}+-` },
    { label: 'Reset Zoom (100%)', keys: `${mod}+0` },
    { label: 'Smooth Zoom', keys: `${mod}+Scroll` },
  ],
}))
</script>

<template>
  <div
    class="contract-editor-wrapper flex flex-col flex-1 h-full min-h-0 bg-zinc-100 dark:bg-zinc-950 font-sans relative overflow-hidden"
  >
    <!-- Top Action & Status Bar -->
    <div
      v-if="!hideTopBar"
      class="no-print sticky top-0 z-40 flex flex-wrap items-center justify-between gap-3 px-4 py-2.5 bg-white dark:bg-[#15171a] border-b border-zinc-200 dark:border-zinc-800 shadow-2xs"
    >
      <!-- Left: Back, Document Title & Contract Number -->
      <div class="flex items-center gap-3 min-w-0">
        <button
          type="button"
          @click="emit('back')"
          class="px-2.5 py-1.5 rounded-xl border border-zinc-200 dark:border-zinc-800 bg-zinc-50 dark:bg-zinc-900 text-zinc-700 dark:text-zinc-300 hover:text-blue-600 hover:bg-blue-50 dark:hover:bg-zinc-800 text-xs font-semibold transition-all cursor-pointer flex items-center gap-1.5"
          :title="backLabel"
        >
          <span>&larr;</span>
          <span>{{ backLabel }}</span>
        </button>

        <div class="h-4 w-px bg-zinc-200 dark:border-zinc-800 hidden sm:block"></div>

        <div class="min-w-0 flex items-center gap-2">
          <span
            v-if="contractNumber"
            class="px-2 py-0.5 rounded-md bg-zinc-100 dark:bg-zinc-800 text-zinc-700 dark:text-zinc-300 font-mono text-[11px] font-bold border border-zinc-200 dark:border-zinc-700/60"
          >
            {{ contractNumber }}
          </span>
          <h2 class="text-xs sm:text-sm font-bold text-zinc-900 dark:text-zinc-100 truncate">
            {{ title || 'Contract Document' }}
          </h2>
          <span v-if="studentName" class="text-[11px] text-zinc-400 dark:text-zinc-500 hidden md:inline">
            ({{ studentName }})
          </span>
        </div>
      </div>

      <!-- Right: Autosave Status & Primary Action Buttons -->
      <div class="flex items-center gap-2 sm:gap-3 shrink-0">
        <!-- Autosave Indicator -->
        <div class="flex items-center gap-1.5 text-[11px] font-medium px-2.5 py-1 rounded-lg">
          <template v-if="saveStatus === 'saving'">
            <Loader2 class="w-3.5 h-3.5 text-blue-500 animate-spin" />
            <span class="text-blue-600 dark:text-blue-400 font-semibold">Saving...</span>
          </template>
          <template v-else-if="saveStatus === 'saved'">
            <CheckCircle2 class="w-3.5 h-3.5 text-emerald-500" />
            <span class="text-zinc-500 dark:text-zinc-400">
              Saved <span v-if="formattedLastSaved" class="font-mono text-[10px]">({{ formattedLastSaved }})</span>
            </span>
          </template>
          <template v-else-if="saveStatus === 'error'">
            <AlertCircle class="w-3.5 h-3.5 text-rose-500" />
            <span class="text-rose-600 dark:text-rose-400 font-semibold">Save error</span>
          </template>
          <template v-else>
            <span class="text-zinc-400 text-[10px] hidden sm:inline">Auto-saving</span>
          </template>
        </div>

        <!-- Preview Modal Button -->
        <button
          type="button"
          @click="emit('preview')"
          class="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-800 text-xs font-semibold text-zinc-700 dark:text-zinc-300 hover:bg-zinc-50 dark:hover:bg-zinc-700 transition-colors cursor-pointer shadow-2xs"
          title="Preview"
        >
          <Eye class="w-3.5 h-3.5 text-zinc-400" />
          <span class="hidden sm:inline">Preview</span>
        </button>

        <!-- Bajaruvchi Rekvizitlarini joylash Button -->
        <button
          v-if="!readonly"
          type="button"
          @click="insertCompanyRequisites"
          class="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl border border-indigo-200 dark:border-indigo-900/60 bg-indigo-50/80 hover:bg-indigo-100 dark:bg-indigo-950/40 dark:hover:bg-indigo-900/60 text-indigo-700 dark:text-indigo-300 text-xs font-bold transition-all shadow-2xs cursor-pointer active:scale-95"
          title="Kompaniya (Bajaruvchi) rekvizitlarini sahifaga joylash"
        >
          <Building2 class="w-3.5 h-3.5 text-indigo-600 dark:text-indigo-400" />
          <span>Bajaruvchi</span>
        </button>

        <!-- Mijoz Rekvizitlarini joylash Button -->
        <button
          v-if="!readonly"
          type="button"
          @click="insertClientRequisites"
          class="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl border border-emerald-200 dark:border-emerald-900/60 bg-emerald-50/80 hover:bg-emerald-100 dark:bg-emerald-950/40 dark:hover:bg-emerald-900/60 text-emerald-700 dark:text-emerald-300 text-xs font-bold transition-all shadow-2xs cursor-pointer active:scale-95"
          title="Mijoz ma'lumotlari (F.I.O, Passport, Imzo) blokini sahifaga joylash"
        >
          <UserCheck class="w-3.5 h-3.5 text-emerald-600 dark:text-emerald-400" />
          <span>Mijoz</span>
        </button>

        <!-- Download PDF Button (Direct) -->
        <button
          type="button"
          @click="downloadDocument('pdf')"
          :disabled="isDownloadingPdf"
          class="inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-xl border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-800 text-xs font-semibold text-zinc-700 dark:text-zinc-300 hover:bg-zinc-50 dark:hover:bg-zinc-750 transition-colors cursor-pointer shadow-2xs"
          title="PDF yuklab olish"
        >
          <Loader2 v-if="isDownloadingPdf" class="w-3.5 h-3.5 animate-spin text-blue-500" />
          <Download v-else class="w-3.5 h-3.5 text-blue-500" />
          <span>PDF</span>
        </button>

        <!-- Manual Save Button -->
        <button
          v-if="!readonly"
          type="button"
          @click="emit('save')"
          class="inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-xl bg-blue-600 hover:bg-blue-700 text-white text-xs font-bold transition-all shadow-xs cursor-pointer"
          title="Save"
        >
          <Save class="w-3.5 h-3.5" />
          <span>Save</span>
        </button>
      </div>
    </div>

    <!-- Word + Canva Style Free Positioning Document Toolbar -->
    <div
      v-if="!readonly"
      class="no-print editor-toolbar z-30 flex flex-wrap items-center gap-1 p-2 bg-zinc-50/95 dark:bg-[#1a1d20]/95 backdrop-blur-md border-b border-zinc-200 dark:border-zinc-800 text-zinc-700 dark:text-zinc-300 select-none text-xs"
      :class="hideTopBar ? 'sticky top-0' : 'sticky top-[53px]'"
    >
      <!-- History Group: Undo / Redo -->
      <div class="flex items-center gap-0.5 pr-1.5 border-r border-zinc-200 dark:border-zinc-700/60">
        <button
          type="button"
          @click="performUndo()"
          :disabled="!canvas.history.canUndo.value"
          class="toolbar-btn"
          title="Undo (Ctrl+Z)"
        >
          <Undo2 class="w-4 h-4" />
        </button>
        <button
          type="button"
          @click="performRedo()"
          :disabled="!canvas.history.canRedo.value"
          class="toolbar-btn"
          title="Redo (Ctrl+Y)"
        >
          <Redo2 class="w-4 h-4" />
        </button>
      </div>


      <!-- Font Family & Font Size Group -->
      <div class="flex items-center gap-1 px-1.5 border-r border-zinc-200 dark:border-zinc-700/60">
        <div class="flex items-center gap-1 px-2 py-1 rounded-lg bg-zinc-100 dark:bg-zinc-800 text-[11px] font-serif font-bold text-zinc-700 dark:text-zinc-200 border border-zinc-200/80 dark:border-zinc-700/60 select-none shadow-2xs" title="Font: Times New Roman">
          <span>Times New Roman</span>
        </div>

        <select
          :value="currentFontSize"
          @change="setFontSize(($event.target as HTMLSelectElement).value)"
          class="h-7 px-2 py-0.5 text-xs font-bold rounded-lg border border-zinc-200 dark:border-zinc-700 bg-white dark:bg-zinc-800 text-zinc-800 dark:text-zinc-200 focus:outline-none focus:ring-1 focus:ring-blue-500 cursor-pointer font-mono shadow-2xs hover:border-zinc-300 dark:hover:border-zinc-600 transition-colors"
          title="Font size"
        >
          <option v-for="sz in fontSizes" :key="sz" :value="sz">
            {{ sz }} pt
          </option>
        </select>
      </div>


      <!-- Text Formatting: Bold, Italic, Underline, Strikethrough -->
      <div class="flex items-center gap-0.5 px-1.5 border-r border-zinc-200 dark:border-zinc-700/60">
        <button
          type="button"
          @click="toggleBold"
          class="toolbar-btn font-bold"
          :class="{ 'bg-blue-100 dark:bg-blue-950/60 text-blue-700 font-black': (canvas.selectedElement.value as any)?.style?.fontWeight === 'bold' }"
          title="Bold (Ctrl+B)"
        >
          <Bold class="w-3.5 h-3.5" />
        </button>
        <button
          type="button"
          @click="toggleItalic"
          class="toolbar-btn italic font-serif"
          :class="{ 'bg-blue-100 dark:bg-blue-950/60 text-blue-700 font-bold': (canvas.selectedElement.value as any)?.style?.fontStyle === 'italic' }"
          title="Italic (Ctrl+I)"
        >
          <Italic class="w-3.5 h-3.5" />
        </button>
        <button
          type="button"
          @click="toggleUnderline"
          class="toolbar-btn underline"
          :class="{ 'bg-blue-100 dark:bg-blue-950/60 text-blue-700 font-bold': ((canvas.selectedElement.value as any)?.style?.textDecoration || '').includes('underline') }"
          title="Underline (Ctrl+U)"
        >
          <UnderlineIcon class="w-3.5 h-3.5" />
        </button>
        <button
          type="button"
          @click="toggleStrike"
          class="toolbar-btn line-through"
          :class="{ 'bg-blue-100 dark:bg-blue-950/60 text-blue-700 font-bold': ((canvas.selectedElement.value as any)?.style?.textDecoration || '').includes('line-through') }"
          title="Strikethrough"
        >
          <Strikethrough class="w-3.5 h-3.5" />
        </button>

        <div class="h-4 w-px bg-zinc-200 dark:bg-zinc-700 my-auto mx-0.5"></div>

        <!-- Canva Copy Style (Format Painter) -->
        <button
          type="button"
          @click="handleCopyStyleButtonClick"
          @dblclick.prevent="activateCopyStyle('persistent')"
          class="toolbar-btn relative transition-all"
          :class="[
            copyStyleMode
              ? 'bg-blue-600 text-white dark:bg-blue-600 hover:bg-blue-700 shadow-xs ring-1 ring-blue-500'
              : '',
            !isTextSelected && !copyStyleMode ? 'opacity-40 cursor-not-allowed' : ''
          ]"
          :disabled="!isTextSelected && !copyStyleMode"
          :title="
            copyStyleMode === 'persistent'
              ? 'Copy Style faol (Ko\'p martalik qulflangan) • Bekor qilish: Esc'
              : copyStyleMode === 'single'
              ? 'Copy Style faol (1 marta qo\'llash) • Bekor qilish: Esc'
              : 'Uslubdan nusxa olish (1 marta bosish: 1 matnga, 2 marta tez bosish: ko\'p matnga) • Ctrl+Alt+C'
          "
        >
          <PaintRoller class="w-3.5 h-3.5" />
          <span
            v-if="copyStyleMode === 'persistent'"
            class="absolute -top-1 -right-1 w-2 h-2 rounded-full bg-amber-400 ring-2 ring-white dark:ring-zinc-900 animate-pulse"
          ></span>
        </button>
      </div>

      <!-- Text Color & Fill Color Pickers -->
      <div class="flex items-center gap-1 px-1.5 border-r border-zinc-200 dark:border-zinc-700/60">
        <!-- Text Color -->
        <div class="relative editor-dropdown-container" :class="{ 'z-50': showColorPicker }">
          <button
            type="button"
            @click.stop="toggleColorPicker()"
            class="toolbar-btn flex items-center gap-1 h-7 px-1.5"
            title="Text color"
          >
            <span class="font-bold text-xs font-serif leading-none" :style="{ color: currentFontColor }">A</span>
            <span class="w-3 h-1 rounded-xs" :style="{ backgroundColor: currentFontColor }"></span>
          </button>
          <div
            v-if="showColorPicker"
            class="absolute top-full left-0 mt-1 w-48 bg-white dark:bg-zinc-800 rounded-xl border border-zinc-200 dark:border-zinc-700 shadow-xl p-2 z-[200] space-y-1.5 animate-scale-in"
            @click.stop
          >
            <div class="text-[10px] font-bold text-zinc-400 uppercase tracking-wider">Text Color</div>
            <div class="grid grid-cols-5 gap-1.5">
              <button
                v-for="c in TEXT_COLORS"
                :key="c.value"
                type="button"
                @click="setFontColor(c.value)"
                class="w-6 h-6 rounded-full border border-zinc-300 dark:border-zinc-600 transition-transform hover:scale-110 flex items-center justify-center cursor-pointer shadow-2xs"
                :style="{ backgroundColor: c.value }"
                :title="c.name"
              >
                <Check v-if="currentFontColor === c.value" class="w-3 h-3 text-white" />
              </button>
            </div>
          </div>
        </div>

        <!-- Background / Cell Fill Color -->
        <div class="relative editor-dropdown-container" :class="{ 'z-50': showHighlightPicker }">
          <button
            type="button"
            @click.stop="toggleHighlightPicker()"
            class="toolbar-btn flex items-center gap-1 h-7 px-1.5"
            title="Fill / Highlight color"
          >
            <PaintBucket class="w-3.5 h-3.5 text-amber-500" />
            <span class="w-3 h-1 rounded-xs" :style="{ backgroundColor: currentHighlightColor }"></span>
          </button>
          <div
            v-if="showHighlightPicker"
            class="absolute top-full left-0 mt-1 w-52 bg-white dark:bg-zinc-800 rounded-xl border border-zinc-200 dark:border-zinc-700 shadow-xl p-2 z-[200] space-y-1.5 animate-scale-in"
            @click.stop
          >
            <div class="text-[10px] font-bold text-zinc-400 uppercase tracking-wider">Fill Color (20 Tones)</div>
            <div class="grid grid-cols-5 gap-1.5">
              <button
                v-for="c in CELL_BG_COLORS"
                :key="c.value"
                type="button"
                @click="setHighlightColor(c.value)"
                class="w-6 h-6 rounded-full border border-zinc-300 dark:border-zinc-600 transition-transform hover:scale-110 flex items-center justify-center cursor-pointer shadow-2xs"
                :style="{ backgroundColor: c.value }"
                :title="c.name"
              >
                <Check v-if="currentHighlightColor === c.value" class="w-3 h-3" :class="c.value === '#ffffff' ? 'text-black' : 'text-white'" />
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- Text Alignment — single cycle button (Left→Center→Right→Justify→…) -->
      <div class="flex items-center px-1.5 border-r border-zinc-200 dark:border-zinc-700/60">
        <button
          type="button"
          @click="cycleTextAlign()"
          class="toolbar-btn"
          :class="canvas.selectedElement.value ? 'text-blue-600 dark:text-blue-400' : 'opacity-50'"
          :title="`Alignment: ${currentTextAlign} — click to cycle`"
        >
          <AlignLeft     v-if="currentTextAlign === 'left'"    class="w-3.5 h-3.5" />
          <AlignCenter   v-else-if="currentTextAlign === 'center'"  class="w-3.5 h-3.5" />
          <AlignRight    v-else-if="currentTextAlign === 'right'"   class="w-3.5 h-3.5" />
          <AlignJustify  v-else                                class="w-3.5 h-3.5" />
        </button>
      </div>

      <!-- List Dropdown & Indent Group (Canva / Word Style) -->
      <div class="flex items-center gap-0.5 px-1.5 border-r border-zinc-200 dark:border-zinc-700/60">
        <!-- List Dropdown Button -->
        <div
          class="relative editor-dropdown-container"
          :class="{ 'z-50': showListMenu }"
        >
          <button
            type="button"
            @mousedown.prevent
            @click.stop="toggleListMenu()"
            class="toolbar-btn flex items-center gap-1 h-7 px-1.5"
            :class="[
              showListMenu || activeListType ? 'bg-blue-100 dark:bg-blue-950/60 text-blue-700 dark:text-blue-400 font-bold shadow-2xs' : '',
              !isTextSelected ? 'opacity-40 cursor-not-allowed' : ''
            ]"
            :disabled="!isTextSelected"
            :title="activeListType ? `Ro'yxat faol: ${activeListType === 'ordered' ? 'Numbered' : 'Bulleted'} (Tanlash uchun bosing)` : 'Ro\'yxat (List): Raqamlangan yoki Nuqtali'"
          >
            <ListOrdered v-if="activeListType === 'ordered'" class="w-3.5 h-3.5 text-blue-600 dark:text-blue-400" />
            <List v-else class="w-3.5 h-3.5" />
            <ChevronDown class="w-2.5 h-2.5 opacity-60" />
          </button>

          <!-- List Options Popover -->
          <div
            v-if="showListMenu && isTextSelected"
            class="absolute top-full left-0 mt-1.5 w-52 bg-white dark:bg-zinc-900 rounded-2xl border border-zinc-200 dark:border-zinc-700 shadow-2xl p-1.5 z-[250] space-y-1 select-none animate-scale-in"
            @click.stop
          >
            <div class="text-[10px] font-bold text-zinc-400 uppercase tracking-wider px-2 py-1">Ro'yxat turi (List)</div>
            
            <!-- 1. Numbered List Option -->
            <button
              type="button"
              @mousedown.prevent
              @click="applyListFormat('ordered')"
              class="w-full flex items-center gap-2.5 px-2.5 py-2 rounded-xl text-xs font-medium transition-colors hover:bg-blue-50 dark:hover:bg-zinc-800 cursor-pointer"
              :class="activeListType === 'ordered' ? 'bg-blue-50 dark:bg-blue-950/60 text-blue-700 dark:text-blue-300 font-bold border border-blue-200 dark:border-blue-900' : 'text-zinc-700 dark:text-zinc-200'"
            >
              <div class="w-6 h-6 rounded-lg bg-blue-100 dark:bg-blue-900/60 flex items-center justify-center shrink-0">
                <ListOrdered class="w-3.5 h-3.5 text-blue-600 dark:text-blue-400" />
              </div>
              <div class="text-left flex-1">
                <div class="font-bold text-xs">Numbered List</div>
                <div class="text-[10px] text-zinc-400 font-mono">1. 2. 3. (a. b. c.)</div>
              </div>
              <Check v-if="activeListType === 'ordered'" class="w-3.5 h-3.5 text-blue-600 dark:text-blue-400 shrink-0" />
            </button>

            <!-- 2. Bulleted List Option -->
            <button
              type="button"
              @mousedown.prevent
              @click="applyListFormat('unordered')"
              class="w-full flex items-center gap-2.5 px-2.5 py-2 rounded-xl text-xs font-medium transition-colors hover:bg-blue-50 dark:hover:bg-zinc-800 cursor-pointer"
              :class="activeListType === 'unordered' ? 'bg-blue-50 dark:bg-blue-950/60 text-blue-700 dark:text-blue-300 font-bold border border-blue-200 dark:border-blue-900' : 'text-zinc-700 dark:text-zinc-200'"
            >
              <div class="w-6 h-6 rounded-lg bg-blue-100 dark:bg-blue-900/60 flex items-center justify-center shrink-0">
                <List class="w-3.5 h-3.5 text-blue-600 dark:text-blue-400" />
              </div>
              <div class="text-left flex-1">
                <div class="font-bold text-xs">Bulleted List</div>
                <div class="text-[10px] text-zinc-400 font-mono">• • • (○ ▪)</div>
              </div>
              <Check v-if="activeListType === 'unordered'" class="w-3.5 h-3.5 text-blue-600 dark:text-blue-400 shrink-0" />
            </button>
          </div>
        </div>

        <!-- Decrease Indent Button -->
        <button
          type="button"
          @mousedown.prevent
          @click="decreaseIndent()"
          class="toolbar-btn"
          :class="!isTextSelected ? 'opacity-40 cursor-not-allowed' : ''"
          :disabled="!isTextSelected"
          title="Indentni kamaytirish (Shift+Tab)"
        >
          <IndentDecrease class="w-3.5 h-3.5" />
        </button>

        <!-- Increase Indent Button -->
        <button
          type="button"
          @mousedown.prevent
          @click="increaseIndent()"
          class="toolbar-btn"
          :class="!isTextSelected ? 'opacity-40 cursor-not-allowed' : ''"
          :disabled="!isTextSelected"
          title="Indentni oshirish (Tab)"
        >
          <IndentIncrease class="w-3.5 h-3.5" />
        </button>
      </div>

      <!-- Text Spacing: Letter Spacing & Line Spacing (Canva Style) -->
      <div
        class="relative px-1 border-r border-zinc-200 dark:border-zinc-700/60 editor-dropdown-container"
        :class="{ 'z-50': showSpacingMenu }"
      >
        <button
          type="button"
          @click.stop="toggleSpacingMenu()"
          class="toolbar-btn flex items-center gap-1 h-7 px-1.5"
          :class="[
            showSpacingMenu ? 'bg-blue-100 dark:bg-blue-950/60 text-blue-700 dark:text-blue-400' : '',
            !isTextSelected ? 'opacity-50 cursor-not-allowed' : ''
          ]"
          :disabled="!isTextSelected"
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
          <span class="text-[11px] font-medium hidden md:inline">Spacing</span>
        </button>

        <!-- Canva Style Spacing Popover -->
        <div
          v-if="showSpacingMenu && isTextSelected"
          class="absolute top-full left-0 mt-1.5 w-64 bg-white dark:bg-zinc-900 rounded-2xl border border-zinc-200 dark:border-zinc-700 shadow-2xl p-3.5 z-[250] space-y-3.5 select-none"
          @click.stop
        >
          <div class="flex items-center justify-between pb-1 border-b border-zinc-100 dark:border-zinc-800">
            <span class="text-[11px] font-bold text-zinc-700 dark:text-zinc-200 uppercase tracking-wider">Spacing</span>
            <span class="text-[10px] text-zinc-400 font-mono font-semibold">Canva</span>
          </div>

          <!-- Letter Spacing Control -->
          <div class="space-y-1.5">
            <div class="flex items-center justify-between text-xs">
              <span class="font-medium text-zinc-700 dark:text-zinc-300">Letter spacing</span>
              <div class="flex items-center gap-1">
                <input
                  type="number"
                  step="0.5"
                  min="-3"
                  max="25"
                  :value="currentLetterSpacing"
                  @input="setLetterSpacing(($event.target as HTMLInputElement).value)"
                  @change="commitSpacingChange"
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
              @change="commitSpacingChange"
              class="w-full accent-blue-600 h-1.5 bg-zinc-200 dark:bg-zinc-700 rounded-lg cursor-pointer"
            />
          </div>

          <!-- Line Spacing Control -->
          <div class="space-y-1.5">
            <div class="flex items-center justify-between text-xs">
              <span class="font-medium text-zinc-700 dark:text-zinc-300">Line spacing</span>
              <div class="flex items-center gap-1">
                <input
                  type="number"
                  step="0.05"
                  min="0.8"
                  max="3.0"
                  :value="currentLineHeight"
                  @input="setLineHeight(($event.target as HTMLInputElement).value)"
                  @change="commitSpacingChange"
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
              @change="commitSpacingChange"
              class="w-full accent-blue-600 h-1.5 bg-zinc-200 dark:bg-zinc-700 rounded-lg cursor-pointer"
            />
          </div>

          <!-- Quick Presets -->
          <div class="pt-2 border-t border-zinc-100 dark:border-zinc-800 flex items-center justify-between text-[10px]">
            <span class="text-zinc-400">Presets:</span>
            <div class="flex items-center gap-1">
              <button
                type="button"
                @click="setLineHeight(1.15); setLetterSpacing(0); commitSpacingChange()"
                class="px-1.5 py-0.5 rounded bg-zinc-100 dark:bg-zinc-800 hover:bg-zinc-200 dark:hover:bg-zinc-700 text-zinc-600 dark:text-zinc-300 font-medium"
              >
                Tight (1.15)
              </button>
              <button
                type="button"
                @click="setLineHeight(1.5); setLetterSpacing(0); commitSpacingChange()"
                class="px-1.5 py-0.5 rounded bg-zinc-100 dark:bg-zinc-800 hover:bg-zinc-200 dark:hover:bg-zinc-700 text-zinc-600 dark:text-zinc-300 font-medium"
              >
                Normal (1.5)
              </button>
              <button
                type="button"
                @click="setLineHeight(1.8); setLetterSpacing(0.5); commitSpacingChange()"
                class="px-1.5 py-0.5 rounded bg-zinc-100 dark:bg-zinc-800 hover:bg-zinc-200 dark:hover:bg-zinc-700 text-zinc-600 dark:text-zinc-300 font-medium"
              >
                Loose (1.8)
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- Page Addition Button -->
      <div class="flex items-center px-1.5 border-r border-zinc-200 dark:border-zinc-700/60">
        <button
          type="button"
          @click="canvas.addPage()"
          class="toolbar-btn flex items-center gap-1 font-bold text-[11px] text-blue-600 dark:text-blue-400 bg-blue-50/80 dark:bg-blue-950/40 px-2 py-1 rounded-lg border border-blue-200/80 dark:border-blue-900/60 shadow-2xs hover:bg-blue-100"
          title="Add new A4 page"
        >
          <FilePlus class="w-3.5 h-3.5" />
          <span>+ Page</span>
        </button>
      </div>

      <!-- Page Margins Dropdown -->
      <div
        class="relative px-1 border-r border-zinc-200 dark:border-zinc-700/60 editor-dropdown-container"
        :class="{ 'z-50': showMarginMenu }"
      >
        <button
          type="button"
          @click.stop="toggleMarginMenu()"
          class="toolbar-btn flex items-center gap-1.5 h-7 px-2 text-[11px] font-bold justify-between bg-zinc-100/80 dark:bg-zinc-800/80 hover:bg-zinc-200 dark:hover:bg-zinc-700 rounded-lg shadow-2xs cursor-pointer"
          title="Page margins"
        >
          <SlidersHorizontal class="w-3 h-3 text-zinc-500" />
          <span>Margins: {{ currentMarginPresetName }}</span>
          <ChevronDown class="w-2.5 h-2.5 opacity-60" />
        </button>

        <div
          v-if="showMarginMenu"
          class="absolute top-full left-0 mt-1.5 w-[280px] bg-white dark:bg-zinc-900 rounded-2xl border border-zinc-200 dark:border-zinc-700 shadow-2xl p-3 z-[250] animate-scale-in"
          @click.stop
        >
          <div class="flex items-center justify-between mb-2">
            <div class="text-[10px] font-bold text-zinc-400 uppercase tracking-widest">Margin Presets</div>
            <div class="text-[10px] font-mono text-zinc-400">A4 (210×297mm)</div>
          </div>
          <div class="grid grid-cols-2 gap-2">
            <button
              v-for="preset in marginPresets"
              :key="preset.name"
              type="button"
              @click="applyMarginPreset(preset)"
              class="p-2.5 rounded-xl border text-left cursor-pointer transition-all"
              :class="currentMarginPresetName === preset.name
                ? 'border-blue-500 bg-blue-50/80 dark:bg-blue-950/50 text-blue-700 dark:text-blue-300 ring-2 ring-blue-500/20 shadow-xs'
                : 'border-zinc-200 dark:border-zinc-700 hover:bg-zinc-50 dark:hover:bg-zinc-800 text-zinc-700 dark:text-zinc-300 hover:border-zinc-300'"
            >
              <div class="text-xs font-bold mb-0.5 flex items-center justify-between">
                <span>{{ preset.name }}</span>
                <Check v-if="currentMarginPresetName === preset.name" class="w-3 h-3 text-blue-600 dark:text-blue-400" />
              </div>
              <div class="text-[9px] font-mono text-zinc-400 leading-tight">
                L{{ preset.left }} R{{ preset.right }}<br>T{{ preset.top }} B{{ preset.bottom }} mm
              </div>
            </button>
          </div>
        </div>
      </div>

      <!-- Line (Ruler & Margins Guide) Toggle -->
      <div class="flex items-center px-1 border-r border-zinc-200 dark:border-zinc-700/60">
        <button
          type="button"
          @click="canvas.showMarginGuides.value = !canvas.showMarginGuides.value; canvas.showRulers.value = canvas.showMarginGuides.value"
          :class="[
            'toolbar-btn flex items-center gap-1.5 px-2 h-7 rounded-lg text-[11px] font-bold transition-all',
            canvas.showMarginGuides.value
              ? 'bg-blue-100 dark:bg-blue-950/60 text-blue-700 dark:text-blue-300 border border-blue-200 dark:border-blue-800/80 shadow-2xs'
              : 'text-zinc-500 hover:bg-zinc-100 dark:hover:bg-zinc-800'
          ]"
          title="Toggle page border line & rulers"
        >
          <Ruler class="w-3.5 h-3.5 text-blue-500" />
          <span>Line</span>
        </button>
      </div>

      <!-- Checkboxes Group (☑ / ☐) -->
      <div class="flex items-center gap-0.5 px-1.5 border-r border-zinc-200 dark:border-zinc-700/60">
        <button
          type="button"
          @click="insertCheckboxElement(true)"
          class="toolbar-btn flex items-center gap-1 font-bold text-[11px] text-blue-600 dark:text-blue-400"
          title="Checkbox (checked)"
        >
          <CheckSquare class="w-3.5 h-3.5" />
        </button>
        <button
          type="button"
          @click="insertCheckboxElement(false)"
          class="toolbar-btn flex items-center gap-1 font-bold text-[11px] text-zinc-500"
          title="Checkbox (empty)"
        >
          <Square class="w-3.5 h-3.5" />
        </button>
      </div>

      <!-- Selected Checkbox Controls (Text label editor and Checked state toggle) -->
      <div
        v-if="canvas.selectedElement.value?.type === 'checkbox'"
        class="flex items-center gap-1.5 px-2 py-0.5 bg-blue-50/90 dark:bg-blue-950/50 border border-blue-300/80 dark:border-blue-800 rounded-xl shadow-2xs border-r pr-2"
      >
        <!-- Toggle checked state -->
        <button
          type="button"
          @click="toggleSelectedCheckboxState"
          class="flex items-center gap-1.5 px-2 py-1 text-xs font-semibold rounded-lg transition-all cursor-pointer"
          :class="(canvas.selectedElement.value as any).checked
            ? 'bg-blue-600 text-white shadow-xs hover:bg-blue-700'
            : 'bg-white dark:bg-zinc-800 text-zinc-700 dark:text-zinc-300 border border-zinc-200 dark:border-zinc-700 hover:bg-zinc-100 dark:hover:bg-zinc-700'"
          :title="(canvas.selectedElement.value as any).checked ? 'Holat: Belgilangan (o\'zgartirish uchun bosing)' : 'Holat: Belgilanmagan (o\'zgartirish uchun bosing)'"
        >
          <CheckSquare v-if="(canvas.selectedElement.value as any).checked" class="w-3.5 h-3.5 text-white" />
          <Square v-else class="w-3.5 h-3.5 text-zinc-400" />
          <span>{{ (canvas.selectedElement.value as any).checked ? 'Belgilangan' : 'Belgilanmagan' }}</span>
        </button>

        <div class="w-px h-4 bg-blue-200 dark:bg-blue-800"></div>

        <!-- Label text input -->
        <div class="flex items-center gap-1.5">
          <label class="text-[11px] font-bold text-blue-900 dark:text-blue-200 whitespace-nowrap">
            Checkbox matni:
          </label>
          <input
            type="text"
            :value="(canvas.selectedElement.value as any).label || ''"
            @input="updateSelectedCheckboxLabel(($event.target as HTMLInputElement).value)"
            placeholder="Tanlov varianti matni..."
            class="h-7 px-2.5 py-1 text-xs font-serif rounded-lg border border-blue-300 dark:border-blue-700 bg-white dark:bg-zinc-800 text-zinc-900 dark:text-zinc-100 focus:outline-none focus:ring-2 focus:ring-blue-500 w-48 sm:w-64 shadow-2xs"
          />
        </div>
      </div>

      <!-- Table Inserter Dropdown -->
      <div
        class="relative px-1 border-r border-zinc-200 dark:border-zinc-700/60 editor-dropdown-container"
        :class="{ 'z-50': showTableInsertMenu }"
      >
        <button
          type="button"
          @click.stop="toggleTableInsertMenu()"
          class="toolbar-btn flex items-center gap-1.5 px-2.5 py-1 text-xs font-bold text-blue-700 dark:text-blue-300 bg-blue-50/80 dark:bg-blue-950/40 border border-blue-200/80 dark:border-blue-900/60 rounded-lg shadow-2xs cursor-pointer"
          title="Insert table"
        >
          <TableIcon class="w-3.5 h-3.5 text-blue-600 dark:text-blue-400" />
          <span>Table</span>
          <ChevronDown class="w-2.5 h-2.5 opacity-60" />
        </button>

        <div
          v-if="showTableInsertMenu"
          class="absolute top-full left-0 mt-1.5 w-60 bg-white dark:bg-zinc-900 rounded-2xl border border-zinc-200 dark:border-zinc-700 shadow-2xl p-2.5 z-[200] space-y-2 animate-scale-in"
          @click.stop
        >
          <div class="text-[10px] font-bold text-zinc-400 uppercase tracking-wider">Presets</div>
          <div class="grid grid-cols-2 gap-1.5">
            <button
              type="button"
              @click="insertPresetTable(3, 3)"
              class="px-2 py-1.5 rounded-xl border border-zinc-200 dark:border-zinc-700 hover:bg-blue-50 hover:border-blue-300 text-left transition-colors cursor-pointer"
            >
              <div class="font-bold text-xs">3 × 3</div>
              <div class="text-[10px] text-zinc-400">Standard</div>
            </button>
            <button
              type="button"
              @click="insertPresetTable(3, 2)"
              class="px-2 py-1.5 rounded-xl border border-zinc-200 dark:border-zinc-700 hover:bg-blue-50 hover:border-blue-300 text-left transition-colors cursor-pointer"
            >
              <div class="font-bold text-xs">2 × 3</div>
              <div class="text-[10px] text-zinc-400">2 Columns</div>
            </button>
            <button
              type="button"
              @click="insertPresetTable(1, 2, 'none')"
              class="px-2 py-1.5 rounded-xl border border-blue-200 bg-blue-50/50 hover:bg-blue-100 text-left transition-colors cursor-pointer col-span-2"
            >
              <div class="font-bold text-xs text-blue-700">Signatures (2 × 1)</div>
              <div class="text-[10px] text-zinc-500">Border-free</div>
            </button>
          </div>
        </div>
      </div>

      <!-- Variables Dropdown -->
      <div
        class="relative px-1 border-r border-zinc-200 dark:border-zinc-700/60 editor-dropdown-container"
        :class="{ 'z-50': showVariablePicker }"
      >
        <button
          type="button"
          @mousedown.prevent
          @click.stop="toggleVariablePicker()"
          class="toolbar-btn flex items-center gap-1.5 px-2 h-7 rounded-lg text-xs font-semibold text-zinc-700 dark:text-zinc-200 hover:bg-zinc-100 dark:hover:bg-zinc-800"
          title="Contract variables"
        >
          <Variable class="w-3.5 h-3.5 text-indigo-500" />
          <span>Variables</span>
          <ChevronDown class="w-2.5 h-2.5 opacity-60" />
        </button>

        <div
          v-if="showVariablePicker"
          class="absolute top-full left-0 mt-1 w-64 bg-white dark:bg-zinc-900 rounded-2xl border border-zinc-200 dark:border-zinc-700 shadow-2xl p-2 z-[200] max-h-60 overflow-y-auto space-y-1 animate-scale-in"
          @click.stop
        >
          <div class="text-[10px] font-bold text-zinc-400 uppercase tracking-wider px-2 py-1">Insert Variable</div>
          <button
            v-for="v in CONTRACT_VARIABLES"
            :key="v.key"
            type="button"
            @mousedown.prevent
            @click="insertVariable(v.key)"
            class="w-full text-left px-2 py-1.5 rounded-lg hover:bg-blue-50 dark:hover:bg-zinc-800 flex items-center justify-between text-xs cursor-pointer group"
          >
            <div>
              <div class="font-bold text-zinc-800 dark:text-zinc-200 group-hover:text-blue-600">{{ v.label }}</div>
              <div class="font-mono text-[9.5px] text-zinc-400">{{ v.token }}</div>
            </div>
            <span class="text-blue-500 font-bold opacity-0 group-hover:opacity-100">+</span>
          </button>
        </div>
      </div>

      <!-- Rekvizitlar Toolbar Buttons -->
      <div class="flex items-center gap-0.5 px-1 border-r border-zinc-200 dark:border-zinc-700/60">
        <button
          type="button"
          @click="insertCompanyRequisites"
          class="toolbar-btn flex items-center gap-1.5 px-2 h-7 rounded-lg text-xs font-semibold text-indigo-700 dark:text-indigo-300 hover:bg-indigo-50 dark:hover:bg-indigo-950/50 cursor-pointer"
          title="Kompaniya (Bajaruvchi) rekvizitlarini sahifaga joylash"
        >
          <Building2 class="w-3.5 h-3.5 text-indigo-600 dark:text-indigo-400" />
          <span>Bajaruvchi</span>
        </button>

        <button
          type="button"
          @click="insertClientRequisites"
          class="toolbar-btn flex items-center gap-1.5 px-2 h-7 rounded-lg text-xs font-semibold text-emerald-700 dark:text-emerald-300 hover:bg-emerald-50 dark:hover:bg-emerald-950/50 cursor-pointer"
          title="Mijoz ma'lumotlari va imzo blokini sahifaga joylash"
        >
          <UserCheck class="w-3.5 h-3.5 text-emerald-600 dark:text-emerald-400" />
          <span>Mijoz</span>
        </button>
      </div>

      <!-- "+ Text" Button: Directly inserts a new Text element (Times New Roman, 14pt) -->
      <div class="pl-1">
        <button
          type="button"
          @click="handleAddText"
          class="inline-flex items-center gap-1.5 px-3 py-1 rounded-xl bg-blue-600 hover:bg-blue-700 active:scale-95 text-white font-bold text-xs shadow-xs cursor-pointer select-none transition-all"
          title="Matn qo'shish (Times New Roman, 14pt)"
        >
          <Plus class="w-3.5 h-3.5" />
          <span>Text</span>
        </button>
      </div>
    </div>

    <!-- Free-Positioning Multi-Page A4 Canvas Workspace -->
    <!--
      Layout Architecture:
      - canvasWorkspaceRef is the SINGLE unified scroll container owning BOTH X and Y scrollbars (overflow: auto).
      - Inner stage has width: max-content; min-width: 100%; display: flex; flex-direction: column; align-items: center;
        * When content < viewport (low zoom), min-width: 100% and items-center keep the page centered.
        * When content > viewport (high zoom), max-content expands to fit the scaled sheets,
          horizontal/vertical scrollbars appear automatically, and the user can scroll from the leftmost edge
          (with padding) all the way to the rightmost edge.
    -->
    <div
      ref="canvasWorkspaceRef"
      class="canvas-workspace flex-1 h-0 min-h-0 overflow-auto relative z-0 isolate select-none"
      :class="{ 'cursor-grab': isSpacePressed && !isPanning, 'cursor-grabbing': isPanning, 'copy-style-active': !!copyStyleMode }"
      @click.self="canvas.clearSelection()"
    >
      <!-- Floating Canva-style Copy Style Active Notification / Control Pill -->
      <div
        v-if="copyStyleMode"
        class="no-print sticky top-3 z-50 flex justify-center pointer-events-none mb-2"
      >
        <div class="pointer-events-auto bg-zinc-900/95 dark:bg-zinc-100/95 text-white dark:text-zinc-900 px-4 py-2 rounded-full shadow-2xl text-xs font-semibold flex items-center gap-2.5 backdrop-blur-md border border-white/15 dark:border-zinc-300 select-none ring-1 ring-black/10">
          <PaintRoller class="w-4 h-4 text-blue-400 dark:text-blue-600 animate-pulse shrink-0" />
          <span>
            {{ copyStyleMode === 'persistent' ? 'Format nusxalash (Qulflangan): Bir nechta matnga bosing' : 'Format nusxalash: Kerakli matnga bosing' }}
          </span>
          <span class="text-[11px] opacity-60 font-mono pl-1 border-l border-white/20 dark:border-zinc-400">Esc - bekor qilish</span>
          <button
            type="button"
            @click="deactivateCopyStyle"
            class="ml-1 p-0.5 hover:bg-white/20 dark:hover:bg-zinc-300 rounded-full cursor-pointer transition-colors"
            title="Bekor qilish (Esc)"
          >
            <X class="w-3.5 h-3.5" />
          </button>
        </div>
      </div>

      <div
        class="canvas-stage flex flex-col items-center pt-6 pb-36 px-8 sm:px-16"
        style="width: max-content; min-width: 100%;"
        @click.self="canvas.clearSelection()"
      >
        <!-- Loop through every A4 sheet in the document -->
        <CanvasA4Page
          v-for="(page, pageIdx) in canvas.document.value.pages"
          :key="page.id"
          :page="page"
          :page-index="pageIdx"
          :readonly="readonly"
          :is-active-page="canvas.activePageIndex.value === pageIdx"
          :total-pages="canvas.document.value.pages.length"
          :margins="canvas.document.value.margins"
          :zoom-level="canvas.zoomLevel.value"
          :selected-element-ids="canvas.selectedElementIds.value"
          :editing-element-id="canvas.editingElementId.value"
          :show-margin-guides="canvas.showMarginGuides.value"
          :show-rulers="canvas.showRulers.value"
          :show-grid="canvas.showGrid.value"
          :active-guides="canvas.activeGuides.value"
          :active-distance-guides="canvas.activeDistanceGuides.value"
          :is-copy-style-active="!!copyStyleMode"
          :copy-style-mode="copyStyleMode"
          :variable-values="variableValues"
          :calculate-snapping="canvas.calculateSnapping"
          @set-active-page="canvas.setActivePageIndex($event)"
          @select-element="(id, multi) => handleSelectElement(id, multi, pageIdx)"
          @select-elements="(ids) => { canvas.setActivePageIndex(pageIdx); canvas.selectedElementIds.value = ids }"
          @copy-style="handleCopyStyleButtonClick"
          @clear-selection="canvas.clearSelection()"
          @double-click-element="canvas.editingElementId.value = (canvas.editingElementId.value === $event ? null : $event)"
          @update-element="(id, updates, record) => canvas.updateElement(id, updates, record !== false)"
          @update-element-bounds="(id, bounds) => canvas.updateElementBounds(id, bounds)"
          @duplicate-element="canvas.duplicateSelectedElements($event)"
          @delete-element="canvas.deleteSelectedElements($event)"
          @toggle-lock="canvas.toggleLock($event)"
          @bring-forward="canvas.bringForward($event)"
          @send-backward="canvas.sendBackward($event)"
          @set-guides="(guides, distGuides) => {
            canvas.activeGuides.value = guides;
            canvas.activeDistanceGuides.value = distGuides || [];
          }"
          @finish-edit="canvas.editingElementId.value = null"
          @drag-start="(id) => canvas.startDrag(id)"
          @drag-end="() => { canvas.endDrag(); onDragResizeEnd() }"
          @resize-end="onDragResizeEnd()"
          @duplicate-page="canvas.duplicatePage($event)"
          @delete-page="canvas.deletePage($event)"
        />
      </div>
    </div>

    <!-- ─── Vertical Zoom Slider (Right Rail) ─── -->
    <!-- Placed OUTSIDE canvasWorkspaceRef so it stays fixed to the editor
         corner and doesn't scroll with the canvas content. -->
    <div
      class="zoom-rail no-print"
      @click.stop
    >
      <!-- Zoom In (+) -->
      <button
        type="button"
        class="zoom-rail-btn"
        :disabled="canvas.zoomLevel.value >= 500"
        title="Zoom in (Ctrl + Scroll)"
        @click="zoomInAroundCenter"
      >
        <ZoomIn class="w-3.5 h-3.5" />
      </button>

      <!-- Vertical Slider Track (Custom Pointer-Driven) -->
      <div
        ref="zoomSliderTrackRef"
        class="zoom-custom-track-container"
        title="Zoom level (Drag or Click to adjust)"
        @pointerdown="onSliderPointerDown"
        @pointermove="onSliderPointerMove"
        @pointerup="onSliderPointerUp"
        @pointercancel="onSliderPointerUp"
      >
        <!-- Background Track Bar -->
        <div class="zoom-custom-track-bar">
          <!-- Active Fill Bar (bottom-up) -->
          <div
            class="zoom-custom-fill-bar"
            :style="{ height: `${sliderPercent}%` }"
          />
        </div>

        <!-- Draggable Thumb Knob -->
        <div
          class="zoom-custom-thumb"
          :style="{ bottom: `calc(${sliderPercent}% - 7px)` }"
        />
      </div>

      <!-- Percentage Label -->
      <span class="zoom-rail-label">{{ canvas.zoomLevel.value }}%</span>

      <!-- Zoom Out (-) -->
      <button
        type="button"
        class="zoom-rail-btn"
        :disabled="canvas.zoomLevel.value <= 25"
        title="Zoom out"
        @click="zoomOutAroundCenter"
      >
        <ZoomOut class="w-3.5 h-3.5" />
      </button>

      <!-- Reset to 100% -->
      <button
        type="button"
        class="zoom-rail-btn zoom-rail-reset"
        title="Reset zoom to 100% (Ctrl+0)"
        @click="zoomResetAroundCenter"
      >
        <span class="text-[9px] font-bold font-mono leading-none">1:1</span>
      </button>
    </div>

    <!-- ─── Keyboard Shortcut Help Modal ─── -->
    <Teleport to="body">
      <div
        v-if="showShortcutHelp"
        class="fixed inset-0 z-[9999] flex items-center justify-center p-4"
        @click.self="showShortcutHelp = false"
      >
        <!-- Backdrop -->
        <div class="absolute inset-0 bg-black/40 backdrop-blur-sm" @click="showShortcutHelp = false"></div>

        <!-- Modal card -->
        <div class="relative z-10 w-full max-w-2xl max-h-[80vh] overflow-y-auto bg-white dark:bg-zinc-900 rounded-2xl shadow-2xl border border-zinc-200 dark:border-zinc-700 p-6">
          <!-- Header -->
          <div class="flex items-center justify-between mb-5">
            <div class="flex items-center gap-2">
              <div class="w-7 h-7 rounded-lg bg-blue-600 flex items-center justify-center">
                <span class="text-white text-xs font-bold">⌨</span>
              </div>
              <h2 class="text-base font-bold text-zinc-900 dark:text-zinc-100">Keyboard Shortcuts</h2>
            </div>
            <button
              type="button"
              @click="showShortcutHelp = false"
              class="w-7 h-7 flex items-center justify-center rounded-lg hover:bg-zinc-100 dark:hover:bg-zinc-800 text-zinc-400 hover:text-zinc-700 cursor-pointer transition-colors"
            >
              ✕
            </button>
          </div>

          <!-- Shortcut Grid -->
          <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <!-- General -->
            <div class="space-y-1">
              <div class="text-[10px] font-bold uppercase tracking-widest text-zinc-400 dark:text-zinc-500 mb-2">General</div>
              <div v-for="s in shortcutCategories.general" :key="s.label" class="shortcut-row">
                <span class="shortcut-label">{{ s.label }}</span>
                <span class="shortcut-keys">{{ s.keys }}</span>
              </div>
            </div>
            <!-- Text -->
            <div class="space-y-1">
              <div class="text-[10px] font-bold uppercase tracking-widest text-zinc-400 dark:text-zinc-500 mb-2">Text Formatting</div>
              <div v-for="s in shortcutCategories.text" :key="s.label" class="shortcut-row">
                <span class="shortcut-label">{{ s.label }}</span>
                <span class="shortcut-keys">{{ s.keys }}</span>
              </div>
            </div>
            <!-- Elements -->
            <div class="space-y-1">
              <div class="text-[10px] font-bold uppercase tracking-widest text-zinc-400 dark:text-zinc-500 mb-2">Elements</div>
              <div v-for="s in shortcutCategories.elements" :key="s.label" class="shortcut-row">
                <span class="shortcut-label">{{ s.label }}</span>
                <span class="shortcut-keys">{{ s.keys }}</span>
              </div>
            </div>
            <!-- Zoom -->
            <div class="space-y-1">
              <div class="text-[10px] font-bold uppercase tracking-widest text-zinc-400 dark:text-zinc-500 mb-2">Zoom & View</div>
              <div v-for="s in shortcutCategories.zoom" :key="s.label" class="shortcut-row">
                <span class="shortcut-label">{{ s.label }}</span>
                <span class="shortcut-keys">{{ s.keys }}</span>
              </div>
            </div>
          </div>

          <div class="mt-4 pt-4 border-t border-zinc-100 dark:border-zinc-800 text-[11px] text-zinc-400 text-center">
            Press <kbd class="kbd-badge">?</kbd> or <kbd class="kbd-badge">Ctrl+/</kbd> to toggle this panel
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<style>
.contract-editor-wrapper .toolbar-btn {
  padding: 0.35rem 0.45rem;
  border-radius: 0.5rem;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  color: inherit;
  transition: all 0.15s ease;
  cursor: pointer;
}

.contract-editor-wrapper .toolbar-btn:hover:not(:disabled) {
  background-color: rgba(0, 0, 0, 0.05);
}

.dark .contract-editor-wrapper .toolbar-btn:hover:not(:disabled) {
  background-color: rgba(255, 255, 255, 0.08);
}

.contract-editor-wrapper .toolbar-btn:disabled {
  opacity: 0.35;
  cursor: not-allowed;
}

.animate-scale-in {
  animation: scaleIn 0.12s ease-out;
}

@keyframes scaleIn {
  from {
    opacity: 0;
    transform: scale(0.96) translateY(-4px);
  }
  to {
    opacity: 1;
    transform: scale(1) translateY(0);
  }
}

/* Panning grab cursor classes */
.cursor-grab,
.cursor-grab * {
  cursor: grab !important;
}
.cursor-grabbing,
.cursor-grabbing * {
  cursor: grabbing !important;
}

/* ─── Vertical Zoom Rail ─── */
/* Pinned to the bottom-right corner of the visible editor frame */
.contract-editor-wrapper {
  position: relative;
}

.editor-toolbar {
  position: sticky;
  z-index: 30;
}

.canvas-workspace {
  position: relative;
  z-index: 0;
  isolation: isolate;
}

.zoom-rail {
  position: absolute;
  right: 16px;
  bottom: 24px;
  z-index: 20;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
  background: rgba(255,255,255,0.92);
  border: 1px solid rgba(0,0,0,0.1);
  border-radius: 14px;
  padding: 8px 6px 10px;
  box-shadow: 0 4px 24px rgba(0,0,0,0.12), 0 1px 4px rgba(0,0,0,0.07);
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
  user-select: none;
}

.dark .zoom-rail {
  background: rgba(24, 27, 32, 0.92);
  border-color: rgba(255,255,255,0.09);
  box-shadow: 0 4px 24px rgba(0,0,0,0.4), 0 1px 4px rgba(0,0,0,0.3);
}

.zoom-rail-btn {
  width: 26px;
  height: 26px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 8px;
  border: none;
  background: transparent;
  color: #52525b;
  cursor: pointer;
  transition: background 0.15s, color 0.15s;
  flex-shrink: 0;
}

.zoom-rail-btn:hover:not(:disabled) {
  background: rgba(59,130,246,0.12);
  color: #2563eb;
}

.zoom-rail-btn:disabled {
  opacity: 0.3;
  cursor: not-allowed;
}

.dark .zoom-rail-btn {
  color: #a1a1aa;
}

.dark .zoom-rail-btn:hover:not(:disabled) {
  background: rgba(96,165,250,0.15);
  color: #60a5fa;
}

.zoom-rail-reset {
  border-top: 1px solid rgba(0,0,0,0.07);
  padding-top: 4px;
  margin-top: 2px;
  color: #3b82f6;
  font-size: 9px;
}

.dark .zoom-rail-reset {
  border-top-color: rgba(255,255,255,0.08);
}

.zoom-rail-label {
  font-size: 9.5px;
  font-weight: 700;
  font-family: 'JetBrains Mono', 'Fira Code', monospace;
  color: #3f3f46;
  text-align: center;
  min-width: 28px;
  letter-spacing: 0.01em;
}

.dark .zoom-rail-label {
  color: #d4d4d8;
}

/* ─── Custom Vertical Slider Track ─── */
.zoom-custom-track-container {
  width: 24px;
  height: 110px;
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
  cursor: pointer;
  user-select: none;
  touch-action: none;
}

.zoom-custom-track-bar {
  width: 4px;
  height: 100%;
  border-radius: 9999px;
  background: #e4e4e7;
  position: relative;
}

.dark .zoom-custom-track-bar {
  background: #3f3f46;
}

.zoom-custom-fill-bar {
  position: absolute;
  bottom: 0;
  left: 0;
  width: 100%;
  background: #2563eb;
  border-radius: 9999px;
}

.dark .zoom-custom-fill-bar {
  background: #60a5fa;
}

.zoom-custom-thumb {
  position: absolute;
  left: 50%;
  transform: translateX(-50%);
  width: 14px;
  height: 14px;
  border-radius: 50%;
  background: #2563eb;
  border: 2px solid #ffffff;
  box-shadow: 0 1px 4px rgba(37,99,235,0.4);
  cursor: grab;
  transition: transform 0.1s, box-shadow 0.1s;
}

.dark .zoom-custom-thumb {
  background: #60a5fa;
  border-color: #18181b;
}

.zoom-custom-track-container:hover .zoom-custom-thumb {
  transform: translateX(-50%) scale(1.2);
  box-shadow: 0 2px 8px rgba(37,99,235,0.5);
}

/* ─── Shortcut Help Modal ─── */
.shortcut-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 4px 8px;
  border-radius: 6px;
  font-size: 11.5px;
  transition: background 0.1s;
}
.shortcut-row:hover {
  background: rgba(59,130,246,0.06);
}
.shortcut-label {
  color: #374151;
  font-weight: 500;
}
.dark .shortcut-label {
  color: #d1d5db;
}
.shortcut-keys {
  font-family: 'JetBrains Mono', 'Fira Code', ui-monospace, monospace;
  font-size: 10.5px;
  color: #6b7280;
  background: #f3f4f6;
  border: 1px solid #e5e7eb;
  padding: 1px 6px;
  border-radius: 5px;
  white-space: nowrap;
  letter-spacing: 0.02em;
}
.dark .shortcut-keys {
  color: #9ca3af;
  background: #27272a;
  border-color: #3f3f46;
}
.kbd-badge {
  display: inline-block;
  font-family: 'JetBrains Mono', ui-monospace, monospace;
  font-size: 10px;
  background: #f3f4f6;
  border: 1px solid #d1d5db;
  border-radius: 4px;
  padding: 1px 5px;
  color: #374151;
}
.dark .kbd-badge {
  background: #27272a;
  border-color: #3f3f46;
  color: #d1d5db;
}

/* ─── Canva Copy Style Active Cursor & State ─── */
.canvas-workspace.copy-style-active,
.canvas-workspace.copy-style-active * {
  cursor: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='24' height='24' viewBox='0 0 24 24' fill='none' stroke='%232563eb' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Crect width='14' height='5' x='2' y='2' rx='1.5' fill='%23bfdbfe'/%3E%3Cpath d='M9 15v-2a2 2 0 0 1 2-2h7a2 2 0 0 0 2-2V6a2 2 0 0 0-2-2h-1'/%3E%3Crect width='4' height='7' x='7' y='15' rx='1' fill='%232563eb'/%3E%3C/svg%3E") 3 3, crosshair !important;
}
</style>
