<script setup lang="ts">
import { ref, computed, watch, nextTick, onMounted } from 'vue'
import type { TextCanvasElement } from '../../types/contractCanvas'
import { cleanClipboardContent } from '../../utils/clipboardUtils'
import { scaleInlineStyles, normalizeLegacyRequisites } from '../../utils/canvasZoomUtils'
import { replaceVariablesInHtml } from '../../utils/contractVariables'

const MM_TO_PX_BASE = 3.779527559

const props = withDefaults(
  defineProps<{
    element: TextCanvasElement
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
  'update:content': [val: string]
  'finish-edit': []
  'auto-resize-height': [heightMm: number]
}>()

const editableRef = ref<HTMLDivElement | null>(null)
let lastEmittedHtml = ''

const elementStyle = computed(() => {
  const st = props.element.style || {}
  const fontSizePt = st.fontSize || 14
  // Scale font size proportionally with zoom
  const scaledFontSizePx = fontSizePt * (4 / 3) * (props.zoomLevel / 100)
  const resolvedFont = st.fontFamily
    ? `"${st.fontFamily}", 'Times New Roman', Times, Georgia, serif`
    : "'Times New Roman', Times, Georgia, serif"

  return {
    '--canvas-element-font': resolvedFont,
    fontFamily: resolvedFont,
    fontSize: `${scaledFontSizePx}px`,
    fontWeight: st.fontWeight || (props.element.type === 'heading' ? 'bold' : 'normal'),
    fontStyle: st.fontStyle || 'normal',
    textDecoration: st.textDecoration || 'none',
    color: st.color || '#000000',
    backgroundColor: st.backgroundColor || 'transparent',
    textAlign: st.textAlign || (props.element.type === 'heading' ? 'center' : 'left'),
    lineHeight: st.lineHeight || 1.5,
    letterSpacing: typeof st.letterSpacing === 'number' && st.letterSpacing !== 0
      ? `${st.letterSpacing * (props.zoomLevel / 100)}px`
      : 'normal',
    textTransform: st.textTransform || 'none',
    padding: st.padding ? `${st.padding * 3.78 * (props.zoomLevel / 100)}px` : '0px',
  }
})

// Replace variables in preview mode and scale inline styles proportionally with zoom
const displayContent = computed(() => {
  let text = props.element.content || ''
  if (!props.isEditing && (props.readonly || (props.variableValues && Object.keys(props.variableValues).length > 0))) {
    text = replaceVariablesInHtml(text, props.variableValues || {})
  }
  if (!props.isEditing) {
    text = scaleInlineStyles(text, props.zoomLevel)
  }
  return text
})

function measureAndEmitHeight() {
  if (!editableRef.value) return

  let contentHeightPx = 0

  // 1. Primary: Measure the Range of the actual content inside the editable container
  try {
    const range = window.document.createRange()
    range.selectNodeContents(editableRef.value)
    const rangeRect = range.getBoundingClientRect()
    if (rangeRect.height > 0) {
      contentHeightPx = rangeRect.height
    }
  } catch {}

  // 2. Secondary fallback: Check children bounding rect or scrollHeight
  if (contentHeightPx <= 0) {
    const firstChild = editableRef.value.firstElementChild as HTMLElement | null
    if (firstChild) {
      contentHeightPx = firstChild.getBoundingClientRect().height
    }
  }

  // 3. Fallback: computed line-height for empty content
  if (contentHeightPx <= 0) {
    const computedStyle = window.getComputedStyle(editableRef.value)
    const fs = parseFloat(computedStyle.fontSize) || 16
    const lh = parseFloat(computedStyle.lineHeight) || (fs * 1.5)
    contentHeightPx = lh
  }

  // Convert px to mm at current zoom level
  const zoomFactor = MM_TO_PX_BASE * (props.zoomLevel / 100)
  const heightMm = contentHeightPx / zoomFactor

  // Add a small 0.8mm padding buffer for descenders (g, y, p, q, j) so bounding box fits cleanly
  const finalMm = Math.max(4, Math.round((heightMm + 0.8) * 10) / 10)

  // Only emit if there is a noticeable difference (> 0.3mm)
  if (Math.abs(finalMm - props.element.height) > 0.3) {
    emit('auto-resize-height', finalMm)
  }
}

let lastHandledZoom = props.zoomLevel

// Sync initial DOM content without triggering reactivity reset
onMounted(() => {
  if (editableRef.value) {
    editableRef.value.innerHTML = props.isEditing
      ? normalizeLegacyRequisites(props.element.content || '')
      : displayContent.value
  }
  // Auto-fit height to actual text content on mount
  nextTick(() => {
    measureAndEmitHeight()
    if (typeof document !== 'undefined' && 'fonts' in document) {
      document.fonts.ready.then(() => measureAndEmitHeight())
    }
  })
})

// Watch external content changes (e.g. Undo/Redo or Variable insertion from outside)
watch(
  () => props.element.content,
  newContent => {
    if (newContent === lastEmittedHtml) return
    const normalized = normalizeLegacyRequisites(newContent || '')
    if (editableRef.value && editableRef.value.innerHTML !== normalized) {
      editableRef.value.innerHTML = props.isEditing ? normalized : scaleInlineStyles(normalized, props.zoomLevel)
    }
    nextTick(() => measureAndEmitHeight())
  }
)

// Watch zoomLevel changes when NOT editing
watch(
  () => props.zoomLevel,
  newZoom => {
    lastHandledZoom = newZoom
    if (!props.isEditing && editableRef.value) {
      editableRef.value.innerHTML = displayContent.value || ''
    }
    // Do NOT trigger measureAndEmitHeight on pure zoom slider movements
  }
)

// Watch displayContent changes when NOT editing
watch(displayContent, newVal => {
  if (!props.isEditing && editableRef.value) {
    editableRef.value.innerHTML = newVal || ''
  }
  // Only auto-resize height if content/variables changed, not pure zoom change
  if (props.zoomLevel === lastHandledZoom) {
    nextTick(() => measureAndEmitHeight())
  }
})

// Watch width changes (e.g. resizing text box width triggers text re-flow and height change)
watch(
  () => props.element.width,
  () => {
    nextTick(() => measureAndEmitHeight())
  }
)

// Watch font size, line height, letter spacing, font family, and text transform styling changes
watch(
  () => [
    props.element.style?.fontSize,
    props.element.style?.lineHeight,
    props.element.style?.letterSpacing,
    props.element.style?.fontFamily,
    props.element.style?.textTransform,
  ],
  () => {
    nextTick(() => measureAndEmitHeight())
  }
)

// Autofocus and place cursor when editing begins; clear selection when editing ends
watch(
  () => props.isEditing,
  (isEdit, oldEdit) => {
    if (isEdit) {
      nextTick(() => {
        if (!editableRef.value) return
        const normalized = normalizeLegacyRequisites(props.element.content || '')
        editableRef.value.innerHTML = normalized
        lastEmittedHtml = normalized
        editableRef.value.focus({ preventScroll: true })

        const range = window.document.createRange()
        const sel = window.getSelection()
        range.selectNodeContents(editableRef.value)

        // If it's the initial placeholder text, leave the entire content selected
        // so typing or pasting immediately replaces the placeholder cleanly!
        const currentText = editableRef.value.innerText.trim()
        const isPlaceholder = currentText === 'Yangi matn bloki...' || currentText === 'Shartnoma matnini bu yerga yozing...'
        if (!isPlaceholder) {
          range.collapse(false)
        }

        sel?.removeAllRanges()
        sel?.addRange(range)
        measureAndEmitHeight()
      })
    } else if (oldEdit && !isEdit) {
      // Exiting edit mode
      if (editableRef.value) {
        editableRef.value.innerHTML = displayContent.value
      }
      // Clean up browser text highlight
      try {
        window.getSelection()?.removeAllRanges()
      } catch {}
      nextTick(() => measureAndEmitHeight())
    }
  }
)

function onBlur() {
  if (!editableRef.value) return
  const newHtml = editableRef.value.innerHTML
  lastEmittedHtml = newHtml
  emit('update:content', newHtml)
  measureAndEmitHeight()
  emit('finish-edit')
  try {
    window.getSelection()?.removeAllRanges()
  } catch {}
}

function onInput() {
  if (!editableRef.value) return
  const newHtml = editableRef.value.innerHTML
  lastEmittedHtml = newHtml
  emit('update:content', newHtml)
  measureAndEmitHeight()
}

function onKeyDown(e: KeyboardEvent) {
  if (e.key === 'Escape') {
    emit('finish-edit')
    try {
      window.getSelection()?.removeAllRanges()
    } catch {}
    return
  }

  // Handle Tab / Shift+Tab inside lists for Indent / Outdent (Nested Lists)
  if (e.key === 'Tab') {
    const sel = window.getSelection()
    if (sel && sel.rangeCount > 0) {
      const range = sel.getRangeAt(0)
      let node: Node | null = range.startContainer
      if (node.nodeType === Node.TEXT_NODE) node = node.parentNode
      const li = (node as HTMLElement)?.closest('li')
      if (li) {
        e.preventDefault()
        if (e.shiftKey) {
          document.execCommand('outdent', false)
        } else {
          document.execCommand('indent', false)
        }
        onInput()
        return
      }
    }
  }

  // Handle Enter on empty list item (double Enter -> exit list or outdent nested list)
  if (e.key === 'Enter' && !e.shiftKey) {
    const sel = window.getSelection()
    if (sel && sel.rangeCount > 0) {
      const range = sel.getRangeAt(0)
      let node: Node | null = range.startContainer
      if (node.nodeType === Node.TEXT_NODE) node = node.parentNode
      const li = (node as HTMLElement)?.closest('li')
      if (li) {
        const text = li.textContent?.replace(/\u200B/g, '').trim() || ''
        const isEffectivelyEmpty = text === '' && !li.querySelector('img, table, input')
        if (isEffectivelyEmpty) {
          e.preventDefault()
          const parentList = li.closest('ol, ul')
          const grandParentList = parentList?.parentElement?.closest('ol, ul')
          if (grandParentList) {
            document.execCommand('outdent', false)
          } else {
            const listCommand = parentList?.tagName.toLowerCase() === 'ol' ? 'insertOrderedList' : 'insertUnorderedList'
            document.execCommand(listCommand, false)
          }
          onInput()
          return
        }
      }
    }
  }

  // Handle Backspace at start of empty list item -> exit list formatting
  if (e.key === 'Backspace') {
    const sel = window.getSelection()
    if (sel && sel.rangeCount > 0 && sel.isCollapsed) {
      const range = sel.getRangeAt(0)
      let node: Node | null = range.startContainer
      if (node.nodeType === Node.TEXT_NODE) node = node.parentNode
      const li = (node as HTMLElement)?.closest('li')
      if (li) {
        const text = li.textContent?.replace(/\u200B/g, '').trim() || ''
        if (text === '') {
          e.preventDefault()
          const parentList = li.closest('ol, ul')
          const grandParentList = parentList?.parentElement?.closest('ol, ul')
          if (grandParentList) {
            document.execCommand('outdent', false)
          } else {
            const listCommand = parentList?.tagName.toLowerCase() === 'ol' ? 'insertOrderedList' : 'insertUnorderedList'
            document.execCommand(listCommand, false)
          }
          onInput()
          return
        }
      }
    }
  }
}

function onPaste(e: ClipboardEvent) {
  e.preventDefault()
  const clipboardData = e.clipboardData
  if (!clipboardData) return

  // Sanitize clipboard HTML/text, stripping Telegram white fonts and dark backgrounds
  const cleanHtml = cleanClipboardContent(clipboardData, props.element.style?.color || '#000000')
  if (!cleanHtml) return

  const currentText = editableRef.value?.innerText?.trim() || ''
  const isPlaceholder =
    currentText === 'Yangi matn bloki...' ||
    currentText === 'Shartnoma matnini bu yerga yozing...' ||
    currentText === ''

  if (isPlaceholder && editableRef.value) {
    // Completely overwrite placeholder with the pasted text
    editableRef.value.innerHTML = cleanHtml
  } else {
    // Insert at current selection / caret
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
    } else if (editableRef.value) {
      editableRef.value.innerHTML = cleanHtml
    }
  }

  onInput()
}
</script>

<template>
  <div
    ref="editableRef"
    class="canvas-text-element w-full h-full min-h-full outline-none focus:outline-none focus-visible:outline-none border-none break-words overflow-visible"
    :class="[
      isEditing
        ? 'select-text cursor-text'
        : 'select-none'
    ]"
    :style="elementStyle"
    :contenteditable="isEditing"
    @blur="onBlur"
    @input="onInput"
    @keydown="onKeyDown"
    @paste="onPaste"
  ></div>
</template>

<style>
.canvas-text-element {
  font-family: var(--canvas-element-font, 'Times New Roman', Times, Georgia, serif) !important;
  outline: none !important;
  border: none !important;
  box-shadow: none !important;
}
.canvas-text-element,
.canvas-text-element * {
  font-family: var(--canvas-element-font, 'Times New Roman', Times, Georgia, serif) !important;
}

/* Guard against clipboard HTML carrying white text from Telegram dark mode */
.canvas-text-element [style*="color: rgb(255, 255, 255)"],
.canvas-text-element [style*="color: #fff"],
.canvas-text-element [style*="color: #ffffff"],
.canvas-text-element [style*="color: white"],
.canvas-text-element [style*="color:white"],
.canvas-text-element font[color="#ffffff"],
.canvas-text-element font[color="white"],
.canvas-text-element font[color="#fff"] {
  color: inherit !important;
}

/* Guard against dark background from Telegram clipboard */
.canvas-text-element [style*="background-color: rgb(33, 33, 33)"],
.canvas-text-element [style*="background-color: #212121"],
.canvas-text-element [style*="background-color"] {
  background-color: transparent !important;
}

.canvas-text-element:focus,
.canvas-text-element:focus-visible {
  outline: none !important;
  border: none !important;
  box-shadow: none !important;
}
.canvas-text-element p {
  margin: 0.25em 0;
  font-family: inherit !important;
}
.canvas-text-element p:first-child,
.canvas-text-element h1:first-child,
.canvas-text-element h2:first-child,
.canvas-text-element h3:first-child {
  margin-top: 0 !important;
}
.canvas-text-element p:last-child,
.canvas-text-element h1:last-child,
.canvas-text-element h2:last-child,
.canvas-text-element h3:last-child {
  margin-bottom: 0 !important;
}
.canvas-text-element span,
.canvas-text-element div {
  font-family: inherit !important;
}
.canvas-text-element h1,
.canvas-text-element h2,
.canvas-text-element h3 {
  margin: 0.35em 0;
  font-family: inherit !important;
}
.canvas-text-element ol {
  list-style-type: decimal !important;
  padding-left: 1.8em !important;
  margin: 0.3em 0 !important;
  font-family: inherit !important;
}
.canvas-text-element ol ol {
  list-style-type: lower-alpha !important;
  padding-left: 1.6em !important;
  margin: 0.15em 0 !important;
}
.canvas-text-element ol ol ol {
  list-style-type: lower-roman !important;
  padding-left: 1.6em !important;
  margin: 0.15em 0 !important;
}
.canvas-text-element ul {
  list-style-type: disc !important;
  padding-left: 1.8em !important;
  margin: 0.3em 0 !important;
  font-family: inherit !important;
}
.canvas-text-element ul ul {
  list-style-type: circle !important;
  padding-left: 1.6em !important;
  margin: 0.15em 0 !important;
}
.canvas-text-element ul ul ul {
  list-style-type: square !important;
  padding-left: 1.6em !important;
  margin: 0.15em 0 !important;
}
.canvas-text-element li {
  margin: 0.15em 0 !important;
  font-family: inherit !important;
  line-height: inherit !important;
}
</style>
