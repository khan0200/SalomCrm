<script setup lang="ts">
import { ref, computed, watch, onMounted, onBeforeUnmount } from 'vue'
import { useRoute } from 'vue-router'
import {
  ShieldCheck, ScanFace, FileSignature, CheckCircle2, AlertCircle,
  Loader2, ArrowRight, ExternalLink, RotateCw, XCircle, Download, ShieldAlert,
} from 'lucide-vue-next'
import {
  onlineContractsApi,
  type ContractSignStatusResponse,
  type IdentityVerificationStatus,
} from '@/api/onlineContracts'
import { downloadContractAsPdf } from '@/modules/contracts/utils/contractPdf'
import {
  isCanvasDocumentJson,
  deserializeCanvasDocument,
  convertCanvasDocumentToHtml,
} from '@/modules/contracts/utils/contractCanvasConverter'
import { buildVariableValues } from '@/modules/contracts/utils/contractVariables'
import OnlineContractSignatureModal from '../components/OnlineContractSignatureModal.vue'

// Single-page state machine for the staff-prefilled, no-login signing
// flow. Order matches the agreed spec: greeting -> confirm identity ->
// preview+declarations -> Didit KYC -> student signature -> (if minor)
// guardian declarations+signature -> done+download.
type PageStep = 'loading' | 'invalid' | 'identity' | 'preview' | 'kyc' | 'signature' | 'guardian' | 'done'

const route = useRoute()
const token = computed(() => (route.params.token as string) || '')

const step = ref<PageStep>('loading')
const invalidReason = ref('')
const invalidDetail = ref('')
const contractInfo = ref<ContractSignStatusResponse | null>(null)
const isMinor = computed(() => !!contractInfo.value?.is_minor_hint)

// ── Step: identity confirmation ─────────────────────────────────────────
const dobInput = ref('')
const passportInput = ref('')
const identityError = ref('')
const isConfirmingIdentity = ref(false)

const dobDays = Array.from({ length: 31 }, (_, i) => i + 1)
const dobMonths = Array.from({ length: 12 }, (_, i) => i + 1)
const currentYear = new Date().getFullYear()
const dobYears = Array.from({ length: 80 }, (_, i) => currentYear - i)
const dobDay = ref<number | null>(null)
const dobMonth = ref<number | null>(null)
const dobYear = ref<number | null>(null)

function syncDobInput() {
  if (dobDay.value && dobMonth.value && dobYear.value) {
    dobInput.value = `${dobYear.value}-${String(dobMonth.value).padStart(2, '0')}-${String(dobDay.value).padStart(2, '0')}`
  } else {
    dobInput.value = ''
  }
}

// ── Step: Didit KYC ───────────────────────────────────────────────────────
const kycStatus = ref<IdentityVerificationStatus>('NOT_STARTED')
const kycSessionUrl = ref('')
const isStartingKyc = ref(false)
const kycError = ref('')
let pollTimer: ReturnType<typeof setInterval> | null = null
const extracted = ref({ full_name: '', document_number: '', date_of_birth: '' })
const isConfirmingKyc = ref(false)
const kycConfirmError = ref('')

// Didit's hosted flow runs in a separate tab. When it finishes, Didit
// redirects THAT tab back to our own callback URL (/sign/:token?
// verificationSessionId=...) instead of its own static "verified" screen.
// Landing here with that query param means this load IS the popup tab
// returning - close it immediately so the visitor ends up back on the
// original tab, which is already polling.
const isDiditCallbackTab = !!new URLSearchParams(window.location.search).get('verificationSessionId')
const showManualCloseMessage = ref(false)
if (isDiditCallbackTab) {
  window.close()
  setTimeout(() => { showManualCloseMessage.value = true }, 600)
}

// ── Preview + declarations (student) ──────────────────────────────────────
const declRead = ref(false)
const declDataCorrect = ref(false)
const declInformed = ref(false)
const declEsignature = ref(false)
const canProceedFromPreview = computed(() =>
  declRead.value && declDataCorrect.value && declInformed.value && declEsignature.value
)
const isDownloadingPreview = ref(false)

// A canvas-contract tariff (built in the A4 editor) stores fixed
// 210x297mm pages - rendering contract.content (flattened HTML) as one
// unbroken v-html blob loses that sizing and page boundaries entirely,
// same issue ContractCreateDialog.vue's own preview had. canvas_source
// (the original, per-page-sized JSON) is used instead when present, split
// into one scaled sheet per page; otherwise this just flows as plain text.
const isCanvasPreview = computed(() => isCanvasDocumentJson(contractInfo.value?.canvas_source || ''))
const previewPages = computed<string[]>(() => {
  const source = contractInfo.value?.canvas_source || ''
  if (!isCanvasDocumentJson(source)) return []
  const doc = deserializeCanvasDocument(source)
  if (!doc) return []
  const c = contractInfo.value
  // canvas_source still carries unresolved {{tokens}} (full_name,
  // passport_number, date_of_birth, etc.) - ContractCreateDialog.vue
  // resolves these from the staff-entered form fields; here they're
  // resolved from this same contract's own fields as returned by
  // ContractSignStatusView, the same duck-typed shape buildVariableValues
  // already expects elsewhere.
  const vars = buildVariableValues(c, {
    contractNumber: c?.contract_number,
    templateName: c?.tariff_name,
    price: c?.tariff_price,
    discount: c?.discount,
    office: c?.office,
    educationLevel: c?.education_level,
  })
  const totalPages = doc.pages.length
  return doc.pages.map((p, pageOffset) =>
    convertCanvasDocumentToHtml({ ...doc, pages: [p] }, vars, { pageOffset, totalPages })
  )
})

// Same mm->px scaling approach as ContractCreateDialog.vue's preview -
// browser's own 96dpi conversion instead of measuring the rendered
// element (unreliable right after a step change, before v-html paints).
const PAGE_WIDTH_PX = 210 * (96 / 25.4)
const PAGE_HEIGHT_PX = 297 * (96 / 25.4)
const previewWrapperRef = ref<HTMLElement | null>(null)
const previewWrapperWidth = ref(0)
const previewScale = computed(() => {
  if (!previewWrapperWidth.value) return 1
  return Math.min(1, previewWrapperWidth.value / PAGE_WIDTH_PX)
})
let previewResizeObserver: ResizeObserver | null = null

watch(previewWrapperRef, (el) => {
  previewResizeObserver?.disconnect()
  previewResizeObserver = null
  if (el) {
    previewWrapperWidth.value = el.clientWidth
    previewResizeObserver = new ResizeObserver((entries) => {
      const width = entries[0]?.contentRect.width
      if (width) previewWrapperWidth.value = width
    })
    previewResizeObserver.observe(el)
  }
})

async function handleDownloadPreview() {
  if (!contractInfo.value?.content) return
  isDownloadingPreview.value = true
  try {
    await downloadContractAsPdf(
      contractInfo.value.title || 'shartnoma',
      contractInfo.value.canvas_source || contractInfo.value.content,
      undefined,
      undefined,
      undefined,
      { status: 'pending' },
      isMinor.value && contractInfo.value.guardian_contract_text
        ? { content: contractInfo.value.guardian_contract_text }
        : undefined
    )
  } finally {
    isDownloadingPreview.value = false
  }
}

// ── Step: signature ───────────────────────────────────────────────────────
const isSignatureModalOpen = ref(false)
const studentSignature = ref('')
const submitError = ref('')
const isSubmitting = ref(false)

// ── Step: guardian (minors only) - declarations + signature, no Didit ────
const guardianFullName = ref('')
const guardianPassport = ref('')
const guardianRelation = ref('')
const guardianPhone = ref('')
const guardianAddress = ref('')
const guardianSignature = ref('')
const isGuardianSignatureModalOpen = ref(false)
const guardianDeclRead = ref(false)
const guardianDeclDataCorrect = ref(false)
const guardianDeclInformed = ref(false)
const guardianDeclEsignature = ref(false)

function stopPolling() {
  if (pollTimer) clearInterval(pollTimer)
  pollTimer = null
}

async function loadStatus() {
  try {
    const res = await onlineContractsApi.getSignableContract(token.value)
    if (res.reason !== 'ok') {
      invalidReason.value = res.reason
      invalidDetail.value = res.detail || ''
      step.value = 'invalid'
      return
    }
    contractInfo.value = res

    // Resume at whichever step matches server state, so a returning
    // student (closed the tab mid-flow) never has to redo a finished step.
    if (res.has_signature) {
      step.value = 'done'
    } else if (res.kyc_status === 'VERIFIED') {
      step.value = 'signature'
    } else if (res.identity_confirmed) {
      step.value = 'preview'
    } else {
      step.value = 'identity'
    }
  } catch (err: any) {
    invalidReason.value = 'not_found'
    invalidDetail.value = err?.response?.data?.detail || "Havolani yuklab bo'lmadi."
    step.value = 'invalid'
  }
}

async function handleConfirmIdentity() {
  identityError.value = ''
  syncDobInput()
  if (!dobInput.value.trim() || !passportInput.value.trim()) {
    identityError.value = "Tug'ilgan sana va pasport raqamini kiriting."
    return
  }
  isConfirmingIdentity.value = true
  try {
    await onlineContractsApi.confirmSignIdentity(token.value, {
      date_of_birth: dobInput.value.trim(),
      passport_number: passportInput.value.trim(),
    })
    step.value = 'preview'
  } catch (err: any) {
    if (err?.response?.status === 429) {
      invalidReason.value = 'locked'
      invalidDetail.value = err.response.data?.detail || ''
      step.value = 'invalid'
      return
    }
    identityError.value = err?.response?.data?.detail || "Ma'lumotlar mos kelmadi."
  } finally {
    isConfirmingIdentity.value = false
  }
}

async function refreshKycStatus() {
  try {
    const res = await onlineContractsApi.getSignKycStatus(token.value)
    kycStatus.value = res.status
    if (res.status === 'PENDING_REVIEW' && res.extracted) {
      extracted.value = { ...res.extracted }
      stopPolling()
    } else if (res.status === 'VERIFIED') {
      stopPolling()
      step.value = 'signature'
    }
  } catch {
    // Transient poll errors are ignored - the next tick tries again.
  }
}

function startKycPolling() {
  stopPolling()
  pollTimer = setInterval(refreshKycStatus, 4000)
}

async function handleStartKyc() {
  kycError.value = ''
  isStartingKyc.value = true
  try {
    const res = await onlineContractsApi.startSignKyc(token.value, 'PASSPORT')
    kycStatus.value = res.status
    kycSessionUrl.value = res.url
    // No 'noopener' on purpose: severing window.opener would block
    // window.close() from working once Didit's callback lands back on
    // this same page.
    window.open(res.url, '_blank')
    startKycPolling()
  } catch (err: any) {
    kycError.value = err?.response?.data?.detail
      || "Tekshiruv xizmatini boshlab bo'lmadi. Birozdan so'ng qayta urinib ko'ring."
  } finally {
    isStartingKyc.value = false
  }
}

function handleReopenKyc() {
  if (kycSessionUrl.value) window.open(kycSessionUrl.value, '_blank')
}

function handleRetryKyc() {
  kycStatus.value = 'NOT_STARTED'
  kycSessionUrl.value = ''
  kycError.value = ''
  stopPolling()
}

async function handleConfirmKyc() {
  kycConfirmError.value = ''
  if (!extracted.value.full_name.trim() || !extracted.value.document_number.trim() || !extracted.value.date_of_birth.trim()) {
    kycConfirmError.value = "Barcha maydonlarni to'ldiring."
    return
  }
  isConfirmingKyc.value = true
  try {
    await onlineContractsApi.confirmSignKyc(token.value, extracted.value)
    step.value = 'signature'
  } catch (err: any) {
    if (err?.response?.status === 409) {
      invalidReason.value = 'mismatch'
      invalidDetail.value = err.response.data?.detail || ''
      step.value = 'invalid'
      return
    }
    kycConfirmError.value = err?.response?.data?.detail || 'Tasdiqlashda xatolik yuz berdi.'
  } finally {
    isConfirmingKyc.value = false
  }
}

function handleStudentSignatureConfirm(dataUrl: string) {
  studentSignature.value = dataUrl
}

function handleGuardianSignatureConfirm(dataUrl: string) {
  guardianSignature.value = dataUrl
}

const canSubmitStudentSignature = computed(() => !!studentSignature.value)

async function handleStudentSignContinue() {
  submitError.value = ''
  if (!canSubmitStudentSignature.value) {
    submitError.value = "Imzo chizishingiz kerak."
    return
  }
  if (isMinor.value) {
    step.value = 'guardian'
    return
  }
  await doSubmit()
}

const canSubmitGuardian = computed(() => {
  return !!(
    guardianFullName.value.trim() && guardianPassport.value.trim().length >= 6 &&
    guardianRelation.value.trim() && guardianPhone.value.trim() &&
    guardianAddress.value.trim() && guardianSignature.value &&
    guardianDeclRead.value && guardianDeclDataCorrect.value &&
    guardianDeclInformed.value && guardianDeclEsignature.value
  )
})

async function handleGuardianSubmit() {
  submitError.value = ''
  if (!canSubmitGuardian.value) {
    submitError.value = "Barcha maydonlarni to'ldiring, shartlarni tasdiqlang va imzo chizing."
    return
  }
  await doSubmit()
}

async function doSubmit() {
  isSubmitting.value = true
  try {
    await onlineContractsApi.submitSignedContract(token.value, {
      signature_data: studentSignature.value,
      declarations: {
        read_full_contract: declRead.value,
        data_correct: declDataCorrect.value,
        informed: declInformed.value,
        esignature_consent: declEsignature.value,
      },
      ...(isMinor.value ? {
        guardian_full_name: guardianFullName.value.trim().toUpperCase(),
        guardian_passport_number: guardianPassport.value.trim().toUpperCase(),
        guardian_relation: guardianRelation.value.trim(),
        guardian_phone: guardianPhone.value.trim(),
        guardian_address: guardianAddress.value.trim(),
        guardian_signature_data: guardianSignature.value,
        guardian_declarations: {
          read_full_contract: guardianDeclRead.value,
          data_correct: guardianDeclDataCorrect.value,
          informed: guardianDeclInformed.value,
          esignature_consent: guardianDeclEsignature.value,
        },
      } : {}),
    })
    step.value = 'done'
  } catch (err: any) {
    submitError.value = err?.response?.data?.detail || "Shartnomani yuborishda xatolik yuz berdi."
  } finally {
    isSubmitting.value = false
  }
}

async function handleFinalDownload() {
  if (!contractInfo.value) return
  try {
    const fresh = await onlineContractsApi.getSignableContract(token.value)
    await downloadContractAsPdf(
      fresh.title || 'shartnoma',
      fresh.canvas_source || fresh.content || '',
      undefined,
      undefined,
      studentSignature.value || undefined,
      { status: 'pending' },
      isMinor.value && fresh.guardian_contract_text
        ? { content: fresh.guardian_contract_text }
        : undefined
    )
  } catch (err) {
    console.error('Failed to download signed contract:', err)
  }
}

onMounted(async () => {
  if (isDiditCallbackTab) return
  await loadStatus()
})

onBeforeUnmount(() => {
  stopPolling()
  previewResizeObserver?.disconnect()
})
</script>

<template>
  <!-- Orphan callback tab: only shown if window.close() was refused -->
  <div v-if="isDiditCallbackTab" class="min-h-screen flex items-center justify-center p-6 bg-[#fafafa] dark:bg-[#09090b]">
    <div v-if="showManualCloseMessage" class="text-center max-w-xs">
      <CheckCircle2 class="w-8 h-8 text-emerald-500 mx-auto mb-3" />
      <p class="text-sm font-medium text-zinc-700 dark:text-zinc-300 mb-1">Tasdiqlandi!</p>
      <p class="text-xs text-zinc-500 dark:text-zinc-400">Ushbu oynani yopib, avvalgi oynaga qayting - u avtomatik davom etadi.</p>
    </div>
  </div>

  <div v-else class="min-h-screen bg-[#fafafa] dark:bg-[#09090b] text-zinc-900 dark:text-zinc-100 flex flex-col">
    <header class="sticky top-0 z-10 w-full bg-white/90 dark:bg-zinc-950/90 backdrop-blur-md border-b border-zinc-200/80 dark:border-zinc-800/80">
      <div class="max-w-lg mx-auto px-4 h-14 flex items-center gap-2.5">
        <div
          v-if="contractInfo?.tenant?.logo_url"
          class="w-7 h-7 rounded-lg overflow-hidden bg-white border border-zinc-200 dark:border-zinc-800 p-0.5 flex items-center justify-center shrink-0"
        >
          <img :src="contractInfo.tenant.logo_url" :alt="contractInfo.tenant.name" class="w-full h-full object-contain" />
        </div>
        <div
          v-else
          class="w-7 h-7 rounded-lg bg-zinc-900 dark:bg-zinc-100 text-white dark:text-zinc-950 flex items-center justify-center font-mono font-bold text-xs shrink-0"
        >
          {{ (contractInfo?.tenant?.name || 'U')[0] }}
        </div>
        <span class="font-semibold text-sm tracking-tight truncate">
          {{ contractInfo?.tenant?.name || 'Shartnomani imzolash' }}
        </span>
      </div>
    </header>

    <main class="flex-1 w-full">
      <div class="max-w-lg mx-auto px-4 py-6 sm:py-10">

        <!-- STATE: loading -->
        <div v-if="step === 'loading'" class="flex flex-col items-center justify-center py-20">
          <Loader2 class="w-6 h-6 animate-spin text-zinc-400" />
        </div>

        <!-- STATE: invalid/expired/used/locked/mismatch -->
        <div v-else-if="step === 'invalid'" class="bg-white dark:bg-zinc-900/60 border border-zinc-200/80 dark:border-zinc-800 rounded-xl p-8 shadow-xs text-center">
          <div class="w-12 h-12 rounded-full bg-red-50 dark:bg-red-950/40 text-red-600 dark:text-red-400 flex items-center justify-center mx-auto mb-4">
            <XCircle class="w-6 h-6" />
          </div>
          <h1 class="text-base font-semibold text-zinc-900 dark:text-zinc-100 mb-1.5">
            <template v-if="invalidReason === 'used'">Shartnoma allaqachon imzolangan</template>
            <template v-else-if="invalidReason === 'expired'">Havola muddati tugagan</template>
            <template v-else-if="invalidReason === 'locked'">Havola bloklandi</template>
            <template v-else-if="invalidReason === 'mismatch'">Ma'lumotlar mos kelmadi</template>
            <template v-else>Havola topilmadi</template>
          </h1>
          <p class="text-xs text-zinc-500 dark:text-zinc-400 leading-relaxed">
            {{ invalidDetail || "Konsalting agentligiga murojaat qiling." }}
          </p>
        </div>

        <!-- Greeting header (shown on every active step) -->
        <div v-if="step !== 'loading' && step !== 'invalid' && contractInfo" class="mb-5 p-4 rounded-xl bg-white dark:bg-zinc-900/60 border border-zinc-200/80 dark:border-zinc-800 shadow-xs">
          <p class="text-sm font-semibold text-zinc-900 dark:text-zinc-100">
            Assalomu alaykum, {{ contractInfo.full_name }}
          </p>
          <div class="flex items-center gap-3 mt-1.5 text-xs text-zinc-500 dark:text-zinc-400">
            <span>Shartnoma:</span>
            <span v-if="contractInfo.tariff_name" class="font-medium text-zinc-700 dark:text-zinc-300">{{ contractInfo.tariff_name }}</span>
          </div>
        </div>

        <!-- STEP: identity confirmation -->
        <div v-if="step === 'identity'" class="bg-white dark:bg-zinc-900/60 border border-zinc-200/80 dark:border-zinc-800 rounded-xl p-8 shadow-xs">
          <div class="mb-6">
            <div class="w-10 h-10 rounded-xl bg-zinc-900 dark:bg-zinc-100 text-white dark:text-zinc-950 flex items-center justify-center mb-3">
              <ShieldCheck class="w-5 h-5" />
            </div>
            <h1 class="text-xl font-semibold tracking-tight text-zinc-900 dark:text-zinc-100">
              Shaxsingizni tasdiqlang
            </h1>
            <p class="text-xs text-zinc-500 dark:text-zinc-400 mt-1.5 leading-relaxed">
              Konsalting tomonidan kiritilgan ma'lumotlarni tasdiqlash uchun pasport raqamingiz va tug'ilgan
              kuningizni kiriting.
            </p>
          </div>

          <div
            v-if="identityError"
            class="mb-4 p-3 rounded-lg bg-red-50 dark:bg-red-950/40 border border-red-200 dark:border-red-900/60 text-xs text-red-700 dark:text-red-300 flex items-start gap-2"
          >
            <AlertCircle class="w-4 h-4 shrink-0 mt-0.5 text-red-500" />
            <span>{{ identityError }}</span>
          </div>

          <form @submit.prevent="handleConfirmIdentity" class="space-y-4">
            <div>
              <label class="block text-xs font-medium text-zinc-700 dark:text-zinc-300 mb-1.5">Pasport raqamingizni kiriting</label>
              <input
                v-model="passportInput"
                type="text"
                required
                class="w-full px-3 py-2.5 rounded-lg border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-950 text-sm font-mono text-zinc-900 dark:text-zinc-100 focus:outline-hidden focus:border-zinc-400 dark:focus:border-zinc-600 transition-colors uppercase"
                @input="passportInput = passportInput.toUpperCase()"
              />
            </div>
            <div>
              <label class="block text-xs font-medium text-zinc-700 dark:text-zinc-300 mb-1.5">Tug'ilgan kuningizni kiriting</label>
              <div class="grid grid-cols-3 gap-2">
                <select
                  v-model="dobYear"
                  required
                  class="px-2 py-2.5 rounded-lg border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-950 text-sm text-zinc-900 dark:text-zinc-100 focus:outline-hidden focus:border-zinc-400 dark:focus:border-zinc-600"
                  @change="syncDobInput"
                >
                  <option :value="null" disabled>Yil</option>
                  <option v-for="y in dobYears" :key="y" :value="y">{{ y }}</option>
                </select>
                <select
                  v-model="dobMonth"
                  required
                  class="px-2 py-2.5 rounded-lg border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-950 text-sm text-zinc-900 dark:text-zinc-100 focus:outline-hidden focus:border-zinc-400 dark:focus:border-zinc-600"
                  @change="syncDobInput"
                >
                  <option :value="null" disabled>Oy</option>
                  <option v-for="m in dobMonths" :key="m" :value="m">{{ m }}</option>
                </select>
                <select
                  v-model="dobDay"
                  required
                  class="px-2 py-2.5 rounded-lg border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-950 text-sm text-zinc-900 dark:text-zinc-100 focus:outline-hidden focus:border-zinc-400 dark:focus:border-zinc-600"
                  @change="syncDobInput"
                >
                  <option :value="null" disabled>Kun</option>
                  <option v-for="d in dobDays" :key="d" :value="d">{{ d }}</option>
                </select>
              </div>
            </div>

            <button
              type="submit"
              :disabled="isConfirmingIdentity"
              class="w-full inline-flex items-center justify-center gap-2 py-3 px-4 rounded-lg bg-zinc-900 hover:bg-zinc-800 text-white dark:bg-zinc-100 dark:hover:bg-white dark:text-zinc-950 text-sm font-medium transition-all cursor-pointer disabled:opacity-50 active:scale-98 shadow-xs"
            >
              <Loader2 v-if="isConfirmingIdentity" class="w-4 h-4 animate-spin" />
              <span v-else>Shartnomani imzolash</span>
              <ArrowRight v-if="!isConfirmingIdentity" class="w-4 h-4" />
            </button>
          </form>
        </div>

        <!-- STEP: preview + 4 declarations -->
        <div v-else-if="step === 'preview'" class="bg-white dark:bg-zinc-900/60 border border-zinc-200/80 dark:border-zinc-800 rounded-xl p-6 sm:p-8 shadow-xs">
          <div class="mb-5 flex items-center justify-between gap-3">
            <h1 class="text-xl font-semibold tracking-tight text-zinc-900 dark:text-zinc-100">
              Shartnoma bilan tanishing
            </h1>
            <button
              type="button"
              @click="handleDownloadPreview"
              :disabled="isDownloadingPreview"
              class="shrink-0 inline-flex items-center gap-1.5 text-xs font-medium text-zinc-600 dark:text-zinc-300 hover:text-zinc-900 dark:hover:text-white border border-zinc-200 dark:border-zinc-700 rounded-lg px-2.5 py-1.5 transition-colors cursor-pointer disabled:opacity-50"
            >
              <Loader2 v-if="isDownloadingPreview" class="w-3.5 h-3.5 animate-spin" />
              <Download v-else class="w-3.5 h-3.5" />
              <span>Yuklab olish</span>
            </button>
          </div>

          <div
            ref="previewWrapperRef"
            class="max-h-[45vh] overflow-y-auto overflow-x-hidden rounded-lg border border-zinc-200 dark:border-zinc-800 bg-zinc-100 dark:bg-zinc-950 p-3 mb-5"
          >
            <!-- Canvas-contract tariff: one scaled A4 sheet per page, so
                 page boundaries and each page's true 210x297mm sizing
                 stay visible (mirrors ContractCreateDialog.vue's preview). -->
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
            <div v-else class="bg-white p-4 text-[13px] leading-relaxed" v-html="contractInfo?.content || ''" />
          </div>

          <div class="space-y-3 mb-5">
            <label class="flex items-start gap-2.5 cursor-pointer">
              <input type="checkbox" v-model="declRead" class="mt-0.5 w-3.5 h-3.5 accent-zinc-900 dark:accent-zinc-100 cursor-pointer" />
              <span class="text-xs text-zinc-700 dark:text-zinc-300 leading-relaxed">Shartnomani o'qib, tanishib chiqdim</span>
            </label>
            <label class="flex items-start gap-2.5 cursor-pointer">
              <input type="checkbox" v-model="declDataCorrect" class="mt-0.5 w-3.5 h-3.5 accent-zinc-900 dark:accent-zinc-100 cursor-pointer" />
              <span class="text-xs text-zinc-700 dark:text-zinc-300 leading-relaxed">Mening ma'lumotlarim to'g'ri kiritilganini tasdiqlayman</span>
            </label>
            <label class="flex items-start gap-2.5 cursor-pointer">
              <input type="checkbox" v-model="declInformed" class="mt-0.5 w-3.5 h-3.5 accent-zinc-900 dark:accent-zinc-100 cursor-pointer" />
              <span class="text-xs text-zinc-700 dark:text-zinc-300 leading-relaxed">Shartnoma shartlari va jarayoni haqida xabarim bor</span>
            </label>
            <label class="flex items-start gap-2.5 cursor-pointer">
              <input type="checkbox" v-model="declEsignature" class="mt-0.5 w-3.5 h-3.5 accent-zinc-900 dark:accent-zinc-100 cursor-pointer" />
              <span class="text-xs text-zinc-700 dark:text-zinc-300 leading-relaxed">Elektron imzoning yuridik kuchga ega ekanligini tasdiqlayman</span>
            </label>
          </div>

          <button
            type="button"
            @click="step = 'kyc'"
            :disabled="!canProceedFromPreview"
            class="w-full inline-flex items-center justify-center gap-2 py-3 px-4 rounded-lg bg-zinc-900 hover:bg-zinc-800 text-white dark:bg-zinc-100 dark:hover:bg-white dark:text-zinc-950 text-sm font-medium transition-all cursor-pointer disabled:opacity-40 active:scale-98 shadow-xs"
          >
            <span>Imzolash</span>
            <ArrowRight class="w-4 h-4" />
          </button>
        </div>

        <!-- STEP: Didit identity verification -->
        <div v-else-if="step === 'kyc'" class="bg-white dark:bg-zinc-900/60 border border-zinc-200/80 dark:border-zinc-800 rounded-xl p-8 shadow-xs">
          <div class="mb-6">
            <div class="w-10 h-10 rounded-xl bg-zinc-900 dark:bg-zinc-100 text-white dark:text-zinc-950 flex items-center justify-center mb-3">
              <ScanFace class="w-5 h-5" />
            </div>
            <h1 class="text-xl font-semibold tracking-tight text-zinc-900 dark:text-zinc-100">
              Hujjat tekshiruvi
            </h1>
            <p class="text-xs text-zinc-500 dark:text-zinc-400 mt-1.5 leading-relaxed">
              Pasportingizni skanerlab, selfie olishingiz kerak bo'ladi.
            </p>
          </div>

          <template v-if="kycStatus === 'NOT_STARTED' || kycStatus === 'DECLINED' || kycStatus === 'ABANDONED'">
            <div
              v-if="kycStatus === 'DECLINED'"
              class="mb-4 p-3 rounded-lg bg-red-50 dark:bg-red-950/40 border border-red-200 dark:border-red-900/60 text-xs text-red-700 dark:text-red-300 flex items-start gap-2"
            >
              <AlertCircle class="w-4 h-4 shrink-0 mt-0.5 text-red-500" />
              <span>Tekshiruv rad etildi. Hujjatingiz aniq va yorug'likda suratga olinganiga ishonch hosil qilib, qayta urinib ko'ring.</span>
            </div>
            <div
              v-else-if="kycStatus === 'ABANDONED'"
              class="mb-4 p-3 rounded-lg bg-amber-50 dark:bg-amber-950/40 border border-amber-200 dark:border-amber-900/60 text-xs text-amber-700 dark:text-amber-300 flex items-start gap-2"
            >
              <AlertCircle class="w-4 h-4 shrink-0 mt-0.5 text-amber-500" />
              <span>Tekshiruv jarayoni yakunlanmadi. Qaytadan boshlang.</span>
            </div>
            <div
              v-if="kycError"
              class="mb-4 p-3 rounded-lg bg-red-50 dark:bg-red-950/40 border border-red-200 dark:border-red-900/60 text-xs text-red-700 dark:text-red-300 flex items-start gap-2"
            >
              <AlertCircle class="w-4 h-4 shrink-0 mt-0.5 text-red-500" />
              <span>{{ kycError }}</span>
            </div>

            <p class="text-[11px] text-zinc-500 dark:text-zinc-400 mb-4">
              Tugmani bosgach yangi oyna ochiladi - u yerda hujjatingizni skanerlaysiz.
            </p>

            <button
              type="button"
              @click="handleStartKyc"
              :disabled="isStartingKyc"
              class="w-full inline-flex items-center justify-center gap-2 py-2.5 px-4 rounded-lg bg-zinc-900 hover:bg-zinc-800 text-white dark:bg-zinc-100 dark:hover:bg-white dark:text-zinc-950 text-xs font-medium transition-all cursor-pointer disabled:opacity-50 active:scale-98 shadow-xs"
            >
              <Loader2 v-if="isStartingKyc" class="w-3.5 h-3.5 animate-spin" />
              <ScanFace v-else class="w-3.5 h-3.5" />
              <span>Tasdiqlashni boshlash</span>
              <ArrowRight v-if="!isStartingKyc" class="w-3.5 h-3.5" />
            </button>
          </template>

          <template v-else-if="kycStatus === 'IN_PROGRESS'">
            <div class="flex flex-col items-center text-center py-6">
              <Loader2 class="w-6 h-6 animate-spin text-zinc-900 dark:text-white mb-3" />
              <p class="text-xs font-medium text-zinc-700 dark:text-zinc-300 mb-1">
                Tekshiruv oynasida davom eting
              </p>
              <p class="text-[11px] text-zinc-500 dark:text-zinc-400 max-w-xs leading-relaxed mb-5">
                Yangi ochilgan oynada hujjatingizni skanerlab, selfie oling. Tasdiqlangach, o'sha oynani yoping va
                <strong>shu sahifaga qayting</strong> - avtomatik davom etadi.
              </p>
              <div class="flex items-center gap-3">
                <button
                  type="button"
                  @click="handleReopenKyc"
                  class="inline-flex items-center gap-1.5 text-xs font-medium text-zinc-700 dark:text-zinc-300 hover:text-zinc-900 dark:hover:text-white underline transition-colors cursor-pointer"
                >
                  <ExternalLink class="w-3.5 h-3.5" />
                  <span>Oynani qayta ochish</span>
                </button>
                <button
                  type="button"
                  @click="refreshKycStatus"
                  class="inline-flex items-center gap-1.5 text-xs font-medium text-zinc-700 dark:text-zinc-300 hover:text-zinc-900 dark:hover:text-white underline transition-colors cursor-pointer"
                >
                  <RotateCw class="w-3.5 h-3.5" />
                  <span>Hozir tekshirish</span>
                </button>
              </div>
            </div>
          </template>

          <template v-else-if="kycStatus === 'PENDING_REVIEW'">
            <div class="mb-4 p-3 rounded-lg bg-emerald-50 dark:bg-emerald-950/40 border border-emerald-200 dark:border-emerald-900/60 text-xs text-emerald-700 dark:text-emerald-300 flex items-start gap-2">
              <CheckCircle2 class="w-4 h-4 shrink-0 mt-0.5 text-emerald-500" />
              <span>Hujjatingiz tasdiqlandi. Quyidagi ma'lumotlar to'g'ri ekanini tekshiring.</span>
            </div>

            <div
              v-if="kycConfirmError"
              class="mb-4 p-3 rounded-lg bg-red-50 dark:bg-red-950/40 border border-red-200 dark:border-red-900/60 text-xs text-red-700 dark:text-red-300 flex items-start gap-2"
            >
              <AlertCircle class="w-4 h-4 shrink-0 mt-0.5 text-red-500" />
              <span>{{ kycConfirmError }}</span>
            </div>

            <form @submit.prevent="handleConfirmKyc" class="space-y-4">
              <div>
                <label class="block text-xs font-medium text-zinc-700 dark:text-zinc-300 mb-1.5">To'liq ismingiz</label>
                <input
                  v-model="extracted.full_name"
                  type="text"
                  required
                  class="w-full px-3 py-2 rounded-lg border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-950 text-xs text-zinc-900 dark:text-zinc-100 focus:outline-hidden focus:border-zinc-400 dark:focus:border-zinc-600 transition-colors"
                />
              </div>
              <div>
                <label class="block text-xs font-medium text-zinc-700 dark:text-zinc-300 mb-1.5">Hujjat raqami</label>
                <input
                  v-model="extracted.document_number"
                  type="text"
                  required
                  class="w-full px-3 py-2 rounded-lg border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-950 text-xs font-mono text-zinc-900 dark:text-zinc-100 focus:outline-hidden focus:border-zinc-400 dark:focus:border-zinc-600 transition-colors uppercase"
                />
              </div>
              <div>
                <label class="block text-xs font-medium text-zinc-700 dark:text-zinc-300 mb-1.5">Tug'ilgan sana</label>
                <input
                  v-model="extracted.date_of_birth"
                  type="text"
                  required
                  placeholder="KK.OO.YYYY"
                  class="w-full px-3 py-2 rounded-lg border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-950 text-xs font-mono text-zinc-900 dark:text-zinc-100 focus:outline-hidden focus:border-zinc-400 dark:focus:border-zinc-600 transition-colors"
                />
              </div>

              <button
                type="submit"
                :disabled="isConfirmingKyc"
                class="w-full inline-flex items-center justify-center gap-2 py-2.5 px-4 rounded-lg bg-zinc-900 hover:bg-zinc-800 text-white dark:bg-zinc-100 dark:hover:bg-white dark:text-zinc-950 text-xs font-medium transition-all cursor-pointer disabled:opacity-50 active:scale-98 shadow-xs"
              >
                <Loader2 v-if="isConfirmingKyc" class="w-3.5 h-3.5 animate-spin" />
                <span v-else>Ma'lumotlar to'g'ri, tasdiqlayman</span>
              </button>
            </form>
          </template>

          <button
            v-if="kycStatus !== 'NOT_STARTED'"
            type="button"
            @click="handleRetryKyc"
            class="mt-4 mx-auto flex items-center gap-1.5 text-[11px] text-zinc-400 hover:text-zinc-600 dark:hover:text-zinc-300 transition-colors cursor-pointer"
          >
            <RotateCw class="w-3 h-3" />
            <span>Boshqa hujjat bilan qaytadan boshlash</span>
          </button>
        </div>

        <!-- STEP: student signature -->
        <div v-else-if="step === 'signature'" class="bg-white dark:bg-zinc-900/60 border border-zinc-200/80 dark:border-zinc-800 rounded-xl p-8 shadow-xs">
          <div class="mb-6">
            <div class="w-10 h-10 rounded-xl bg-zinc-900 dark:bg-zinc-100 text-white dark:text-zinc-950 flex items-center justify-center mb-3">
              <FileSignature class="w-5 h-5" />
            </div>
            <h1 class="text-xl font-semibold tracking-tight text-zinc-900 dark:text-zinc-100">
              Elektron imzo
            </h1>
            <p class="text-xs text-zinc-500 dark:text-zinc-400 mt-1.5 leading-relaxed">
              Quyida imzoingizni chizing.
            </p>
          </div>

          <div
            v-if="submitError"
            class="mb-4 p-3 rounded-lg bg-red-50 dark:bg-red-950/40 border border-red-200 dark:border-red-900/60 text-xs text-red-700 dark:text-red-300 flex items-start gap-2"
          >
            <AlertCircle class="w-4 h-4 shrink-0 mt-0.5 text-red-500" />
            <span>{{ submitError }}</span>
          </div>

          <div class="mb-5">
            <button
              type="button"
              @click="isSignatureModalOpen = true"
              class="w-full h-28 rounded-lg border-2 border-dashed border-zinc-300 dark:border-zinc-700 flex items-center justify-center overflow-hidden bg-zinc-50/60 dark:bg-zinc-950/40 hover:border-zinc-400 dark:hover:border-zinc-600 transition-colors cursor-pointer"
            >
              <img v-if="studentSignature" :src="studentSignature" alt="Imzo" class="h-full object-contain" />
              <span v-else class="text-xs text-zinc-400">Imzo chizish uchun bosing</span>
            </button>
          </div>

          <button
            type="button"
            @click="handleStudentSignContinue"
            :disabled="!canSubmitStudentSignature || isSubmitting"
            class="w-full inline-flex items-center justify-center gap-2 py-3 px-4 rounded-lg bg-zinc-900 hover:bg-zinc-800 text-white dark:bg-zinc-100 dark:hover:bg-white dark:text-zinc-950 text-sm font-medium transition-all cursor-pointer disabled:opacity-40 active:scale-98 shadow-xs"
          >
            <Loader2 v-if="isSubmitting" class="w-4 h-4 animate-spin" />
            <span v-else-if="isMinor">Davom etish - kafil ma'lumotlari</span>
            <span v-else>Shartnomani yuborish</span>
          </button>
        </div>

        <!-- STEP: guardian declarations + signature (minors only, no Didit) -->
        <div v-else-if="step === 'guardian'" class="bg-white dark:bg-zinc-900/60 border border-zinc-200/80 dark:border-zinc-800 rounded-xl p-8 shadow-xs">
          <div class="mb-6">
            <div class="w-10 h-10 rounded-xl bg-amber-500 text-white flex items-center justify-center mb-3">
              <ShieldAlert class="w-5 h-5" />
            </div>
            <h1 class="text-xl font-semibold tracking-tight text-zinc-900 dark:text-zinc-100">
              Kafil (ota-ona/vasiy) tasdig'i
            </h1>
            <p class="text-xs text-zinc-500 dark:text-zinc-400 mt-1.5 leading-relaxed">
              Talaba 18 yoshdan kichik bo'lgani uchun kafilning roziligi va imzosi talab qilinadi.
            </p>
          </div>

          <div
            v-if="submitError"
            class="mb-4 p-3 rounded-lg bg-red-50 dark:bg-red-950/40 border border-red-200 dark:border-red-900/60 text-xs text-red-700 dark:text-red-300 flex items-start gap-2"
          >
            <AlertCircle class="w-4 h-4 shrink-0 mt-0.5 text-red-500" />
            <span>{{ submitError }}</span>
          </div>

          <div class="space-y-3 mb-5">
            <input v-model="guardianFullName" type="text" placeholder="Kafil F.I.O." class="w-full px-3 py-2 rounded-lg border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-950 text-xs text-zinc-900 dark:text-zinc-100 focus:outline-hidden uppercase" />
            <input v-model="guardianPassport" type="text" placeholder="Kafil pasport raqami" class="w-full px-3 py-2 rounded-lg border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-950 text-xs font-mono uppercase text-zinc-900 dark:text-zinc-100 focus:outline-hidden" />
            <input v-model="guardianRelation" type="text" placeholder="Qarindoshlik darajasi (ota, ona, vasiy...)" class="w-full px-3 py-2 rounded-lg border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-950 text-xs text-zinc-900 dark:text-zinc-100 focus:outline-hidden" />
            <input v-model="guardianPhone" type="text" placeholder="Kafil telefon raqami" class="w-full px-3 py-2 rounded-lg border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-950 text-xs text-zinc-900 dark:text-zinc-100 focus:outline-hidden" />
            <input v-model="guardianAddress" type="text" placeholder="Yashash manzili" class="w-full px-3 py-2 rounded-lg border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-950 text-xs text-zinc-900 dark:text-zinc-100 focus:outline-hidden" />
          </div>

          <div class="space-y-3 mb-5">
            <label class="flex items-start gap-2.5 cursor-pointer">
              <input type="checkbox" v-model="guardianDeclRead" class="mt-0.5 w-3.5 h-3.5 accent-zinc-900 dark:accent-zinc-100 cursor-pointer" />
              <span class="text-xs text-zinc-700 dark:text-zinc-300 leading-relaxed">Shartnomani o'qib, tanishib chiqdim</span>
            </label>
            <label class="flex items-start gap-2.5 cursor-pointer">
              <input type="checkbox" v-model="guardianDeclDataCorrect" class="mt-0.5 w-3.5 h-3.5 accent-zinc-900 dark:accent-zinc-100 cursor-pointer" />
              <span class="text-xs text-zinc-700 dark:text-zinc-300 leading-relaxed">Ma'lumotlar to'g'ri kiritilganini tasdiqlayman</span>
            </label>
            <label class="flex items-start gap-2.5 cursor-pointer">
              <input type="checkbox" v-model="guardianDeclInformed" class="mt-0.5 w-3.5 h-3.5 accent-zinc-900 dark:accent-zinc-100 cursor-pointer" />
              <span class="text-xs text-zinc-700 dark:text-zinc-300 leading-relaxed">Shartnoma shartlari va jarayoni haqida xabarim bor</span>
            </label>
            <label class="flex items-start gap-2.5 cursor-pointer">
              <input type="checkbox" v-model="guardianDeclEsignature" class="mt-0.5 w-3.5 h-3.5 accent-zinc-900 dark:accent-zinc-100 cursor-pointer" />
              <span class="text-xs text-zinc-700 dark:text-zinc-300 leading-relaxed">Elektron imzoning yuridik kuchga ega ekanligini tasdiqlayman</span>
            </label>
          </div>

          <div class="mb-5">
            <p class="text-xs font-medium text-zinc-700 dark:text-zinc-300 mb-2">Kafilning imzosi</p>
            <button
              type="button"
              @click="isGuardianSignatureModalOpen = true"
              class="w-full h-28 rounded-lg border-2 border-dashed border-zinc-300 dark:border-zinc-700 flex items-center justify-center overflow-hidden bg-white dark:bg-zinc-950/40 hover:border-zinc-400 dark:hover:border-zinc-600 transition-colors cursor-pointer"
            >
              <img v-if="guardianSignature" :src="guardianSignature" alt="Kafil imzosi" class="h-full object-contain" />
              <span v-else class="text-xs text-zinc-400">Imzo chizish uchun bosing</span>
            </button>
          </div>

          <button
            type="button"
            @click="handleGuardianSubmit"
            :disabled="!canSubmitGuardian || isSubmitting"
            class="w-full inline-flex items-center justify-center gap-2 py-3 px-4 rounded-lg bg-zinc-900 hover:bg-zinc-800 text-white dark:bg-zinc-100 dark:hover:bg-white dark:text-zinc-950 text-sm font-medium transition-all cursor-pointer disabled:opacity-40 active:scale-98 shadow-xs"
          >
            <Loader2 v-if="isSubmitting" class="w-4 h-4 animate-spin" />
            <span v-else>Shartnomani yuborish</span>
          </button>
        </div>

        <!-- STATE: done -->
        <div v-else-if="step === 'done'" class="bg-white dark:bg-zinc-900/60 border border-zinc-200/80 dark:border-zinc-800 rounded-xl p-8 shadow-xs text-center">
          <div class="w-12 h-12 rounded-full bg-emerald-50 dark:bg-emerald-950/40 text-emerald-600 dark:text-emerald-400 flex items-center justify-center mx-auto mb-4">
            <CheckCircle2 class="w-6 h-6" />
          </div>
          <h1 class="text-base font-semibold text-zinc-900 dark:text-zinc-100 mb-1.5">
            Shartnomangiz muvaffaqiyatli imzolandi
          </h1>
          <p class="text-xs text-zinc-500 dark:text-zinc-400 leading-relaxed mb-5">
            Konsalting agentligi tez orada ko'rib chiqadi. Qo'shimcha savollar uchun agentlikka murojaat qiling.
          </p>
          <button
            type="button"
            @click="handleFinalDownload"
            class="inline-flex items-center justify-center gap-2 py-2.5 px-5 rounded-lg bg-zinc-900 hover:bg-zinc-800 text-white dark:bg-zinc-100 dark:hover:bg-white dark:text-zinc-950 text-xs font-semibold transition-all cursor-pointer active:scale-98 shadow-xs"
          >
            <Download class="w-3.5 h-3.5" />
            <span>Shartnomani yuklab olish</span>
          </button>
        </div>
      </div>
    </main>

    <OnlineContractSignatureModal
      :is-open="isSignatureModalOpen"
      role="student"
      @close="isSignatureModalOpen = false"
      @confirm="handleStudentSignatureConfirm"
    />
    <OnlineContractSignatureModal
      :is-open="isGuardianSignatureModalOpen"
      role="guardian"
      @close="isGuardianSignatureModalOpen = false"
      @confirm="handleGuardianSignatureConfirm"
    />
  </div>
</template>
