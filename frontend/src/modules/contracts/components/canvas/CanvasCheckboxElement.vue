<script setup lang="ts">
import { ref, computed, watch, nextTick } from 'vue'
import { CheckSquare, Square } from 'lucide-vue-next'
import type { CheckboxCanvasElement, TextStyleProps } from '../../types/contractCanvas'

const props = withDefaults(
  defineProps<{
    element: CheckboxCanvasElement
    zoomLevel: number
    isEditing?: boolean
    readonly?: boolean
  }>(),
  {
    isEditing: false,
    readonly: false,
  }
)

const emit = defineEmits<{
  'update:checked': [val: boolean]
  'update:label': [val: string]
  'update:style': [style: TextStyleProps]
  'finish-edit': []
  'auto-resize-width': [widthMm: number]
}>()

const inputRef = ref<HTMLInputElement | null>(null)
const localLabel = ref(props.element.label || '')

watch(
  () => props.element.label,
  (newVal) => {
    localLabel.value = newVal || ''
  }
)

watch(
  () => props.isEditing,
  (isEdit) => {
    if (isEdit) {
      localLabel.value = props.element.label || ''
      nextTick(() => {
        if (inputRef.value) {
          inputRef.value.focus()
          inputRef.value.select()
        }
      })
    }
  },
  { immediate: true }
)

function toggle() {
  if (props.readonly) return
  emit('update:checked', !props.element.checked)
}

function onInput(e: Event) {
  const val = (e.target as HTMLInputElement).value
  localLabel.value = val
  emit('update:label', val)
  autoAdjustWidth(val)
}

function autoAdjustWidth(text: string) {
  const fontSize = effectiveFontSizePt.value
  const isBold = props.element.style?.fontWeight === 'bold' || props.element.style?.fontWeight === 700
  // Roughly 2.3mm per char at 12pt (bold is slightly wider: 2.6mm) plus 14mm for checkbox icon, gap, and padding
  const charWidthMm = (fontSize / 12) * (isBold ? 2.6 : 2.3)
  const neededWidthMm = Math.max(30, Math.ceil(text.length * charWidthMm + 14))
  if (neededWidthMm > props.element.width) {
    emit('auto-resize-width', neededWidthMm)
  }
}

function toggleInlineStyle(prop: 'bold' | 'italic' | 'underline') {
  const currentSt: TextStyleProps = { ...(props.element.style || {}) }
  if (prop === 'bold') {
    currentSt.fontWeight = currentSt.fontWeight === 'bold' || currentSt.fontWeight === 700 ? 'normal' : 'bold'
  } else if (prop === 'italic') {
    currentSt.fontStyle = currentSt.fontStyle === 'italic' ? 'normal' : 'italic'
  } else if (prop === 'underline') {
    const cur = currentSt.textDecoration || ''
    currentSt.textDecoration = cur.includes('underline')
      ? cur.replace('underline', '').trim() || 'none'
      : (cur === 'none' || !cur ? 'underline' : `${cur} underline`)
  }
  emit('update:style', currentSt)
}

function onKeyDown(e: KeyboardEvent) {
  if (e.key === 'Enter' || e.key === 'Escape') {
    e.preventDefault()
    e.stopPropagation()
    emit('finish-edit')
    return
  }
  const isMod = e.ctrlKey || e.metaKey
  if (isMod && (e.key === 'b' || e.key === 'B')) {
    e.preventDefault()
    e.stopPropagation()
    toggleInlineStyle('bold')
    return
  }
  if (isMod && (e.key === 'i' || e.key === 'I')) {
    e.preventDefault()
    e.stopPropagation()
    toggleInlineStyle('italic')
    return
  }
  if (isMod && (e.key === 'u' || e.key === 'U')) {
    e.preventDefault()
    e.stopPropagation()
    toggleInlineStyle('underline')
    return
  }
  e.stopPropagation()
}

function onBlur() {
  emit('finish-edit')
}

// Typography & Zoom scaling
const effectiveFontSizePt = computed(() => {
  return props.element.style?.fontSize || props.element.fontSize || 12
})

const scaledFontSizePx = computed(() => {
  return effectiveFontSizePt.value * (4 / 3) * (props.zoomLevel / 100)
})

// Box size scales proportionally with the font size and zoom level!
const boxSizePx = computed(() => {
  return Math.max(6, Math.round(scaledFontSizePx.value * 0.95))
})

const boxStrokeWidth = computed(() => {
  if (boxSizePx.value < 10) return 1.2
  if (boxSizePx.value < 14) return 1.6
  return 2
})

const scaledGapPx = computed(() => {
  return Math.max(2, Math.round(scaledFontSizePx.value * 0.35))
})

const textStyle = computed(() => {
  const st = props.element.style || {}
  const color = st.color || props.element.color || '#111827'
  const fontFamily = st.fontFamily || `'Times New Roman', Times, serif`
  const fontWeight = st.fontWeight || 'normal'
  const fontStyle = st.fontStyle || 'normal'
  const textDecoration = st.textDecoration || 'none'
  const letterSpacing = typeof st.letterSpacing === 'number' && st.letterSpacing !== 0
    ? `${st.letterSpacing * (props.zoomLevel / 100)}px`
    : 'normal'
  const backgroundColor = st.backgroundColor && st.backgroundColor !== '#ffffff'
    ? st.backgroundColor
    : 'transparent'
  const textTransform = (st.textTransform as any) || 'none'

  return {
    fontSize: `${scaledFontSizePx.value}px`,
    color,
    fontFamily,
    fontWeight,
    fontStyle,
    textDecoration,
    letterSpacing,
    backgroundColor,
    textTransform,
  }
})
</script>

<template>
  <div
    class="canvas-checkbox-element w-full h-full flex items-center select-none"
    :style="{
      fontFamily: textStyle.fontFamily,
      gap: `${scaledGapPx}px`,
    }"
  >
    <!-- Checkbox Icon Toggle Button (Scales dynamically with zoom & font-size) -->
    <div
      class="shrink-0 rounded transition-transform pointer-events-auto flex items-center justify-center"
      :class="readonly ? 'cursor-default' : 'cursor-pointer hover:scale-110 hover:bg-blue-50 dark:hover:bg-blue-950/60'"
      :style="{
        width: `${boxSizePx}px`,
        height: `${boxSizePx}px`,
      }"
      :title="element.checked ? 'Holat: Belgilangan (o\'zgartirish uchun bosing)' : 'Holat: Belgilanmagan (o\'zgartirish uchun bosing)'"
      @click.stop="toggle"
      @pointerdown.stop
    >
      <CheckSquare
        v-if="element.checked"
        :size="boxSizePx"
        :stroke-width="boxStrokeWidth"
        :style="{ width: `${boxSizePx}px`, height: `${boxSizePx}px` }"
        class="text-blue-600 dark:text-blue-400"
      />
      <Square
        v-else
        :size="boxSizePx"
        :stroke-width="boxStrokeWidth"
        :style="{ width: `${boxSizePx}px`, height: `${boxSizePx}px` }"
        class="text-zinc-400 dark:text-zinc-500"
      />
    </div>

    <!-- Editing Mode: Inline Text Input -->
    <div v-if="isEditing && !readonly" class="flex-1 min-w-0 pointer-events-auto">
      <input
        ref="inputRef"
        type="text"
        :value="localLabel"
        @input="onInput"
        @keydown="onKeyDown"
        @blur="onBlur"
        @click.stop
        @pointerdown.stop
        placeholder="Tanlov varianti..."
        class="w-full bg-transparent border-b border-dashed border-blue-500 focus:outline-none leading-tight p-0 m-0"
        :style="textStyle"
      />
    </div>

    <!-- Display Mode: Static Label -->
    <span
      v-else
      class="leading-tight select-none truncate flex-1 min-w-0"
      :class="readonly ? '' : 'cursor-text'"
      :style="textStyle"
      title="Tahrirlash uchun ikki marta bosing"
    >
      {{ element.label || 'Tanlov varianti' }}
    </span>
  </div>
</template>
