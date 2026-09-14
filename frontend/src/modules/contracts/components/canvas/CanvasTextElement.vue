<script setup lang="ts">
import { ref, computed, watch, nextTick, onMounted } from 'vue'
import type { TextCanvasElement } from '../../types/contractCanvas'

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
    color: st.color || '#111827',
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

// Autofocus and place cursor at end when editing begins; clear selection when editing ends
watch(
  () => props.isEditing,
  (isEdit, oldEdit) => {
    if (isEdit) {
      nextTick(() => {
        if (!editableRef.value) return
        editableRef.value.innerHTML = props.element.content || ''
        lastEmittedHtml = editableRef.value.innerHTML
        editableRef.value.focus()
        // Place caret at end of text
        const range = window.document.createRange()
        const sel = window.getSelection()
        range.selectNodeContents(editableRef.value)
        range.collapse(false)
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
