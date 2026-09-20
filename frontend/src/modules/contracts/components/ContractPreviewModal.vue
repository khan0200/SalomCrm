<script setup lang="ts">
import { ref, computed, watch } from 'vue'
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
  Check,
  AlertCircle,
  Archive,
  ArchiveRestore,
} from 'lucide-vue-next'
import BaseModal from '@/components/common/BaseModal.vue'
import { useAuthStore } from '@/stores/auth'
import { contractsApi, type Contract } from '@/api/contracts'
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

const authStore = useAuthStore()

const emit = defineEmits<{
  close: []
  edit: [contract: Contract]
  assign: [contract: Contract]
  reject: [contract: Contract]
  regenerate: [contract: Contract]
  duplicate: [contract: Contract]
  delete: [contract: Contract]
  archive: [contract: Contract]
  unarchive: [contract: Contract]
}>()

const detailedContract = ref<Contract | null>(null)
const isLoadingDetail = ref(false)

watch(
  () => [props.isOpen, props.contract?.id],
  async ([isOpen, contractId]) => {
    if (!isOpen || !contractId) {
      detailedContract.value = null
      return
    }
    const current = props.contract
    if (current && current.content) {
      detailedContract.value = current
      return
    }
    isLoadingDetail.value = true
    try {
      const full = await contractsApi.getContract(String(contractId))
      detailedContract.value = full
    } catch (err) {
      console.error('Failed to load contract detail for preview:', err)
      detailedContract.value = current
    } finally {
      isLoadingDetail.value = false
    }
  },
  { immediate: true }
)

const activeContract = computed<Contract | null>(() => {
  return detailedContract.value || props.contract
})

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

interface RenderedPage {
  html: string
  isCanvas: boolean
}

function pagesFromContent(raw: string | undefined, vars: Record<string, string>): RenderedPage[] {
  if (!raw) return []

  if (isCanvasDocumentJson(raw)) {
    const doc = deserializeCanvasDocument(raw)
    if (doc) {
      return doc.pages.map(p => ({
        html: convertCanvasDocumentToHtml({ ...doc, pages: [p] }, vars),
        isCanvas: true,
      }))
    }
  }

  let cleaned = raw
    .replace(/^[\s\S]*?(?:1-BET\s*═{5,}|1-BET\s*={5,}|={10,}\s*1-BET\s*={10,}|═{10,}\s*1-BET\s*═{10,})/i, '')
    .replace(/(?:═{5,}\s*\d+-BET\s*═{5,}|={5,}\s*\d+-BET\s*={5,}|_{10,}\s*\d+-BET\s*_{10,})/gi, '<hr data-page-break="true" />')

  cleaned = replaceVariablesInHtml(cleaned, vars)
  const parts = cleaned.split(/<hr[^>]*\/?>/i).map(p => p.trim()).filter(p => p.length > 0)
  return (parts.length > 0 ? parts : [cleaned]).map(html => ({ html, isCanvas: false }))
}

const contractVariables = computed<Record<string, string>>(() => {
  const c = activeContract.value
  if (!c) return {}
  return buildVariableValues(c, {
    contractNumber: c.student_id_assigned || c.contract_number,
    templateName: c.tariff_name || c.title,
    price: c.tariff_price ?? undefined,
    discount: c.discount ?? undefined,
    signatureData: c.signature_data || undefined,
    verificationCode: c.verification_code || undefined,
    office: c.office || c.tenant_office_name || undefined,
    educationLevel: c.education_level || undefined,
    email: c.email || undefined,
  })
})

const splitPages = computed<RenderedPage[]>(() => {
  const c = activeContract.value
  if (!c) return []
  const mainPages = pagesFromContent(c.content, contractVariables.value)
  // A minor's guardian consent appendix - same pages the PDF download
  // appends, so "Ko'rish" in the internal Contracts admin matches what
  // staff actually hand the student.
  const appendixPages = c.is_minor
    ? pagesFromContent(c.guardian_contract_text || '', contractVariables.value)
    : []
  return [...mainPages, ...appendixPages]
})

async function handleDownload(format: 'pdf' | 'doc' = 'pdf') {
  const c = activeContract.value
  if (!c || isDownloadingPdf.value) return
  const safeTitle = `${c.contract_number}_${c.student_name || c.full_name || c.title}`.replace(/[/\\?%*:|"<>]/g, '_')
  const rawContent = c.content || ''

  if (format === 'doc') {
    downloadWordDoc(safeTitle, rawContent)
    return
  }

  isDownloadingPdf.value = true
  try {
    const verificationMeta = {
      contractNumber: c.contract_number || c.student_id_assigned || undefined,
      studentId: c.student_id_assigned || undefined,
      studentName: c.full_name || c.student_name || undefined,
      verifiedAt: c.verified_at ? new Date(c.verified_at).toLocaleDateString('uz-UZ') : undefined,
      status: c.status,
    }
    await downloadContractAsPdf(
      safeTitle,
      rawContent,
      { top: 20, right: 15, bottom: 20, left: 25 },
      contractVariables.value,
      c.signature_data || undefined,
      verificationMeta,
      c.is_minor && c.guardian_contract_text
        ? { content: c.guardian_contract_text, variableValues: contractVariables.value }
        : undefined
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

function formatRejectionDate(dateStr?: string | null): string {
  if (!dateStr) return ''
  try {
    const d = new Date(dateStr)
    return d.toLocaleString('uz-UZ', {
      day: '2-digit',
      month: 'short',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    })
  } catch {
    return dateStr
  }
}
</script>

<template>
  <BaseModal
    :is-open="isOpen"
    title="Contract Preview"
    :subtitle="activeContract ? `${activeContract.contract_number} — ${activeContract.title}` : ''"
    max-width="max-w-4xl"
    @close="emit('close')"
  >
    <!-- Modal Action Buttons Bar -->
    <div class="px-6 py-2.5 bg-zinc-50 dark:bg-zinc-850 border-b border-zinc-200 dark:border-zinc-800 flex flex-wrap items-center justify-between gap-3 no-print">
      <!-- Left: Status & Metadata -->
      <div class="flex items-center gap-2.5 flex-wrap">
        <span
          v-if="activeContract?.status"
          class="px-2.5 py-0.5 rounded-full text-[11px] font-medium border uppercase tracking-wider"
          :class="[
            activeContract.status === 'completed'
              ? 'bg-teal-500/10 text-teal-700 dark:text-teal-400 border-teal-500/20'
              : activeContract.status === 'verified'
              ? 'bg-emerald-500/10 text-emerald-700 dark:text-emerald-400 border-emerald-500/20'
              : activeContract.status === 'signed'
              ? 'bg-sky-500/10 text-sky-700 dark:text-sky-400 border-sky-500/20'
              : activeContract.status === 'pending'
              ? 'bg-amber-500/10 text-amber-700 dark:text-amber-400 border-amber-500/20'
              : activeContract.status === 'rejected'
              ? 'bg-rose-500/10 text-rose-700 dark:text-rose-400 border-rose-500/20'
              : activeContract.status === 'cancelled'
              ? 'bg-violet-500/10 text-violet-700 dark:text-violet-400 border-violet-500/20'
              : 'bg-zinc-500/10 text-zinc-600 dark:text-zinc-400 border-zinc-500/20'
          ]"
        >
          {{ activeContract.status }}
        </span>

        <span v-if="activeContract?.student_id_assigned" class="text-xs font-mono text-zinc-500 dark:text-zinc-400">
          ID: <strong class="text-zinc-800 dark:text-zinc-200">{{ activeContract.student_id_assigned }}</strong>
        </span>

        <span class="text-xs text-zinc-400">
          v{{ activeContract?.version || 1 }}
        </span>
      </div>

      <!-- Right: Actions Toolbar -->
      <div class="flex items-center gap-2 flex-wrap" v-if="activeContract">
        <!-- Tasdiqlash kodi: generatsiya qilish (Pending, kod hali yo'q) -->
        <button
          v-if="activeContract.status === 'pending' && !activeContract.verification_code && authStore.isManager"
          type="button"
          @click="emit('assign', activeContract)"
          class="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-zinc-900 hover:bg-black text-white dark:bg-zinc-100 dark:hover:bg-white dark:text-zinc-950 text-xs font-medium shadow-2xs transition-all active:scale-[0.98] cursor-pointer"
          title="Student ID biriktirish va tasdiqlash kodi berish"
        >
          <KeyRound class="w-3.5 h-3.5 text-zinc-300 dark:text-zinc-600" />
          <span>Tasdiqlash kodini generatsiya qilish</span>
        </button>

        <!-- Tasdiqlash kodi: allaqachon berilgan bo'lsa, ko'rsatish + nusxalash + qayta olish -->
        <div
          v-else-if="activeContract.status === 'pending' && activeContract.verification_code"
          class="flex items-center gap-1.5"
        >
          <div class="inline-flex items-center gap-1.5 px-2.5 py-1.5 bg-zinc-100 dark:bg-zinc-800/80 border border-zinc-200/80 dark:border-zinc-700/80 rounded-lg">
            <span class="font-mono font-semibold text-xs text-zinc-900 dark:text-zinc-100 tracking-wider">{{ activeContract.verification_code }}</span>
            <button
              type="button"
              @click="copyCodeToClipboard(activeContract.verification_code)"
              class="p-0.5 hover:text-zinc-900 dark:hover:text-zinc-100 text-zinc-400 transition-colors cursor-pointer"
              title="Kodni nusxalash"
            >
              <Check v-if="copyFeedback" class="w-3.5 h-3.5 text-emerald-500" />
              <Copy v-else class="w-3.5 h-3.5" />
            </button>
          </div>
          <button
            v-if="authStore.isManager"
            type="button"
            @click="emit('regenerate', activeContract)"
            class="p-1.5 rounded-lg border border-zinc-200 dark:border-zinc-700 text-zinc-400 hover:text-amber-600 hover:bg-zinc-100 dark:hover:bg-zinc-800 transition-colors cursor-pointer"
            title="Kodni qayta olish"
          >
            <RotateCcw class="w-3.5 h-3.5 text-amber-500" />
          </button>
        </div>

        <!-- Bekor qilish (Reject - Pending yoki Verified holatida) -->
        <button
          v-if="(activeContract.status === 'pending' || activeContract.status === 'verified') && authStore.isManager"
          type="button"
          @click="emit('reject', activeContract)"
          class="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-rose-200 dark:border-rose-900/60 text-rose-600 dark:text-rose-400 hover:bg-rose-50 dark:hover:bg-rose-950/40 text-xs font-medium transition-colors cursor-pointer"
          title="Arizani bekor qilish"
        >
          <Ban class="w-3.5 h-3.5" />
          <span>Bekor qilish</span>
        </button>

        <!-- Shartnomani butunlay o'chirish (Permanently Delete - Faqat Rejected holatida) -->
        <button
          v-if="activeContract.status === 'rejected' && authStore.isManager"
          type="button"
          @click="emit('delete', activeContract)"
          class="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-rose-200 dark:border-rose-900/60 bg-rose-50/80 dark:bg-rose-950/40 text-rose-600 dark:text-rose-400 hover:bg-rose-100 dark:hover:bg-rose-900/60 text-xs font-medium transition-all shadow-2xs cursor-pointer active:scale-95"
          title="Rad etilgan shartnomani bazadan butunlay o'chirib yuborish"
        >
          <Trash2 class="w-3.5 h-3.5" />
          <span>O'chirib yuborish</span>
        </button>

        <!-- Arxivlash / Arxivdan qaytarish (istalgan holatdagi shartnoma uchun) -->
        <button
          v-if="authStore.isManager"
          type="button"
          @click="activeContract.is_archived ? emit('unarchive', activeContract) : emit('archive', activeContract)"
          class="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg border text-xs font-medium transition-all shadow-2xs cursor-pointer active:scale-95"
          :class="activeContract.is_archived
            ? 'border-blue-200 dark:border-blue-900/60 bg-blue-50/80 dark:bg-blue-950/40 text-blue-600 dark:text-blue-400 hover:bg-blue-100 dark:hover:bg-blue-900/60'
            : 'border-zinc-200 dark:border-zinc-700 bg-white dark:bg-zinc-800 text-zinc-700 dark:text-zinc-200 hover:bg-zinc-50 dark:hover:bg-zinc-750'"
          :title="activeContract.is_archived ? 'Arxivdan qaytarish' : 'Arxivlash'"
        >
          <ArchiveRestore v-if="activeContract.is_archived" class="w-3.5 h-3.5" />
          <Archive v-else class="w-3.5 h-3.5" />
          <span>{{ activeContract.is_archived ? 'Arxivdan qaytarish' : 'Arxivlash' }}</span>
        </button>

        <!-- Yuklab olish (Faqat PDF) -->
        <button
          type="button"
          @click="handleDownload('pdf')"
          :disabled="isDownloadingPdf || isLoadingDetail"
          class="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-zinc-200 dark:border-zinc-700 bg-white dark:bg-zinc-800 text-xs font-medium text-zinc-700 dark:text-zinc-200 hover:bg-zinc-50 dark:hover:bg-zinc-750 transition-colors shadow-2xs cursor-pointer"
          title="PDF yuklab olish"
        >
          <Loader2 v-if="isDownloadingPdf" class="w-3.5 h-3.5 animate-spin text-blue-500" />
          <Download v-else class="w-3.5 h-3.5 text-zinc-500" />
          <span>Yuklab olish (PDF)</span>
        </button>
      </div>
    </div>

    <!-- Rejection Reason Note Banner (Preview oynasida sabab note) -->
    <div
      v-if="activeContract?.status === 'rejected' || activeContract?.rejection_reason"
      class="mx-4 sm:mx-6 my-3 p-3.5 bg-rose-50/95 dark:bg-rose-950/40 border border-rose-200 dark:border-rose-900/60 rounded-xl flex items-start gap-3 text-xs text-rose-900 dark:text-rose-200 shadow-2xs no-print"
    >
      <div class="p-1.5 rounded-lg bg-rose-100 dark:bg-rose-900/50 text-rose-600 dark:text-rose-400 shrink-0 mt-0.5">
        <AlertCircle class="w-4 h-4" />
      </div>
      <div class="flex-1 min-w-0 space-y-1.5">
        <div class="flex items-center justify-between gap-2 flex-wrap">
          <span class="font-semibold text-rose-800 dark:text-rose-200 text-xs">
            Rad etish sababi:
          </span>
          <span v-if="activeContract.rejected_at" class="font-mono text-[11px] text-rose-600/90 dark:text-rose-400/90">
            {{ formatRejectionDate(activeContract.rejected_at) }}
          </span>
        </div>
        <div class="text-rose-700 dark:text-rose-300 font-sans text-xs leading-relaxed whitespace-pre-wrap bg-white/70 dark:bg-black/30 p-2.5 rounded-lg border border-rose-200/60 dark:border-rose-900/40 font-medium">
          {{ activeContract.rejection_reason || "Sabab ko'rsatilmagan." }}
        </div>
        <div v-if="activeContract.rejected_by_name" class="text-[11px] text-rose-600/90 dark:text-rose-400/90">
          Rad etgan xodim: <strong class="font-semibold text-rose-900 dark:text-rose-200">{{ activeContract.rejected_by_name }}</strong>
        </div>
      </div>
    </div>

    <!-- Scrollable Multi-Page A4 Document Sheet View -->
    <div class="p-4 sm:p-8 bg-zinc-100 dark:bg-zinc-950 max-h-[78vh] overflow-y-auto flex flex-col items-center gap-8">
      <div v-if="isLoadingDetail" class="py-16 flex flex-col items-center justify-center text-zinc-400 gap-2">
        <Loader2 class="w-7 h-7 animate-spin text-blue-600 mb-2" />
        <span class="text-xs font-mono">Shartnoma ma'lumotlari yuklanmoqda...</span>
      </div>
      <template v-else-if="splitPages.length > 0">
        <div
          v-for="(page, pageIndex) in splitPages"
          :key="pageIndex"
          class="preview-a4-sheet relative bg-white text-zinc-900 shadow-xl border border-zinc-200/90 font-serif rounded-xs"
          :class="page.isCanvas ? 'is-canvas-sheet p-0 overflow-hidden w-[210mm] min-h-[297mm] shrink-0' : 'p-8 sm:p-14 min-h-[1050px] w-full max-w-[794px]'"
          style="font-family: 'Times New Roman', Times, serif;"
        >
          <!-- Top Page badge (non-canvas only) -->
          <div v-if="!page.isCanvas" class="absolute top-4 right-6 text-[10.5px] uppercase font-bold tracking-widest text-zinc-400 select-none no-print">
            Page {{ pageIndex + 1 }} / {{ splitPages.length }}
          </div>

          <div v-html="page.html" />

          <!-- Bottom page footer (non-canvas only) -->
          <div v-if="!page.isCanvas" class="absolute bottom-5 inset-x-0 text-center text-[11px] text-zinc-400 select-none font-serif tracking-widest no-print">
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

.preview-a4-sheet:not(.is-canvas-sheet) p {
  margin-top: 0.4rem;
  margin-bottom: 0.4rem;
}

.preview-a4-sheet:not(.is-canvas-sheet) table {
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
