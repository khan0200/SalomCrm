<script setup lang="ts">
import { ref, watch, onMounted, onBeforeUnmount } from 'vue'
import { Eraser, Check, AlertCircle } from 'lucide-vue-next'
import { trimSignatureCanvas } from '../utils/trimSignature'

const props = defineProps<{
  modelValue?: string
}>()

const emit = defineEmits<{
  'update:modelValue': [value: string]
  'change': [value: string]
}>()

const canvasRef = ref<HTMLCanvasElement | null>(null)
const isDrawing = ref(false)
const hasSignature = ref(false)
const previewDataUrl = ref<string>(props.modelValue || '')
// Original default was 2.5; 2.9 is ~15% thicker (within the requested 10-20% range).
const strokeWidth = ref(2.9)

let ctx: CanvasRenderingContext2D | null = null
let lastX = 0
let lastY = 0

watch(strokeWidth, (val) => {
  if (ctx) ctx.lineWidth = val
})

function initCanvas() {
  const canvas = canvasRef.value
  if (!canvas) return

  // Set internal resolution higher than display size for crisp PDF export
  const rect = canvas.getBoundingClientRect()
  const dpr = Math.max(window.devicePixelRatio || 1, 2)
  canvas.width = rect.width * dpr
  canvas.height = rect.height * dpr

  ctx = canvas.getContext('2d')
  if (!ctx) return

  ctx.scale(dpr, dpr)
  ctx.strokeStyle = '#1e3a8a'
  ctx.lineWidth = strokeWidth.value
  ctx.lineCap = 'round'
  ctx.lineJoin = 'round'

  const currentSrc = props.modelValue || previewDataUrl.value
  if (currentSrc) {
    const img = new Image()
    img.onload = () => {
      // A previously-trimmed signature is small and rarely square - draw it
      // centered at its own aspect ratio instead of stretching it to fill
      // the whole pad.
      const scale = Math.min(rect.width / img.width, rect.height / img.height, 1)
      const drawWidth = img.width * scale
      const drawHeight = img.height * scale
      const offsetX = (rect.width - drawWidth) / 2
      const offsetY = (rect.height - drawHeight) / 2
      ctx?.drawImage(img, offsetX, offsetY, drawWidth, drawHeight)
      hasSignature.value = true
    }
    img.src = currentSrc
  }
}

function getPos(e: MouseEvent | TouchEvent): { x: number; y: number } {
  const canvas = canvasRef.value
  if (!canvas) return { x: 0, y: 0 }
  const rect = canvas.getBoundingClientRect()
  if ('touches' in e && e.touches.length > 0) {
    return {
      x: e.touches[0].clientX - rect.left,
      y: e.touches[0].clientY - rect.top,
    }
  }
  const me = e as MouseEvent
  return {
    x: me.clientX - rect.left,
    y: me.clientY - rect.top,
  }
}

function startDrawing(e: MouseEvent | TouchEvent) {
  e.preventDefault()
  isDrawing.value = true
  const pos = getPos(e)
  lastX = pos.x
  lastY = pos.y
}

function draw(e: MouseEvent | TouchEvent) {
  if (!isDrawing.value || !ctx) return
  e.preventDefault()
  const pos = getPos(e)

  ctx.beginPath()
  ctx.moveTo(lastX, lastY)
  ctx.lineTo(pos.x, pos.y)
  ctx.stroke()

  lastX = pos.x
  lastY = pos.y
  hasSignature.value = true
}

function stopDrawing(e?: MouseEvent | TouchEvent) {
  if (!isDrawing.value) return
  if (e) e.preventDefault()
  isDrawing.value = false
  exportSignature()
}

function clearCanvas() {
  const canvas = canvasRef.value
  if (!canvas || !ctx) return
  const rect = canvas.getBoundingClientRect()
  ctx.clearRect(0, 0, rect.width, rect.height)
  hasSignature.value = false
  previewDataUrl.value = ''
  emit('update:modelValue', '')
  emit('change', '')
}

function exportSignature() {
  const canvas = canvasRef.value
  if (!canvas || !hasSignature.value) return
  // Trim to the ink's bounding box so the signature lands in the same spot
  // on the document regardless of where it was drawn on the pad.
  const dataUrl = trimSignatureCanvas(canvas)
  previewDataUrl.value = dataUrl
  emit('update:modelValue', dataUrl)
  emit('change', dataUrl)
}

onMounted(() => {
  initCanvas()
  window.addEventListener('resize', initCanvas)
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', initCanvas)
})
</script>

<template>
  <div class="electronic-signature-card bg-white dark:bg-zinc-900 border border-zinc-300 dark:border-zinc-800 rounded-xl p-5 shadow-xs">
    <div class="flex items-center justify-between mb-3">
      <div>
        <h4 class="text-sm font-bold text-black dark:text-white flex items-center gap-2">
          <span>Elektron Imzo / Electronic Signature</span>
          <span v-if="hasSignature" class="inline-flex items-center gap-1 text-[11px] font-bold px-2 py-0.5 rounded-full bg-emerald-100 text-emerald-800 dark:bg-emerald-950/60 dark:text-emerald-300 border border-emerald-500/20">
            <Check class="w-3 h-3" /> Imzolandi
          </span>
        </h4>
        <p class="text-xs text-zinc-700 dark:text-zinc-300 font-medium mt-0.5">
          Quyidagi maydonga sichqoncha, barmog'ingiz yoki stilus bilan imzo cheking.
        </p>
      </div>

      <button
        type="button"
        @click="clearCanvas"
        class="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-bold text-black dark:text-white hover:text-red-600 dark:hover:text-red-400 hover:bg-zinc-100 dark:hover:bg-zinc-800 rounded-lg transition-colors cursor-pointer border border-zinc-300 dark:border-zinc-700 shadow-2xs"
      >
        <Eraser class="w-3.5 h-3.5" />
        <span>Tozalash</span>
      </button>
    </div>

    <!-- Stroke thickness control -->
    <div class="flex items-center gap-2.5 mb-2.5">
      <span class="text-xs font-semibold text-zinc-600 dark:text-zinc-400 shrink-0">Chiziq qalinligi</span>
      <input
        type="range"
        min="1"
        max="6"
        step="0.5"
        v-model.number="strokeWidth"
        class="flex-1 h-1.5 accent-black dark:accent-white cursor-pointer"
      />
      <span class="text-xs font-mono font-bold text-zinc-500 dark:text-zinc-400 w-7 text-right shrink-0">{{ strokeWidth }}</span>
    </div>

    <!-- Canvas drawing box -->
    <div class="relative w-full aspect-square bg-zinc-50/80 dark:bg-zinc-950/70 border-2 border-dashed border-zinc-400 dark:border-zinc-700 rounded-xl overflow-hidden touch-none cursor-default">
      <canvas
        ref="canvasRef"
        class="w-full h-full block"
        @mousedown="startDrawing"
        @mousemove="draw"
        @mouseup="stopDrawing"
        @mouseleave="stopDrawing"
        @touchstart="startDrawing"
        @touchmove="draw"
        @touchend="stopDrawing"
        @touchcancel="stopDrawing"
      />

      <!-- Placeholder watermark when empty -->
      <div
        v-if="!hasSignature"
        class="absolute left-4 bottom-3.5 pointer-events-none select-none"
      >
        <span class="text-xs font-semibold tracking-wide text-zinc-500 dark:text-zinc-400">Draw Signature</span>
      </div>
    </div>

    <div class="mt-3 flex items-center justify-between text-xs">
      <span class="flex items-center gap-1.5 text-amber-700 dark:text-amber-400 font-medium">
        <AlertCircle class="w-3.5 h-3.5 shrink-0" />
        <span>Imzo shartnoma tasdiqlangach o'zgarmas holatda saqlanadi.</span>
      </span>

      <span v-if="hasSignature" class="text-emerald-700 dark:text-emerald-400 font-bold">
        ✓ Imzo saqlandi
      </span>
    </div>
  </div>
</template>
