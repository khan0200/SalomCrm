<script setup lang="ts">
import { ref, computed } from 'vue'
import {
  Edit3,
  X,
  Download,
  Loader2,
  ChevronDown,
  FileText,
  KeyRound,
  Copy,
  RotateCcw,
  Ban,
  Trash2,
  Check
} from 'lucide-vue-next'
import BaseModal from '@/components/common/BaseModal.vue'
import type { Contract } from '@/api/contracts'
import { downloadContractAsPdf } from '@/modules/contracts/utils/contractPdf'
import {
  isCanvasDocumentJson,
  deserializeCanvasDocument,
  convertCanvasDocumentToHtml,
} from '@/modules/contracts/utils/contractCanvasConverter'
import { buildVariableValues, replaceVariablesInHtml } from '@/modules/contracts/utils/contractVariables'

const props = defineProps<{
  isOpen: boolean
  contract: Contract | null
}>()

const emit = defineEmits<{
  close: []
  edit: [contract: Contract]
  assign: [contract: Contract]
  reject: [contract: Contract]
  regenerate: [contract: Contract]
  duplicate: [contract: Contract]
  delete: [contract: Contract]
}>()

const copyFeedback = ref(false)
async function copyCodeToClipboard(code: string) {
  try {
    await navigator.clipboard.writeText(code)
    copyFeedback.value = true
    setTimeout(() => {
      copyFeedback.value = false
    }, 2000)
  } catch (err) {
    console.error('Failed to copy', err)
  }
}

const isDownloadingPdf = ref(false)
const showDownloadMenu = ref(false)

const isCanvas = computed(() => isCanvasDocumentJson(props.contract?.content || ''))

const contractVariables = computed<Record<string, string>>(() => {
  if (!props.contract) return {}
  return buildVariableValues(props.contract, {
    contractNumber: props.contract.student_id_assigned || props.contract.contract_number,
    templateName: props.contract.tariff_name || props.contract.title,
    price: props.contract.tariff_price ?? undefined,
    discount: props.contract.discount ?? undefined,
    signatureData: props.contract.signature_data || undefined,
    verificationCode: props.contract.verification_code || undefined,
    office: props.contract.office || props.contract.tenant_office_name || undefined,
    educationLevel: props.contract.education_level || undefined,
  })
})

const splitPages = computed<string[]>(() => {
  const raw = props.contract?.content
  if (!raw) return []

  if (isCanvasDocumentJson(raw)) {
    const doc = deserializeCanvasDocument(raw)
    if (doc) {
      return doc.pages.map(p => {
        return convertCanvasDocumentToHtml({
          ...doc,
          pages: [p],
        }, contractVariables.value)
      })
    }
  }

  // Standardize any ASCII page markers
  let cleaned = raw
    .replace(/^[\s\S]*?(?:1-BET\s*═{5,}|1-BET\s*={5,}|={10,}\s*1-BET\s*={10,}|═{10,}\s*1-BET\s*═{10,})/i, '')
    .replace(/(?:═{5,}\s*\d+-BET\s*═{5,}|={5,}\s*\d+-BET\s*={5,}|_{10,}\s*\d+-BET\s*_{10,})/gi, '<hr data-page-break="true" />')
  
  cleaned = replaceVariablesInHtml(cleaned, contractVariables.value)
  const parts = cleaned.split(/<hr[^>]*\/?>/i).map(p => p.trim()).filter(p => p.length > 0)
  return parts.length > 0 ? parts : [cleaned]
})

async function handleDownload(format: 'pdf' | 'doc' = 'pdf') {
  if (!props.contract || isDownloadingPdf.value) return
  const safeTitle = `${props.contract.contract_number}_${props.contract.student_name || props.contract.full_name || props.contract.title}`.replace(/[/\\?%*:|"<>]/g, '_')
  const rawContent = props.contract.content || ''

  if (format === 'doc') {
    downloadWordDoc(safeTitle, rawContent)
    return
  }

  isDownloadingPdf.value = true
  try {
    const verificationMeta = {
      contractNumber: props.contract.contract_number || props.contract.student_id_assigned || undefined,
      studentId: props.contract.student_id_assigned || undefined,
      studentName: props.contract.full_name || props.contract.student_name || undefined,
      verifiedAt: props.contract.verified_at ? new Date(props.contract.verified_at).toLocaleDateString('uz-UZ') : undefined,
      status: props.contract.status,
    }
    await downloadContractAsPdf(
      safeTitle,
      rawContent,
      { top: 20, right: 15, bottom: 20, left: 25 },
      contractVariables.value,
      props.contract.signature_data || undefined,
      verificationMeta
    )
  } catch (err) {
    console.error('Failed to download PDF:', err)
    downloadWordDoc(safeTitle, rawContent)
  } finally {
    isDownloadingPdf.value = false
  }
}

function downloadWordDoc(safeTitle: string, rawContent: string) {
  let htmlBody = rawContent.replace(/<hr[^>]*\/?>/gi, '<br clear="all" style="page-break-before:always;mso-break-type:section-break" />')
  
  const content = `<!DOCTYPE html>
<html xmlns:o='urn:schemas-microsoft-com:office:office' 
      xmlns:w='urn:schemas-microsoft-com:office:word' 
      xmlns='http://www.w3.org/TR/REC-html40'>
<head>
<meta charset='utf-8'>
<title>${safeTitle}</title>
<!--[if gte mso 9]>
<xml>
<w:WordDocument>
<w:View>Print</w:View>
<w:Zoom>100</w:Zoom>
<w:DoNotOptimizeForBrowser/>
</w:WordDocument>
</xml>
<![endif]-->
<style>
@page Section1 {
  size: 595.35pt 841.95pt;
  margin: 54pt 54pt 54pt 54pt;
}
div.Section1 { page: Section1; }
body { font-family: 'Times New Roman', Georgia, serif; font-size: 11pt; line-height: 1.5; color: #000; }
table { width: 100%; border-collapse: collapse; margin: 10pt 0; }
table, th, td { border: 1px solid #333; padding: 5pt; }
p { margin: 6pt 0; text-align: justify; }
h1, h2, h3 { font-family: 'Times New Roman', Georgia, serif; text-align: center; font-weight: bold; margin: 12pt 0 6pt; }
</style>
</head>
<body>
<div class="Section1">
${htmlBody}
</div>
</body>
</html>`
  const blob = new Blob(['\ufeff', content], { type: 'application/msword;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `${safeTitle}.doc`
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  URL.revokeObjectURL(url)
}
</script>

<template>
  <BaseModal
    :is-open="isOpen"
    title="Contract Preview"
    :subtitle="contract ? `${contract.contract_number} — ${contract.title}` : ''"
    max-width="max-w-4xl"
    @close="emit('close')"
  >
    <!-- Modal Action Buttons Bar -->
    <div class="px-6 py-2.5 bg-zinc-50 dark:bg-zinc-850 border-b border-zinc-200 dark:border-zinc-800 flex flex-wrap items-center justify-between gap-3 no-print">
      <!-- Left: Status & Metadata -->
      <div class="flex items-center gap-2.5 flex-wrap">
        <span
          v-if="contract?.status"
          class="px-2.5 py-0.5 rounded-full text-[11px] font-medium border uppercase tracking-wider"
          :class="[
            contract.status === 'completed'
              ? 'bg-emerald-500/10 text-emerald-700 dark:text-emerald-400 border-emerald-500/20'
              : contract.status === 'verified'
              ? 'bg-emerald-500/10 text-emerald-700 dark:text-emerald-400 border-emerald-500/20'
              : contract.status === 'signed'
              ? 'bg-sky-500/10 text-sky-700 dark:text-sky-400 border-sky-500/20'
              : contract.status === 'pending'
              ? 'bg-amber-500/10 text-amber-700 dark:text-amber-400 border-amber-500/20'
              : contract.status === 'rejected'
              ? 'bg-rose-500/10 text-rose-700 dark:text-rose-400 border-rose-500/20'
              : 'bg-zinc-500/10 text-zinc-600 dark:text-zinc-400 border-zinc-500/20'
          ]"
        >
          {{ contract.status }}
        </span>

        <span v-if="contract?.student_id_assigned" class="text-xs font-mono text-zinc-500 dark:text-zinc-400">
          ID: <strong class="text-zinc-800 dark:text-zinc-200">{{ contract.student_id_assigned }}</strong>
        </span>

        <span class="text-xs text-zinc-400">
          v{{ contract?.version || 1 }}
        </span>
      </div>

      <!-- Right: Actions Toolbar -->
      <div class="flex items-center gap-2 flex-wrap" v-if="contract">
        <!-- Bekor qilish (Reject) -->
        <button
          v-if="contract.status === 'pending'"
          type="button"
          @click="emit('reject', contract)"
          class="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-rose-200 dark:border-rose-900/60 text-rose-600 dark:text-rose-400 hover:bg-rose-50 dark:hover:bg-rose-950/40 text-xs font-medium transition-colors cursor-pointer"
          title="Arizani bekor qilish"
        >
          <Ban class="w-3.5 h-3.5" />
          <span>Bekor qilish</span>
        </button>

        <!-- Yuklab olish (Faqat PDF) -->
        <button
          type="button"
          @click="handleDownload('pdf')"
          :disabled="isDownloadingPdf"
          class="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-zinc-200 dark:border-zinc-700 bg-white dark:bg-zinc-800 text-xs font-medium text-zinc-700 dark:text-zinc-200 hover:bg-zinc-50 dark:hover:bg-zinc-750 transition-colors shadow-2xs cursor-pointer"
          title="PDF yuklab olish"
        >
          <Loader2 v-if="isDownloadingPdf" class="w-3.5 h-3.5 animate-spin text-blue-500" />
          <Download v-else class="w-3.5 h-3.5 text-zinc-500" />
          <span>Yuklab olish (PDF)</span>
        </button>
      </div>
    </div>

    <!-- Scrollable Multi-Page A4 Document Sheet View -->
    <div class="p-4 sm:p-8 bg-zinc-100 dark:bg-zinc-950 max-h-[78vh] overflow-y-auto flex flex-col items-center gap-8">
      <template v-if="splitPages.length > 0">
        <div
          v-for="(pageHtml, pageIndex) in splitPages"
          :key="pageIndex"
          class="preview-a4-sheet relative w-full max-w-[794px] bg-white text-zinc-900 shadow-xl border border-zinc-200/90 font-serif rounded-xs"
          :class="isCanvas ? 'p-0 min-h-[1123px] overflow-hidden' : 'p-8 sm:p-14 min-h-[1050px]'"
          style="font-family: 'Times New Roman', Times, serif;"
        >
          <!-- Top Page badge -->
          <div class="absolute top-4 right-6 text-[10.5px] uppercase font-bold tracking-widest text-zinc-400 select-none no-print">
            Page {{ pageIndex + 1 }} / {{ splitPages.length }}
          </div>

          <div v-html="pageHtml" />

          <!-- Bottom page footer -->
          <div class="absolute bottom-5 inset-x-0 text-center text-[11px] text-zinc-400 select-none font-serif tracking-widest no-print">
            — {{ pageIndex + 1 }} —
          </div>
        </div>
      </template>
      <div v-else class="text-zinc-400 py-12 text-sm">
        No content available
      </div>
    </div>
  </BaseModal>
</template>

<style>
.preview-a4-sheet {
  font-family: 'Times New Roman', Times, serif !important;
  font-size: 13px;
  line-height: 1.6;
}

.preview-a4-sheet,
.preview-a4-sheet * {
  font-family: 'Times New Roman', Times, serif !important;
}

.preview-a4-sheet p {
  margin-top: 0.4rem;
  margin-bottom: 0.4rem;
}

.preview-a4-sheet table {
  width: 100%;
  border-collapse: collapse;
  margin: 0.8rem 0;
}

.preview-a4-sheet table th,
.preview-a4-sheet table td {
  border: 1px solid #71717a;
  padding: 6px 10px;
  vertical-align: top;
  font-size: 12px;
}

.preview-a4-sheet table th {
  background-color: #f4f4f5;
  font-weight: 700;
}

@media print {
  .preview-a4-sheet {
    page-break-after: always !important;
    break-after: page !important;
    box-shadow: none !important;
    border: none !important;
    margin: 0 !important;
    padding: 15mm !important;
    width: 100% !important;
    min-height: auto !important;
  }
}
</style>
