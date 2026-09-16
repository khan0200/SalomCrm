<script setup lang="ts">
import { ref, computed, watch, onBeforeUnmount, defineAsyncComponent } from 'vue'
import { useQuery, useQueryClient } from '@tanstack/vue-query'
import {
  FileSignature,
  Plus,
  Search,
  Copy,
  Trash2,
  Edit3,
  Download,
  CheckCircle2,
  AlertTriangle,
  FileCheck,
  FileClock,
  BookOpen,
  ChevronRight,
  Layers,
  Eye,
  RotateCcw,
  Save,
  Loader2,
  X,
  PanelLeftClose,
  PanelLeftOpen,
  Maximize2,
  ChevronDown,
  KeyRound,
  Check,
  Globe,
  ExternalLink,
  Ban,
  HelpCircle,
  Hash,
  ArrowUpRight,
  Filter,
  Archive,
  ArchiveRestore,
} from 'lucide-vue-next'
import { downloadContractAsPdf } from './utils/contractPdf'
import {
  isCanvasDocumentJson,
  deserializeCanvasDocument,
  convertCanvasDocumentToHtml,
} from './utils/contractCanvasConverter'
import { settingsApi, type TariffOption } from '@/api/settings'
import { getContractTemplate } from './contractTemplates'
import { formatDateIso, buildVariableValues } from './utils/contractVariables'
import { contractsApi, type Contract } from '@/api/contracts'
import { useAuthStore } from '@/stores/auth'
import { useUiStore } from '@/stores/ui'
// TipTap + the canvas editor add ~450 KB; only load them once an editor is opened.
const ContractDocumentEditor = defineAsyncComponent(() => import('./components/ContractDocumentEditor.vue'))
import ContractCreateDialog from './components/ContractCreateDialog.vue'
import ContractPreviewModal from './components/ContractPreviewModal.vue'
import BaseModal from '@/components/common/BaseModal.vue'

const authStore = useAuthStore()
const uiStore = useUiStore()
const queryClient = useQueryClient()

// ── 0. Tariffs Sidebar State ─────────────────────────────────────────────────
const selectedTariffId = ref<string>('')
const showTemplatePreview = ref(false)
const tariffViewMode = ref<'preview' | 'edit'>('preview')
const isSidebarCollapsed = ref(false)
const isEditMode = computed(() => showTemplatePreview.value && tariffViewMode.value === 'edit')
const tariffEditingContent = ref<string>('')
const tariffSaveStatus = ref<'idle' | 'saving' | 'saved' | 'error'>('idle')
const tariffLastSavedAt = ref<Date | null>(null)

const formattedTariffLastSaved = computed(() => {
  if (!tariffLastSavedAt.value) return null
  const d = new Date(tariffLastSavedAt.value)
  return `${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}:${String(d.getSeconds()).padStart(2, '0')}`
})

const {
  data: tariffsData,
  isLoading: isTariffsLoading,
} = useQuery<TariffOption[]>({
  queryKey: computed(() => ['contracts-tenant-tariffs', authStore.activeTenantId]),
  queryFn: () => settingsApi.getTariffs(),
  staleTime: 1000 * 60 * 5,
})

const tariffs = computed<TariffOption[]>(() => tariffsData.value || [])

watch(tariffs, (newTariffs) => {
  if (newTariffs.length && !selectedTariffId.value) {
    selectedTariffId.value = String(newTariffs[0].id)
  }
}, { immediate: true })

const activeTariff = computed<TariffOption | null>(() =>
  tariffs.value.find(t => String(t.id) === selectedTariffId.value) || tariffs.value[0] || null
)

const activeTemplate = computed(() =>
  activeTariff.value ? getContractTemplate(activeTariff.value.name) : null
)

// Deliberately does NOT fall back to CONTRACT_TEMPLATES by name-matching: a
// tariff with no contract_text should show as a genuinely blank page, not
// silently substitute one of the 10 hardcoded legacy templates just because
// its name happens to fuzzy-match one of them. Staff can still pull in a
// known template explicitly via "Reset to Standard Template" below.
function getTariffContent(tariff: TariffOption | null): string {
  return tariff?.contract_text || ''
}

watch(
  () => activeTariff.value?.id,
  () => {
    if (activeTariff.value) {
      tariffEditingContent.value = getTariffContent(activeTariff.value)
      tariffSaveStatus.value = 'idle'
    }
  },
  { immediate: true }
)

function selectTariff(tariff: TariffOption) {
  selectedTariffId.value = String(tariff.id)
  showTemplatePreview.value = true
  tariffViewMode.value = 'preview' // Always reset to preview mode on entry!
  isSidebarCollapsed.value = false
  tariffEditingContent.value = getTariffContent(tariff)
  tariffSaveStatus.value = 'idle'
}

function switchToTariffPreview() {
  tariffViewMode.value = 'preview'
  isSidebarCollapsed.value = false
}

function closeTariffView() {
  tariffViewMode.value = 'preview' // Always reset to preview mode on exit!
  isSidebarCollapsed.value = false
  showTemplatePreview.value = false
  selectedTariffId.value = ''
}

async function handleSaveTariffTemplate() {
  if (!activeTariff.value) return
  tariffSaveStatus.value = 'saving'
  try {
    await settingsApi.updateTariff(String(activeTariff.value.id), {
      contract_text: tariffEditingContent.value,
    })
    tariffSaveStatus.value = 'saved'
    tariffLastSavedAt.value = new Date()
    await queryClient.invalidateQueries({ queryKey: ['contracts-tenant-tariffs'] })
  } catch (err) {
    console.error('Failed to save tariff template:', err)
    tariffSaveStatus.value = 'error'
  }
}

function handleResetTariffTemplate() {
  if (!activeTariff.value) return
  if (confirm(`"${activeTariff.value.name}" shartnoma matnini asl standart shablonga qaytarmoqchimisiz?`)) {
    const tpl = getContractTemplate(activeTariff.value.name)
    if (tpl?.fullText) {
      tariffEditingContent.value = tpl.fullText
      handleSaveTariffTemplate()
    }
  }
}

function downloadContractDoc(title: string, rawOrHtml: string) {
  const safeTitle = (title || 'shartnoma').replace(/[/\\?%*:|"<>]/g, '_')
  let htmlBody = renderFormattedContractHtml(rawOrHtml)
  // Convert any page-breaks into Word native section/page breaks
  htmlBody = htmlBody.replace(/<hr[^>]*\/?>/gi, '<br clear="all" style="page-break-before:always;mso-break-type:section-break" />')
  
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
  mso-header-margin: 35.4pt;
  mso-footer-margin: 35.4pt;
  mso-paper-source: 0;
}
div.Section1 { page: Section1; }
body {
  font-family: 'Times New Roman', Georgia, serif;
  font-size: 11pt;
  line-height: 1.5;
  color: #000000;
}
p {
  margin: 6pt 0;
  line-height: 1.5;
  text-align: justify;
}
h1, h2, h3 {
  font-family: 'Times New Roman', Georgia, serif;
  text-align: center;
  font-weight: bold;
  margin: 12pt 0 6pt;
}
table {
  border-collapse: collapse;
  width: 100%;
  margin: 10pt 0;
}
table, th, td {
  border: 1px solid #333;
  padding: 5pt 7pt;
}
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

const isDownloadingPdf = ref(false)
const showDownloadMenu = ref(false)

async function handleDownloadTariff(format: 'pdf' | 'doc' = 'pdf') {
  if (!activeTariff.value || isDownloadingPdf.value) return
  const content = tariffEditingContent.value
  if (!content || !content.trim()) {
    uiStore.addToast({
      type: 'error',
      title: "Shartnoma matni yo'q",
      message: `"${activeTariff.value.name}" tarifi uchun hali shartnoma matni yozilmagan.`,
    })
    return
  }
  const title = `${activeTariff.value.name}_shartnomasi`
  if (format === 'doc') {
    downloadContractDoc(title, content)
  } else {
    isDownloadingPdf.value = true
    try {
      const variableValues = buildVariableValues(undefined, {
        templateName: activeTariff.value.name,
        price: activeTariff.value.price,
      })
      await downloadContractAsPdf(title, content, { top: 20, right: 15, bottom: 20, left: 25 }, variableValues)
    } catch (e) {
      console.error('PDF download error:', e)
      downloadContractDoc(title, content)
    } finally {
      isDownloadingPdf.value = false
    }
  }
}

async function handleDownloadContract(contract: Contract, format: 'pdf' | 'doc' = 'pdf') {
  if (isDownloadingPdf.value) return
  const content = contract.content_snapshot || contract.content || ''
  const title = `${contract.contract_number || 'Contract'}_${contract.student_name || contract.title}`
  if (format === 'doc') {
    downloadContractDoc(title, content)
  } else {
    isDownloadingPdf.value = true
    try {
      const contractNum = contract.student_id_assigned || contract.contract_number || ''
      const dateIso = formatDateIso(contract.signed_at || contract.created_at)
      const variableValues: Record<string, string> = buildVariableValues(contract, {
        contractNumber: contractNum,
        price: contract.tariff_price || undefined,
        discount: contract.discount || undefined,
        signatureData: contract.signature_data || undefined,
        verificationCode: contract.verification_code || undefined,
        office: contract.office || contract.tenant_office_name || undefined,
        educationLevel: contract.education_level || undefined,
        email: contract.email || (contract as any).student_email || '',
      })
      const verificationMeta = {
        contractNumber: contract.contract_number || contract.student_id_assigned || undefined,
        studentId: contract.student_id_assigned || undefined,
        studentName: contract.student_name || undefined,
        verifiedAt: contract.verified_at ? new Date(contract.verified_at).toLocaleDateString('uz-UZ') : undefined,
        status: contract.status,
      }
      await downloadContractAsPdf(
        title,
        content,
        { top: 20, right: 15, bottom: 20, left: 25 },
        variableValues,
        contract.signature_data || undefined,
        verificationMeta
      )
    } catch (e) {
      console.error('PDF download error:', e)
      downloadContractDoc(title, content)
    } finally {
      isDownloadingPdf.value = false
    }
  }
}

function formatPrice(val: number | string | undefined | null): string {
  if (!val) return ''
  const num = typeof val === 'number' ? val : parseFloat(String(val))
  if (isNaN(num) || num === 0) return ''
  return Math.round(num).toString().replace(/\B(?=(\d{3})+(?!\d))/g, ' ') + ' UZS'
}

function renderFormattedContractHtml(raw: string | undefined | null): string {
  if (!raw) return ''
  if (isCanvasDocumentJson(raw)) {
    const doc = deserializeCanvasDocument(raw)
    if (doc) return convertCanvasDocumentToHtml(doc)
  }
  // Clean raw ASCII markers
  let html = raw.replace(/═{10,}\s*(\d+-BET)\s*═{10,}/g, '<hr data-page-break="true" />')
  
  if (html.includes('<table') || html.includes('<p>') || html.includes('<div') || html.includes('<p ') || html.includes('<hr')) {
    return html
  }

  return html
    .replace(/_{10,}/g, '<hr data-page-break="true" />')
    .split('\n\n')
    .map(para => {
      const trimmed = para.trim()
      if (!trimmed) return ''
      if (trimmed.startsWith('<div') || trimmed.startsWith('<hr')) return trimmed
      if (trimmed === trimmed.toUpperCase() && trimmed.length > 5 && trimmed.length < 80 && !trimmed.includes(':')) {
        return `<h3 style="font-weight:bold;margin:16px 0 8px;text-align:center;font-size:14px;">${trimmed}</h3>`
      }
      return `<p style="margin:8px 0;line-height:1.65;">${trimmed.replace(/\n/g, '<br>')}</p>`
    })
    .join('')
}

function splitContractPages(rawOrHtml: string | undefined | null): string[] {
  if (!rawOrHtml) return []
  if (isCanvasDocumentJson(rawOrHtml)) {
    const doc = deserializeCanvasDocument(rawOrHtml)
    if (doc) {
      return doc.pages.map(p => {
        return convertCanvasDocumentToHtml({
          ...doc,
          pages: [p],
        })
      })
    }
  }
  // Standardize any ASCII page markers to <hr data-page-break="true" />
  let cleaned = rawOrHtml
    .replace(/^[\s\S]*?(?:1-BET\s*═{5,}|1-BET\s*={5,}|={10,}\s*1-BET\s*={10,}|═{10,}\s*1-BET\s*═{10,})/i, '')
    .replace(/(?:═{5,}\s*\d+-BET\s*═{5,}|={5,}\s*\d+-BET\s*={5,}|_{10,}\s*\d+-BET\s*_{10,})/gi, '<hr data-page-break="true" />')
  
  const rendered = renderFormattedContractHtml(cleaned)
  const parts = rendered.split(/<hr[^>]*\/?>/i).map(p => p.trim()).filter(p => p.length > 0)
  return parts.length > 0 ? parts : [rendered]
}

function openCreateFromTariff() {
  isCreateDialogOpen.value = true
}

// Search & Status filters for Contracts list
const searchQuery = ref('')
const statusFilter = ref<string>('all')

// Editing state: ID of the contract currently being edited in A4 editor
const editingContractId = ref<string | null>(null)
const editingContent = ref<string>('')
const saveStatus = ref<'idle' | 'saving' | 'saved' | 'error'>('idle')
const lastSavedAt = ref<Date | null>(null)

// Modal states
const isCreateDialogOpen = computed({
  get: () => uiStore.isCreateContractModalOpen,
  set: (v) => uiStore.isCreateContractModalOpen = v
})
const previewContract = ref<Contract | null>(null)
const deletingContract = ref<Contract | null>(null)
const isDeleting = ref(false)

async function openContractPreview(contract: Contract) {
  previewContract.value = contract
  if (!contract.content) {
    try {
      const full = await contractsApi.getContract(contract.id)
      if (full) {
        previewContract.value = full
      }
    } catch (err) {
      console.error('Failed to load contract detail for preview:', err)
    }
  }
}

// ── 1. Fetch Contracts List ──────────────────────────────────────────────────
const {
  data: contractsData,
  isLoading: isContractsLoading,
  refetch: refetchContracts
} = useQuery<Contract[]>({
  queryKey: computed(() => ['contracts-list', authStore.activeTenantId, searchQuery.value, statusFilter.value]),
  queryFn: () => contractsApi.getContracts({
    search: searchQuery.value,
    status: statusFilter.value === 'all' ? undefined : statusFilter.value
  }),
  staleTime: 1000 * 60 * 2,
})

const {
  data: allContractsData,
} = useQuery<Contract[]>({
  queryKey: computed(() => ['contracts-all-metrics', authStore.activeTenantId]),
  // include_archived: fetches every contract (archived or not) in one shot
  // so tab counts can be computed for both the normal tabs (which must
  // exclude archived contracts) and the Archive tab (which needs only them).
  queryFn: () => contractsApi.getContracts({ include_archived: true }),
  staleTime: 1000 * 60 * 2,
})

const contracts = computed<Contract[]>(() => contractsData.value || [])

// Stats (Resend style metrics)
const contractStats = computed(() => {
  const all = allContractsData.value || contracts.value
  const active = all.filter(c => !c.is_archived)
  return {
    total: active.length,
    pending: active.filter(c => c.status === 'pending').length,
    verified: active.filter(c => c.status === 'verified').length,
    rejected: active.filter(c => c.status === 'rejected').length,
    cancelled: active.filter(c => c.status === 'cancelled').length,
    draft: active.filter(c => c.status === 'draft').length,
    signed: active.filter(c => c.status === 'signed').length,
    completed: active.filter(c => c.status === 'completed').length,
    archived: all.filter(c => c.is_archived).length,
  }
})

function formatContractDate(dateStr?: string | null): string {
  if (!dateStr) return '—'
  const d = new Date(dateStr)
  if (isNaN(d.getTime())) return '—'
  const day = String(d.getDate()).padStart(2, '0')
  const month = d.toLocaleString('en-US', { month: 'short' })
  const year = d.getFullYear()
  return `${day} ${month} ${year}`
}

function getFilterCount(key: string): number {
  if (key === 'all') return contractStats.value.total
  if (key === 'pending') return contractStats.value.pending
  if (key === 'verified') return contractStats.value.verified
  if (key === 'draft') return contractStats.value.draft
  if (key === 'signed') return contractStats.value.signed
  if (key === 'completed') return contractStats.value.completed
  if (key === 'rejected') return contractStats.value.rejected
  if (key === 'cancelled') return contractStats.value.cancelled
  if (key === 'archive') return contractStats.value.archived
  return 0
}

function getStatusBadgeClass(status?: string): string {
  switch (status) {
    case 'pending':
      return 'bg-amber-500/10 text-amber-700 dark:text-amber-400 border-amber-500/20'
    case 'verified':
      return 'bg-emerald-500/10 text-emerald-700 dark:text-emerald-400 border-emerald-500/20'
    case 'signed':
      return 'bg-sky-500/10 text-sky-700 dark:text-sky-400 border-sky-500/20'
    case 'completed':
      return 'bg-teal-500/10 text-teal-700 dark:text-teal-400 border-teal-500/20'
    case 'draft':
      return 'bg-zinc-500/10 text-zinc-600 dark:text-zinc-400 border-zinc-500/20'
    case 'rejected':
      return 'bg-rose-500/10 text-rose-700 dark:text-rose-400 border-rose-500/20'
    case 'cancelled':
      return 'bg-violet-500/10 text-violet-700 dark:text-violet-400 border-violet-500/20'
    default:
      return 'bg-zinc-500/10 text-zinc-600 dark:text-zinc-400 border-zinc-500/20'
  }
}

function getStatusDotClass(status?: string): string {
  switch (status) {
    case 'pending':
      return 'bg-amber-500 animate-pulse'
    case 'verified':
      return 'bg-emerald-500'
    case 'signed':
      return 'bg-sky-500'
    case 'completed':
      return 'bg-teal-500'
    case 'draft':
      return 'bg-zinc-400'
    case 'rejected':
      return 'bg-rose-500'
    case 'cancelled':
      return 'bg-violet-500'
    default:
      return 'bg-zinc-400'
  }
}

function getStatusLabel(status?: string): string {
  switch (status) {
    case 'pending':
      return 'Pending'
    case 'verified':
      return 'Verified'
    case 'signed':
      return 'Signed'
    case 'completed':
      return 'Completed'
    case 'draft':
      return 'Draft'
    case 'rejected':
      return 'Rejected'
    case 'cancelled':
      return 'Cancelled'
    default:
      return status?.toUpperCase() || '—'
  }
}

// ── Online Contract Agency Verification State ───────────────────────────────
const isAssignModalOpen = ref(false)
const assigningContract = ref<Contract | null>(null)
const assignStudentIdInput = ref('')
const assignDiscountInput = ref<number | string>('')
const isAssigning = ref(false)
const assignError = ref('')

const showVerificationCodeResultModal = ref(false)
const generatedCodeResult = ref<{
  student_id: string
  contract_number: string
  discount?: string
  verification_code: string
  expires_at: string
} | null>(null)

const isRejectModalOpen = ref(false)
const rejectingContract = ref<Contract | null>(null)
const rejectionReasonInput = ref('')
const isRejecting = ref(false)
const rejectError = ref('')

const showStaffExplanationModal = ref(false)
const isRegenerating = ref(false)
const copyFeedback = ref(false)

function openAssignModal(contract: Contract) {
  assigningContract.value = contract
  assignStudentIdInput.value = contract.student_id || contract.student_id_assigned || ''
  assignDiscountInput.value = contract.discount ? Number(contract.discount) : ''
  assignError.value = ''
  isAssignModalOpen.value = true
}

async function handleConfirmAssignStudentId() {
  if (!assigningContract.value) return
  const sid = assignStudentIdInput.value.trim().toUpperCase()
  if (!sid) {
    assignError.value = 'Student ID is required.'
    return
  }

  isAssigning.value = true
  assignError.value = ''
  try {
    const res = await contractsApi.assignStudentId(assigningContract.value.id, sid, assignDiscountInput.value)
    generatedCodeResult.value = res
    isAssignModalOpen.value = false
    showVerificationCodeResultModal.value = true
    queryClient.invalidateQueries({ queryKey: ['contracts-list'] })
  } catch (err: any) {
    assignError.value = err?.response?.data?.detail || 'Failed to assign Student ID.'
  } finally {
    isAssigning.value = false
  }
}

async function handleRegenerateCode(contract: Contract) {
  if (isRegenerating.value) return
  isRegenerating.value = true
  try {
    const res = await contractsApi.regenerateCode(contract.id)
    generatedCodeResult.value = res
    showVerificationCodeResultModal.value = true
    queryClient.invalidateQueries({ queryKey: ['contracts-list'] })
  } catch (err: any) {
    alert(err?.response?.data?.detail || 'Failed to regenerate verification code.')
  } finally {
    isRegenerating.value = false
  }
}

function openRejectModal(contract: Contract) {
  rejectingContract.value = contract
  rejectionReasonInput.value = ''
  rejectError.value = ''
  isRejectModalOpen.value = true
}

async function handleConfirmReject() {
  if (!rejectingContract.value) return
  const reason = rejectionReasonInput.value.trim()
  if (!reason) {
    rejectError.value = 'Rejection reason is required.'
    return
  }

  isRejecting.value = true
  rejectError.value = ''
  try {
    await contractsApi.rejectContract(rejectingContract.value.id, reason)
    isRejectModalOpen.value = false
    queryClient.invalidateQueries({ queryKey: ['contracts-list'] })
  } catch (err: any) {
    rejectError.value = err?.response?.data?.detail || 'Failed to reject contract.'
  } finally {
    isRejecting.value = false
  }
}

function copyCodeToClipboard(code: string) {
  if (!code) return
  navigator.clipboard.writeText(code)
  copyFeedback.value = true
  setTimeout(() => {
    copyFeedback.value = false
  }, 2000)
}

// Fetch single contract being edited
const {
  data: currentEditingContract,
  isLoading: isContractDetailLoading,
  refetch: refetchCurrentContract
} = useQuery<Contract>({
  queryKey: computed(() => ['contract-detail', editingContractId.value]),
  queryFn: () => contractsApi.getContract(editingContractId.value!),
  enabled: computed(() => !!editingContractId.value),
  staleTime: 1000 * 60,
})

// Sync editing content when contract detail loads
watch(
  currentEditingContract,
  (c) => {
    if (c) {
      editingContent.value = c.content || ''
      saveStatus.value = 'idle'
    }
  },
  { immediate: true }
)

// ── 2. Autosave & Manual Save Handler ────────────────────────────────────────
async function handleSaveContract() {
  if (!editingContractId.value) return
  if (currentEditingContract.value?.status === 'verified' || currentEditingContract.value?.status === 'pending') {
    alert("Tasdiqlangan (Verified) yoki Kutilayotgan (Pending) holatidagi shartnomalarni o'zgartirib bo'lmaydi.")
    return
  }
  saveStatus.value = 'saving'

  try {
    await contractsApi.updateContract(editingContractId.value, {
      content: editingContent.value,
    })
    saveStatus.value = 'saved'
    lastSavedAt.value = new Date()
    queryClient.invalidateQueries({ queryKey: ['contracts-list'] })
  } catch (err: any) {
    console.error('Failed to save contract:', err)
    saveStatus.value = 'error'
    const errorMsg = err?.response?.data?.detail || "Shartnomani saqlashda xatolik yuz berdi"
    alert(errorMsg)
  }
}

// ── 3. Contract Actions ──────────────────────────────────────────────────────
function handleOpenEditor(contract: Contract) {
  if (contract.status === 'verified' || contract.status === 'pending') {
    alert("Tasdiqlangan (Verified) yoki Kutilayotgan (Pending) holatidagi shartnomalarni tahrirlab bo'lmaydi.")
    return
  }
  queryClient.setQueryData(['contract-detail', contract.id], contract)
  editingContent.value = contract.content || ''
  editingContractId.value = contract.id
}

function handleBackToList() {
  editingContractId.value = null
  refetchContracts()
}

function handleContractCreated(contract: Contract) {
  queryClient.setQueryData(['contract-detail', contract.id], contract)
  queryClient.invalidateQueries({ queryKey: ['contracts-list'] })
  editingContent.value = contract.content || ''
  editingContractId.value = contract.id
}

async function handleDuplicate(contract: Contract) {
  try {
    const duplicated = await contractsApi.duplicateContract(contract.id)
    queryClient.invalidateQueries({ queryKey: ['contracts-list'] })
    editingContractId.value = duplicated.id
  } catch (err) {
    console.error('Failed to duplicate contract:', err)
  }
}

async function confirmDelete() {
  if (!deletingContract.value) return
  if (deletingContract.value.status === 'verified' || deletingContract.value.status === 'pending') {
    alert("Tasdiqlangan (Verified) yoki Kutilayotgan (Pending) holatidagi shartnomalarni o'chirib bo'lmaydi.")
    deletingContract.value = null
    return
  }
  isDeleting.value = true
  try {
    const isPermanent = deletingContract.value.status === 'rejected'
    await contractsApi.deleteContract(deletingContract.value.id, isPermanent)
    deletingContract.value = null
    queryClient.invalidateQueries({ queryKey: ['contracts-list'] })
    queryClient.invalidateQueries({ queryKey: ['contracts-all-metrics'] })
  } catch (err: any) {
    console.error('Failed to delete contract:', err)
    const errorMsg = err?.response?.data?.detail || "Shartnomani o'chirishda xatolik yuz berdi"
    alert(errorMsg)
  } finally {
    isDeleting.value = false
  }
}

// Archive: works for any contract regardless of status. Archiving just hides
// it from every other filter (All/Pending/Verified/Cancelled) - it doesn't
// touch the underlying status, so unarchiving restores it exactly as it was.
async function handleArchive(contract: Contract) {
  try {
    await contractsApi.archiveContract(contract.id)
    uiStore.addToast({ type: 'success', message: 'Shartnoma arxivga o\'tkazildi.', duration: 3000 })
    queryClient.invalidateQueries({ queryKey: ['contracts-list'] })
    queryClient.invalidateQueries({ queryKey: ['contracts-all-metrics'] })
  } catch (err: any) {
    console.error('Failed to archive contract:', err)
    const errorMsg = err?.response?.data?.detail || 'Shartnomani arxivlashda xatolik yuz berdi'
    alert(errorMsg)
  }
}

async function handleUnarchive(contract: Contract) {
  try {
    await contractsApi.unarchiveContract(contract.id)
    uiStore.addToast({ type: 'success', message: 'Shartnoma arxivdan qaytarildi.', duration: 3000 })
    queryClient.invalidateQueries({ queryKey: ['contracts-list'] })
    queryClient.invalidateQueries({ queryKey: ['contracts-all-metrics'] })
  } catch (err: any) {
    console.error('Failed to unarchive contract:', err)
    const errorMsg = err?.response?.data?.detail || 'Shartnomani arxivdan qaytarishda xatolik yuz berdi'
    alert(errorMsg)
  }
}

</script>

<template>
  <div :class="[editingContractId ? 'h-[calc(100vh-90px)] flex flex-col min-h-0 overflow-hidden' : 'space-y-5 animate-page-in']">

    <!-- VIEW A: FULL-SCREEN A4 DOCUMENT EDITOR -->
    <template v-if="editingContractId">
      <div v-if="isContractDetailLoading" class="min-h-[600px] flex flex-col items-center justify-center">
        <div class="w-8 h-8 border-3 border-blue-600 border-t-transparent rounded-full animate-spin mb-3"></div>
        <p class="text-xs text-zinc-500">Loading contract document...</p>
      </div>
      <ContractDocumentEditor
        v-else-if="currentEditingContract"
        v-model:content="editingContent"
        :contract-number="currentEditingContract.contract_number"
        :title="currentEditingContract.title"
        :student-name="currentEditingContract.student_name || currentEditingContract.full_name || undefined"
        :student-data="currentEditingContract"
        :save-status="saveStatus"
        :last-saved-at="lastSavedAt"
        class="flex-1 h-full min-h-0"
        @save="handleSaveContract"
        @preview="previewContract = currentEditingContract"
        @back="handleBackToList"
      />
    </template>

    <!-- VIEW B: SPLIT LAYOUT (sidebar + content) -->
    <template v-else>


      <!-- Split Layout (Robust Flex Side-by-Side on desktop & tablet) -->
      <div class="flex flex-col md:flex-row gap-3 sm:gap-4 items-start transition-all w-full">

        <!-- LEFT SIDEBAR: Tariff List (Compact in Edit Mode, collapsible) -->
        <aside
          v-if="!isSidebarCollapsed || !isEditMode"
          class="bg-white dark:bg-[#0c0c0e] rounded-xl border border-zinc-200/80 dark:border-zinc-800 shadow-2xs overflow-hidden flex flex-col sticky top-3 transition-all shrink-0 w-full"
          :class="isEditMode ? 'md:w-56 lg:w-60' : 'md:w-64 lg:w-72'"
        >
          <div class="px-3.5 py-2.5 border-b border-zinc-100 dark:border-zinc-800 flex items-center justify-between shrink-0">
            <div class="flex items-center gap-1.5 min-w-0">
              <Layers class="w-3.5 h-3.5 text-zinc-400 shrink-0" />
              <span class="text-[11px] font-medium text-zinc-500 dark:text-zinc-400 uppercase tracking-wider truncate">Tariffs</span>
              <span class="text-[10px] font-mono text-zinc-400">({{ tariffs.length }})</span>
            </div>
            <!-- Collapse button in Edit mode -->
            <button
              v-if="isEditMode"
              type="button"
              @click="isSidebarCollapsed = true"
              class="w-6 h-6 rounded-md flex items-center justify-center text-zinc-400 hover:text-zinc-700 dark:hover:text-zinc-200 hover:bg-zinc-100 dark:hover:bg-zinc-800 transition-colors cursor-pointer"
              title="Collapse panel"
            >
              <PanelLeftClose class="w-3.5 h-3.5" />
            </button>
          </div>
          <div class="p-1.5 space-y-0.5 overflow-y-auto max-h-[calc(100vh-190px)]">
            <!-- Loading -->
            <div v-if="isTariffsLoading" class="p-3 space-y-2">
              <div v-for="i in 4" :key="i" class="h-9 bg-zinc-100 dark:bg-zinc-850/60 rounded-lg animate-pulse" />
            </div>
            <template v-else>
              <!-- All contracts -->
              <button
                v-if="!isEditMode"
                type="button"
                @click="closeTariffView"
                class="w-full flex items-center justify-between px-2.5 py-2 rounded-lg text-left transition-all cursor-pointer border"
                :class="!showTemplatePreview
                  ? 'bg-zinc-100 dark:bg-zinc-800/80 border-zinc-200/80 dark:border-zinc-700/80 text-zinc-950 dark:text-white font-medium shadow-2xs'
                  : 'border-transparent text-zinc-600 dark:text-zinc-400 hover:bg-zinc-50 dark:hover:bg-zinc-850/50'"
              >
                <div class="flex items-center gap-2">
                  <div class="w-5 h-5 rounded-md flex items-center justify-center shrink-0 transition-colors"
                    :class="!showTemplatePreview ? 'bg-zinc-900 dark:bg-zinc-100 text-white dark:text-zinc-900' : 'bg-zinc-100 dark:bg-zinc-800 text-zinc-400'">
                    <FileSignature class="w-3 h-3" />
                  </div>
                  <span class="text-xs">All Contracts</span>
                </div>
                <span class="text-[10px] font-mono text-zinc-400">{{ contractStats.total }}</span>
              </button>

              <!-- Each tariff -->
              <button
                v-for="tariff in tariffs"
                :key="tariff.id"
                type="button"
                @click="selectTariff(tariff)"
                class="w-full flex items-center justify-between rounded-lg text-left transition-all cursor-pointer border group"
                :class="[
                  isEditMode ? 'px-2 py-1.5 text-xs' : 'px-2.5 py-2 text-xs',
                  showTemplatePreview && selectedTariffId === String(tariff.id)
                    ? 'bg-zinc-100 dark:bg-zinc-800/80 border-zinc-200/80 dark:border-zinc-700/80 text-zinc-950 dark:text-white font-medium shadow-2xs'
                    : 'border-transparent text-zinc-600 dark:text-zinc-400 hover:bg-zinc-50 dark:hover:bg-zinc-850/50'
                ]"
                :title="tariff.name"
              >
                <div class="flex items-center gap-2 min-w-0 flex-1">
                  <div class="rounded-md flex items-center justify-center shrink-0 transition-colors"
                    :class="[
                      isEditMode ? 'w-4 h-4' : 'w-5 h-5',
                      showTemplatePreview && selectedTariffId === String(tariff.id)
                        ? 'bg-zinc-900 dark:bg-zinc-100 text-white dark:text-zinc-900'
                        : 'bg-zinc-100 dark:bg-zinc-800 text-zinc-400'
                    ]"
                  >
                    <BookOpen :class="isEditMode ? 'w-2.5 h-2.5' : 'w-3 h-3'" />
                  </div>
                  <div class="min-w-0 flex-1">
                    <div class="truncate leading-tight" :class="isEditMode ? 'text-[11px]' : 'text-xs'">{{ tariff.name }}</div>
                    <div v-if="!isEditMode" class="flex items-center gap-1.5 mt-0.5">
                      <span v-if="formatPrice(tariff.price)" class="text-[10px] text-zinc-400 font-mono">{{ formatPrice(tariff.price) }}</span>
                      <span
                        v-if="!tariff.is_active"
                        class="text-[9px] font-bold uppercase tracking-wide text-zinc-500 dark:text-zinc-400 bg-zinc-100 dark:bg-zinc-800 px-1 py-0.5 rounded"
                        title="Onlayn portalda ko'rinmaydi"
                      >
                        Inactive
                      </span>
                    </div>
                  </div>
                </div>
                <ChevronRight v-if="!isEditMode" class="w-3.5 h-3.5 text-zinc-400 shrink-0 opacity-0 group-hover:opacity-100 transition-opacity" />
              </button>
            </template>
          </div>
        </aside>

        <!-- RIGHT PANEL (Expands to fill all remaining width) -->
        <div class="flex-1 w-full min-w-0 space-y-4 transition-all">

          <!-- TEMPLATE PREVIEW & EDIT MODE -->
          <template v-if="showTemplatePreview && activeTariff">
            <div class="bg-white dark:bg-[#111315] rounded-2xl border border-zinc-200 dark:border-zinc-800 shadow-2xs overflow-hidden flex flex-col">
              <!-- Unified Toolbar Header -->
              <div
                class="border-b border-zinc-100 dark:border-zinc-800 flex flex-col sm:flex-row sm:items-center justify-between gap-2.5 bg-white dark:bg-[#111315] transition-all"
                :class="tariffViewMode === 'edit' ? 'px-3 py-2 sm:px-4 sm:py-2' : 'px-4 py-3 sm:px-5 sm:py-3.5'"
              >
                <!-- Left: Title, Price, Status -->
                <div class="flex items-center gap-2.5 min-w-0">
                  <!-- Expand Sidebar Button if collapsed in Edit mode -->
                  <button
                    v-if="isEditMode && isSidebarCollapsed"
                    type="button"
                    @click="isSidebarCollapsed = false"
                    class="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-xl border border-zinc-200 dark:border-zinc-700 bg-white dark:bg-zinc-800 text-xs font-bold text-zinc-700 dark:text-zinc-200 hover:bg-zinc-50 dark:hover:bg-zinc-750 transition-colors shadow-2xs cursor-pointer mr-1"
                    title="Show tariffs"
                  >
                    <PanelLeftOpen class="w-3.5 h-3.5 text-blue-500" />
                    <span class="hidden sm:inline">Tariffs</span>
                  </button>

                  <div
                    class="rounded-xl bg-blue-50 dark:bg-blue-950/40 text-blue-600 dark:text-blue-400 flex items-center justify-center shrink-0 border border-blue-200/50 dark:border-blue-800/40"
                    :class="tariffViewMode === 'edit' ? 'w-8 h-8' : 'w-10 h-10'"
                  >
                    <BookOpen :class="tariffViewMode === 'edit' ? 'w-4 h-4' : 'w-5 h-5'" />
                  </div>
                  <div class="min-w-0">
                    <div class="flex items-center gap-2 flex-wrap">
                      <h2
                        class="font-extrabold text-zinc-900 dark:text-white truncate"
                        :class="tariffViewMode === 'edit' ? 'text-xs sm:text-sm' : 'text-sm sm:text-base'"
                      >
                        {{ activeTariff.name }}
                      </h2>
                      <span
                        v-if="activeTariff.contract_text"
                        class="px-2 py-0.5 rounded-full text-[10px] font-bold bg-emerald-50 dark:bg-emerald-950/50 text-emerald-600 dark:text-emerald-400 border border-emerald-200 dark:border-emerald-800"
                      >
                        Edited
                      </span>
                      <span
                        v-else
                        class="px-2 py-0.5 rounded-full text-[10px] font-bold bg-zinc-100 dark:bg-zinc-800 text-zinc-500 border border-zinc-200 dark:border-zinc-700"
                      >
                        Standard
                      </span>
                    </div>
                    <div v-if="formatPrice(activeTariff.price)" class="text-[11.5px] font-bold text-blue-600 dark:text-blue-400 font-mono mt-0.5">
                      {{ formatPrice(activeTariff.price) }}
                    </div>
                  </div>
                </div>

                <!-- Right: Unified Controls [Preview] [EDIT] [SAVE] [X] -->
                <div class="flex items-center gap-2 shrink-0">
                  <!-- Mode Switcher: [Preview] [EDIT] -->
                  <div class="flex items-center p-0.5 bg-zinc-100 dark:bg-zinc-800 rounded-xl border border-zinc-200/60 dark:border-zinc-700/60">
                    <button
                      type="button"
                      @click="switchToTariffPreview"
                      class="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-bold transition-all cursor-pointer"
                      :class="tariffViewMode === 'preview'
                        ? 'bg-white dark:bg-zinc-700 text-blue-600 dark:text-blue-300 shadow-2xs'
                        : 'text-zinc-500 hover:text-zinc-800 dark:hover:text-zinc-300'"
                      title="Preview"
                    >
                      <Eye class="w-3.5 h-3.5" />
                      <span>Preview</span>
                    </button>
                    <button
                      type="button"
                      @click="tariffViewMode = 'edit'"
                      class="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-bold transition-all cursor-pointer"
                      :class="tariffViewMode === 'edit'
                        ? 'bg-white dark:bg-zinc-700 text-blue-600 dark:text-blue-300 shadow-2xs'
                        : 'text-zinc-500 hover:text-zinc-800 dark:hover:text-zinc-300'"
                      title="Edit"
                    >
                      <Edit3 class="w-3.5 h-3.5" />
                      <span>Edit</span>
                    </button>
                  </div>

                  <!-- EDIT MODE ACTIONS -->
                  <template v-if="tariffViewMode === 'edit'">
                    <!-- Autosave Indicator -->
                    <div class="flex items-center gap-1.5 text-[11px] font-medium px-2 py-1 rounded-lg">
                      <template v-if="tariffSaveStatus === 'saving'">
                        <Loader2 class="w-3.5 h-3.5 text-blue-500 animate-spin" />
                        <span class="text-blue-600 dark:text-blue-400 font-semibold hidden sm:inline">Saving...</span>
                      </template>
                      <template v-else-if="tariffSaveStatus === 'saved'">
                        <CheckCircle2 class="w-3.5 h-3.5 text-emerald-500" />
                        <span class="text-zinc-500 dark:text-zinc-400 hidden sm:inline">
                          Saved <span v-if="formattedTariffLastSaved" class="font-mono text-[10px]">({{ formattedTariffLastSaved }})</span>
                        </span>
                      </template>
                      <template v-else-if="tariffSaveStatus === 'error'">
                        <AlertTriangle class="w-3.5 h-3.5 text-rose-500" />
                        <span class="text-rose-600 dark:text-rose-400 font-semibold hidden sm:inline">Error</span>
                      </template>
                    </div>

                    <!-- [SAVE] Button -->
                    <button
                      type="button"
                      @click="handleSaveTariffTemplate"
                      :disabled="tariffSaveStatus === 'saving'"
                      class="inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-xl bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white text-xs font-bold transition-all shadow-xs cursor-pointer"
                      title="Save"
                    >
                      <Loader2 v-if="tariffSaveStatus === 'saving'" class="w-3.5 h-3.5 animate-spin" />
                      <Save v-else class="w-3.5 h-3.5" />
                      <span>Save</span>
                    </button>
                  </template>

                  <!-- PREVIEW MODE ACTIONS -->
                  <template v-else>
                    <!-- Download PDF Button (Direct) -->
                    <button
                      type="button"
                      @click="handleDownloadTariff('pdf')"
                      :disabled="isDownloadingPdf"
                      class="inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-xl border border-zinc-200 dark:border-zinc-700 bg-white dark:bg-zinc-800 hover:bg-zinc-50 dark:hover:bg-zinc-750 text-xs font-semibold text-zinc-700 dark:text-zinc-300 transition-colors cursor-pointer shadow-2xs"
                      title="PDF yuklab olish"
                    >
                      <Loader2 v-if="isDownloadingPdf" class="w-3.5 h-3.5 animate-spin text-blue-500" />
                      <Download v-else class="w-3.5 h-3.5 text-blue-500" />
                      <span>PDF</span>
                    </button>
                  </template>

                  <!-- Divider -->
                  <div class="h-4 w-px bg-zinc-200 dark:bg-zinc-800 mx-0.5"></div>

                  <!-- [X] Button -->
                  <button
                    type="button"
                    @click="closeTariffView"
                    class="w-8 h-8 rounded-xl flex items-center justify-center text-zinc-400 hover:text-zinc-700 dark:hover:text-zinc-200 hover:bg-zinc-100 dark:hover:bg-zinc-800 transition-colors cursor-pointer"
                    title="Close"
                  >
                    <X class="w-4 h-4" />
                  </button>
                </div>
              </div>

              <!-- UNIFIED CANVAS DOCUMENT VIEW: PREVIEW & EDIT (Pixel-Perfect Fidelity) -->
              <div class="h-[calc(100vh-175px)] min-h-0 flex flex-col overflow-hidden">
                <ContractDocumentEditor
                  v-model:content="tariffEditingContent"
                  :contract-number="activeTariff.name"
                  :title="activeTariff.name + ' Contract Template'"
                  :readonly="tariffViewMode === 'preview'"
                  :save-status="tariffSaveStatus"
                  :last-saved-at="tariffLastSavedAt"
                  :hide-top-bar="true"
                  back-label="Preview"
                  class="flex-1 h-full min-h-0"
                  @save="handleSaveTariffTemplate"
                  @preview="switchToTariffPreview"
                  @back="switchToTariffPreview"
                />
              </div>
            </div>
          </template>

          <!-- CONTRACTS LIST MODE (Resend App UI Style) -->
          <template v-else>
            <!-- Filter & Search Toolbar (Resend Control Bar) -->
            <div class="flex flex-col lg:flex-row lg:items-center justify-between gap-2.5 bg-white dark:bg-[#0c0c0e] p-2.5 rounded-xl border border-zinc-200/80 dark:border-zinc-800 shadow-2xs">
              <!-- Search Input -->
              <div class="relative flex-1 max-w-sm">
                <Search class="w-3.5 h-3.5 text-zinc-400 absolute left-3 top-1/2 -translate-y-1/2 pointer-events-none" />
                <input
                  v-model="searchQuery"
                  type="text"
                  placeholder="Search contracts (number, student, passport)..."
                  class="w-full pl-9 pr-8 py-1.5 bg-zinc-50/70 dark:bg-zinc-900/80 border border-zinc-200 dark:border-zinc-800 rounded-lg text-xs placeholder:text-zinc-400 text-zinc-900 dark:text-zinc-100 focus:outline-none focus:border-zinc-400 dark:focus:border-zinc-600 focus:bg-white dark:focus:bg-zinc-900 shadow-2xs transition-all"
                />
                <button
                  v-if="searchQuery"
                  type="button"
                  @click="searchQuery = ''"
                  class="absolute right-2.5 top-1/2 -translate-y-1/2 text-zinc-400 hover:text-zinc-600 dark:hover:text-zinc-200 cursor-pointer"
                >
                  <X class="w-3 h-3" />
                </button>
                <span v-else class="absolute right-2.5 top-1/2 -translate-y-1/2 text-[10px] font-mono text-zinc-400 select-none bg-zinc-200/50 dark:bg-zinc-800 px-1.5 py-0.5 rounded">
                  /
                </span>
              </div>

              <!-- Resend Segmented Tab Bar -->
              <div class="inline-flex items-center p-1 bg-zinc-100 dark:bg-zinc-850/80 rounded-lg border border-zinc-200/60 dark:border-zinc-750/60 overflow-x-auto max-w-full text-xs">
                <button
                  v-for="st in [
                    { key: 'all', label: 'All' },
                    { key: 'pending', label: 'Pending' },
                    { key: 'verified', label: 'Verified' },
                    { key: 'cancelled', label: 'Cancelled' },
                    { key: 'archive', label: 'Archive' }
                  ]"
                  :key="st.key"
                  type="button"
                  @click="statusFilter = st.key"
                  class="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-medium transition-all cursor-pointer shrink-0 select-none"
                  :class="statusFilter === st.key
                    ? 'bg-white dark:bg-zinc-900 text-zinc-900 dark:text-white shadow-2xs border border-zinc-200/60 dark:border-zinc-700/60 font-semibold'
                    : 'text-zinc-500 hover:text-zinc-900 dark:text-zinc-400 dark:hover:text-zinc-100 border border-transparent font-normal'"
                >
                  <span>{{ st.label }}</span>
                  <span
                    v-if="getFilterCount(st.key) > 0"
                    class="px-1.5 py-0.2 text-[10px] font-mono rounded-full font-medium"
                    :class="statusFilter === st.key
                      ? 'bg-zinc-100 dark:bg-zinc-800 text-zinc-800 dark:text-zinc-200'
                      : 'bg-zinc-200/70 dark:bg-zinc-800/80 text-zinc-600 dark:text-zinc-400'"
                  >
                    {{ getFilterCount(st.key) }}
                  </span>
                </button>
              </div>
            </div>

            <!-- Contracts Table (Resend Emails/Logs Table style) -->
            <div class="bg-white dark:bg-[#0c0c0e] rounded-xl border border-zinc-200/80 dark:border-zinc-800 shadow-2xs overflow-hidden">
              <div v-if="isContractsLoading" class="p-6 space-y-2.5">
                <div v-for="i in 5" :key="i" class="h-14 bg-zinc-100/70 dark:bg-zinc-850/50 rounded-lg animate-pulse"></div>
              </div>
              <div v-else-if="contracts.length === 0" class="py-16 px-4 text-center flex flex-col items-center">
                <div class="w-12 h-12 rounded-xl bg-zinc-100 dark:bg-zinc-850 text-zinc-400 flex items-center justify-center mb-3 border border-zinc-200/80 dark:border-zinc-800">
                  <FileSignature class="w-5 h-5 text-zinc-400" />
                </div>
                <h3 class="text-xs font-semibold text-zinc-900 dark:text-zinc-100">No contracts found</h3>
                <p class="text-xs text-zinc-500 dark:text-zinc-400 mt-1 mb-4 max-w-xs leading-relaxed">
                  {{ searchQuery ? "No contracts matched your search query" : "Get started by sharing the online contract link with students." }}
                </p>
                <button
                  type="button"
                  @click="uiStore.isShareContractLinkModalOpen = true"
                  class="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-zinc-900 hover:bg-black text-white dark:bg-zinc-100 dark:hover:bg-white dark:text-zinc-950 text-xs font-medium cursor-pointer shadow-2xs transition-all active:scale-[0.98]"
                >
                  <Plus class="w-3.5 h-3.5" />
                  <span>New Contract</span>
                </button>
              </div>
              <div v-else class="overflow-x-auto">
                <table class="w-full text-left border-collapse text-xs">
                  <thead class="bg-zinc-50/75 dark:bg-zinc-900/60 border-b border-zinc-200/80 dark:border-zinc-800 text-[11px] font-medium text-zinc-400 uppercase tracking-wider select-none">
                    <tr>
                      <th class="py-2.5 px-4 font-medium w-36">Contract / ID</th>
                      <th class="py-2.5 px-4 font-medium w-52 sm:w-60">Tariff & Price</th>
                      <th class="py-2.5 px-4 font-medium">Student & Passport</th>
                      <th class="py-2.5 px-4 font-medium text-right">Status</th>
                    </tr>
                  </thead>
                  <tbody class="divide-y divide-zinc-100 dark:divide-zinc-800/60">
                    <tr
                      v-for="contract in contracts"
                      :key="contract.id"
                      class="hover:bg-zinc-50/70 dark:hover:bg-zinc-850/40 transition-colors group cursor-pointer"
                      @click="openContractPreview(contract)"
                    >
                      <!-- Column 1: Contract Number / ID -->
                      <td class="py-3 px-4 align-middle">
                        <div v-if="contract.contract_number && contract.contract_number !== 'Pending Student ID'" class="font-mono font-semibold text-xs text-zinc-900 dark:text-zinc-100 group-hover:text-zinc-600 dark:group-hover:text-zinc-300 transition-colors tracking-tight">
                          {{ contract.contract_number }}
                        </div>
                        <div v-else class="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-md bg-zinc-100 dark:bg-zinc-800 text-zinc-600 dark:text-zinc-400 border border-zinc-200/80 dark:border-zinc-700/80 text-[11px] font-mono font-medium">
                          <span class="w-1.5 h-1.5 rounded-full bg-amber-500 animate-pulse"></span>
                          <span>Pending ID</span>
                        </div>
                        <div v-if="contract.student_id_assigned && contract.student_id_assigned !== contract.contract_number" class="text-[11px] font-mono text-zinc-400 mt-1 flex items-center gap-1">
                          <span class="text-zinc-300 dark:text-zinc-600">ID:</span>
                          <span class="font-medium text-zinc-600 dark:text-zinc-300">{{ contract.student_id_assigned }}</span>
                        </div>
                      </td>

                      <!-- Column 2: Tariff & Price -->
                      <td class="py-3 px-4 align-middle">
                        <div class="font-medium text-zinc-900 dark:text-zinc-100 text-xs leading-snug">
                          {{ contract.tariff_name || contract.title?.replace(/\s*shartnomasi\s*$/i, '') }}
                        </div>
                        <div v-if="contract.tariff_price" class="font-mono text-[11px] text-zinc-500 dark:text-zinc-400 mt-0.5">
                          {{ formatPrice(contract.tariff_price) }}
                        </div>
                      </td>

                      <!-- Column 3: Student & Passport (Expands naturally to fill available space) -->
                      <td class="py-3 px-4 align-middle">
                        <div v-if="contract.student_name" class="font-medium text-zinc-900 dark:text-zinc-100 text-xs leading-snug">
                          {{ contract.student_name }}
                        </div>
                        <div v-else class="text-zinc-400 italic text-[11px]">Unassigned</div>
                        <div class="text-[11px] text-zinc-400 flex items-center gap-1.5 mt-0.5 font-mono">
                          <span>{{ contract.passport_number || contract.student_passport || '—' }}</span>
                          <template v-if="contract.tenant_office_name">
                            <span class="text-zinc-300 dark:text-zinc-700">•</span>
                            <span class="font-sans text-zinc-500">{{ contract.tenant_office_name }}</span>
                          </template>
                        </div>
                      </td>

                      <!-- Column 4: Status + Contextual Action (At the right edge) -->
                      <td class="py-3 px-4 align-middle text-right" @click.stop>
                        <div class="flex items-center justify-end gap-2">
                        <!-- Pending status: shows badge + Tasdiqlash button / code -->
                        <div v-if="contract.status === 'pending'" class="flex items-center justify-end gap-2.5 flex-nowrap whitespace-nowrap">
                          <div class="flex flex-col items-end gap-0.5">
                            <span
                              class="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[11px] font-medium border leading-none"
                              :class="getStatusBadgeClass(contract.status)"
                            >
                              <span class="w-1.5 h-1.5 rounded-full shrink-0" :class="getStatusDotClass(contract.status)" />
                              <span>{{ getStatusLabel(contract.status) }}</span>
                            </span>
                            <span class="font-mono text-[10px] text-zinc-400 dark:text-zinc-500 pr-0.5 whitespace-nowrap">
                              {{ formatContractDate(contract.created_at) }}
                            </span>
                          </div>

                          <!-- Tasdiqlash Button (if code not generated yet) -->
                          <button
                            v-if="!contract.verification_code"
                            type="button"
                            @click.stop="openAssignModal(contract)"
                            class="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-zinc-900 hover:bg-black text-white dark:bg-zinc-100 dark:hover:bg-white dark:text-zinc-950 text-xs font-medium shadow-2xs transition-all active:scale-[0.98] cursor-pointer"
                            title="Student ID biriktirish va tasdiqlash kodi berish"
                          >
                            <KeyRound class="w-3.5 h-3.5 text-zinc-300 dark:text-zinc-600" />
                            <span>Tasdiqlash</span>
                          </button>

                          <!-- If Code Already Generated: Show Code + Copy + Regenerate -->
                          <template v-else>
                            <div class="inline-flex items-center gap-1.5 px-2.5 py-1 bg-zinc-100 dark:bg-zinc-800/80 border border-zinc-200/80 dark:border-zinc-700/80 rounded-lg" @click.stop>
                              <span class="font-mono font-semibold text-xs text-zinc-900 dark:text-zinc-100 tracking-wider">{{ contract.verification_code }}</span>
                              <button
                                type="button"
                                @click.stop="copyCodeToClipboard(contract.verification_code)"
                                class="p-0.5 hover:text-zinc-900 dark:hover:text-zinc-100 text-zinc-400 transition-colors cursor-pointer"
                                title="Kodni nusxalash"
                              >
                                <Check v-if="copyFeedback" class="w-3.5 h-3.5 text-emerald-500" />
                                <Copy v-else class="w-3.5 h-3.5" />
                              </button>
                            </div>
                            <button
                              type="button"
                              @click.stop="handleRegenerateCode(contract)"
                              :disabled="isRegenerating"
                              class="p-1.5 rounded-md text-zinc-400 hover:text-amber-600 hover:bg-zinc-100 dark:hover:bg-zinc-800 transition-colors cursor-pointer"
                              title="Kodni qayta olish"
                            >
                              <RotateCcw class="w-3.5 h-3.5 text-amber-500" :class="{ 'animate-spin': isRegenerating }" />
                            </button>
                          </template>
                        </div>

                        <!-- Rejected status: shows badge + permanent delete button -->
                        <div v-else-if="contract.status === 'rejected'" class="flex items-center justify-end gap-2.5 flex-nowrap whitespace-nowrap">
                          <div class="flex flex-col items-end gap-0.5">
                            <span
                              class="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[11px] font-medium border leading-none"
                              :class="getStatusBadgeClass(contract.status)"
                            >
                              <span class="w-1.5 h-1.5 rounded-full shrink-0" :class="getStatusDotClass(contract.status)" />
                              <span>{{ getStatusLabel(contract.status) }}</span>
                            </span>
                            <span class="font-mono text-[10px] text-zinc-400 dark:text-zinc-500 pr-0.5 whitespace-nowrap">
                              {{ formatContractDate(contract.created_at) }}
                            </span>
                          </div>

                          <button
                            type="button"
                            @click.stop="deletingContract = contract"
                            class="p-1.5 rounded-lg border border-rose-200 dark:border-rose-900/60 bg-rose-50/70 dark:bg-rose-950/40 text-rose-600 dark:text-rose-400 hover:bg-rose-100 dark:hover:bg-rose-900/60 transition-all cursor-pointer shadow-2xs active:scale-95"
                            title="Rad etilgan shartnomani bazadan butunlay o'chirib yuborish"
                          >
                            <Trash2 class="w-3.5 h-3.5" />
                          </button>
                        </div>

                        <!-- All other statuses (verified, signed, etc.): Flush right status badge + date -->
                        <div v-else class="flex flex-col items-end gap-1">
                          <span
                            class="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[11px] font-medium border leading-none"
                            :class="getStatusBadgeClass(contract.status)"
                          >
                            <span class="w-1.5 h-1.5 rounded-full shrink-0" :class="getStatusDotClass(contract.status)" />
                            <span>{{ getStatusLabel(contract.status) }}</span>
                          </span>
                          <span class="font-mono text-[10.5px] text-zinc-400 dark:text-zinc-500 pr-0.5 whitespace-nowrap">
                            {{ formatContractDate(contract.created_at) }}
                          </span>
                        </div>

                        <!-- Archive / Unarchive: available for any status, always shown -->
                        <button
                          type="button"
                          @click.stop="contract.is_archived ? handleUnarchive(contract) : handleArchive(contract)"
                          class="p-1.5 rounded-lg border transition-all cursor-pointer shadow-2xs active:scale-95 shrink-0"
                          :class="contract.is_archived
                            ? 'border-blue-200 dark:border-blue-900/60 bg-blue-50/70 dark:bg-blue-950/40 text-blue-600 dark:text-blue-400 hover:bg-blue-100 dark:hover:bg-blue-900/60'
                            : 'border-zinc-200 dark:border-zinc-700 bg-white dark:bg-zinc-850 text-zinc-400 hover:text-zinc-700 dark:hover:text-zinc-200 hover:bg-zinc-100 dark:hover:bg-zinc-800'"
                          :title="contract.is_archived ? 'Arxivdan qaytarish' : 'Arxivlash'"
                        >
                          <ArchiveRestore v-if="contract.is_archived" class="w-3.5 h-3.5" />
                          <Archive v-else class="w-3.5 h-3.5" />
                        </button>
                        </div>
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>
          </template>

        </div><!-- /right panel -->
      </div><!-- /split layout grid -->

    </template><!-- /VIEW B -->

    <!-- CREATE CONTRACT MODAL -->
    <ContractCreateDialog
      :is-open="isCreateDialogOpen"
      :initial-template-key="activeTariff?.name"
      :initial-content="tariffEditingContent"
      @close="isCreateDialogOpen = false"
      @created="handleContractCreated"
    />

    <!-- PREVIEW MODAL -->
    <ContractPreviewModal
      :is-open="!!previewContract"
      :contract="previewContract"
      @close="previewContract = null"
      @edit="handleOpenEditor"
      @assign="c => { previewContract = null; openAssignModal(c) }"
      @reject="c => { previewContract = null; openRejectModal(c) }"
      @regenerate="c => { previewContract = null; handleRegenerateCode(c) }"
      @duplicate="c => { previewContract = null; handleDuplicate(c) }"
      @delete="c => { previewContract = null; deletingContract = c }"
      @archive="c => { previewContract = null; handleArchive(c) }"
      @unarchive="c => { previewContract = null; handleUnarchive(c) }"
    />

    <!-- DELETE MODAL -->
    <BaseModal
      :is-open="!!deletingContract"
      :title="deletingContract?.status === 'rejected' ? 'Shartnomani butunlay o\'chirish' : 'Shartnomani o\'chirish'"
      :subtitle="deletingContract?.status === 'rejected' ? 'Ushbu amal shartnomani bazadan mutlaqo o\'chirib yuboradi' : 'Ushbu amal shartnomani ro\'yxatdan yashiradi'"
      max-width="max-w-md"
      @close="deletingContract = null"
    >
      <div class="p-6 space-y-4">
        <div class="flex items-start gap-3 p-3.5 bg-rose-50 dark:bg-rose-950/40 border border-rose-200 dark:border-rose-800 rounded-xl text-xs text-rose-700 dark:text-rose-300">
          <AlertTriangle class="w-5 h-5 text-rose-500 shrink-0 mt-0.5" />
          <div class="space-y-1.5">
            <span v-if="deletingContract?.status === 'rejected'">
              Rostdan ham rad etilgan <strong>{{ deletingContract?.contract_number !== 'Pending Student ID' ? deletingContract?.contract_number : (deletingContract?.student_name || deletingContract?.title) }}</strong> shartnomasini bazadan <strong>butunlay (permanently)</strong> o'chirib yubormoqchimisiz?
            </span>
            <span v-else>
              Rostdan ham <strong>{{ deletingContract?.title }}</strong> shartnomasini o'chirmoqchimisiz?
            </span>
            <p v-if="deletingContract?.status === 'rejected'" class="text-[11px] text-rose-600/90 dark:text-rose-400/90 font-medium">
              Eslatma: Ushbu amalni ortga qaytarib bo'lmaydi!
            </p>
          </div>
        </div>
        <div class="flex items-center justify-end gap-3 pt-2">
          <button type="button" @click="deletingContract = null" class="px-4 py-2 rounded-xl border border-zinc-200 dark:border-zinc-700 text-xs font-semibold text-zinc-600 dark:text-zinc-400 hover:bg-zinc-100 dark:hover:bg-zinc-800 transition-colors cursor-pointer">
            Bekor qilish
          </button>
          <button type="button" @click="confirmDelete" :disabled="isDeleting" class="px-5 py-2 rounded-xl bg-rose-600 hover:bg-rose-700 text-white text-xs font-bold transition-all shadow-xs cursor-pointer disabled:opacity-50">
            {{ isDeleting ? "O'chirilmoqda..." : (deletingContract?.status === 'rejected' ? "Butunlay o'chirish" : "O'chirish") }}
          </button>
        </div>
      </div>
    </BaseModal>

    <!-- 1. ASSIGN STUDENT ID & GENERATE VERIFICATION CODE MODAL -->
    <BaseModal
      :is-open="isAssignModalOpen"
      title="Assign Student ID & Generate Verification Code"
      subtitle="Link contract to student and issue agency verification code"
      max-width="max-w-lg"
      @close="isAssignModalOpen = false"
    >
      <div class="p-6 space-y-4">
        <!-- Student Info Summary -->
        <div class="p-3.5 bg-zinc-50 dark:bg-zinc-850 rounded-xl border border-zinc-200 dark:border-zinc-750 text-xs space-y-2">
          <div class="flex justify-between items-center">
            <span class="text-zinc-400">Student:</span>
            <span class="font-bold text-zinc-800 dark:text-zinc-200">{{ assigningContract?.student_name || '—' }}</span>
          </div>
          <div class="flex justify-between items-center">
            <span class="text-zinc-400">Passport:</span>
            <span class="font-mono font-semibold text-zinc-800 dark:text-zinc-200">{{ assigningContract?.passport_number || assigningContract?.student_passport || '—' }}</span>
          </div>
          <div v-if="assigningContract?.tariff_name" class="flex justify-between items-center">
            <span class="text-zinc-400">Tariff:</span>
            <span class="font-semibold text-zinc-800 dark:text-zinc-200">{{ assigningContract.tariff_name }}</span>
          </div>
        </div>

        <!-- Student ID Input -->
        <div>
          <label class="block text-xs font-bold text-zinc-700 dark:text-zinc-300 mb-1">
            Student ID (e.g. G108) <span class="text-rose-500">*</span>
          </label>
          <input
            v-model="assignStudentIdInput"
            type="text"
            placeholder="Enter Student ID (e.g. G108)"
            class="w-full px-3.5 py-2.5 bg-zinc-50 dark:bg-zinc-850 border border-zinc-200 dark:border-zinc-700 rounded-xl text-sm font-mono font-bold uppercase tracking-wider focus:outline-none focus:border-zinc-400 dark:focus:border-zinc-500"
            @keyup.enter="handleConfirmAssignStudentId"
          />
          <p class="text-[11px] text-zinc-400 mt-1.5 leading-relaxed">
            <strong>This ID becomes the student's contract number.</strong>
          </p>
        </div>

        <!-- Discount Input -->
        <div>
          <label class="block text-xs font-bold text-zinc-700 dark:text-zinc-300 mb-1">
            Chegirma miqdori (so'm) <span class="text-zinc-400 font-normal">(ixtiyoriy)</span>
          </label>
          <input
            v-model="assignDiscountInput"
            type="number"
            min="0"
            step="1000"
            placeholder="0 — chegirma yo'q"
            class="w-full px-3.5 py-2.5 bg-zinc-50 dark:bg-zinc-850 border border-zinc-200 dark:border-zinc-700 rounded-xl text-sm font-mono focus:outline-none focus:border-zinc-400 dark:focus:border-zinc-500"
          />
          <p class="text-[11px] text-zinc-400 mt-1.5 leading-relaxed">
            Shartnomadagi <code v-pre class="bg-zinc-100 dark:bg-zinc-800 px-1 rounded">{{discount}}</code> o'rnini bosadi va to'lovga qo'shiladi.
          </p>
        </div>

        <!-- Explanation Link -->
        <div class="p-3 bg-zinc-50 dark:bg-zinc-850 border border-zinc-200 dark:border-zinc-750 rounded-xl text-[11.5px] text-zinc-600 dark:text-zinc-400 flex items-start justify-between gap-2">
          <span>Assigns the ID, links the CRM record, and issues a 24-hour code.</span>
          <button
            type="button"
            @click="showStaffExplanationModal = true"
            class="underline font-bold shrink-0 text-zinc-800 dark:text-zinc-200 hover:text-zinc-950 dark:hover:text-white cursor-pointer"
          >
            ⓘ What is this?
          </button>
        </div>

        <!-- Error -->
        <div v-if="assignError" class="p-3 bg-rose-50 dark:bg-rose-950/50 border border-rose-200 dark:border-rose-800 rounded-xl text-xs text-rose-600">
          {{ assignError }}
        </div>

        <!-- Actions -->
        <div class="flex items-center justify-end gap-3 pt-2">
          <button
            type="button"
            @click="isAssignModalOpen = false"
            class="px-4 py-2 rounded-xl border border-zinc-200 dark:border-zinc-700 text-xs font-semibold text-zinc-600 dark:text-zinc-400 hover:bg-zinc-100 dark:hover:bg-zinc-800 transition-colors cursor-pointer"
          >
            Cancel
          </button>
          <button
            type="button"
            @click="handleConfirmAssignStudentId"
            :disabled="isAssigning"
            class="inline-flex items-center gap-1.5 px-5 py-2 rounded-xl bg-zinc-900 hover:bg-black dark:bg-zinc-100 dark:hover:bg-white text-white dark:text-zinc-950 text-xs font-bold transition-all shadow-xs cursor-pointer disabled:opacity-50"
          >
            <Loader2 v-if="isAssigning" class="w-3.5 h-3.5 animate-spin" />
            <KeyRound v-else class="w-3.5 h-3.5" />
            <span>Assign & Generate Code</span>
          </button>
        </div>
      </div>
    </BaseModal>

    <!-- 2. VERIFICATION CODE RESULT MODAL -->
    <BaseModal
      :is-open="showVerificationCodeResultModal"
      title="Verification Code Generated"
      subtitle="Provide this code to the student to complete verification"
      max-width="max-w-md"
      @close="showVerificationCodeResultModal = false"
    >
      <div class="p-6 space-y-4">
        <div class="p-4 bg-emerald-50 dark:bg-emerald-950/40 border border-emerald-200 dark:border-emerald-800 rounded-xl text-center space-y-3">
          <div class="text-xs text-zinc-500 dark:text-zinc-400">
            Student ID: <span class="font-bold text-zinc-900 dark:text-white font-mono">{{ generatedCodeResult?.student_id }}</span>
            &nbsp;•&nbsp;
            Contract Number: <span class="font-bold text-zinc-900 dark:text-white font-mono">{{ generatedCodeResult?.contract_number }}</span>
          </div>

          <div v-if="generatedCodeResult?.discount && Number(generatedCodeResult.discount) > 0" class="text-xs text-emerald-700 dark:text-emerald-400">
            Chegirma: <span class="font-bold font-mono">{{ Number(generatedCodeResult.discount).toLocaleString('uz-UZ') }} so'm</span>
          </div>

          <div class="text-[11px] uppercase tracking-wider font-bold text-emerald-700 dark:text-emerald-400">
            Verification Code:
          </div>

          <div class="py-2.5 px-4 bg-white dark:bg-zinc-900 rounded-lg border border-emerald-300 dark:border-emerald-700/80 font-mono text-xl sm:text-2xl font-black text-zinc-900 dark:text-white tracking-widest select-all">
            {{ generatedCodeResult?.verification_code }}
          </div>

          <div class="flex items-center justify-center gap-2">
            <button
              type="button"
              @click="copyCodeToClipboard(generatedCodeResult?.verification_code || '')"
              class="inline-flex items-center gap-1.5 px-4 py-1.5 rounded-lg bg-zinc-900 hover:bg-black dark:bg-zinc-100 dark:hover:bg-white text-white dark:text-zinc-950 text-xs font-bold transition-all shadow-xs cursor-pointer"
            >
              <Check v-if="copyFeedback" class="w-3.5 h-3.5" />
              <Copy v-else class="w-3.5 h-3.5" />
              <span>{{ copyFeedback ? 'Copied!' : 'Copy Code' }}</span>
            </button>
          </div>

          <div class="text-[11px] text-zinc-500 dark:text-zinc-400 flex items-center justify-center gap-1">
            <FileClock class="w-3.5 h-3.5 text-amber-500" />
            <span>Expires in 24 hours</span>
          </div>
        </div>

        <div class="p-3 bg-zinc-50 dark:bg-zinc-850 rounded-xl border border-zinc-200 dark:border-zinc-750 text-xs text-zinc-600 dark:text-zinc-400 space-y-1">
          <p class="font-bold text-zinc-800 dark:text-zinc-200">Send this code to the student.</p>
          <p class="text-[11px] leading-relaxed">
            They enter it + their password in <strong>Shartnomalarim</strong> to become <strong>VERIFIED</strong>.
          </p>
        </div>

        <div class="flex justify-end pt-2">
          <button
            type="button"
            @click="showVerificationCodeResultModal = false"
            class="px-5 py-2 rounded-xl bg-zinc-900 dark:bg-white text-white dark:text-zinc-900 text-xs font-bold transition-colors cursor-pointer"
          >
            Done
          </button>
        </div>
      </div>
    </BaseModal>

    <!-- 3. REJECT CONTRACT MODAL -->
    <BaseModal
      :is-open="isRejectModalOpen"
      title="Reject Contract"
      subtitle="Give a reason for rejecting this submission"
      max-width="max-w-md"
      @close="isRejectModalOpen = false"
    >
      <div class="p-6 space-y-4">
        <div class="text-xs text-zinc-500">
          Rejecting contract for: <strong class="text-zinc-800 dark:text-zinc-200">{{ rejectingContract?.student_name }}</strong>
        </div>

        <div>
          <label class="block text-xs font-bold text-zinc-700 dark:text-zinc-300 mb-1">
            Reason for rejection <span class="text-rose-500">*</span>
          </label>
          <textarea
            v-model="rejectionReasonInput"
            rows="3"
            placeholder="Reason (e.g. wrong passport, wrong tariff)..."
            class="w-full px-3 py-2 bg-zinc-50 dark:bg-zinc-850 border border-zinc-200 dark:border-zinc-700 rounded-xl text-xs focus:outline-none focus:border-rose-500"
          ></textarea>
        </div>

        <div v-if="rejectError" class="p-2.5 bg-rose-50 dark:bg-rose-950/50 border border-rose-200 dark:border-rose-800 rounded-xl text-xs text-rose-600">
          {{ rejectError }}
        </div>

        <div class="flex items-center justify-end gap-3 pt-2">
          <button
            type="button"
            @click="isRejectModalOpen = false"
            class="px-4 py-2 rounded-xl border border-zinc-200 dark:border-zinc-700 text-xs font-semibold text-zinc-600 dark:text-zinc-400 hover:bg-zinc-100 dark:hover:bg-zinc-800 transition-colors cursor-pointer"
          >
            Cancel
          </button>
          <button
            type="button"
            @click="handleConfirmReject"
            :disabled="isRejecting"
            class="inline-flex items-center gap-1.5 px-5 py-2 rounded-xl bg-rose-600 hover:bg-rose-700 text-white text-xs font-bold transition-all shadow-xs cursor-pointer disabled:opacity-50"
          >
            <Loader2 v-if="isRejecting" class="w-3.5 h-3.5 animate-spin" />
            <Ban v-else class="w-3.5 h-3.5" />
            <span>Reject Contract</span>
          </button>
        </div>
      </div>
    </BaseModal>

    <!-- 4. STAFF EXPLANATION MODAL (Section 18 & 37) -->
    <BaseModal
      :is-open="showStaffExplanationModal"
      title="WHAT IS THE VERIFICATION CODE?"
      subtitle="Quick guide for staff"
      max-width="max-w-lg"
      @close="showStaffExplanationModal = false"
    >
      <div class="p-6 space-y-4 text-xs text-zinc-700 dark:text-zinc-300 leading-relaxed">
        <p class="font-medium">
          A one-time code generated after you assign the Student ID.
        </p>

        <ol class="space-y-2 list-decimal list-inside bg-zinc-50 dark:bg-zinc-850 p-4 rounded-xl border border-zinc-200 dark:border-zinc-750">
          <li>Enter the <strong>Student ID</strong> (e.g. G108).</li>
          <li>Click <strong>'Tasdiqlash'</strong>.</li>
          <li>System generates a code (format: <code>XXXX-XXXX-STUDENTID</code>).</li>
          <li><strong>Copy</strong> and <strong>send it to the student</strong>.</li>
          <li>Student enters it + their password in <strong>'Shartnomalarim'</strong>.</li>
          <li>Correct code + password → contract becomes <strong>VERIFIED</strong>.</li>
        </ol>

        <div class="p-3 bg-amber-50 dark:bg-amber-950/40 border border-amber-200 dark:border-amber-800 rounded-xl text-amber-800 dark:text-amber-300 text-[11.5px]">
          <strong>IMPORTANT:</strong> Generating the code alone does <em>not</em> verify the contract — only the student entering it does.
        </div>

        <div class="flex justify-end pt-2">
          <button
            type="button"
            @click="showStaffExplanationModal = false"
            class="px-5 py-2 rounded-xl bg-zinc-900 hover:bg-black dark:bg-zinc-100 dark:hover:bg-white text-white dark:text-zinc-950 text-xs font-bold transition-colors cursor-pointer"
          >
            I Understand
          </button>
        </div>
      </div>
    </BaseModal>

  </div>
</template>

<style>
.tariff-preview-sheet {
  font-family: 'Times New Roman', Times, Georgia, serif !important;
}
.tariff-preview-sheet,
.tariff-preview-sheet * {
  font-family: 'Times New Roman', Times, Georgia, serif !important;
}
.tariff-preview-sheet table {
  width: 100% !important;
  border-collapse: collapse !important;
  margin: 12px 0 !important;
}
.tariff-preview-sheet table,
.tariff-preview-sheet th,
.tariff-preview-sheet td {
  border: 1px solid #52525b !important;
  padding: 6px 8px !important;
}
.tariff-preview-sheet th {
  background-color: #f4f4f5 !important;
  font-weight: bold !important;
  text-align: center !important;
}
.tariff-preview-sheet p {
  margin: 6px 0 !important;
  text-align: justify !important;
  line-height: 1.55 !important;
}
.tariff-preview-sheet h1,
.tariff-preview-sheet h2,
.tariff-preview-sheet h3 {
  font-weight: bold !important;
  text-align: center !important;
  margin: 14px 0 6px !important;
}
@media print {
  .tariff-preview-sheet {
    page-break-after: always !important;
    break-after: page !important;
    box-shadow: none !important;
    border: none !important;
    margin: 0 !important;
    padding: 15mm 15mm !important;
    width: 100% !important;
    min-height: auto !important;
  }
}
</style>
