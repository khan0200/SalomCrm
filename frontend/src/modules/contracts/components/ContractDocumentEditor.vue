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
} from 'lucide-vue-next'
import { CONTRACT_VARIABLES, type ContractVariableDef, buildVariableValues } from '../utils/contractVariables'
import { downloadContractAsPdf, printContractAsPdf } from '../utils/contractPdf'
import type {
  ContractDocumentModel,
  CanvasPageModel,
  CanvasElement,
  TextCanvasElement,
  TableCanvasElement,
  PageMargins,
  AlignmentGuide,
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

// Compute dynamic variable replacements from studentData
const variableValues = computed(() => {
  return buildVariableValues(props.studentData, {
    contractNumber: props.contractNumber,
    templateName: props.title,
  })
})

// UI Menus & Popovers
const showColorPicker = ref(false)
const showHighlightPicker = ref(false)
const showTableInsertMenu = ref(false)
const showMarginMenu = ref(false)
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
  const el = canvas.selectedElement.value as TextCanvasElement
  return el?.style?.fontSize || 14
})

// Current font color
const currentFontColor = computed(() => {
  const el = canvas.selectedElement.value as TextCanvasElement
  return el?.style?.color || '#000000'
})

// Current text highlight
const currentHighlightColor = computed(() => {
  const el = canvas.selectedElement.value as TextCanvasElement
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
  const activeEl = window.document.activeElement
  const isInTextEdit =
    activeEl &&
    (activeEl.tagName === 'INPUT' ||
      activeEl.tagName === 'TEXTAREA' ||
      (activeEl as HTMLElement).getAttribute('contenteditable') === 'true' ||
      Boolean((activeEl as HTMLElement).closest('.canvas-text-element')) ||
      Boolean((activeEl as HTMLElement).closest('[contenteditable="true"]')))

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

  // ── Escape → close help modal if open ───────────────────────
  if (e.key === 'Escape' && showShortcutHelp.value) {
    showShortcutHelp.value = false
    return
  }

  // ── Text formatting (only when element selected, not in text edit) ──
  if (isMod && !isInTextEdit && canvas.selectedElement.value) {
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

  // ── Delegate remaining shortcuts to canvas handler ──────────
  canvas.handleKeyDown(e)
}

// Canvas workspace ref for wheel events
const canvasWorkspaceRef = ref<HTMLElement | null>(null)

// Ctrl + MouseWheel = zoom (Canva/Figma style)
function onCanvasWheel(e: WheelEvent) {
  if (!e.ctrlKey) return
  e.preventDefault()
  e.stopPropagation()
  const delta = e.deltaY > 0 ? -10 : 10
  canvas.setZoom(canvas.zoomLevel.value + delta)
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
  showEditorDownloadMenu.value = false
}

// Undo / Redo helpers (called once per action — buttons previously called undo() twice!)
function performUndo() {
  const state = canvas.history.undo()
  if (state) canvas.document.value = state
}

function performRedo() {
  const state = canvas.history.redo()
  if (state) canvas.document.value = state
}

// Called when drag or resize finishes — records a history snapshot so Ctrl+Z works
function onDragResizeEnd() {
  canvas.history.recordSnapshot(canvas.document.value)
}

onMounted(() => {
  window.addEventListener('keydown', onKeyDown)
  window.addEventListener('paste', onGlobalPaste)
  // Document-level click → close all open dropdowns
  document.addEventListener('click', closeAllDropdowns)
  // Use passive:false so we can preventDefault on Ctrl+Wheel
  canvasWorkspaceRef.value?.addEventListener('wheel', onCanvasWheel, { passive: false })
  canvasWorkspaceRef.value?.addEventListener('scroll', onWorkspaceScroll, { passive: true })
})

onBeforeUnmount(() => {
  window.removeEventListener('keydown', onKeyDown)
  window.removeEventListener('paste', onGlobalPaste)
  document.removeEventListener('click', closeAllDropdowns)
  canvasWorkspaceRef.value?.removeEventListener('wheel', onCanvasWheel)
  canvasWorkspaceRef.value?.removeEventListener('scroll', onWorkspaceScroll)
  if (scrollRafId) cancelAnimationFrame(scrollRafId)
})

// --- Toolbar Element Styling Helpers ---
function setFontSize(sizePt: number | string) {
  const num = typeof sizePt === 'string' ? parseInt(sizePt, 10) : sizePt
  const el = canvas.selectedElement.value as TextCanvasElement
  if (el) {
    if (!el.style) el.style = {}
    el.style.fontSize = num
  }
}

function toggleBold() {
  const el = canvas.selectedElement.value as TextCanvasElement
  if (!el) return
  if (!el.style) el.style = {}
  el.style.fontWeight = el.style.fontWeight === 'bold' || el.style.fontWeight === 700 ? 'normal' : 'bold'
}

function toggleItalic() {
  const el = canvas.selectedElement.value as TextCanvasElement
  if (!el) return
  if (!el.style) el.style = {}
  el.style.fontStyle = el.style.fontStyle === 'italic' ? 'normal' : 'italic'
}

function toggleUnderline() {
  const el = canvas.selectedElement.value as TextCanvasElement
  if (!el) return
  if (!el.style) el.style = {}
  el.style.textDecoration = el.style.textDecoration === 'underline' ? 'none' : 'underline'
}

function toggleStrike() {
  const el = canvas.selectedElement.value as TextCanvasElement
  if (!el) return
  if (!el.style) el.style = {}
  el.style.textDecoration = el.style.textDecoration === 'line-through' ? 'none' : 'line-through'
}

function setTextAlign(align: 'left' | 'center' | 'right' | 'justify') {
  const el = canvas.selectedElement.value as TextCanvasElement
  if (!el) return
  if (!el.style) el.style = {}
  el.style.textAlign = align
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

// Margins dropdown toggle
function toggleMarginMenu() {
  showMarginMenu.value = !showMarginMenu.value
  if (showMarginMenu.value) {
    showTableInsertMenu.value = false
    showVariablePicker.value = false
    showColorPicker.value = false
    showHighlightPicker.value = false
    showEditorDownloadMenu.value = false
  }
}

function setFontColor(color: string) {
  const el = canvas.selectedElement.value as TextCanvasElement
  if (!el) return
  if (!el.style) el.style = {}
  el.style.color = color
  showColorPicker.value = false
}

function setHighlightColor(color: string) {
  const el = canvas.selectedElement.value
  if (!el) return
  if (el.type === 'table') {
    // Apply fill to all cells in table
    const table = el as TableCanvasElement
    table.cells.forEach(row => {
      row.forEach(c => {
        c.backgroundColor = color === '#ffffff' ? undefined : color
      })
    })
  } else {
    const textEl = el as TextCanvasElement
    if (!textEl.style) textEl.style = {}
    textEl.style.backgroundColor = color === '#ffffff' ? 'transparent' : color
  }
  showHighlightPicker.value = false
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
    height: 14,
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
  const el = canvas.selectedElement.value as TextCanvasElement
  if (el && el.type === 'text') {
    el.content += ` ${vKey} `
  } else {
    const contentWidth = printableContentWidthMm.value
    canvas.addElement({
      id: `var_${Date.now()}`,
      type: 'text',
      x: canvas.document.value.margins.left,
      y: canvas.document.value.margins.top + 10,
      width: 70,
      height: 10,
      zIndex: 1,
      content: `<span class="bg-blue-50 text-blue-700 font-mono font-bold px-1.5 py-0.5 rounded border border-blue-200 text-xs">${vKey}</span>`,
      variableKey: vKey,
      style: {
        fontFamily: 'Times New Roman',
        fontSize: 12,
        color: '#1d4ed8',
      },
    })
  }
  showVariablePicker.value = false
}

// Checkbox insertion
function insertCheckboxElement(checked: boolean) {
  canvas.addElement({
    id: `checkbox_${Date.now()}`,
    type: 'checkbox',
    checked,
    label: 'Tanlov varianti',
    x: canvas.document.value.margins.left,
    y: canvas.document.value.margins.top + 10,
    width: 65,
    height: 8,
    zIndex: 1,
    fontSize: 12,
  })
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
    class="contract-editor-wrapper flex flex-col flex-1 bg-zinc-100 dark:bg-zinc-950 font-sans"
    :class="hideTopBar ? '' : 'min-h-screen'"
  >
    <!-- Top Action & Status Bar -->
    <div
      v-if="!hideTopBar"
      class="no-print sticky top-0 z-30 flex flex-wrap items-center justify-between gap-3 px-4 py-2.5 bg-white dark:bg-[#15171a] border-b border-zinc-200 dark:border-zinc-800 shadow-2xs"
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

        <!-- Download PDF Button & Format Menu -->
        <div class="relative flex items-center editor-dropdown-container">
          <button
            type="button"
            @click="downloadDocument('pdf')"
            :disabled="isDownloadingPdf"
            class="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-l-xl border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-800 text-xs font-semibold text-zinc-700 dark:text-zinc-300 hover:bg-zinc-50 dark:hover:bg-zinc-750 transition-colors cursor-pointer shadow-2xs"
            title="Download PDF"
          >
            <Loader2 v-if="isDownloadingPdf" class="w-3.5 h-3.5 animate-spin text-blue-500" />
            <Download v-else class="w-3.5 h-3.5 text-blue-500" />
            <span>PDF</span>
          </button>
          <button
            type="button"
            @click.stop="showEditorDownloadMenu = !showEditorDownloadMenu"
            class="px-1.5 py-1.5 rounded-r-xl border-y border-r border-zinc-200 dark:border-zinc-800 bg-zinc-50 dark:bg-zinc-750 hover:bg-zinc-100 text-zinc-500 cursor-pointer"
            title="Format"
          >
            <ChevronDown class="w-3 h-3" />
          </button>

          <div
            v-if="showEditorDownloadMenu"
            class="absolute right-0 top-full mt-1 w-48 bg-white dark:bg-zinc-800 rounded-xl border border-zinc-200 dark:border-zinc-700 shadow-xl p-1 z-[200] space-y-0.5"
            @click.stop
          >
            <button
              type="button"
              @click="downloadDocument('pdf'); showEditorDownloadMenu = false"
              class="w-full text-left px-2.5 py-1.5 rounded-lg text-xs hover:bg-zinc-100 dark:hover:bg-zinc-700 flex items-center gap-2 font-bold text-blue-600 cursor-pointer"
            >
              <FileText class="w-3.5 h-3.5" />
              <span>PDF (.pdf)</span>
            </button>
            <button
              type="button"
              @click="downloadDocument('print'); showEditorDownloadMenu = false"
              class="w-full text-left px-2.5 py-1.5 rounded-lg text-xs hover:bg-zinc-100 dark:hover:bg-zinc-700 flex items-center gap-2 text-zinc-700 dark:text-zinc-300 cursor-pointer border-t border-zinc-100 dark:border-zinc-750 pt-1.5"
            >
              <Eye class="w-3.5 h-3.5 text-emerald-500" />
              <span>Print</span>
            </button>
          </div>
        </div>

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
      class="no-print editor-toolbar z-20 flex flex-wrap items-center gap-1 p-2 bg-zinc-50/95 dark:bg-[#1a1d20]/95 backdrop-blur-md border-b border-zinc-200 dark:border-zinc-800 text-zinc-700 dark:text-zinc-300 select-none text-xs"
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

      <!-- Document Zoom Level (25% - 200%) -->
      <div class="flex items-center gap-0.5 px-1.5 border-r border-zinc-200 dark:border-zinc-700/60" title="Zoom">
        <button
          type="button"
          @click="canvas.zoomOut()"
          :disabled="canvas.zoomLevel.value <= 25"
          class="toolbar-btn text-xs font-bold w-6 h-6 p-0 disabled:opacity-40"
          title="Zoom -"
        >
          <ZoomOut class="w-3.5 h-3.5" />
        </button>
        <span class="text-[11px] font-bold font-mono px-1 select-none text-zinc-600 dark:text-zinc-300 min-w-[36px] text-center">
          {{ canvas.zoomLevel.value }}%
        </span>
        <button
          type="button"
          @click="canvas.zoomIn()"
          :disabled="canvas.zoomLevel.value >= 200"
          class="toolbar-btn text-xs font-bold w-6 h-6 p-0 disabled:opacity-40"
          title="Zoom +"
        >
          <ZoomIn class="w-3.5 h-3.5" />
        </button>
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
          :class="{ 'bg-blue-100 dark:bg-blue-950/60 text-blue-700 font-bold': (canvas.selectedElement.value as any)?.style?.textDecoration === 'underline' }"
          title="Underline (Ctrl+U)"
        >
          <UnderlineIcon class="w-3.5 h-3.5" />
        </button>
        <button
          type="button"
          @click="toggleStrike"
          class="toolbar-btn line-through"
          :class="{ 'bg-blue-100 dark:bg-blue-950/60 text-blue-700 font-bold': (canvas.selectedElement.value as any)?.style?.textDecoration === 'line-through' }"
          title="Strikethrough"
        >
          <Strikethrough class="w-3.5 h-3.5" />
        </button>
      </div>

      <!-- Text Color & Fill Color Pickers -->
      <div class="flex items-center gap-1 px-1.5 border-r border-zinc-200 dark:border-zinc-700/60">
        <!-- Text Color -->
        <div class="relative editor-dropdown-container">
          <button
            type="button"
            @click.stop="showColorPicker = !showColorPicker; showHighlightPicker = false; showMarginMenu = false; showTableInsertMenu = false; showVariablePicker = false"
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
        <div class="relative editor-dropdown-container">
          <button
            type="button"
            @click.stop="showHighlightPicker = !showHighlightPicker; showColorPicker = false; showMarginMenu = false; showTableInsertMenu = false; showVariablePicker = false"
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
      <div class="relative px-1 border-r border-zinc-200 dark:border-zinc-700/60 editor-dropdown-container">
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

      <!-- Table Inserter Dropdown -->
      <div class="relative px-1 border-r border-zinc-200 dark:border-zinc-700/60 editor-dropdown-container">
        <button
          type="button"
          @click.stop="showTableInsertMenu = !showTableInsertMenu; showVariablePicker = false; showMarginMenu = false"
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
      <div class="relative px-1 border-r border-zinc-200 dark:border-zinc-700/60 editor-dropdown-container">
        <button
          type="button"
          @click.stop="showVariablePicker = !showVariablePicker; showTableInsertMenu = false; showMarginMenu = false"
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
            @click="insertVariable(v.key)"
            class="w-full text-left px-2 py-1.5 rounded-lg hover:bg-blue-50 dark:hover:bg-zinc-800 flex items-center justify-between text-xs cursor-pointer group"
          >
            <div>
              <div class="font-bold text-zinc-800 dark:text-zinc-200 group-hover:text-blue-600">{{ v.label }}</div>
              <div class="font-mono text-[9.5px] text-zinc-400">{{ v.key }}</div>
            </div>
            <span class="text-blue-500 font-bold opacity-0 group-hover:opacity-100">+</span>
          </button>
        </div>
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
    <div class="canvas-outer-wrapper relative flex flex-1 overflow-hidden" style="isolation: isolate">
      <div
        ref="canvasWorkspaceRef"
        class="document-workspace flex-1 flex flex-col items-center p-4 sm:p-8 overflow-y-auto overflow-x-auto relative"
        :style="hideTopBar ? 'height: calc(100vh - 170px);' : 'height: calc(100vh - 130px);'"
        @click.self="canvas.clearSelection()"
      >
        <!-- Loop through every A4 sheet in the document -->
        <CanvasA4Page
          v-for="(page, pageIdx) in canvas.document.value.pages"
          :key="page.id"
          :page="page"
          :page-index="pageIdx"
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
          :variable-values="variableValues"
          :calculate-snapping="canvas.calculateSnapping"
          @set-active-page="canvas.setActivePageIndex($event)"
          @select-element="(id, multi) => canvas.selectElement(id, multi, pageIdx)"
          @clear-selection="canvas.clearSelection()"
          @double-click-element="canvas.editingElementId.value = $event"
          @update-element="(id, updates) => canvas.updateElement(id, updates)"
          @update-element-bounds="(id, bounds) => canvas.updateElement(id, bounds, false)"
          @duplicate-element="canvas.duplicateSelectedElements($event)"
          @delete-element="canvas.deleteSelectedElements($event)"
          @toggle-lock="canvas.toggleLock($event)"
          @bring-forward="canvas.bringForward($event)"
          @send-backward="canvas.sendBackward($event)"
          @set-guides="canvas.activeGuides.value = $event"
          @finish-edit="canvas.editingElementId.value = null"
          @drag-end="onDragResizeEnd()"
          @resize-end="onDragResizeEnd()"
          @duplicate-page="canvas.duplicatePage($event)"
          @delete-page="canvas.deletePage($event)"
        />
      </div>

      <!-- ─── Vertical Zoom Slider (Right Rail) ─── -->
      <div
        class="zoom-rail no-print"
        @click.stop
      >
        <!-- Zoom In (+) -->
        <button
          type="button"
          class="zoom-rail-btn"
          :disabled="canvas.zoomLevel.value >= 200"
          title="Zoom in (Ctrl + Scroll)"
          @click="canvas.zoomIn()"
        >
          <ZoomIn class="w-3.5 h-3.5" />
        </button>

        <!-- Vertical Slider Track -->
        <div class="zoom-slider-track">
          <input
            type="range"
            class="zoom-slider-input"
            min="25"
            max="200"
            step="5"
            :value="canvas.zoomLevel.value"
            :style="`--v: ${(((canvas.zoomLevel.value - 25) / 175) * 100).toFixed(1)}`"
            @input="canvas.setZoom(+($event.target as HTMLInputElement).value)"
            title="Zoom level"
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
          @click="canvas.zoomOut()"
        >
          <ZoomOut class="w-3.5 h-3.5" />
        </button>

        <!-- Reset to 100% -->
        <button
          type="button"
          class="zoom-rail-btn zoom-rail-reset"
          title="Reset zoom to 100%"
          @click="canvas.setZoom(100)"
        >
          <span class="text-[9px] font-bold font-mono leading-none">1:1</span>
        </button>
      </div>
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

/* ─── Vertical Zoom Rail ─── */
.canvas-outer-wrapper {
  position: relative;
}

.zoom-rail {
  position: absolute;
  right: 12px;
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

/* Vertical slider track container */
.zoom-slider-track {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 120px;
  width: 26px;
}

/* The actual range input – rotated to vertical */
.zoom-slider-input {
  -webkit-appearance: none;
  appearance: none;
  width: 120px;
  height: 4px;
  border-radius: 2px;
  background: linear-gradient(
    to right,
    #3b82f6 0%,
    #3b82f6 calc((var(--v,50)) * 1%),
    #d4d4d8 calc((var(--v,50)) * 1%),
    #d4d4d8 100%
  );
  outline: none;
  cursor: pointer;
  transform: rotate(-90deg);
  transform-origin: center center;
}

.zoom-slider-input::-webkit-slider-thumb {
  -webkit-appearance: none;
  appearance: none;
  width: 14px;
  height: 14px;
  border-radius: 50%;
  background: #2563eb;
  border: 2px solid #fff;
  box-shadow: 0 1px 4px rgba(37,99,235,0.35);
  cursor: pointer;
  transition: transform 0.1s, box-shadow 0.1s;
}

.zoom-slider-input::-webkit-slider-thumb:hover {
  transform: scale(1.2);
  box-shadow: 0 2px 8px rgba(37,99,235,0.5);
}

.zoom-slider-input::-moz-range-thumb {
  width: 14px;
  height: 14px;
  border-radius: 50%;
  background: #2563eb;
  border: 2px solid #fff;
  box-shadow: 0 1px 4px rgba(37,99,235,0.35);
  cursor: pointer;
}

.dark .zoom-slider-input {
  background: linear-gradient(
    to right,
    #60a5fa 0%,
    #60a5fa calc((var(--v,50)) * 1%),
    #3f3f46 calc((var(--v,50)) * 1%),
    #3f3f46 100%
  );
}

.dark .zoom-slider-input::-webkit-slider-thumb {
  background: #60a5fa;
  border-color: #18181b;
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
</style>
