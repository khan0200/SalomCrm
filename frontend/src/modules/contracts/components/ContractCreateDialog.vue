<script setup lang="ts">
import { ref, computed, watch, nextTick, onBeforeUnmount } from 'vue'
import { useQuery } from '@tanstack/vue-query'
import {
  Search,
  Check,
  Copy,
  Globe,
  ArrowRight,
  ArrowLeft,
  ShieldAlert,
  Contact,
  UserRound,
  BookOpenCheck,
  CreditCard,
  GraduationCap,
  Building2,
  Phone,
  Wallet,
  BadgePercent,
  ChevronDown,
} from 'lucide-vue-next'
import BaseModal from '@/components/common/BaseModal.vue'
import { studentsApi } from '@/api/students'
import { contractsApi, type Contract, type ContractCreatePayload } from '@/api/contracts'
import { settingsApi } from '@/api/settings'
import { formatUzPhoneInput, formatPhoneValue } from '@/utils/phone'
import { useCurrency } from '@/composables/useCurrency'
import { CONTRACT_TEMPLATES, getContractTemplate, type ContractTemplate } from '../contractTemplates'
import { resolveContractVariables, buildVariableValues } from '../utils/contractVariables'
import {
  isCanvasDocumentJson,
  deserializeCanvasDocument,
  convertCanvasDocumentToHtml,
} from '../utils/contractCanvasConverter'
import { useUiStore } from '@/stores/ui'
import { useAuthStore } from '@/stores/auth'
import type { Student } from '@/types'

const props = defineProps<{
  isOpen: boolean
}>()

const emit = defineEmits<{
  close: []
  created: [contract: Contract]
}>()

const uiStore = useUiStore()
const authStore = useAuthStore()
const { formatAmountInput, parseAmount, formatCurrency } = useCurrency()

// ── Education Level options from Settings ────────────────────────────────
const { data: levelsData } = useQuery({
  queryKey: ['settings-education-levels', computed(() => authStore.activeTenantId)],
  queryFn: () => settingsApi.getLevels(),
  staleTime: 1000 * 60 * 5,
})

const levelOptions = computed<string[]>(() => {
  const raw = levelsData.value as any
  const list = Array.isArray(raw) ? raw : (raw?.results || [])
  return list.map((item: any) => (typeof item === 'string' ? item : item.name)).filter(Boolean)
})

// ── Branch / Office options from Settings ────────────────────────────────
const { data: officesData } = useQuery({
  queryKey: ['settings-branches', computed(() => authStore.activeTenantId)],
  queryFn: () => settingsApi.getOffices(),
  staleTime: 1000 * 60 * 5,
})

const branchOptions = computed<string[]>(() => {
  const raw = officesData.value as any
  const list = Array.isArray(raw) ? raw : (raw?.results || [])
  return list.map((item: any) => (typeof item === 'string' ? item : item.name)).filter(Boolean)
})

// ── Tariffs from Settings ────────────────────────────────────────────────
const { data: tariffsData } = useQuery({
  queryKey: ['settings-tariffs', computed(() => authStore.activeTenantId)],
  queryFn: () => settingsApi.getTariffs(),
  staleTime: 1000 * 60 * 5,
})

// ── Wizard step ──────────────────────────────────────────────────────────
type Step = 'form' | 'preview' | 'done'
const step = ref<Step>('form')

// ── Template (Default: Select bo'lsin) ────────────────────────────────────
const selectedTemplateKey = ref<string>('')
const templateList = computed(() => {
  const raw = tariffsData.value as any
  const list = Array.isArray(raw) ? raw : (raw?.results || [])
  const dynamicTemplates: ContractTemplate[] = list.map((t: any) => {
    const knownTpl = getContractTemplate(t.name)
    const priceFormatted = t.price ? `${Number(t.price).toLocaleString()} UZS` : (knownTpl?.priceDisplay || '')
    return {
      key: t.name,
      title: knownTpl?.title || `${t.name} SHARTNOMASI`,
      subtitle: knownTpl?.subtitle || "Janubiy Koreya ta'lim konsalting xizmati shartnomasi",
      priceDisplay: priceFormatted,
      duration: knownTpl?.duration || "270 kalendar kuni",
      pdfFile: knownTpl?.pdfFile,
      fullText: t.contract_text || knownTpl?.fullText || "<h1>CONTRACT N: ______</h1><p style=\"text-align:center;\"><strong>AGREEMENT</strong></p><p><br></p>",
    }
  })

  const baseList = dynamicTemplates.length > 0 ? dynamicTemplates : Object.values(CONTRACT_TEMPLATES)

  return [
    ...baseList,
    {
      key: 'BLANK',
      title: "Blank Document",
      subtitle: "Write contract text from scratch",
      priceDisplay: "Custom",
      duration: "Unlimited",
      fullText: "<h1>CONTRACT N: ______</h1><p style=\"text-align:center;\"><strong>AGREEMENT</strong></p><p><br></p>"
    } as ContractTemplate
  ]
})
const selectedTemplate = computed(() => {
  if (!selectedTemplateKey.value) return null
  return templateList.value.find(t => t.key === selectedTemplateKey.value) || null
})

// ── Student: live fullname autocomplete ─────────────────────────────────
const fullNameQuery = ref('')
const isNameFocused = ref(false)
const selectedExistingStudent = ref<Student | null>(null)

const { data: suggestData, isFetching: isSuggestLoading } = useQuery({
  queryKey: ['contract-create-student-suggest', fullNameQuery],
  queryFn: () => studentsApi.getStudents({ search: fullNameQuery.value, page_size: 8 }),
  enabled: computed(() => fullNameQuery.value.trim().length >= 2 && !selectedExistingStudent.value),
  staleTime: 1000 * 30,
})

const suggestions = computed<Student[]>(() => {
  if (selectedExistingStudent.value) return []
  return ((suggestData.value as any)?.results || []).slice(0, 8)
})

const showSuggestions = computed(() => isNameFocused.value && fullNameQuery.value.trim().length >= 2 && (isSuggestLoading.value || suggestions.value.length > 0))

function handleNameBlur() {
  setTimeout(() => { isNameFocused.value = false }, 150)
}

// Mirrors backend normalize_date_to_iso() for the common separators - CRM
// records predate the strict 'YYYY-MM-DD' convention, so an existing
// student's st.birthday can still arrive as DD.MM.YYYY etc.
function normalizeDateToIso(val: string): string {
  const s = (val || '').trim()
  if (!s) return ''
  if (/^\d{4}-\d{2}-\d{2}$/.test(s)) return s
  const m1 = s.match(/^(\d{1,2})[\s.\/-](\d{1,2})[\s.\/-](\d{4})$/)
  if (m1) {
    let d = parseInt(m1[1], 10)
    let m = parseInt(m1[2], 10)
    const y = parseInt(m1[3], 10)
    if (m > 12 && d <= 12) { [d, m] = [m, d] }
    return `${y.toString().padStart(4, '0')}-${m.toString().padStart(2, '0')}-${d.toString().padStart(2, '0')}`
  }
  const m2 = s.match(/^(\d{4})[\s.\/-](\d{1,2})[\s.\/-](\d{1,2})$/)
  if (m2) {
    const y = parseInt(m2[1], 10)
    const m = parseInt(m2[2], 10)
    const d = parseInt(m2[3], 10)
    return `${y.toString().padStart(4, '0')}-${m.toString().padStart(2, '0')}-${d.toString().padStart(2, '0')}`
  }
  return ''
}

function pickExistingStudent(st: Student) {
  selectedExistingStudent.value = st
  fullNameQuery.value = st.full_name
  studentIdAssigned.value = st.id
  isNameFocused.value = false

  passportNumber.value = st.passport || ''
  educationLevel.value = st.level || ''
  dateOfBirth.value = normalizeDateToIso(st.birthday || '')
  office.value = st.office || ''
  phone1.value = formatPhoneValue(st.phone1)
  phone2.value = formatPhoneValue(st.phone2)
  if (st.discount && Number(st.discount) > 0) {
    discount.value = formatAmountInput(String(st.discount))
  }

  // Auto-select tariff template if student already has a matching tariff
  if (st.tariff) {
    const tpl = getContractTemplate(st.tariff)
    if (tpl) {
      selectedTemplateKey.value = tpl.key
    } else {
      const clean = st.tariff.trim().toLowerCase()
      const match = templateList.value.find(
        t => t.key.toLowerCase() === clean ||
             t.title.toLowerCase().includes(clean) ||
             clean.includes(t.key.toLowerCase())
      )
      if (match) {
        selectedTemplateKey.value = match.key
      }
    }
  }
}

// Typing after a match was picked un-picks it, dropping back to manual entry.
watch(fullNameQuery, (val) => {
  if (selectedExistingStudent.value && val !== selectedExistingStudent.value.full_name) {
    selectedExistingStudent.value = null
  }
})

// ── Manual fields (new OR existing - always editable) ───────────────────
const studentIdAssigned = ref('')
const passportNumber = ref('')
const educationLevel = ref('')
// Always kept as strict ISO 'YYYY-MM-DD' (or '') - the sole source of
// truth submitted to the backend (date_of_birth) and stored on Student.
// The 3 day/month/year dropdowns below only ever read/write through this.
const dateOfBirth = ref('')
const office = ref('')
const phone1 = ref('')
const phone2 = ref('')
// Read-only display, always the selected tariff's price - never
// separately typed (see the Narx field in the template, which is
// readonly), so this just mirrors selectedTemplate instead of being its
// own state that could fall out of sync with it.
const tariffPrice = computed(() => selectedTemplate.value?.priceDisplay || '')
const discount = ref<string>('')

// ── Date of birth: 3 separate day/month/year dropdowns instead of a
// native <input type="date"> (illegible in some browsers/OSes). These are
// the only things the template binds to; dateOfBirth itself is derived
// and is what actually gets submitted/validated, so there's exactly one
// path into the ISO string the backend expects.
const dobDay = ref<number | null>(null)
const dobMonth = ref<number | null>(null)
const dobYear = ref<number | null>(null)
const dobDays = Array.from({ length: 31 }, (_, i) => i + 1)
const dobMonths = Array.from({ length: 12 }, (_, i) => i + 1)
const dobCurrentYear = new Date().getFullYear()
const dobYears = Array.from({ length: 90 }, (_, i) => dobCurrentYear - i)

function syncDobToIso() {
  if (dobDay.value && dobMonth.value && dobYear.value) {
    dateOfBirth.value = `${dobYear.value}-${String(dobMonth.value).padStart(2, '0')}-${String(dobDay.value).padStart(2, '0')}`
  } else {
    dateOfBirth.value = ''
  }
}

// Keeps the 3 dropdowns in sync whenever dateOfBirth changes from
// elsewhere (existing-student autocomplete, form reset) - not just when
// the user operates the dropdowns themselves.
watch(dateOfBirth, (iso) => {
  const m = /^(\d{4})-(\d{2})-(\d{2})$/.exec(iso || '')
  if (m) {
    dobYear.value = parseInt(m[1], 10)
    dobMonth.value = parseInt(m[2], 10)
    dobDay.value = parseInt(m[3], 10)
  } else {
    dobYear.value = null
    dobMonth.value = null
    dobDay.value = null
  }
}, { immediate: true })

const isNewStudent = computed(() => !selectedExistingStudent.value)

// ── Minor detection (mirrors backend's age calc) ─────────────────────────
const isMinor = computed(() => {
  if (!dateOfBirth.value) return false
  const d = new Date(dateOfBirth.value)
  if (isNaN(d.getTime())) return false
  const today = new Date()
  let age = today.getFullYear() - d.getFullYear()
  const hasHadBirthdayThisYear = (today.getMonth() > d.getMonth()) ||
    (today.getMonth() === d.getMonth() && today.getDate() >= d.getDate())
  if (!hasHadBirthdayThisYear) age -= 1
  return age < 18
})

// ── Guardian sub-form (minors only) ──────────────────────────────────────
const guardianFullName = ref('')
const guardianPassportNumber = ref('')
const guardianRelation = ref('')
const guardianPhone = ref('')
const guardianAddress = ref('')

// ── Contract metadata ─────────────────────────────────────────────────────
// Contract Number always mirrors the Student ID (existing or staff-typed
// for a new student) - matches assign_student_id's own convention
// elsewhere (contract_number := student_id), so this is derived, never a
// separately-typed value.
const customContractNumber = computed(() => {
  return selectedExistingStudent.value ? selectedExistingStudent.value.id : studentIdAssigned.value.trim().toUpperCase()
})
// Also always derived, never typed - mirrors the template + student name.
const customTitle = computed(() => {
  const tplTitle = selectedTemplate.value ? selectedTemplate.value.title.replace(' SHARTNOMASI', '') : 'SHARTNOMA'
  const name = fullNameQuery.value.trim()
  return name ? `${tplTitle} - ${name.toUpperCase()}` : `${tplTitle} SHARTNOMASI`
})

// ── Resolved preview content ──────────────────────────────────────────────
const previewStudentShape = computed(() => ({
  full_name: fullNameQuery.value.trim().toUpperCase(),
  passport_number: passportNumber.value.trim().toUpperCase(),
  date_of_birth: dateOfBirth.value,
  level: educationLevel.value,
  office: office.value,
  phone1: phone1.value,
  phone2: phone2.value,
  tariff_price: tariffPrice.value,
  discount: discount.value ? parseAmount(discount.value) : 0,
}))

// Array of per-page HTML, not one flat string - a canvas-contract document
// (see ContractDocumentEditor.vue / contractCanvasConverter.ts) can be
// several fixed 297mm-tall A4 pages, and flattening them into one v-html
// blob loses the page breaks entirely (each page's "isLastPage" ends up
// true since convertCanvasDocumentToHtml was called once per page), so
// a 4-page contract visually collapsed into one long unbroken column.
// Rendering each page as its own block (mirrors ContractPreviewModal.vue's
// splitPages pattern) keeps the actual page boundaries visible.
const previewPages = computed<string[]>(() => {
  const templateContent = selectedTemplate.value?.fullText || '<p></p>'
  const meta = {
    contractNumber: customContractNumber.value,
    templateName: selectedTemplate.value?.key || '',
    price: tariffPrice.value,
  }

  if (isCanvasDocumentJson(templateContent)) {
    const doc = deserializeCanvasDocument(templateContent)
    if (doc) {
      const vars = buildVariableValues(previewStudentShape.value, meta)
      const totalPages = doc.pages.length
      // Each page is converted from a single-page slice (so contract
      // page-break CSS/markers stay per-page), which on its own would
      // make every page compute pageIdx=0/totalPages=1 for {{page_number}}
      // - pageNumbering supplies this page's real position in the full
      // document instead.
      return doc.pages.map((p, pageOffset) =>
        convertCanvasDocumentToHtml({ ...doc, pages: [p] }, vars, { pageOffset, totalPages })
      )
    }
  }

  return [resolveContractVariables(templateContent, previewStudentShape.value, meta)]
})

// Flattened for submission - the backend's Contract.content is a single
// TextField, same shape every other creation path already saves, and the
// student signing page (contract_sign_views.ContractSignStatusView)
// serves this value verbatim with no further token substitution, so it
// MUST already be fully rendered (unlike ContractPreviewModal.vue, which
// re-renders {{tokens}} from the Contract row's own columns and so could
// safely take raw template+tokens instead - that asymmetry is why this
// stays rendered HTML rather than switching to saving the raw template).
// Pages are joined with the same <hr data-page-break="true" /> marker
// ContractPreviewModal.vue/contractPdf.ts already split non-canvas
// content on, so a canvas-contract's page boundaries survive being
// flattened into one TextField instead of collapsing into one sheet.
const previewHtml = computed(() => previewPages.value.join('<hr data-page-break="true" />'))

// Saved alongside the flattened content above, into Contract.canvas_source -
// the ORIGINAL canvas-contract JSON, {{tokens}} still unresolved. PDF
// export (contractPdf.ts) needs this exact structured, per-page-sized
// source to lay the document out correctly; content's flattened HTML
// collapses each page's fixed 210x297mm sizing and corrupts the PDF
// layout. Blank for non-canvas (plain HTML) tariffs - there's no
// structured source to preserve there, `content` alone is sufficient.
const canvasSourceToSave = computed<string>(() => {
  const templateContent = selectedTemplate.value?.fullText || ''
  return isCanvasDocumentJson(templateContent) ? templateContent : ''
})

// Canvas tariffs render as fixed 210x297mm A4 pages (contractCanvasConverter.ts
// hard-codes PAGE_WIDTH_MM/PAGE_HEIGHT_MM), which overflow the New
// Contract dialog's narrower body - without scaling, pages get clipped.
// The browser's own mm->px conversion (96dpi => 1mm = 96/25.4px) is used
// instead of measuring the rendered element, since that measurement
// proved unreliable (0 or stale right after a step change, before v-html
// content has actually painted) - this way the scale is correct on the
// very first render, no observer race possible, and every page in a
// multi-page contract scales identically since they all share one fixed
// source size.
const isCanvasPreview = computed(() => isCanvasDocumentJson(selectedTemplate.value?.fullText || ''))
const PAGE_WIDTH_PX = 210 * (96 / 25.4)
const PAGE_HEIGHT_PX = 297 * (96 / 25.4)
const previewWrapperRef = ref<HTMLElement | null>(null)
const previewWrapperWidth = ref(0)
const previewScale = computed(() => {
  if (!previewWrapperWidth.value) return 1
  return Math.min(1, previewWrapperWidth.value / PAGE_WIDTH_PX)
})

let wrapperResizeObserver: ResizeObserver | null = null

watch(previewWrapperRef, (el) => {
  wrapperResizeObserver?.disconnect()
  wrapperResizeObserver = null
  if (el) {
    previewWrapperWidth.value = el.clientWidth
    wrapperResizeObserver = new ResizeObserver((entries) => {
      const width = entries[0]?.contentRect.width
      if (width) previewWrapperWidth.value = width
    })
    wrapperResizeObserver.observe(el)
  }
})

onBeforeUnmount(() => wrapperResizeObserver?.disconnect())

// ── Validation ─────────────────────────────────────────────────────────────
const errorMessage = ref('')

function validateForm(): string {
  if (!selectedTemplateKey.value) return "Please select a tariff"
  if (!fullNameQuery.value.trim()) return "Enter the student's full name"
  if (isNewStudent.value && !studentIdAssigned.value.trim()) return "Enter a Student ID"
  if (!passportNumber.value.trim()) return "Enter the passport number"
  if (!dateOfBirth.value.trim()) return "Enter the date of birth"
  if (isMinor.value) {
    if (!guardianFullName.value.trim()) return "Enter the guardian's full name"
    if (!guardianPassportNumber.value.trim()) return "Enter the guardian's passport number"
    if (!guardianRelation.value.trim()) return "Enter the guardian's relation to the student"
    if (!guardianPhone.value.trim()) return "Enter the guardian's phone number"
    if (!guardianAddress.value.trim()) return "Enter the guardian's address"
  }
  return ''
}

function goToPreview() {
  const err = validateForm()
  if (err) {
    errorMessage.value = err
    return
  }
  errorMessage.value = ''
  step.value = 'preview'
}

// ── Submit / create ────────────────────────────────────────────────────────
const isSubmitting = ref(false)
const createdContract = ref<Contract | null>(null)
const isCopiedSignLink = ref(false)

const signLinkUrl = computed(() => {
  if (!createdContract.value?.sign_token) return ''
  const origin = typeof window !== 'undefined' ? window.location.origin : 'http://localhost:3000'
  return `${origin}/sign/${createdContract.value.sign_token}`
})

async function copySignLink() {
  const url = signLinkUrl.value
  if (!url) return
  try {
    if (navigator?.clipboard?.writeText) {
      await navigator.clipboard.writeText(url)
    } else {
      const textArea = document.createElement('textarea')
      textArea.value = url
      document.body.appendChild(textArea)
      textArea.select()
      document.execCommand('copy')
      document.body.removeChild(textArea)
    }
    isCopiedSignLink.value = true
    uiStore.addToast({
      type: 'success',
      title: 'Link copied!',
      message: `${url} copied to clipboard. You can now send it to the student.`,
      duration: 4000
    })
    setTimeout(() => { isCopiedSignLink.value = false }, 2500)
  } catch (err) {
    console.error('Failed to copy sign link:', err)
  }
}

async function handleCreate() {
  isSubmitting.value = true
  errorMessage.value = ''

  try {
    const resolvedContent = previewHtml.value
    const numericDiscount = discount.value ? parseAmount(discount.value) : 0
    // tariffPrice is a display string (e.g. "13 000 000 UZS") - the
    // backend's tariff_price is a plain DecimalField and 400s on anything
    // that isn't a bare number, so strip it down the same way parseAmount
    // already does for discount.
    const numericTariffPrice = tariffPrice.value ? parseAmount(tariffPrice.value) : 0

    const payload: ContractCreatePayload = {
      student: selectedExistingStudent.value?.id || null,
      contract_number: customContractNumber.value || undefined,
      title: customTitle.value || 'CONTRACT',
      template_name: selectedTemplate.value?.key,
      content: resolvedContent,
      canvas_source: canvasSourceToSave.value || undefined,
      status: 'draft',
      passport_number: passportNumber.value.trim().toUpperCase(),
      full_name: fullNameQuery.value.trim().toUpperCase(),
      education_level: educationLevel.value.trim() || undefined,
      date_of_birth: dateOfBirth.value.trim(),
      office: office.value.trim() || undefined,
      phone1: phone1.value.trim() || undefined,
      phone2: phone2.value.trim() || undefined,
      tariff_name: selectedTemplate.value?.key,
      tariff_price: numericTariffPrice > 0 ? String(numericTariffPrice) : undefined,
      discount: numericDiscount > 0 ? String(numericDiscount) : undefined,
    }

    const assignedId = selectedExistingStudent.value ? selectedExistingStudent.value.id : studentIdAssigned.value.trim()
    if (assignedId) {
      payload.student_id_assigned = assignedId.toUpperCase()
    }

    if (isMinor.value) {
      payload.guardian_full_name = guardianFullName.value.trim().toUpperCase()
      payload.guardian_passport_number = guardianPassportNumber.value.trim().toUpperCase()
      payload.guardian_relation = guardianRelation.value.trim()
      payload.guardian_phone = guardianPhone.value.trim()
      payload.guardian_address = guardianAddress.value.trim()
    }

    const created = await contractsApi.createContract(payload)
    createdContract.value = created
    step.value = 'done'
    emit('created', created)
  } catch (err: any) {
    console.error('Failed to create contract:', err)
    errorMessage.value = err.response?.data?.detail || "Something went wrong while saving the contract"
    step.value = 'form'
  } finally {
    isSubmitting.value = false
  }
}

// ── Reset on open ──────────────────────────────────────────────────────────
watch(
  () => props.isOpen,
  (val) => {
    if (val) {
      step.value = 'form'
      errorMessage.value = ''
      selectedTemplateKey.value = ''
      fullNameQuery.value = ''
      selectedExistingStudent.value = null
      isNameFocused.value = false
      studentIdAssigned.value = ''
      passportNumber.value = ''
      educationLevel.value = ''
      dateOfBirth.value = ''
      office.value = ''
      phone1.value = ''
      phone2.value = ''
      discount.value = ''
      guardianFullName.value = ''
      guardianPassportNumber.value = ''
      guardianRelation.value = ''
      guardianPhone.value = ''
      guardianAddress.value = ''
      createdContract.value = null
      isCopiedSignLink.value = false
    }
  }
)
</script>

<template>
  <BaseModal
    :is-open="isOpen"
    title="New Contract"
    subtitle="Enter the student's details to generate an online signing link"
    max-width="max-w-2xl"
    @close="emit('close')"
  >
    <!-- STEP: done - show the per-contract signing link -->
    <div v-if="step === 'done'" class="space-y-5">
      <div class="flex flex-col items-center text-center py-2">
        <div class="w-12 h-12 rounded-full bg-emerald-50 dark:bg-emerald-950/40 text-emerald-600 dark:text-emerald-400 flex items-center justify-center mb-3">
          <Check class="w-6 h-6" />
        </div>
        <h3 class="text-sm font-bold text-zinc-900 dark:text-zinc-100">Contract created</h3>
        <p class="text-xs text-zinc-500 dark:text-zinc-400 mt-1">
          Send the link below to the student - no account needed, they just confirm their date of birth and
          passport number, complete identity verification, and sign.
        </p>
      </div>

      <!-- Student details summary -->
      <div class="rounded-2xl border border-zinc-200 dark:border-zinc-800 bg-zinc-50/60 dark:bg-zinc-900/40 overflow-hidden">
        <div class="px-4 py-3 border-b border-zinc-200 dark:border-zinc-800 flex items-center gap-2.5">
          <div class="w-8 h-8 rounded-lg bg-zinc-900 dark:bg-zinc-100 text-white dark:text-zinc-950 flex items-center justify-center shrink-0">
            <UserRound class="w-4 h-4" />
          </div>
          <div class="min-w-0">
            <div class="text-sm font-bold text-zinc-900 dark:text-zinc-100 truncate">
              {{ createdContract?.full_name || '—' }}
            </div>
            <div class="text-[11px] text-zinc-500 dark:text-zinc-400 font-mono">
              {{ createdContract?.contract_number || '—' }}
            </div>
          </div>
        </div>
        <div class="grid grid-cols-2 sm:grid-cols-3 gap-px bg-zinc-200 dark:bg-zinc-800">
          <div class="bg-zinc-50/60 dark:bg-zinc-900/40 px-4 py-2.5">
            <div class="flex items-center gap-1.5 text-[10px] font-semibold uppercase tracking-wider text-zinc-400 dark:text-zinc-500 mb-0.5">
              <CreditCard class="w-3 h-3" />
              <span>Passport</span>
            </div>
            <div class="text-xs font-mono font-semibold text-zinc-800 dark:text-zinc-200 truncate">
              {{ createdContract?.passport_number || '—' }}
            </div>
          </div>
          <div class="bg-zinc-50/60 dark:bg-zinc-900/40 px-4 py-2.5">
            <div class="flex items-center gap-1.5 text-[10px] font-semibold uppercase tracking-wider text-zinc-400 dark:text-zinc-500 mb-0.5">
              <CreditCard class="w-3 h-3" />
              <span>Date of Birth</span>
            </div>
            <div class="text-xs font-semibold text-zinc-800 dark:text-zinc-200 truncate">
              {{ createdContract?.date_of_birth || '—' }}
            </div>
          </div>
          <div class="bg-zinc-50/60 dark:bg-zinc-900/40 px-4 py-2.5">
            <div class="flex items-center gap-1.5 text-[10px] font-semibold uppercase tracking-wider text-zinc-400 dark:text-zinc-500 mb-0.5">
              <GraduationCap class="w-3 h-3" />
              <span>Tariff</span>
            </div>
            <div class="text-xs font-semibold text-zinc-800 dark:text-zinc-200 truncate">
              {{ createdContract?.tariff_name || '—' }}
            </div>
          </div>
          <div class="bg-zinc-50/60 dark:bg-zinc-900/40 px-4 py-2.5">
            <div class="flex items-center gap-1.5 text-[10px] font-semibold uppercase tracking-wider text-zinc-400 dark:text-zinc-500 mb-0.5">
              <Building2 class="w-3 h-3" />
              <span>Office</span>
            </div>
            <div class="text-xs font-semibold text-zinc-800 dark:text-zinc-200 truncate">
              {{ createdContract?.office || '—' }}
            </div>
          </div>
          <div class="bg-zinc-50/60 dark:bg-zinc-900/40 px-4 py-2.5">
            <div class="flex items-center gap-1.5 text-[10px] font-semibold uppercase tracking-wider text-zinc-400 dark:text-zinc-500 mb-0.5">
              <Phone class="w-3 h-3" />
              <span>Phone</span>
            </div>
            <div class="text-xs font-semibold text-zinc-800 dark:text-zinc-200 truncate">
              {{ createdContract?.phone1 || '—' }}
            </div>
          </div>
          <div v-if="createdContract?.discount" class="bg-zinc-50/60 dark:bg-zinc-900/40 px-4 py-2.5">
            <div class="flex items-center gap-1.5 text-[10px] font-semibold uppercase tracking-wider text-zinc-400 dark:text-zinc-500 mb-0.5">
              <Wallet class="w-3 h-3" />
              <span>Discount</span>
            </div>
            <div class="text-xs font-semibold text-zinc-800 dark:text-zinc-200 truncate">
              {{ formatCurrency(createdContract.discount) }}
            </div>
          </div>
        </div>
      </div>

      <div v-if="signLinkUrl" class="p-3.5 rounded-2xl bg-gradient-to-r from-blue-50 to-indigo-50 dark:from-blue-950/40 dark:to-indigo-950/30 border border-blue-200/80 dark:border-blue-900/50 flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs shadow-2xs">
        <div class="flex items-center gap-2.5 min-w-0">
          <div class="w-7 h-7 rounded-lg bg-blue-600 text-white flex items-center justify-center shrink-0 shadow-xs">
            <Globe class="w-3.5 h-3.5" />
          </div>
          <div class="min-w-0">
            <div class="font-bold text-blue-900 dark:text-blue-200 text-[11px] uppercase tracking-wider">
              Signing Link
            </div>
            <div class="font-mono text-xs font-semibold text-blue-700 dark:text-blue-300 truncate" :title="signLinkUrl">
              {{ signLinkUrl }}
            </div>
          </div>
        </div>
        <button
          type="button"
          @click="copySignLink"
          class="shrink-0 inline-flex items-center justify-center gap-1.5 px-3.5 py-1.5 rounded-xl bg-blue-600 hover:bg-blue-700 text-white font-bold text-xs shadow-xs transition-all cursor-pointer select-none"
          :class="{ '!bg-emerald-600 hover:!bg-emerald-700': isCopiedSignLink }"
        >
          <Check v-if="isCopiedSignLink" class="w-3.5 h-3.5 text-emerald-100" />
          <Copy v-else class="w-3.5 h-3.5" />
          <span>{{ isCopiedSignLink ? 'Copied!' : 'Copy Link' }}</span>
        </button>
      </div>
      <div v-else class="p-3.5 rounded-2xl bg-amber-50 dark:bg-amber-950/40 border border-amber-200/80 dark:border-amber-900/50 text-xs text-amber-700 dark:text-amber-300">
        Signing link is not available for this contract yet.
      </div>

      <div class="flex items-center justify-end gap-3 pt-2">
        <button
          type="button"
          @click="emit('close')"
          class="px-4 py-2 rounded-xl border border-zinc-200 dark:border-zinc-700 text-xs font-semibold text-zinc-600 dark:text-zinc-400 hover:bg-zinc-100 dark:hover:bg-zinc-800 transition-colors cursor-pointer"
        >
          Close
        </button>
      </div>
    </div>

    <!-- STEP: preview - read-only render before generating the link -->
    <div v-else-if="step === 'preview'" class="space-y-4">
      <div v-if="errorMessage" class="p-3 bg-rose-50 dark:bg-rose-950/40 border border-rose-200 dark:border-rose-800 rounded-xl text-xs text-rose-600 dark:text-rose-300 flex items-center gap-2">
        <span class="font-bold">Error:</span> {{ errorMessage }}
      </div>

      <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <div>
          <label class="block text-xs font-semibold text-zinc-600 dark:text-zinc-400 mb-1">Contract Number</label>
          <p
            class="truncate text-xs font-mono font-bold text-zinc-700 dark:text-zinc-300"
            title="The contract number always matches the Student ID"
          >
            {{ customContractNumber || '—' }}
          </p>
        </div>
        <div>
          <label class="block text-xs font-semibold text-zinc-600 dark:text-zinc-400 mb-1">Contract Title</label>
          <p class="truncate text-xs font-bold text-zinc-700 dark:text-zinc-300" :title="customTitle">
            {{ customTitle || '—' }}
          </p>
        </div>
      </div>

      <div class="flex items-center justify-between">
        <label class="block text-xs font-bold text-zinc-700 dark:text-zinc-300 uppercase tracking-wider">
          Contract Preview
        </label>
        <span v-if="isMinor" class="inline-flex items-center gap-1 px-2 py-0.5 rounded-lg bg-amber-50 dark:bg-amber-950/40 text-amber-600 dark:text-amber-400 text-[10px] font-bold">
          <ShieldAlert class="w-3 h-3" /> Under 18 - guardian details will be included
        </span>
      </div>

      <div
        ref="previewWrapperRef"
        class="max-h-[48vh] overflow-y-auto overflow-x-hidden rounded-xl border border-zinc-200 dark:border-zinc-800 bg-zinc-100 dark:bg-zinc-950 p-3"
      >
        <!-- Canvas tariff: one scaled A4 sheet per page, stacked with a gap
             between them so page boundaries stay visible (mirrors
             ContractPreviewModal.vue's splitPages rendering). -->
        <div v-if="isCanvasPreview" class="flex flex-col items-center gap-3">
          <div
            v-for="(pageHtml, idx) in previewPages"
            :key="idx"
            class="shrink-0 bg-white shadow-sm overflow-hidden"
            :style="{ width: `${PAGE_WIDTH_PX * previewScale}px`, height: `${PAGE_HEIGHT_PX * previewScale}px` }"
          >
            <div
              class="origin-top-left"
              :style="{ width: `${PAGE_WIDTH_PX}px`, height: `${PAGE_HEIGHT_PX}px`, transform: `scale(${previewScale})` }"
              v-html="pageHtml"
            />
          </div>
        </div>
        <!-- Plain HTML template (not an A4 canvas document) - no fixed
             page size to scale against, just render as flowing text. -->
        <div v-else class="bg-white p-4 text-[13px] leading-relaxed" v-html="previewHtml" />
      </div>

      <div class="flex items-center justify-between gap-3 pt-2">
        <button
          type="button"
          @click="step = 'form'"
          class="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl border border-zinc-200 dark:border-zinc-700 text-xs font-semibold text-zinc-600 dark:text-zinc-400 hover:bg-zinc-100 dark:hover:bg-zinc-800 transition-colors cursor-pointer"
        >
          <ArrowLeft class="w-3.5 h-3.5" /> Back
        </button>

        <button
          type="button"
          @click="handleCreate"
          :disabled="isSubmitting"
          class="inline-flex items-center gap-2 px-5 py-2 rounded-xl bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white text-xs font-bold transition-all shadow-xs cursor-pointer"
        >
          <span v-if="isSubmitting">Creating...</span>
          <span v-else class="flex items-center gap-1.5">
            <span>Generate Signing Link</span>
            <ArrowRight class="w-3.5 h-3.5" />
          </span>
        </button>
      </div>
    </div>

    <!-- STEP: form - staff enters everything -->
    <div v-else class="space-y-3">
      <div v-if="errorMessage" class="p-2.5 bg-rose-50 dark:bg-rose-950/40 border border-rose-200 dark:border-rose-800 rounded-xl text-xs text-rose-600 dark:text-rose-300 flex items-center gap-2">
        <span class="font-bold">Error:</span> {{ errorMessage }}
      </div>

      <!-- 1. Student ID (15%) & Fullname (85%) in one row -->
      <div class="space-y-1">
        <div class="flex items-start gap-2.5">
          <!-- Student ID (15%) -->
          <div class="w-[22%] sm:w-[17%] shrink-0">
            <label class="block text-[11px] font-semibold text-zinc-500 dark:text-zinc-400 mb-0.5">Student ID</label>
            <div class="relative">
              <Contact class="w-3.5 h-3.5 text-zinc-400 absolute left-2.5 top-1/2 -translate-y-1/2 pointer-events-none" />
              <input
                :value="selectedExistingStudent ? selectedExistingStudent.id : studentIdAssigned"
                @input="(e: any) => { if (!selectedExistingStudent) studentIdAssigned = (e.target.value || '').toUpperCase() }"
                :readonly="!!selectedExistingStudent"
                type="text"
                placeholder="UB120"
                class="w-full pl-7 pr-2 py-2.5 bg-white dark:bg-zinc-800/80 border border-zinc-200 dark:border-zinc-700 rounded-xl text-xs font-mono font-bold text-zinc-800 dark:text-zinc-200 focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-500/15 uppercase tracking-tight shadow-sm transition-shadow"
                :class="{ 'opacity-70 cursor-not-allowed': !!selectedExistingStudent }"
              />
            </div>
          </div>

          <!-- Full name (85%) with live autocomplete -->
          <div class="flex-1 min-w-0">
            <label class="block text-[11px] font-semibold text-zinc-500 dark:text-zinc-400 mb-0.5">Student Full Name</label>
            <div class="relative">
              <Search class="w-3.5 h-3.5 text-zinc-400 absolute left-3 top-1/2 -translate-y-1/2 pointer-events-none" />
              <input
                v-model="fullNameQuery"
                type="text"
                placeholder="Enter first and last name..."
                autocomplete="off"
                @focus="isNameFocused = true"
                @blur="handleNameBlur"
                class="w-full pl-8 pr-3 py-2.5 bg-white dark:bg-zinc-800/80 border border-zinc-200 dark:border-zinc-700 rounded-xl text-xs font-semibold text-zinc-800 dark:text-zinc-200 focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-500/15 uppercase shadow-sm transition-shadow"
              />

              <div
                v-if="showSuggestions"
                class="absolute z-20 mt-1 w-full rounded-xl border border-zinc-200 dark:border-zinc-700 bg-white dark:bg-zinc-900 shadow-lg max-h-48 overflow-y-auto divide-y divide-zinc-100 dark:divide-zinc-800"
              >
                <div v-if="isSuggestLoading" class="px-3 py-2 flex items-center gap-2 text-xs text-zinc-400">
                  <svg class="w-3 h-3 animate-spin shrink-0" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
                    <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z" />
                  </svg>
                  Searching...
                </div>
                <button
                  v-else
                  v-for="st in suggestions"
                  :key="st.id"
                  type="button"
                  @mousedown.prevent="pickExistingStudent(st)"
                  class="w-full px-3 py-1.5 text-left text-xs transition-colors flex items-center justify-between hover:bg-zinc-50 dark:hover:bg-zinc-800 cursor-pointer"
                >
                  <div class="flex items-center gap-2 min-w-0">
                    <div class="w-5 h-5 rounded-full bg-zinc-200 dark:bg-zinc-700 text-zinc-600 dark:text-zinc-300 flex items-center justify-center shrink-0 text-[10px] font-bold">
                      {{ st.full_name?.charAt(0) || 'T' }}
                    </div>
                    <div class="truncate">
                      <span class="font-bold text-zinc-800 dark:text-zinc-200">{{ st.full_name }}</span>
                      <span class="text-[10px] text-zinc-400 ml-2 font-mono">{{ st.id }}</span>
                    </div>
                  </div>
                  <span v-if="st.tariff" class="px-1.5 py-0.5 rounded bg-zinc-100 dark:bg-zinc-800 text-[10px] text-zinc-500 shrink-0">{{ st.tariff }}</span>
                </button>
              </div>
            </div>
          </div>
        </div>

        <div v-if="selectedExistingStudent" class="flex items-center gap-1.5 text-[11px] text-emerald-600 dark:text-emerald-400 font-medium">
          <Check class="w-3 h-3" /> {{ selectedExistingStudent.full_name }} ({{ selectedExistingStudent.id }})
        </div>
      </div>

      <!-- 2. Tariff (defaults to unselected) -->
      <div class="space-y-0.5">
        <label class="block text-[11px] font-semibold text-zinc-500 dark:text-zinc-400 mb-0.5">Tariff</label>
        <div class="relative">
          <BookOpenCheck class="w-3.5 h-3.5 text-zinc-400 absolute left-3 top-1/2 -translate-y-1/2 pointer-events-none" />
          <select
            v-model="selectedTemplateKey"
            class="w-full pl-8 pr-7 py-2.5 bg-white dark:bg-zinc-800/80 border border-zinc-200 dark:border-zinc-700 rounded-xl text-xs font-semibold text-zinc-800 dark:text-zinc-200 focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-500/15 cursor-pointer shadow-sm transition-shadow appearance-none"
          >
            <option value="" disabled>Select tariff...</option>
            <option v-for="tpl in templateList" :key="tpl.key" :value="tpl.key">
              {{ tpl.key }} — {{ tpl.priceDisplay }}
            </option>
          </select>
          <ChevronDown class="w-3.5 h-3.5 text-zinc-400 absolute right-3 top-1/2 -translate-y-1/2 pointer-events-none" />
        </div>
      </div>

      <!-- 3. Details -->
      <div class="space-y-1">
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-2">
          <div>
            <label class="block text-[11px] font-semibold text-zinc-500 dark:text-zinc-400 mb-0.5">Passport</label>
            <div class="relative">
              <CreditCard class="w-3.5 h-3.5 text-zinc-400 absolute left-3 top-1/2 -translate-y-1/2 pointer-events-none" />
              <input
                v-model="passportNumber"
                type="text"
                placeholder="AB1234567"
                class="w-full pl-8 pr-3 py-2.5 bg-white dark:bg-zinc-800/80 border border-zinc-200 dark:border-zinc-700 rounded-xl text-xs font-mono font-semibold text-zinc-800 dark:text-zinc-200 focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-500/15 uppercase shadow-sm transition-shadow"
              />
            </div>
          </div>
          <div>
            <label class="block text-[11px] font-semibold text-zinc-500 dark:text-zinc-400 mb-0.5">Date of Birth</label>
            <div class="grid grid-cols-3 gap-1.5">
              <div class="relative">
                <select
                  v-model="dobYear"
                  @change="syncDobToIso"
                  class="w-full pl-2.5 pr-7 py-2.5 bg-white dark:bg-zinc-800/80 border border-zinc-200 dark:border-zinc-700 rounded-xl text-xs font-mono text-zinc-800 dark:text-zinc-200 focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-500/15 cursor-pointer shadow-sm transition-shadow appearance-none"
                >
                  <option :value="null" disabled>Year</option>
                  <option v-for="y in dobYears" :key="y" :value="y">{{ y }}</option>
                </select>
                <ChevronDown class="w-3.5 h-3.5 text-zinc-400 absolute right-2 top-1/2 -translate-y-1/2 pointer-events-none" />
              </div>
              <div class="relative">
                <select
                  v-model="dobMonth"
                  @change="syncDobToIso"
                  class="w-full pl-2.5 pr-7 py-2.5 bg-white dark:bg-zinc-800/80 border border-zinc-200 dark:border-zinc-700 rounded-xl text-xs font-mono text-zinc-800 dark:text-zinc-200 focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-500/15 cursor-pointer shadow-sm transition-shadow appearance-none"
                >
                  <option :value="null" disabled>Month</option>
                  <option v-for="m in dobMonths" :key="m" :value="m">{{ m }}</option>
                </select>
                <ChevronDown class="w-3.5 h-3.5 text-zinc-400 absolute right-2 top-1/2 -translate-y-1/2 pointer-events-none" />
              </div>
              <div class="relative">
                <select
                  v-model="dobDay"
                  @change="syncDobToIso"
                  class="w-full pl-2.5 pr-7 py-2.5 bg-white dark:bg-zinc-800/80 border border-zinc-200 dark:border-zinc-700 rounded-xl text-xs font-mono text-zinc-800 dark:text-zinc-200 focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-500/15 cursor-pointer shadow-sm transition-shadow appearance-none"
                >
                  <option :value="null" disabled>Day</option>
                  <option v-for="d in dobDays" :key="d" :value="d">{{ d }}</option>
                </select>
                <ChevronDown class="w-3.5 h-3.5 text-zinc-400 absolute right-2 top-1/2 -translate-y-1/2 pointer-events-none" />
              </div>
            </div>
          </div>
          <div>
            <label class="block text-[11px] font-semibold text-zinc-500 dark:text-zinc-400 mb-0.5">Education Level</label>
            <div class="relative">
              <GraduationCap class="w-3.5 h-3.5 text-zinc-400 absolute left-3 top-1/2 -translate-y-1/2 pointer-events-none" />
              <select
                v-model="educationLevel"
                class="w-full pl-8 pr-7 py-2.5 bg-white dark:bg-zinc-800/80 border border-zinc-200 dark:border-zinc-700 rounded-xl text-xs text-zinc-800 dark:text-zinc-200 focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-500/15 cursor-pointer shadow-sm transition-shadow appearance-none"
              >
                <option value="">Select...</option>
                <option v-for="lvl in levelOptions" :key="lvl" :value="lvl">
                  {{ lvl }}
                </option>
              </select>
              <ChevronDown class="w-3.5 h-3.5 text-zinc-400 absolute right-3 top-1/2 -translate-y-1/2 pointer-events-none" />
            </div>
          </div>
          <div>
            <label class="block text-[11px] font-semibold text-zinc-500 dark:text-zinc-400 mb-0.5">Office / Branch</label>
            <div class="relative">
              <Building2 class="w-3.5 h-3.5 text-zinc-400 absolute left-3 top-1/2 -translate-y-1/2 pointer-events-none" />
              <select
                v-model="office"
                class="w-full pl-8 pr-7 py-2.5 bg-white dark:bg-zinc-800/80 border border-zinc-200 dark:border-zinc-700 rounded-xl text-xs text-zinc-800 dark:text-zinc-200 focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-500/15 cursor-pointer shadow-sm transition-shadow appearance-none"
              >
                <option value="">Select...</option>
                <option v-for="br in branchOptions" :key="br" :value="br">
                  {{ br }}
                </option>
              </select>
              <ChevronDown class="w-3.5 h-3.5 text-zinc-400 absolute right-3 top-1/2 -translate-y-1/2 pointer-events-none" />
            </div>
          </div>
          <div>
            <label class="block text-[11px] font-semibold text-zinc-500 dark:text-zinc-400 mb-0.5">Phone 1</label>
            <div class="relative">
              <Phone class="w-3.5 h-3.5 text-zinc-400 absolute left-3 top-1/2 -translate-y-1/2 pointer-events-none" />
              <input
                :value="phone1"
                @input="(e: any) => phone1 = formatUzPhoneInput(e.target.value)"
                type="tel"
                placeholder="88-146-47-07"
                class="w-full pl-8 pr-3 py-2.5 bg-white dark:bg-zinc-800/80 border border-zinc-200 dark:border-zinc-700 rounded-xl text-xs font-mono text-zinc-800 dark:text-zinc-200 focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-500/15 shadow-sm transition-shadow"
              />
            </div>
          </div>
          <div>
            <label class="block text-[11px] font-semibold text-zinc-500 dark:text-zinc-400 mb-0.5">Phone 2</label>
            <div class="relative">
              <Phone class="w-3.5 h-3.5 text-zinc-400 absolute left-3 top-1/2 -translate-y-1/2 pointer-events-none" />
              <input
                :value="phone2"
                @input="(e: any) => phone2 = formatUzPhoneInput(e.target.value)"
                type="tel"
                placeholder="88-083-56-83"
                class="w-full pl-8 pr-3 py-2.5 bg-white dark:bg-zinc-800/80 border border-zinc-200 dark:border-zinc-700 rounded-xl text-xs font-mono text-zinc-800 dark:text-zinc-200 focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-500/15 shadow-sm transition-shadow"
              />
            </div>
          </div>
          <div>
            <label class="block text-[11px] font-semibold text-zinc-500 dark:text-zinc-400 mb-0.5">Price</label>
            <div class="relative">
              <Wallet class="w-3.5 h-3.5 text-zinc-400 absolute left-3 top-1/2 -translate-y-1/2 pointer-events-none" />
              <input
                :value="tariffPrice"
                type="text"
                readonly
                tabindex="-1"
                placeholder="Select a tariff first"
                title="The price is automatically set by the selected tariff in Settings"
                class="w-full pl-8 pr-3 py-2.5 bg-zinc-100 dark:bg-zinc-800/40 border border-zinc-200 dark:border-zinc-700 rounded-xl text-xs font-mono text-zinc-600 dark:text-zinc-300 cursor-not-allowed shadow-sm"
              />
            </div>
          </div>
          <div>
            <label class="block text-[11px] font-semibold text-zinc-500 dark:text-zinc-400 mb-0.5">Discount</label>
            <div class="relative">
              <BadgePercent class="w-3.5 h-3.5 text-zinc-400 absolute left-3 top-1/2 -translate-y-1/2 pointer-events-none" />
              <input
                :value="discount"
                @input="(e: any) => discount = formatAmountInput(e.target.value)"
                type="text"
                placeholder="0"
                class="w-full pl-8 pr-3 py-2.5 bg-white dark:bg-zinc-800/80 border border-zinc-200 dark:border-zinc-700 rounded-xl text-xs font-mono text-zinc-800 dark:text-zinc-200 focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-500/15 shadow-sm transition-shadow"
              />
            </div>
          </div>
        </div>
      </div>

      <!-- Guardian sub-form, only for minors -->
      <div v-if="isMinor" class="space-y-2 p-3 rounded-xl border border-amber-200 dark:border-amber-900/50 bg-amber-50/50 dark:bg-amber-950/20">
        <label class="flex items-center gap-2 text-[11px] font-bold text-amber-700 dark:text-amber-400 uppercase tracking-wider">
          <ShieldAlert class="w-3.5 h-3.5" />
          4. Guardian — Under 18
        </label>

        <div class="grid grid-cols-1 sm:grid-cols-2 gap-2">
          <div class="sm:col-span-2">
            <label class="block text-[11px] font-semibold text-zinc-500 dark:text-zinc-400 mb-0.5">Full Name</label>
            <div class="relative">
              <UserRound class="w-3.5 h-3.5 text-zinc-400 absolute left-3 top-1/2 -translate-y-1/2 pointer-events-none" />
              <input v-model="guardianFullName" type="text" class="w-full pl-8 pr-3 py-2.5 bg-white dark:bg-zinc-800/80 border border-zinc-200 dark:border-zinc-700 rounded-xl text-xs font-semibold text-zinc-800 dark:text-zinc-200 focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-500/15 uppercase shadow-sm transition-shadow" />
            </div>
          </div>
          <div>
            <label class="block text-[11px] font-semibold text-zinc-500 dark:text-zinc-400 mb-0.5">Passport</label>
            <div class="relative">
              <CreditCard class="w-3.5 h-3.5 text-zinc-400 absolute left-3 top-1/2 -translate-y-1/2 pointer-events-none" />
              <input v-model="guardianPassportNumber" type="text" class="w-full pl-8 pr-3 py-2.5 bg-white dark:bg-zinc-800/80 border border-zinc-200 dark:border-zinc-700 rounded-xl text-xs font-mono font-semibold text-zinc-800 dark:text-zinc-200 focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-500/15 uppercase shadow-sm transition-shadow" />
            </div>
          </div>
          <div>
            <label class="block text-[11px] font-semibold text-zinc-500 dark:text-zinc-400 mb-0.5">Relation to Student</label>
            <div class="relative">
              <UserRound class="w-3.5 h-3.5 text-zinc-400 absolute left-3 top-1/2 -translate-y-1/2 pointer-events-none" />
              <input v-model="guardianRelation" type="text" placeholder="Father / Mother" class="w-full pl-8 pr-3 py-2.5 bg-white dark:bg-zinc-800/80 border border-zinc-200 dark:border-zinc-700 rounded-xl text-xs text-zinc-800 dark:text-zinc-200 focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-500/15 shadow-sm transition-shadow" />
            </div>
          </div>
          <div>
            <label class="block text-[11px] font-semibold text-zinc-500 dark:text-zinc-400 mb-0.5">Phone</label>
            <div class="relative">
              <Phone class="w-3.5 h-3.5 text-zinc-400 absolute left-3 top-1/2 -translate-y-1/2 pointer-events-none" />
              <input v-model="guardianPhone" type="text" class="w-full pl-8 pr-3 py-2.5 bg-white dark:bg-zinc-800/80 border border-zinc-200 dark:border-zinc-700 rounded-xl text-xs font-mono text-zinc-800 dark:text-zinc-200 focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-500/15 shadow-sm transition-shadow" />
            </div>
          </div>
          <div>
            <label class="block text-[11px] font-semibold text-zinc-500 dark:text-zinc-400 mb-0.5">Address</label>
            <div class="relative">
              <Building2 class="w-3.5 h-3.5 text-zinc-400 absolute left-3 top-1/2 -translate-y-1/2 pointer-events-none" />
              <input v-model="guardianAddress" type="text" class="w-full pl-8 pr-3 py-2.5 bg-white dark:bg-zinc-800/80 border border-zinc-200 dark:border-zinc-700 rounded-xl text-xs text-zinc-800 dark:text-zinc-200 focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-500/15 shadow-sm transition-shadow" />
            </div>
          </div>
        </div>
      </div>

      <!-- Footer -->
      <div class="flex items-center justify-end gap-3 pt-1">
        <button
          type="button"
          @click="emit('close')"
          class="px-4 py-2 rounded-xl border border-zinc-200 dark:border-zinc-700 text-xs font-semibold text-zinc-600 dark:text-zinc-400 hover:bg-zinc-100 dark:hover:bg-zinc-800 transition-colors cursor-pointer"
        >
          Cancel
        </button>

        <button
          type="button"
          @click="goToPreview"
          class="inline-flex items-center gap-2 px-5 py-2 rounded-xl bg-blue-600 hover:bg-blue-700 text-white text-xs font-bold transition-all shadow-xs cursor-pointer"
        >
          <span>Preview</span>
          <ArrowRight class="w-3.5 h-3.5" />
        </button>
      </div>
    </div>
  </BaseModal>
</template>
