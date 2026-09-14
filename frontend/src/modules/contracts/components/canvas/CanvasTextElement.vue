<script setup lang="ts">
import { ref, computed, watch, nextTick, onMounted } from 'vue'
import type { TextCanvasElement } from '../../types/contractCanvas'
import { cleanClipboardContent } from '../../utils/clipboardUtils'

const props = defineProps<{
  element: TextCanvasElement
  isEditing: boolean
  zoomLevel: number
  variableValues?: Record<string, string>
}>()

const emit = defineEmits<{
  'update:content': [val: string]
  'finish-edit': []
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
    letterSpacing: st.letterSpacing ? `${st.letterSpacing}px` : 'normal',
    padding: st.padding ? `${st.padding * 3.78 * (props.zoomLevel / 100)}px` : '0px',
  }
})

// Replace variables in preview mode
const displayContent = computed(() => {
  let text = props.element.content || ''
  if (!props.isEditing && props.variableValues) {
    for (const [key, val] of Object.entries(props.variableValues)) {
      text = text.split(key).join(val)
    }
  }
  return text
})

// Sync initial DOM content without triggering reactivity reset
onMounted(() => {
  if (editableRef.value) {
    editableRef.value.innerHTML = props.isEditing ? (props.element.content || '') : displayContent.value
  }
})

// Watch external content changes (e.g. Undo/Redo or Variable insertion from outside)
watch(
  () => props.element.content,
  newContent => {
    // If this update was emitted from our own active typing, DO NOT overwrite DOM
    if (newContent === lastEmittedHtml) return
    if (editableRef.value && editableRef.value.innerHTML !== newContent) {
      editableRef.value.innerHTML = newContent || ''
    }
  }
)

// Watch displayContent changes when NOT editing
watch(displayContent, newVal => {
  if (!props.isEditing && editableRef.value) {
    editableRef.value.innerHTML = newVal || ''
  }
})

// Autofocus and place cursor when editing begins; clear selection when editing ends
watch(
  () => props.isEditing,
  (isEdit, oldEdit) => {
    if (isEdit) {
      nextTick(() => {
        if (!editableRef.value) return
        editableRef.value.innerHTML = props.element.content || ''
        lastEmittedHtml = editableRef.value.innerHTML
        editableRef.value.focus()

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
    }
  }
)

function onBlur() {
  if (!editableRef.value) return
  const newHtml = editableRef.value.innerHTML
  lastEmittedHtml = newHtml
  emit('update:content', newHtml)
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
}

function onKeyDown(e: KeyboardEvent) {
  if (e.key === 'Escape') {
    emit('finish-edit')
    try {
      window.getSelection()?.removeAllRanges()
    } catch {}
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
.canvas-text-element ul,
.canvas-text-element ol {
  padding-left: 1.5em;
  margin: 0.3em 0;
  font-family: inherit !important;
}
.canvas-text-element li {
  margin: 0.15em 0;
  font-family: inherit !important;
}
</style>
