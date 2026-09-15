<script setup lang="ts">
import { ref, computed } from 'vue'
import { X, ZoomIn, ZoomOut, RotateCcw, Check, BookOpen } from 'lucide-vue-next'
import {
  isCanvasDocumentJson,
  deserializeCanvasDocument,
  convertCanvasDocumentToHtml,
} from '@/modules/contracts/utils/contractCanvasConverter'
import { replaceVariablesInHtml } from '@/modules/contracts/utils/contractVariables'

const props = defineProps<{
  isOpen: boolean
  contractTitle: string
  content: string
  variableValues?: Record<string, string>
}>()

const emit = defineEmits<{
  close: []
  confirmRead: []
}>()

const zoom = ref(1)

function zoomIn() {
  if (zoom.value < 1.6) zoom.value += 0.1
}

function zoomOut() {
  if (zoom.value > 0.6) zoom.value -= 0.1
}

function resetZoom() {
  zoom.value = 1
}

const renderedPages = computed<string[]>(() => {
  const raw = props.content || ''
  if (!raw) return ['<p style="text-align:center;color:#6b7280;margin-top:40px;">Shartnoma matni mavjud emas</p>']

  if (isCanvasDocumentJson(raw)) {
    const doc = deserializeCanvasDocument(raw)
    if (doc && doc.pages?.length) {
      return doc.pages.map(page => {
        return convertCanvasDocumentToHtml(
          { ...doc, pages: [page] },
          props.variableValues
        )
      })
    }
  }

  // Fallback: render HTML formatted paragraphs
  let cleaned = raw
    .replace(/^[\s\S]*?(?:1-BET\s*═{5,}|1-BET\s*={5,}|={10,}\s*1-BET\s*={10,}|═{10,}\s*1-BET\s*═{10,})/i, '')
    .replace(/(?:═{5,}\s*\d+-BET\s*═{5,}|={5,}\s*\d+-BET\s*={5,}|_{10,}\s*\d+-BET\s*_{10,})/gi, '<hr data-page-break="true" />')

  // Substitute variable values if passed
  if (props.variableValues) {
    cleaned = replaceVariablesInHtml(cleaned, props.variableValues)
  }

  const parts = cleaned.split(/<hr[^>]*\/?>/i).map(p => p.trim()).filter(p => p.length > 0)
  return parts.length > 0 ? parts : [cleaned]
})

function handleConfirm() {
  emit('confirmRead')
  emit('close')
}
</script>

<template>
  <div
    v-if="isOpen"
    class="fixed inset-0 z-50 flex items-center justify-center p-2 sm:p-4 bg-black/60 backdrop-blur-xs animate-in fade-in duration-200"
    @click.self="emit('close')"
  >
    <div
      class="bg-white dark:bg-zinc-900 rounded-2xl shadow-2xl w-full max-w-5xl h-[92vh] flex flex-col overflow-hidden border border-zinc-200 dark:border-zinc-800"
    >
      <!-- Header -->
      <div class="px-6 py-4 border-b border-zinc-200 dark:border-zinc-800 flex items-center justify-between bg-zinc-50 dark:bg-zinc-850">
        <div class="flex items-center gap-2.5">
          <div class="w-8 h-8 rounded-lg bg-blue-100 dark:bg-blue-950/60 text-blue-600 dark:text-blue-400 flex items-center justify-center font-bold">
            <BookOpen class="w-4 h-4" />
          </div>
          <div>
            <h3 class="text-sm font-bold text-zinc-900 dark:text-white line-clamp-1">
              {{ contractTitle || "Shartnoma to'liq matni" }}
            </h3>
            <p class="text-xs text-zinc-500">
              Shartnomani imzolashdan oldin barcha sahifalarni diqqat bilan o'qib chiqing.
            </p>
          </div>
        </div>

        <div class="flex items-center gap-2">
          <!-- Zoom controls -->
          <div class="flex items-center gap-1 bg-white dark:bg-zinc-800 border border-zinc-200 dark:border-zinc-700 rounded-xl p-0.5">
            <button
              type="button"
              @click="zoomOut"
              class="p-1.5 hover:bg-zinc-100 dark:hover:bg-zinc-700 rounded-lg text-zinc-600 dark:text-zinc-300 transition-colors"
              title="Zoom out"
            >
              <ZoomOut class="w-4 h-4" />
            </button>
            <span class="text-xs font-semibold px-1 text-zinc-600 dark:text-zinc-300 min-w-[36px] text-center">
              {{ Math.round(zoom * 100) }}%
            </span>
            <button
              type="button"
              @click="zoomIn"
              class="p-1.5 hover:bg-zinc-100 dark:hover:bg-zinc-700 rounded-lg text-zinc-600 dark:text-zinc-300 transition-colors"
              title="Zoom in"
            >
              <ZoomIn class="w-4 h-4" />
            </button>
            <button
              type="button"
              @click="resetZoom"
              class="p-1.5 hover:bg-zinc-100 dark:hover:bg-zinc-700 rounded-lg text-zinc-600 dark:text-zinc-300 transition-colors"
              title="Reset"
            >
              <RotateCcw class="w-3.5 h-3.5" />
            </button>
          </div>

          <button
            type="button"
            @click="emit('close')"
            class="p-2 rounded-xl text-zinc-400 hover:text-zinc-600 dark:hover:text-zinc-200 hover:bg-zinc-100 dark:hover:bg-zinc-800 transition-colors cursor-pointer"
          >
            <X class="w-5 h-5" />
          </button>
        </div>
      </div>

      <!-- Contract A4 Pages Viewer Area -->
      <div class="flex-1 overflow-y-auto bg-zinc-200/70 dark:bg-zinc-950 p-6 flex flex-col items-center gap-6">
        <div
          v-for="(pageHtml, idx) in renderedPages"
          :key="idx"
          class="relative bg-white text-zinc-900 shadow-xl rounded-xs transition-transform origin-top"
          :style="{
            width: '210mm',
            minHeight: '297mm',
            padding: '20mm 20mm',
            transform: `scale(${zoom})`,
            marginBottom: zoom > 1 ? `${(zoom - 1) * 320}px` : '0px',
            fontFamily: 'Times New Roman, serif',
            fontSize: '13px',
            lineHeight: '1.6',
            boxSizing: 'border-box'
          }"
        >
          <!-- Page Number Indicator -->
          <div class="absolute right-4 bottom-3 text-[11px] text-zinc-400">
            Sahifa {{ idx + 1 }} / {{ renderedPages.length }}
          </div>

          <!-- Page HTML Content -->
          <div v-html="pageHtml" class="contract-page-content text-justify" />
        </div>
      </div>

      <!-- Bottom Confirmation Bar -->
      <div class="px-6 py-4 border-t border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-900 flex flex-col sm:flex-row items-center justify-between gap-3">
        <div class="text-xs text-zinc-500">
          Shartnomaning barcha sahifalari bilan tanishib chiqqaningizni tasdiqlang.
        </div>

        <div class="flex items-center gap-3 w-full sm:w-auto">
          <button
            type="button"
            @click="emit('close')"
            class="flex-1 sm:flex-none px-4 py-2.5 rounded-xl border border-zinc-300 dark:border-zinc-700 text-xs font-semibold text-zinc-700 dark:text-zinc-300 hover:bg-zinc-100 dark:hover:bg-zinc-800 transition-colors"
          >
            Yopish
          </button>
          <button
            type="button"
            @click="handleConfirm"
            class="flex-1 sm:flex-none inline-flex items-center justify-center gap-2 px-6 py-2.5 rounded-xl bg-blue-600 hover:bg-blue-700 text-white text-xs font-bold shadow-md shadow-blue-500/20 transition-all cursor-pointer"
          >
            <Check class="w-4 h-4" />
            <span>Shartnomani to'liq o'qib chiqdim</span>
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.contract-page-content :deep(p) {
  margin: 6px 0;
  text-align: justify;
}
.contract-page-content :deep(h1),
.contract-page-content :deep(h2),
.contract-page-content :deep(h3) {
  text-align: center;
  font-weight: bold;
  margin: 14px 0 8px;
}
.contract-page-content :deep(table) {
  width: 100%;
  border-collapse: collapse;
  margin: 10px 0;
}
.contract-page-content :deep(td),
.contract-page-content :deep(th) {
  border: 1px solid #94a3b8;
  padding: 6px 10px;
  font-size: 12px;
}
</style>
