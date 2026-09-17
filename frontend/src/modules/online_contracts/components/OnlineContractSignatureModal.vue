<script setup lang="ts">
import { ref, watch, nextTick, onMounted, onBeforeUnmount } from 'vue'
import { X, Eraser, Check } from 'lucide-vue-next'

const props = defineProps<{
  isOpen: boolean
  modelValue?: string
}>()

const emit = defineEmits<{
  close: []
  confirm: [signatureData: string]
  'update:modelValue': [signatureData: string]
}>()

const canvasRef = ref<HTMLCanvasElement | null>(null)
const isDrawing = ref(false)
const hasSignature = ref(false)
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

  const rect = canvas.getBoundingClientRect()
  if (rect.width === 0 || rect.height === 0) return

  const dpr = Math.max(window.devicePixelRatio || 1, 2)
  canvas.width = rect.width * dpr
  canvas.height = rect.height * dpr

  ctx = canvas.getContext('2d')
  if (!ctx) return

  ctx.scale(dpr, dpr)
  ctx.strokeStyle = '#0f172a'
  ctx.lineWidth = strokeWidth.value
  ctx.lineCap = 'round'
  ctx.lineJoin = 'round'

  if (props.modelValue) {
    const img = new Image()
    img.onload = () => {
      ctx?.drawImage(img, 0, 0, rect.width, rect.height)
      hasSignature.value = true
    }
    img.src = props.modelValue
  } else {
    hasSignature.value = false
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
}

function clearCanvas() {
  const canvas = canvasRef.value
  if (!canvas || !ctx) return
  const rect = canvas.getBoundingClientRect()
  ctx.clearRect(0, 0, rect.width, rect.height)
  hasSignature.value = false
}

function handleConfirm() {
  const canvas = canvasRef.value
  if (!canvas || !hasSignature.value) return
  const dataUrl = canvas.toDataURL('image/png')
  emit('update:modelValue', dataUrl)
  emit('confirm', dataUrl)
  emit('close')
}

watch(
  () => props.isOpen,
  (open) => {
    if (open) {
      nextTick(() => {
        initCanvas()
      })
    }
  }
)

function onResize() {
  if (props.isOpen) {
    initCanvas()
  }
}

onMounted(() => {
  if (props.isOpen) {
    initCanvas()
  }
  window.addEventListener('resize', onResize)
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', onResize)
})
</script>

<template>
  <Teleport to="body">
    <div
      v-if="isOpen"
      class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-xs"
      @click.self="emit('close')"
    >
      <!-- Modal Box: 500px by 500px on desktop, responsive on smaller mobile -->
      <div
        class="relative w-full max-w-[500px] h-[500px] max-h-[92vh] bg-white dark:bg-zinc-900 border border-zinc-300 dark:border-zinc-800 rounded-2xl shadow-2xl flex flex-col overflow-hidden animate-in fade-in zoom-in-95 duration-200"
      >
        <!-- Modal Header -->
        <div class="px-5 py-4 border-b border-zinc-200 dark:border-zinc-800 flex items-center justify-between shrink-0">
          <div>
            <h3 class="text-sm sm:text-base font-bold text-black dark:text-white tracking-tight">
              Shartnomani imzoyingiz bilan tasdiqlang
            </h3>
            <p class="text-xs text-zinc-600 dark:text-zinc-400 mt-0.5">
              Quyidagi maydonga sichqoncha yoki barmog'ingiz bilan imzo cheking
            </p>
          </div>

          <button
            type="button"
            @click="emit('close')"
            class="p-1.5 rounded-lg text-zinc-500 hover:text-black dark:hover:text-white hover:bg-zinc-100 dark:hover:bg-zinc-800 transition-colors cursor-pointer"
          >
            <X class="w-5 h-5" />
          </button>
        </div>

        <!-- Canvas Body (flex-1 to fill the 500px modal) -->
        <div class="p-4 flex-1 flex flex-col min-h-0">
          <!-- Stroke thickness control -->
          <div class="flex items-center gap-2.5 mb-2.5 px-0.5 shrink-0">
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

          <div class="relative flex-1 w-full bg-zinc-50/80 dark:bg-zinc-950/70 border-2 border-dashed border-zinc-400 dark:border-zinc-700 rounded-xl overflow-hidden touch-none cursor-default">
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

            <!-- Watermark at left bottom corner -->
            <div
              v-if="!hasSignature"
              class="absolute left-4 bottom-3.5 pointer-events-none select-none"
            >
              <span class="text-xs font-semibold tracking-wide text-zinc-500 dark:text-zinc-400">Draw Signature</span>
            </div>

            <!-- Clear button inside canvas top-right -->
            <button
              type="button"
              @click="clearCanvas"
              class="absolute top-3 right-3 inline-flex items-center gap-1.5 px-2.5 py-1 text-xs font-bold text-black dark:text-white hover:text-red-600 dark:hover:text-red-400 bg-white/90 dark:bg-zinc-900/90 hover:bg-white dark:hover:bg-zinc-850 rounded-md transition-colors cursor-pointer border border-zinc-300 dark:border-zinc-700 shadow-2xs backdrop-blur-xs select-none"
            >
              <Eraser class="w-3.5 h-3.5" />
              <span>Tozalash</span>
            </button>
          </div>
        </div>

        <!-- Modal Footer -->
        <div class="px-5 py-3.5 bg-zinc-50/70 dark:bg-zinc-950/50 border-t border-zinc-200 dark:border-zinc-800 flex items-center justify-between shrink-0">
          <button
            type="button"
            @click="emit('close')"
            class="px-4 py-2 text-xs font-bold text-zinc-700 dark:text-zinc-300 hover:text-black dark:hover:text-white rounded-lg hover:bg-zinc-200/60 dark:hover:bg-zinc-800 transition-colors cursor-pointer"
          >
            Bekor qilish
          </button>

          <button
            type="button"
            @click="handleConfirm"
            :disabled="!hasSignature"
            class="inline-flex items-center gap-2 px-5 py-2.5 rounded-lg bg-black hover:bg-zinc-800 text-white dark:bg-white dark:hover:bg-zinc-200 dark:text-black text-xs font-bold shadow-xs transition-all cursor-pointer active:scale-98 disabled:opacity-40 disabled:cursor-not-allowed"
          >
            <Check class="w-3.5 h-3.5" />
            <span>Tasdiqlash va davom etish</span>
          </button>
        </div>
      </div>
    </div>
  </Teleport>
</template>
