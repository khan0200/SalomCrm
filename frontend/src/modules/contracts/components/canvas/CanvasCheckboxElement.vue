<script setup lang="ts">
import { ref, computed, watch, nextTick } from 'vue'
import { CheckSquare, Square } from 'lucide-vue-next'
import type { CheckboxCanvasElement } from '../../types/contractCanvas'

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
  const fontSize = props.element.fontSize || 12
  // Roughly 2.3mm per char at 12pt plus 14mm for checkbox icon, gap, and padding
  const charWidthMm = (fontSize / 12) * 2.3
  const neededWidthMm = Math.max(35, Math.ceil(text.length * charWidthMm + 14))
  if (neededWidthMm > props.element.width) {
    emit('auto-resize-width', neededWidthMm)
  }
}

function onKeyDown(e: KeyboardEvent) {
  e.stopPropagation()
  if (e.key === 'Enter' || e.key === 'Escape') {
    e.preventDefault()
    emit('finish-edit')
  }
}

function onBlur() {
  emit('finish-edit')
}

const scaledFontSizePx = computed(() => {
  const fontSizePt = props.element.fontSize || 12
  return fontSizePt * (4 / 3) * (props.zoomLevel / 100)
})
</script>

<template>
  <div
    class="canvas-checkbox-element w-full h-full flex items-center gap-2 font-serif select-none"
    style="font-family: 'Times New Roman', Times, serif;"
  >
    <!-- Checkbox Icon Toggle Button -->
    <div
      class="shrink-0 text-blue-600 dark:text-blue-400 p-0.5 rounded transition-transform pointer-events-auto"
      :class="readonly ? 'cursor-default' : 'cursor-pointer hover:scale-110 hover:bg-blue-50 dark:hover:bg-blue-950/60'"
      :title="element.checked ? 'Holat: Belgilangan (o\'zgartirish uchun bosing)' : 'Holat: Belgilanmagan (o\'zgartirish uchun bosing)'"
      @click.stop="toggle"
      @pointerdown.stop
    >
      <CheckSquare v-if="element.checked" class="w-4 h-4" />
      <Square v-else class="w-4 h-4 text-zinc-400" />
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
        class="w-full bg-transparent border-b border-dashed border-blue-500 focus:outline-none leading-tight font-medium text-zinc-900 dark:text-zinc-100 p-0 m-0"
        :style="{
          fontSize: `${scaledFontSizePx}px`,
          color: element.color || '#111827',
          fontFamily: `'Times New Roman', Times, serif`,
        }"
      />
    </div>

    <!-- Display Mode: Static Label -->
    <span
      v-else
      class="text-zinc-900 dark:text-zinc-100 leading-tight font-medium select-none truncate flex-1 min-w-0"
      :class="readonly ? '' : 'cursor-text'"
      :style="{
        fontSize: `${scaledFontSizePx}px`,
        color: element.color || '#111827',
        fontFamily: `'Times New Roman', Times, serif`,
      }"
      title="Tahrirlash uchun ikki marta bosing"
    >
      {{ element.label || 'Tanlov varianti' }}
    </span>
  </div>
</template>
