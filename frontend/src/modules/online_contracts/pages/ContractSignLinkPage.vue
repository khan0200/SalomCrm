<script setup lang="ts">
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
import { useRoute } from 'vue-router'
import {
  ShieldCheck, ScanFace, FileSignature, CheckCircle2, AlertCircle,
  Loader2, ArrowRight, ExternalLink, RotateCw, XCircle, Download, ShieldAlert,
  FileText,
} from 'lucide-vue-next'
import {
  onlineContractsApi,
  type ContractSignStatusResponse,
  type IdentityVerificationStatus,
} from '@/api/onlineContracts'
import { downloadContractAsPdf } from '@/modules/contracts/utils/contractPdf'
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
// true only right after doSubmit() succeeds in THIS visit - false when the
// 'done' step is reached because the student (re-)opened an already-signed
// link, so the two cases can show slightly different copy.
const justSigned = ref(false)

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
// Set when this tab navigated to Didit itself (popup was blocked), so the
// return is a normal navigation in the SAME tab - there is nothing to
// close and no other tab waiting behind it. Survives the round trip via
// sessionStorage because the page fully reloads on the way back.
const KYC_SAME_TAB_KEY = 'kyc_same_tab_flow'

const isDiditCallback = !!new URLSearchParams(window.location.search).get('verificationSessionId')
const isSameTabReturn = sessionStorage.getItem(KYC_SAME_TAB_KEY) === '1'
// Only the popup variant should try to close itself and show the
// "close this window" notice.
const isDiditCallbackTab = isDiditCallback && !isSameTabReturn
const showManualCloseMessage = ref(false)
if (isDiditCallbackTab) {
  window.close()
  setTimeout(() => { showManualCloseMessage.value = true }, 600)
}
if (isDiditCallback && isSameTabReturn) {
  // Returned into the original tab: drop the flag and strip the query so a
  // refresh does not look like another callback, then let the normal flow
  // resume - the status fetch below picks the verification up.
  sessionStorage.removeItem(KYC_SAME_TAB_KEY)
  window.history.replaceState({}, '', window.location.pathname)
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

const resolvedVariableValues = computed<Record<string, string>>(() => {
  const c = contractInfo.value
  if (!c) return {}
  return buildVariableValues(c, {
    contractNumber: c?.contract_number,
    templateName: c?.tariff_name,
    price: c?.tariff_price,
    discount: c?.discount,
    office: c?.office,
    educationLevel: c?.education_level,
  })
})

async function handleDownloadPreview() {
  if (!contractInfo.value?.content) return
  isDownloadingPreview.value = true
  try {
    const c = contractInfo.value
    const vars = resolvedVariableValues.value
    const verificationMeta = {
      contractNumber: c?.contract_number,
      studentName: c?.full_name,
      status: 'pending',
    }
    await downloadContractAsPdf(
      // Matches the staff Contracts admin's own download filename
      // convention (ContractsPage.vue) - `${contract_number}_${full_name}`
      // - so the same contract carries the same filename whoever
      // downloads it, staff or student.
      `${c.contract_number || 'Contract'}_${c.full_name || c.title || 'shartnoma'}`,
      c.canvas_source || c.content || '',
      undefined,
      vars,
      undefined,
      verificationMeta,
      isMinor.value && c.guardian_contract_text
        ? { content: c.guardian_contract_text, variableValues: vars }
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
    // Preloaded so the 'kyc' step can skip itself straight to 'signature'
    // once identity is re-verified, without a second network round-trip -
    // KYC's own completion (unlike identity) stays valid across visits,
    // since Didit already independently verified the document+face once.
    kycStatus.value = res.kyc_status || 'NOT_STARTED'

    // Resume at whichever step matches server state, so a returning
    // student (closed the tab, or scanned the QR on the finished contract
    // weeks later) never has to redo a finished step - has_signature now
    // stays true forever once set, so this same link permanently lands here.
    //
    // identity_confirmed/kyc_status are intentionally NOT used to skip
    // straight to 'preview'/'signature': a sign_token is one shared link,
    // and a past successful confirm-identity or KYC call doesn't prove
    // THIS visitor is the real student - every visit must re-enter
    // passport+DOB before anything else, so a signature can never be
    // collected from someone who never typed in the real student's own
    // identifying details. handleConfirmIdentity() picks the right next
    // step (kyc vs signature) once identity is freshly re-verified.
    if (res.has_signature) {
      justSigned.value = false
      step.value = 'done'
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

// True when a window.open() call was swallowed by the browser. Mobile
// Chrome/Safari only honour window.open inside the click handler itself;
// ours runs after an await, so the popup is routinely blocked and the
// visitor was left staring at "continue in the verification window" with
// no window ever having opened.
const kycPopupBlocked = ref(false)

function openKycWindow(url: string): boolean {
  // No 'noopener' on purpose: severing window.opener would block
  // window.close() from working once Didit's callback lands back on
  // this same page.
  const w = window.open(url, '_blank')
  const blocked = !w || w.closed || typeof w.closed === 'undefined'
  kycPopupBlocked.value = blocked
  return !blocked
}

// Fallback for a blocked popup: Didit redirects back to this same URL when
// it finishes, so navigating the current tab completes the flow just as
// well - the page reloads into the callback branch and resumes polling.
function openKycHere() {
  if (!kycSessionUrl.value) return
  sessionStorage.setItem(KYC_SAME_TAB_KEY, '1')
  window.location.href = kycSessionUrl.value
}

async function handleStartKyc() {
  kycError.value = ''
  isStartingKyc.value = true
  try {
    const res = await onlineContractsApi.startSignKyc(token.value, 'PASSPORT')
    kycStatus.value = res.status
    kycSessionUrl.value = res.url
    openKycWindow(res.url)
    startKycPolling()
  } catch (err: any) {
    kycError.value = err?.response?.data?.detail
      || "Tekshiruv xizmatini boshlab bo'lmadi. Birozdan so'ng qayta urinib ko'ring."
  } finally {
    isStartingKyc.value = false
  }
}

function handleReopenKyc() {
  if (kycSessionUrl.value) openKycWindow(kycSessionUrl.value)
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
    const res = await onlineContractsApi.submitSignedContract(token.value, {
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
    // Merge the freshly-generated verification_code into the already-loaded
    // contractInfo so handleFinalDownload's {{qr_code}}/{{verification_link}}
    // resolve without waiting on a second round-trip.
    if (contractInfo.value) {
      contractInfo.value = { ...contractInfo.value, verification_code: res.verification_code }
    }
    justSigned.value = true
    step.value = 'done'
  } catch (err: any) {
    submitError.value = err?.response?.data?.detail || "Shartnomani yuborishda xatolik yuz berdi."
  } finally {
    isSubmitting.value = false
  }
}

const isDownloadingFinal = ref(false)
const finalDownloadError = ref('')

// Stage 3: the finalized download now fetches the canonical, server-
// rendered PDF (ContractSignDownloadPdfView) instead of re-rendering
// locally with html2canvas/jsPDF - every device downloads the exact same
// stored bytes, and the signature comes from the server's own persisted
// Contract.signature_data rather than this page's studentSignature ref
// (which is empty on a returning visit, after the tab was closed and
// reopened - the bug the server-side path sidesteps by construction).
//
// Minor-student contracts still use the old client-side path: the server
// renderer doesn't yet compose the guardian consent appendix onto the PDF
// (deferred in Stage 2 - see that stage's report), so routing a minor's
// download through it would silently produce a PDF missing a legally
// required page. Safer to keep the known-complete path for that one case
// until appendix rendering is built server-side too.
async function handleFinalDownload() {
  const c = contractInfo.value
  if (!c) return
  if (isDownloadingFinal.value) return // guard against double-click firing two requests
  isDownloadingFinal.value = true
  finalDownloadError.value = ''

  if (isMinor.value && c.guardian_contract_text) {
    try {
      const signUrl = `${window.location.origin}/sign/${token.value}`
      const vars = buildVariableValues(c, {
        contractNumber: c.contract_number,
        templateName: c.tariff_name,
        price: c.tariff_price,
        discount: c.discount,
        office: c.office,
        educationLevel: c.education_level,
        signatureData: studentSignature.value || undefined,
        verificationCode: c.verification_code || undefined,
        signUrl,
      })
      const verificationMeta = {
        contractNumber: c.contract_number,
        studentName: c.full_name,
        verifiedAt: new Date().toLocaleDateString('uz-UZ'),
        status: 'signed',
      }
      await downloadContractAsPdf(
        `${c.contract_number || 'Contract'}_${c.full_name || c.title || 'shartnoma'}`,
        c.canvas_source || c.content || '',
        undefined,
        vars,
        studentSignature.value || undefined,
        verificationMeta,
        { content: c.guardian_contract_text, variableValues: vars }
      )
    } catch (err) {
      console.error('Failed to download signed contract (minor path):', err)
      finalDownloadError.value = "Shartnomani yuklab olishda xatolik yuz berdi. Qayta urinib ko'ring."
    } finally {
      isDownloadingFinal.value = false
    }
    return
  }

  let objectUrl: string | null = null
  try {
    const blob = await onlineContractsApi.downloadFinalPdf(token.value)
    objectUrl = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = objectUrl
    // Matches the staff Contracts admin's own download filename convention
    // (ContractsPage.vue) - `${contract_number}_${full_name}` - so the same
    // contract carries the same filename whoever downloads it.
    a.download = `${c.contract_number || 'Contract'}_${c.full_name || c.title || 'shartnoma'}.pdf`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
  } catch (err) {
    console.error('Failed to download signed contract:', err)
    finalDownloadError.value = "Shartnomani yuklab olishda xatolik yuz berdi. Qayta urinib ko'ring."
  } finally {
    if (objectUrl) URL.revokeObjectURL(objectUrl)
    isDownloadingFinal.value = false
  }
}

onMounted(async () => {
  if (isDiditCallbackTab) return
  await loadStatus()
})

onBeforeUnmount(() => {
  stopPolling()
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
        <div v-else-if="step === 'preview'" class="bg-white dark:bg-zinc-900/60 border border-zinc-200/80 dark:border-zinc-800 rounded-xl p-5 sm:p-8 shadow-xs">
          <div class="mb-4">
            <h1 class="text-lg sm:text-xl font-semibold tracking-tight text-zinc-900 dark:text-zinc-100">
              Shartnoma bilan tanishing
            </h1>
            <p class="text-xs text-zinc-500 dark:text-zinc-400 mt-1.5 leading-relaxed">
              Shartnomani PDF faylda yuklab olib, to'liq o'qib chiqing.
            </p>
          </div>

          <button
            type="button"
            @click="handleDownloadPreview"
            :disabled="isDownloadingPreview"
            class="w-full mb-5 inline-flex items-center justify-center gap-2.5 py-4 px-4 rounded-xl border-2 border-dashed border-zinc-300 dark:border-zinc-700 bg-zinc-50 dark:bg-zinc-950/40 hover:border-zinc-400 dark:hover:border-zinc-600 hover:bg-zinc-100 dark:hover:bg-zinc-900 transition-colors cursor-pointer disabled:opacity-60"
          >
            <Loader2 v-if="isDownloadingPreview" class="w-5 h-5 animate-spin text-zinc-500" />
            <FileText v-else class="w-5 h-5 text-zinc-500" />
            <span class="text-sm font-medium text-zinc-700 dark:text-zinc-300">
              {{ isDownloadingPreview ? 'Tayyorlanmoqda...' : 'Shartnomani yuklab olish (PDF)' }}
            </span>
            <Download v-if="!isDownloadingPreview" class="w-4 h-4 text-zinc-400" />
          </button>

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
            @click="step = kycStatus === 'VERIFIED' ? 'signature' : 'kyc'"
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
              <!-- Popup blocked (the normal case on mobile): lead with the
                   button that continues in this tab, since telling the
                   visitor to use a window that never opened is what left
                   them stuck here. -->
              <template v-if="kycPopupBlocked">
                <ScanFace class="w-6 h-6 text-zinc-900 dark:text-white mb-3" />
                <p class="text-xs font-medium text-zinc-700 dark:text-zinc-300 mb-1">
                  Tekshiruvni davom ettiring
                </p>
                <p class="text-[11px] text-zinc-500 dark:text-zinc-400 max-w-xs leading-relaxed mb-4">
                  Brauzeringiz yangi oynani ochishga ruxsat bermadi. Quyidagi tugma orqali
                  shu sahifada davom eting - tasdiqlangach avtomatik qaytasiz.
                </p>
                <button
                  type="button"
                  @click="openKycHere"
                  class="w-full max-w-xs inline-flex items-center justify-center gap-2 py-2.5 px-4 rounded-lg bg-zinc-900 hover:bg-zinc-800 text-white dark:bg-zinc-100 dark:hover:bg-white dark:text-zinc-950 text-xs font-medium transition-all cursor-pointer active:scale-98 shadow-xs mb-4"
                >
                  <ScanFace class="w-3.5 h-3.5" />
                  <span>Tekshiruvni ochish</span>
                  <ArrowRight class="w-3.5 h-3.5" />
                </button>
              </template>

              <template v-else>
                <Loader2 class="w-6 h-6 animate-spin text-zinc-900 dark:text-white mb-3" />
                <p class="text-xs font-medium text-zinc-700 dark:text-zinc-300 mb-1">
                  Tekshiruv oynasida davom eting
                </p>
                <p class="text-[11px] text-zinc-500 dark:text-zinc-400 max-w-xs leading-relaxed mb-5">
                  Yangi ochilgan oynada hujjatingizni skanerlab, selfie oling. Tasdiqlangach, o'sha oynani yoping va
                  <strong>shu sahifaga qayting</strong> - avtomatik davom etadi.
                </p>
              </template>

              <div class="flex items-center gap-3">
                <button
                  type="button"
                  @click="kycPopupBlocked ? openKycHere() : handleReopenKyc()"
                  class="inline-flex items-center gap-1.5 text-xs font-medium text-zinc-700 dark:text-zinc-300 hover:text-zinc-900 dark:hover:text-white underline transition-colors cursor-pointer"
                >
                  <ExternalLink class="w-3.5 h-3.5" />
                  <span>{{ kycPopupBlocked ? 'Shu sahifada ochish' : 'Oynani qayta ochish' }}</span>
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
            {{ justSigned ? "Shartnomangiz muvaffaqiyatli imzolandi" : "Shartnoma imzolangan" }}
          </h1>
          <p class="text-xs text-zinc-500 dark:text-zinc-400 leading-relaxed mb-5">
            {{ justSigned
              ? "Konsalting agentligi tez orada ko'rib chiqadi. Qo'shimcha savollar uchun agentlikka murojaat qiling."
              : "Shartnomangizning rasmiy nusxasini istalgan vaqtda shu havoladan yuklab olishingiz mumkin." }}
          </p>
          <div
            v-if="finalDownloadError"
            class="mb-4 p-3 rounded-lg bg-red-50 dark:bg-red-950/40 border border-red-200 dark:border-red-900/60 text-xs text-red-700 dark:text-red-300 flex items-start gap-2 text-left"
          >
            <AlertCircle class="w-4 h-4 shrink-0 mt-0.5 text-red-500" />
            <span>{{ finalDownloadError }}</span>
          </div>
          <button
            type="button"
            @click="handleFinalDownload"
            :disabled="isDownloadingFinal"
            class="inline-flex items-center justify-center gap-2 py-2.5 px-5 rounded-lg bg-zinc-900 hover:bg-zinc-800 text-white dark:bg-zinc-100 dark:hover:bg-white dark:text-zinc-950 text-xs font-semibold transition-all cursor-pointer active:scale-98 shadow-xs disabled:opacity-60"
          >
            <Loader2 v-if="isDownloadingFinal" class="w-3.5 h-3.5 animate-spin" />
            <Download v-else class="w-3.5 h-3.5" />
            <span>{{ isDownloadingFinal ? 'Tayyorlanmoqda...' : "Shartnomani yuklab olish" }}</span>
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
