<script setup lang="ts">
import { ref, reactive, computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import {
  onlineContractsApi,
  type TenantInfoResponse,
  type OnlineTariff,
} from '@/api/onlineContracts'
import OnlineContractLayout from '../layouts/OnlineContractLayout.vue'
import OnlineContractSignatureModal from '../components/OnlineContractSignatureModal.vue'
import FullContractViewerModal from '../components/FullContractViewerModal.vue'
import LegalBasisModal from '../components/LegalBasisModal.vue'
import { getTariffSampleContractHtml } from '../utils/sampleContract'
import { buildVariableValues } from '@/modules/contracts/utils/contractVariables'
import { usePhoneVerification } from '@/composables/usePhoneVerification'
import {
  FileText,
  User,
  BookOpen,
  CheckCircle2,
  AlertCircle,
  ArrowRight,
  ArrowLeft,
  Lock,
  Loader2,
  Calendar,
  Building2,
  ShieldCheck,
  Eye,
  EyeOff,
  Check,
  Phone,
  ShieldCheckIcon,
  KeyRound,
} from 'lucide-vue-next'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()

const tenantSlug = computed(() => (route.params.tenantname as string) || '')
const queryTariffId = computed(() => (route.query.tariffId as string) || '')
const resubmitContractId = computed(() => (route.query.resubmitContractId as string) || '')

const isLoading = ref(true)
const tenantInfo = ref<TenantInfoResponse | null>(null)

// Step Tracking: 1 = Form & Tariff, 2 = Contract Read & Sign, 3 = Review & Submit
const currentStep = ref<1 | 2 | 3>(1)

// ── Firebase Phone Verification ──────────────────────────────────────────────
// phone1 va guardian_phone uchun alohida verifier instance
// tenantSlug computed bo'lgani uchun verifier'larni init paytida yaratamiz
const phone1OtpCode = ref('')
const guardianOtpCode = ref('')

// Composable'lar onMounted da init qilinadi (tenantSlug tayyor bo'lganda)
let phone1Verifier: ReturnType<typeof usePhoneVerification> | null = null
let guardianVerifier: ReturnType<typeof usePhoneVerification> | null = null

// Reactive proxy refs — template uchun
const phone1Step = ref<'idle' | 'sending' | 'code_sent' | 'verifying' | 'verified'>('idle')
const phone1Loading = ref(false)
const phone1Error = ref<string | null>(null)
const phone1IsVerified = ref(false)
const phone1SessionToken = ref<string | null>(null)

const guardianStep = ref<'idle' | 'sending' | 'code_sent' | 'verifying' | 'verified'>('idle')
const guardianLoading = ref(false)
const guardianError = ref<string | null>(null)
const guardianIsVerified = ref(false)
const guardianSessionToken = ref<string | null>(null)

function syncPhone1State() {
  if (!phone1Verifier) return
  phone1Step.value = phone1Verifier.step.value
  phone1Loading.value = phone1Verifier.loading.value
  phone1Error.value = phone1Verifier.error.value
  phone1IsVerified.value = phone1Verifier.isVerified.value
  phone1SessionToken.value = phone1Verifier.sessionToken.value
}

function syncGuardianState() {
  if (!guardianVerifier) return
  guardianStep.value = guardianVerifier.step.value
  guardianLoading.value = guardianVerifier.loading.value
  guardianError.value = guardianVerifier.error.value
  guardianIsVerified.value = guardianVerifier.isVerified.value
  guardianSessionToken.value = guardianVerifier.sessionToken.value
}

async function sendPhone1Otp() {
  if (!phone1Verifier) {
    phone1Verifier = usePhoneVerification('phone1', tenantSlug.value)
  }
  phone1Error.value = null
  try {
    await phone1Verifier.sendOtp(formData.phone1, 'recaptcha-phone1')
  } catch {
    // error is set inside composable
  }
  syncPhone1State()
}

async function confirmPhone1Otp() {
  if (!phone1Verifier) return
  try {
    await phone1Verifier.confirmOtp(phone1OtpCode.value, formData.phone1)
  } catch {
    // error is set inside composable
  }
  syncPhone1State()
}

async function sendGuardianOtp() {
  if (!guardianVerifier) {
    guardianVerifier = usePhoneVerification('guardian_phone', tenantSlug.value)
  }
  guardianError.value = null
  try {
    await guardianVerifier.sendOtp(guardianData.phone, 'recaptcha-guardian')
  } catch {
    // error is set inside composable
  }
  syncGuardianState()
}

async function confirmGuardianOtp() {
  if (!guardianVerifier) return
  try {
    await guardianVerifier.confirmOtp(guardianOtpCode.value, guardianData.phone)
  } catch {
    // error is set inside composable
  }
  syncGuardianState()
}

// phone1 raqami o'zgarganda verification reset qilinsin
watch(() => formData.phone1, () => {
  if (phone1IsVerified.value) {
    phone1Verifier?.reset()
    syncPhone1State()
    phone1OtpCode.value = ''
  }
})

watch(() => guardianData.phone, () => {
  if (guardianIsVerified.value) {
    guardianVerifier?.reset()
    syncGuardianState()
    guardianOtpCode.value = ''
  }
})
// ────────────────────────────────────────────────────────────────────────────

// Selected Tariff
const selectedTariffId = ref<string>('')
const selectedTariff = computed<OnlineTariff | null>(() => {
  if (!tenantInfo.value?.tariffs) return null
  return tenantInfo.value.tariffs.find(t => String(t.id) === selectedTariffId.value) || null
})

// Student Form Data (starts with +998 by default, but user can backspace/erase it)
const formData = reactive({
  passportNumber: '',
  fullName: '',
  educationLevel: '',
  dobDay: '',
  dobMonth: '',
  dobYear: '',
  office: '',
  phone1: '+998 ',
  phone2: '+998 ',
  email: authStore.user?.email || '',
  signatureData: '',
})

// Auto-convert Full Name and Passport Number to Uppercase
watch(() => formData.fullName, (newVal) => {
  if (newVal && newVal !== newVal.toUpperCase()) {
    formData.fullName = newVal.toUpperCase()
  }
})

watch(() => formData.passportNumber, (newVal) => {
  if (newVal && newVal !== newVal.toUpperCase()) {
    formData.passportNumber = newVal.toUpperCase()
  }
})

// Declarations
const declarations = reactive({
  readFullContract: false,
  voluntarySign: false,
  confirmationCodeMeaning: false,
  legalBasisAcknowledged: false,
})

// Contract Viewer Modal
const isViewerModalOpen = ref(false)
const hasReadFullContract = ref(false)

// Legal Basis Modal
const isLegalBasisModalOpen = ref(false)

// Guardian (kafil) consent - required only when the student is under 18 at
// signing time (Fuqarolik kodeksi 27-modda: a minor's contract is void
// without the parent/guardian's own written consent and signature).
const guardianData = reactive({
  fullName: '',
  passportNumber: '',
  relation: '',
  phone: '+998 ',
  address: '',
})
const guardianSignatureData = ref('')
const isGuardianSignatureModalOpen = ref(false)
const isGuardianContractViewerOpen = ref(false)

const GUARDIAN_RELATION_OPTIONS = ['Ota', 'Ona', 'Aka'] as const
const guardianRelationOption = ref<'Ota' | 'Ona' | 'Aka' | 'Other' | ''>('')
watch(guardianRelationOption, (val) => {
  if (val === 'Other') {
    guardianData.relation = ''
  } else if (val) {
    guardianData.relation = val
  }
})

/**
 * Format phone input on keystroke:
 * - Initially or if typing Uzbek number (+998, 998, or raw digits):
 *   formats as "+998 XX-XXX-XX-XX"
 * - User CAN backspace and erase "+998" to type any international number (e.g. "+82 10-2614-1012", "+7...", etc.)!
 */
function formatPhoneInput(raw: string): string {
  if (!raw) return ''
  const trimmed = raw.trimStart()
  if (trimmed === '+' || trimmed === '') return trimmed

  const allDigits = trimmed.replace(/\D/g, '')

  // If Uzbek number (+998, 998, or typing digits without +)
  if (trimmed.startsWith('+998') || trimmed.startsWith('998') || (!trimmed.startsWith('+') && allDigits.length <= 9)) {
    const local = allDigits.replace(/^998/, '').slice(0, 9)
    let formatted = ''
    for (let i = 0; i < local.length; i++) {
      if (i === 2 || i === 5 || i === 7) formatted += '-'
      formatted += local[i]
    }
    return local ? `+998 ${formatted}` : '+998 '
  }

  // International format (e.g. +82 10-2614-1012): allow +, numbers, spaces, dashes
  return trimmed.replace(/[^\d+\-\s]/g, '')
}

function isCompletePhone(val: string): boolean {
  if (!val) return false
  const trimmed = val.trim()
  const digits = trimmed.replace(/\D/g, '')
  if (trimmed.startsWith('+998') || trimmed.startsWith('998') || (!trimmed.startsWith('+') && digits.length === 9)) {
    return digits.replace(/^998/, '').length === 9
  }
  return digits.length >= 7 && digits.length <= 15
}

/**
 * Converts input phone value to storage format.
 * IMPORTANT: For Uzbek numbers, strips country code (+998) and returns bare local "XX-XXX-XX-XX"
 * (e.g. "90-123-45-67") so StudentDetailDrawer and Student models format without country code.
 * For foreign/international numbers, returns full international format.
 */
function toStoragePhone(val: string): string {
  if (!val) return ''
  const trimmed = val.trim()
  const digits = trimmed.replace(/\D/g, '')
  if (trimmed.startsWith('+998') || trimmed.startsWith('998') || (!trimmed.startsWith('+') && digits.length === 9)) {
    const local = digits.replace(/^998/, '').slice(0, 9)
    let formatted = ''
    for (let i = 0; i < local.length; i++) {
      if (i === 2 || i === 5 || i === 7) formatted += '-'
      formatted += local[i]
    }
    return formatted // "90-123-45-67" (country code siz!)
  }
  return trimmed
}

// Display-only for previews or printed contracts
function displayPhone(val: string): string {
  if (!val) return ''
  const trimmed = val.trim()
  if (trimmed.startsWith('+')) return trimmed
  return `+998 ${trimmed}`
}

function onPhone1Input(e: Event) {
  formData.phone1 = formatPhoneInput((e.target as HTMLInputElement).value)
}
function onPhone2Input(e: Event) {
  formData.phone2 = formatPhoneInput((e.target as HTMLInputElement).value)
}
function onGuardianPhoneInput(e: Event) {
  guardianData.phone = formatPhoneInput((e.target as HTMLInputElement).value)
}

// Password Confirmation Modal
const isPasswordModalOpen = ref(false)
const accountPassword = ref('')
const showAccountPassword = ref(false)
const isSubmitting = ref(false)
const submitError = ref('')
const submitSuccess = ref(false)
const createdContractId = ref('')

// Date of Birth Dropdown options
const days = Array.from({ length: 31 }, (_, i) => String(i + 1).padStart(2, '0'))
const months = [
  { value: '01', name: 'Yanvar' },
  { value: '02', name: 'Fevral' },
  { value: '03', name: 'Mart' },
  { value: '04', name: 'Aprel' },
  { value: '05', name: 'May' },
  { value: '06', name: 'Iyun' },
  { value: '07', name: 'Iyul' },
  { value: '08', name: 'Avgust' },
  { value: '09', name: 'Sentabr' },
  { value: '10', name: 'Oktabr' },
  { value: '11', name: 'Noyabr' },
  { value: '12', name: 'Dekabr' },
]
const currentYear = new Date().getFullYear()
const years = Array.from({ length: 70 }, (_, i) => String(currentYear - 14 - i))

const formattedDob = computed(() => {
  if (formData.dobDay && formData.dobMonth && formData.dobYear) {
    return `${formData.dobDay}.${formData.dobMonth}.${formData.dobYear}`
  }
  return ''
})

// Fuqarolik kodeksi 27-modda: under 18 on the day of signing needs a
// guardian's written consent for the contract to be valid at all.
const isMinor = computed(() => {
  if (!formData.dobDay || !formData.dobMonth || !formData.dobYear) return false
  const dob = new Date(Number(formData.dobYear), Number(formData.dobMonth) - 1, Number(formData.dobDay))
  if (Number.isNaN(dob.getTime())) return false
  const today = new Date()
  let age = today.getFullYear() - dob.getFullYear()
  const notYetHadBirthdayThisYear =
    today.getMonth() < dob.getMonth() ||
    (today.getMonth() === dob.getMonth() && today.getDate() < dob.getDate())
  if (notYetHadBirthdayThisYear) age -= 1
  return age < 18
})

const variableValues = computed<Record<string, string>>(() => {
  return buildVariableValues(
    {
      full_name: (formData.fullName || '').toUpperCase().trim(),
      passport_number: (formData.passportNumber || '').toUpperCase().trim(),
      education_level: formData.educationLevel || '',
      office: formData.office || '',
      date_of_birth: formattedDob.value || '',
      phone1: formData.phone1 || '',
      phone2: formData.phone2 || '',
      signature_data: formData.signatureData || '',
      email: formData.email || authStore.user?.email || '',
      guardian_full_name: isMinor.value ? (guardianData.fullName || '').toUpperCase().trim() : '',
      guardian_passport_number: isMinor.value ? (guardianData.passportNumber || '').toUpperCase().trim() : '',
      guardian_relation: isMinor.value ? guardianData.relation || '' : '',
      guardian_phone: isMinor.value ? guardianData.phone || '' : '',
      guardian_address: isMinor.value ? guardianData.address || '' : '',
      guardian_signature_data: isMinor.value ? guardianSignatureData.value || '' : '',
    },
    {
      price: selectedTariff.value?.price,
      contractNumber: 'Pending Student ID',
      templateName: selectedTariff.value?.name,
      signatureData: formData.signatureData || '',
      educationLevel: formData.educationLevel || '',
      office: formData.office || '',
      email: formData.email || authStore.user?.email || '',
    }
  )
})

const effectiveContractText = computed(() => {
  if (selectedTariff.value?.contract_text && selectedTariff.value.contract_text.trim()) {
    return selectedTariff.value.contract_text
  }
  if (selectedTariff.value) {
    const companyName = tenantInfo.value?.name || 'Konsalting Kompaniyasi'
    return getTariffSampleContractHtml(companyName, selectedTariff.value)
  }
  return ''
})

function formatPrice(val: number | string | undefined): string {
  if (!val) return '0 UZS'
  const num = typeof val === 'number' ? val : parseFloat(String(val))
  return num.toLocaleString('uz-UZ') + ' UZS'
}

async function init() {
  isLoading.value = true
  try {
    const tInfo = await onlineContractsApi.getTenantInfo(tenantSlug.value)
    tenantInfo.value = tInfo

    // Pre-select tariff ONLY if explicitly provided in query params (e.g. from landing card)
    if (queryTariffId.value) {
      selectedTariffId.value = queryTariffId.value
    } else {
      selectedTariffId.value = ''
    }

    // Only load previous data if resubmitting a specific rejected contract
    if (resubmitContractId.value) {
      try {
        const contract = await onlineContractsApi.getContractDetail(resubmitContractId.value)
        if (contract.tariff_id) selectedTariffId.value = String(contract.tariff_id)
        if (contract.full_name) formData.fullName = contract.full_name.toUpperCase()
        if (contract.passport_number) formData.passportNumber = contract.passport_number.toUpperCase()
        if (contract.education_level) formData.educationLevel = contract.education_level
        if (contract.office) formData.office = contract.office
        if (contract.phone1) formData.phone1 = formatPhoneInput(contract.phone1)
        if (contract.phone2) formData.phone2 = formatPhoneInput(contract.phone2)
        if (contract.email) formData.email = contract.email
        if (contract.date_of_birth) {
          const s = contract.date_of_birth.trim()
          if (s.includes('.')) {
            const parts = s.split('.')
            if (parts.length === 3) {
              formData.dobDay = parts[0].padStart(2, '0')
              formData.dobMonth = parts[1].padStart(2, '0')
              formData.dobYear = parts[2]
            }
          } else if (s.includes('-')) {
            const parts = s.split('-')
            if (parts.length === 3) {
              formData.dobYear = parts[0]
              formData.dobMonth = parts[1].padStart(2, '0')
              formData.dobDay = parts[2].padStart(2, '0')
            }
          }
        }
      } catch (err) {
        console.error('Failed to load contract for resubmission:', err)
      }
    } else if (authStore.isAuthenticated) {
      try {
        const prof = await onlineContractsApi.getProfile()
        if (prof.user.full_name) formData.fullName = prof.user.full_name.toUpperCase()
        if (prof.profile.passport_number) formData.passportNumber = prof.profile.passport_number.toUpperCase()
        if (prof.profile.education_level) formData.educationLevel = prof.profile.education_level
        if (prof.profile.office) formData.office = prof.profile.office
        if (prof.profile.phone1) formData.phone1 = formatPhoneInput(prof.profile.phone1)
        if (prof.profile.phone2) formData.phone2 = formatPhoneInput(prof.profile.phone2)
        if (prof.user.email) formData.email = prof.user.email
        if (prof.profile.date_of_birth) {
          const s = prof.profile.date_of_birth.trim()
          if (s.includes('.')) {
            const parts = s.split('.')
            if (parts.length === 3) {
              formData.dobDay = parts[0].padStart(2, '0')
              formData.dobMonth = parts[1].padStart(2, '0')
              formData.dobYear = parts[2]
            }
          } else if (s.includes('-')) {
            const parts = s.split('-')
            if (parts.length === 3) {
              formData.dobYear = parts[0]
              formData.dobMonth = parts[1].padStart(2, '0')
              formData.dobDay = parts[2].padStart(2, '0')
            }
          }
        }
      } catch (err) {
        console.error('Failed to load profile for auto-fill:', err)
      }
    }
  } catch (err) {
    console.error('Failed to init sign page:', err)
  } finally {
    isLoading.value = false
  }
}

function handleOpenFullContract() {
  isViewerModalOpen.value = true
}

function handleConfirmReadContract() {
  hasReadFullContract.value = true
  declarations.readFullContract = true
}

const isStep1Valid = computed(() => {
  return (
    !!selectedTariff.value &&
    formData.passportNumber.trim().length >= 6 &&
    formData.fullName.trim().length >= 3 &&
    !!formData.educationLevel &&
    !!formData.dobDay &&
    !!formData.dobMonth &&
    !!formData.dobYear &&
    !!formData.office &&
    isCompletePhone(formData.phone1) &&
    isCompletePhone(formData.phone2) &&
    formData.email.trim().length > 0 &&
    formData.email.includes('@') &&
    phone1IsVerified.value  // ← Telefon 1 Firebase bilan tasdiqlangan bo'lishi shart
  )
})

// Set only once the student tries to move past a step while it's still
// incomplete - so a blank form doesn't greet them with red text on every
// field before they've touched anything, but every unmet requirement lights
// up together the moment they actually try to proceed.
const attemptStep1 = ref(false)
const attemptStep2 = ref(false)

const isSignatureModalOpen = ref(false)

const isStep2DeclarationsValid = computed(() => {
  return (
    declarations.readFullContract &&
    declarations.voluntarySign &&
    declarations.confirmationCodeMeaning &&
    declarations.legalBasisAcknowledged
  )
})

const isGuardianInfoValid = computed(() => {
  if (!isMinor.value) return true
  return (
    guardianData.fullName.trim().length >= 3 &&
    guardianData.passportNumber.trim().length >= 6 &&
    guardianData.relation.trim().length > 0 &&
    isCompletePhone(guardianData.phone) &&
    guardianIsVerified.value &&  // ← Kafil telefoni SMS bilan tasdiqlangan bo'lishi shart
    guardianData.address.trim().length >= 3 &&
    !!guardianSignatureData.value
  )
})

const isStep2Valid = computed(() => {
  return (
    isStep2DeclarationsValid.value &&
    isGuardianInfoValid.value &&
    !!formData.signatureData
  )
})

function goToStep2() {
  if (!isStep1Valid.value) {
    attemptStep1.value = true
    return
  }
  currentStep.value = 2
  window.scrollTo({ top: 0, behavior: 'smooth' })
}

function handleGuardianSignatureConfirmed(sigData: string) {
  guardianSignatureData.value = sigData
  isGuardianSignatureModalOpen.value = false
}

function handleProceedToReview() {
  if (!isStep2DeclarationsValid.value || !isGuardianInfoValid.value) {
    attemptStep2.value = true
    return
  }
  isSignatureModalOpen.value = true
}

function handleSignatureConfirmed(sigData: string) {
  formData.signatureData = sigData
  hasReadFullContract.value = true
  isSignatureModalOpen.value = false
  currentStep.value = 3
  window.scrollTo({ top: 0, behavior: 'smooth' })
}

function goToStep3() {
  if (!isStep2Valid.value) {
    if (isStep2DeclarationsValid.value && isGuardianInfoValid.value) {
      isSignatureModalOpen.value = true
    }
    return
  }
  currentStep.value = 3
  window.scrollTo({ top: 0, behavior: 'smooth' })
}

function openPasswordModal() {
  if (!authStore.isAuthenticated) {
    router.push({
      name: 'online-sign-in',
      params: { tenantname: tenantSlug.value },
      query: { redirect: route.fullPath }
    })
    return
  }
  accountPassword.value = ''
  showAccountPassword.value = false
  submitError.value = ''
  isPasswordModalOpen.value = true
}

async function handleFinalSubmit() {
  if (!accountPassword.value) {
    submitError.value = 'Profil parolini kiriting.'
    return
  }

  isSubmitting.value = true
  submitError.value = ''

  try {
    const res = await onlineContractsApi.submitContract({
      tariff_id: selectedTariff.value!.id,
      passport_number: formData.passportNumber.toUpperCase().trim(),
      full_name: formData.fullName.toUpperCase().trim(),
      education_level: formData.educationLevel,
      date_of_birth: formattedDob.value,
      office: formData.office,
      phone1: toStoragePhone(formData.phone1),
      phone2: toStoragePhone(formData.phone2),
      email: formData.email.trim(),
      signature_data: formData.signatureData,
      declarations: {
        read_full_contract: declarations.readFullContract,
        voluntary_sign: declarations.voluntarySign,
        confirmation_code_meaning: declarations.confirmationCodeMeaning,
      },
      password: accountPassword.value,
      // Firebase Phone Auth session tokenlar
      phone1_session_token: phone1SessionToken.value || '',
      ...(isMinor.value ? {
        guardian_full_name: guardianData.fullName.toUpperCase().trim(),
        guardian_passport_number: guardianData.passportNumber.toUpperCase().trim(),
        guardian_relation: guardianData.relation.trim(),
        guardian_phone: toStoragePhone(guardianData.phone),
        guardian_address: guardianData.address.trim(),
        guardian_signature_data: guardianSignatureData.value,
        guardian_phone_session_token: guardianSessionToken.value || '',
      } : {}),
    })

    createdContractId.value = res.contract_id
    submitSuccess.value = true
    isPasswordModalOpen.value = false

    // Clear session draft
    sessionStorage.removeItem('selected_tariff_id')

    setTimeout(() => {
      router.push({ name: 'online-profile', params: { tenantname: tenantSlug.value } })
    }, 1500)
  } catch (err: any) {
    submitError.value = err?.response?.data?.detail || 'Shartnomani imzolashda xatolik yuz berdi.'
  } finally {
    isSubmitting.value = false
  }
}

onMounted(() => {
  init()
})
</script>

<template>
  <OnlineContractLayout :tenant-info="tenantInfo">
    <div v-if="isLoading" class="py-24 flex flex-col items-center justify-center text-zinc-400">
      <Loader2 class="w-6 h-6 animate-spin text-zinc-900 dark:text-white mb-2" />
      <span class="text-xs font-mono">Shartnoma ma'lumotlari yuklanmoqda...</span>
    </div>

    <div v-else class="max-w-3xl mx-auto space-y-6 sm:space-y-8">
      <!-- Step Indicator Bar (Resend Minimalist, High Contrast) -->
      <div class="border border-zinc-300 dark:border-zinc-800 bg-white dark:bg-zinc-900/60 rounded-xl p-2 shadow-2xs">
        <div class="grid grid-cols-3 gap-1.5 sm:gap-2 text-xs">
          <button
            type="button"
            @click="currentStep = 1"
            class="py-2.5 px-3 rounded-lg font-bold transition-all flex items-center justify-center gap-1.5 sm:gap-2 text-center cursor-pointer"
            :class="currentStep === 1 ? 'bg-black text-white dark:bg-white dark:text-black shadow-xs' : 'text-black dark:text-white hover:bg-zinc-100 dark:hover:bg-zinc-800'"
          >
            <span class="font-mono text-xs font-bold">01</span>
            <span class="hidden sm:inline">Ma'lumotlar</span>
          </button>

          <button
            type="button"
            @click="isStep1Valid ? currentStep = 2 : null"
            :disabled="!isStep1Valid"
            class="py-2.5 px-3 rounded-lg font-bold transition-all flex items-center justify-center gap-1.5 sm:gap-2 text-center disabled:opacity-50"
            :class="currentStep === 2 ? 'bg-black text-white dark:bg-white dark:text-black shadow-xs' : 'text-black dark:text-white hover:bg-zinc-100 dark:hover:bg-zinc-800 cursor-pointer'"
          >
            <span class="font-mono text-xs font-bold">02</span>
            <span class="hidden sm:inline">O'qish & Imzo</span>
          </button>

          <button
            type="button"
            @click="isStep2Valid ? currentStep = 3 : null"
            :disabled="!isStep2Valid"
            class="py-2.5 px-3 rounded-lg font-bold transition-all flex items-center justify-center gap-1.5 sm:gap-2 text-center disabled:opacity-50"
            :class="currentStep === 3 ? 'bg-black text-white dark:bg-white dark:text-black shadow-xs' : 'text-black dark:text-white'"
          >
            <span class="font-mono text-xs font-bold">03</span>
            <span class="hidden sm:inline">Tasdiqlash</span>
          </button>
        </div>
      </div>

      <!-- Success Alert after submission -->
      <div
        v-if="submitSuccess"
        class="p-8 bg-white dark:bg-zinc-900/60 border border-emerald-500/30 rounded-xl text-center space-y-3 shadow-xs"
      >
        <div class="w-12 h-12 rounded-xl bg-emerald-50 dark:bg-emerald-950/60 border border-emerald-500/20 text-emerald-600 dark:text-emerald-400 flex items-center justify-center mx-auto">
          <CheckCircle2 class="w-6 h-6" />
        </div>
        <h3 class="text-base font-bold text-black dark:text-white tracking-tight">
          Shartnoma muvaffaqiyatli imzolandi va yuborildi
        </h3>
        <p class="text-xs text-zinc-700 dark:text-zinc-300 max-w-md mx-auto leading-relaxed font-medium">
          Shartnomangiz ko'rib chiqish uchun yuborildi. Agentlik tomonidan tasdiqlangach, tasdiq kodi profilingizda paydo bo'ladi.
        </p>
        <div class="pt-2">
          <span class="text-xs font-mono text-zinc-500 font-semibold">Profilingizga yo'naltirilmoqda...</span>
        </div>
      </div>

      <!-- STEP 1: TARIFF SELECTION & STUDENT INFORMATION FORM -->
      <div v-else-if="currentStep === 1" class="space-y-6">
        <!-- 1.1 Tariff Selection (Dropdown) -->
        <section class="bg-white dark:bg-zinc-900/60 border border-zinc-300 dark:border-zinc-800 rounded-xl p-6 sm:p-8 shadow-xs">
          <div class="flex items-center justify-between mb-4 pb-4 border-b border-zinc-200 dark:border-zinc-850">
            <div>
              <h2 class="text-base font-bold text-black dark:text-white tracking-tight">
                1. Xizmat tarifini tanlang
              </h2>
              <p class="text-xs text-zinc-700 dark:text-zinc-300 font-medium">
                Imzolamoqchi bo'lgan rasmiy konsalting tarifingizni belgilang
              </p>
            </div>
            <div v-if="selectedTariff" class="text-right hidden sm:block">
              <span class="text-xs font-bold uppercase tracking-wide text-zinc-700 dark:text-zinc-300 block">Shartnoma to'lovi</span>
              <span class="text-sm font-bold font-mono text-black dark:text-white">
                {{ formatPrice(selectedTariff.price) }}
              </span>
            </div>
          </div>

          <div class="space-y-2">
            <label class="block text-xs font-bold uppercase tracking-wide text-black dark:text-white">
              Konsalting tarifi <span class="text-red-600">*</span>
            </label>
            <select
              v-model="selectedTariffId"
              class="w-full px-3.5 py-2.5 text-xs rounded-lg border border-zinc-300 dark:border-zinc-700 bg-white dark:bg-zinc-900 text-black dark:text-white focus:outline-hidden focus:border-black dark:focus:border-white transition-colors shadow-2xs font-semibold cursor-pointer"
            >
              <option value="" disabled>Tarifni tanlang</option>
              <option
                v-for="tariff in tenantInfo?.tariffs || []"
                :key="tariff.id"
                :value="String(tariff.id)"
              >
                {{ tariff.name }} — {{ formatPrice(tariff.price) }}
              </option>
            </select>
            <p v-if="attemptStep1 && !selectedTariff" class="text-[11px] font-semibold text-red-600 dark:text-red-400">
              Tarifni tanlang!
            </p>

            <div v-if="selectedTariff" class="sm:hidden pt-1.5 flex items-center justify-between text-xs text-zinc-700">
              <span class="font-semibold">Shartnoma to'lovi:</span>
              <strong class="font-mono text-black dark:text-white font-bold">{{ formatPrice(selectedTariff.price) }}</strong>
            </div>
          </div>
        </section>

        <!-- 1.2 Student Information Form -->
        <section class="bg-white dark:bg-zinc-900/60 border border-zinc-300 dark:border-zinc-800 rounded-xl p-6 sm:p-8 shadow-xs space-y-5">
          <div class="pb-4 border-b border-zinc-200 dark:border-zinc-850">
            <h2 class="text-base font-bold text-black dark:text-white tracking-tight">
              2. Shaxsiy ma'lumotlar
            </h2>
            <p class="text-xs text-zinc-700 dark:text-zinc-300 font-medium">
              Ma'lumotlar shartnomaga avtomatik kiritiladi, pasportingiz bilan bir xil bo'lishi shart
            </p>
          </div>

          <div class="grid grid-cols-1 sm:grid-cols-2 gap-4 sm:gap-5">
            <!-- Passport Number -->
            <div>
              <label class="block text-xs font-bold uppercase tracking-wide text-black dark:text-white mb-1.5">
                Pasport raqami <span class="text-red-600">*</span>
              </label>
              <input
                v-model="formData.passportNumber"
                @input="formData.passportNumber = (formData.passportNumber || '').toUpperCase()"
                type="text"
                required
                maxlength="15"
                placeholder="Masalan: AB1234567"
                class="w-full px-3.5 py-2.5 text-xs font-mono font-bold rounded-lg border border-zinc-300 dark:border-zinc-700 bg-white dark:bg-zinc-900 text-black dark:text-white placeholder:text-zinc-400 focus:outline-hidden focus:border-black dark:focus:border-white transition-colors shadow-2xs uppercase"
              />
              <p v-if="attemptStep1 && formData.passportNumber.trim().length < 6" class="mt-1 text-[11px] font-semibold text-red-600 dark:text-red-400">
                Pasport raqamini kiriting!
              </p>
            </div>

            <!-- Full Name (as in Passport) -->
            <div>
              <label class="block text-xs font-bold uppercase tracking-wide text-black dark:text-white mb-1.5">
                To'liq ism-sharif (F.I.O) <span class="text-red-600">*</span>
              </label>
              <input
                v-model="formData.fullName"
                @input="formData.fullName = (formData.fullName || '').toUpperCase()"
                type="text"
                required
                placeholder="Pasport bo'yicha to'liq ismingiz"
                class="w-full px-3.5 py-2.5 text-xs font-bold rounded-lg border border-zinc-300 dark:border-zinc-700 bg-white dark:bg-zinc-900 text-black dark:text-white placeholder:text-zinc-400 focus:outline-hidden focus:border-black dark:focus:border-white transition-colors shadow-2xs uppercase"
              />
              <p v-if="attemptStep1 && formData.fullName.trim().length < 3" class="mt-1 text-[11px] font-semibold text-red-600 dark:text-red-400">
                F.I.O ni kiriting!
              </p>
            </div>

            <!-- Education Level Dropdown -->
            <div>
              <label class="block text-xs font-bold uppercase tracking-wide text-black dark:text-white mb-1.5">
                Ta'lim bosqichi <span class="text-red-600">*</span>
              </label>
              <select
                v-model="formData.educationLevel"
                required
                class="w-full px-3.5 py-2.5 text-xs font-semibold rounded-lg border border-zinc-300 dark:border-zinc-700 bg-white dark:bg-zinc-900 text-black dark:text-white focus:outline-hidden focus:border-black dark:focus:border-white transition-colors shadow-2xs cursor-pointer"
              >
                <option value="" disabled>Ta'lim bosqichini tanlang</option>
                <option
                  v-for="lvl in tenantInfo?.education_levels || []"
                  :key="lvl.id"
                  :value="lvl.name"
                >
                  {{ lvl.name }}
                </option>
              </select>
              <p v-if="attemptStep1 && !formData.educationLevel" class="mt-1 text-[11px] font-semibold text-red-600 dark:text-red-400">
                Ta'lim bosqichini tanlang!
              </p>
            </div>

            <!-- Tenant Office Dropdown -->
            <div>
              <label class="block text-xs font-bold uppercase tracking-wide text-black dark:text-white mb-1.5">
                Qabul ofisi / Filial <span class="text-red-600">*</span>
              </label>
              <select
                v-model="formData.office"
                required
                class="w-full px-3.5 py-2.5 text-xs font-semibold rounded-lg border border-zinc-300 dark:border-zinc-700 bg-white dark:bg-zinc-900 text-black dark:text-white focus:outline-hidden focus:border-black dark:focus:border-white transition-colors shadow-2xs cursor-pointer"
              >
                <option value="" disabled>Ofisni tanlang</option>
                <option
                  v-for="office in tenantInfo?.offices || []"
                  :key="office.id"
                  :value="office.name"
                >
                  {{ office.name }}
                </option>
              </select>
              <p v-if="attemptStep1 && !formData.office" class="mt-1 text-[11px] font-semibold text-red-600 dark:text-red-400">
                Ofisni tanlang!
              </p>
            </div>

            <!-- Date of Birth Picker -->
            <div class="sm:col-span-2">
              <label class="block text-xs font-bold uppercase tracking-wide text-black dark:text-white mb-1.5">
                Tug'ilgan sana <span class="text-red-600">*</span>
              </label>
              <div class="grid grid-cols-3 gap-2.5 sm:gap-3">
                <select
                  v-model="formData.dobDay"
                  required
                  class="w-full px-3 py-2.5 text-xs font-semibold rounded-lg border border-zinc-300 dark:border-zinc-700 bg-white dark:bg-zinc-900 text-black dark:text-white focus:outline-hidden focus:border-black dark:focus:border-white shadow-2xs cursor-pointer"
                >
                  <option value="" disabled>Kun</option>
                  <option v-for="d in days" :key="d" :value="d">{{ d }}</option>
                </select>

                <select
                  v-model="formData.dobMonth"
                  required
                  class="w-full px-3 py-2.5 text-xs font-semibold rounded-lg border border-zinc-300 dark:border-zinc-700 bg-white dark:bg-zinc-900 text-black dark:text-white focus:outline-hidden focus:border-black dark:focus:border-white shadow-2xs cursor-pointer"
                >
                  <option value="" disabled>Oy</option>
                  <option v-for="m in months" :key="m.value" :value="m.value">{{ m.name }}</option>
                </select>

                <select
                  v-model="formData.dobYear"
                  required
                  class="w-full px-3 py-2.5 text-xs font-semibold rounded-lg border border-zinc-300 dark:border-zinc-700 bg-white dark:bg-zinc-900 text-black dark:text-white focus:outline-hidden focus:border-black dark:focus:border-white shadow-2xs cursor-pointer"
                >
                  <option value="" disabled>Yil</option>
                  <option v-for="y in years" :key="y" :value="y">{{ y }}</option>
                </select>
              </div>
              <p v-if="attemptStep1 && (!formData.dobDay || !formData.dobMonth || !formData.dobYear)" class="mt-1 text-[11px] font-semibold text-red-600 dark:text-red-400">
                Tug'ilgan sanani to'liq kiriting!
              </p>
            </div>

            <!-- Phone 1 + Firebase OTP Verification -->
            <div class="sm:col-span-2">
              <label class="block text-xs font-bold uppercase tracking-wide text-black dark:text-white mb-1.5">
                Mobil telefon 1 <span class="text-red-600">*</span>
                <span class="ml-1 text-[10px] font-normal text-zinc-500 normal-case">(SMS orqali tasdiqlanadi)</span>
              </label>

              <!-- reCAPTCHA invisible container -->
              <div id="recaptcha-phone1"></div>

              <!-- Phone input + Send OTP button -->
              <div class="flex items-stretch gap-2">
                <div class="flex-1">
                  <input
                    :value="formData.phone1"
                    @input="onPhone1Input"
                    type="tel"
                    required
                    :disabled="phone1IsVerified"
                    placeholder="+998 90-123-45-67"
                    class="w-full px-3.5 py-2.5 text-xs font-mono font-bold rounded-lg border border-zinc-300 dark:border-zinc-700 bg-white dark:bg-zinc-900 text-black dark:text-white placeholder:text-zinc-400 focus:outline-hidden focus:border-black dark:focus:border-white transition-colors shadow-2xs disabled:opacity-60"
                  />
                </div>

                <!-- Verified badge -->
                <template v-if="phone1IsVerified">
                  <div class="inline-flex items-center gap-1.5 px-3 py-2 rounded-lg bg-emerald-50 dark:bg-emerald-950/60 border border-emerald-400/50 text-emerald-700 dark:text-emerald-300 text-xs font-bold whitespace-nowrap">
                    <CheckCircle2 class="w-3.5 h-3.5" />
                    Tasdiqlandi
                  </div>
                </template>

                <!-- Send OTP button -->
                <template v-else-if="phone1Step === 'idle' || phone1Step === 'sending'">
                  <button
                    type="button"
                    @click="sendPhone1Otp"
                    :disabled="!isCompletePhone(formData.phone1) || phone1Loading"
                    class="px-3 py-2 rounded-lg bg-zinc-900 hover:bg-zinc-700 dark:bg-zinc-100 dark:hover:bg-white text-white dark:text-black text-xs font-bold transition-all disabled:opacity-40 whitespace-nowrap cursor-pointer inline-flex items-center gap-1.5"
                  >
                    <Loader2 v-if="phone1Loading" class="w-3.5 h-3.5 animate-spin" />
                    <Phone v-else class="w-3.5 h-3.5" />
                    SMS yuborish
                  </button>
                </template>

                <!-- Resend button when code sent -->
                <template v-else>
                  <button
                    type="button"
                    @click="sendPhone1Otp"
                    :disabled="phone1Loading"
                    class="px-3 py-2 rounded-lg border border-zinc-300 dark:border-zinc-700 text-xs font-bold text-zinc-700 dark:text-zinc-300 hover:bg-zinc-100 dark:hover:bg-zinc-800 transition-all disabled:opacity-40 whitespace-nowrap cursor-pointer"
                  >
                    Qayta yuborish
                  </button>
                </template>
              </div>

              <!-- OTP code input (shown after SMS sent) -->
              <div v-if="phone1Step === 'code_sent' || phone1Step === 'verifying'" class="mt-2.5 flex items-stretch gap-2">
                <div class="relative flex-1">
                  <KeyRound class="w-3.5 h-3.5 text-zinc-400 absolute left-3 top-1/2 -translate-y-1/2 pointer-events-none" />
                  <input
                    v-model="phone1OtpCode"
                    type="text"
                    maxlength="6"
                    placeholder="6 xonali SMS kod"
                    class="w-full pl-9 pr-3 py-2.5 text-xs font-mono tracking-widest text-center rounded-lg border border-zinc-300 dark:border-zinc-700 bg-white dark:bg-zinc-900 text-black dark:text-white focus:outline-hidden focus:border-black dark:focus:border-white transition-colors shadow-2xs"
                  />
                </div>
                <button
                  type="button"
                  @click="confirmPhone1Otp"
                  :disabled="phone1OtpCode.length < 6 || phone1Loading"
                  class="px-4 py-2 rounded-lg bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-bold transition-all disabled:opacity-40 cursor-pointer inline-flex items-center gap-1.5"
                >
                  <Loader2 v-if="phone1Loading" class="w-3.5 h-3.5 animate-spin" />
                  <Check v-else class="w-3.5 h-3.5" />
                  Tasdiqlash
                </button>
              </div>

              <!-- Error message -->
              <p v-if="phone1Error" class="mt-1.5 text-[11px] font-semibold text-red-600 dark:text-red-400 flex items-center gap-1">
                <AlertCircle class="w-3 h-3 shrink-0" />
                {{ phone1Error }}
              </p>

              <!-- Validation error (tried to proceed without verification) -->
              <p v-if="attemptStep1 && !phone1IsVerified && isCompletePhone(formData.phone1)" class="mt-1 text-[11px] font-semibold text-amber-600 dark:text-amber-400">
                ⚠️ Telefon raqamini SMS orqali tasdiqlang!
              </p>
              <p v-if="attemptStep1 && !isCompletePhone(formData.phone1)" class="mt-1 text-[11px] font-semibold text-red-600 dark:text-red-400">
                Telefon raqamini to'liq kiriting!
              </p>
            </div>

            <!-- Phone 2 -->
            <div>
              <label class="block text-xs font-bold uppercase tracking-wide text-black dark:text-white mb-1.5">
                Mobil telefon 2 <span class="text-red-600">*</span>
              </label>
              <div>
                <input
                  :value="formData.phone2"
                  @input="onPhone2Input"
                  type="tel"
                  required
                  placeholder="+998 93-765-43-21"
                  class="w-full px-3.5 py-2.5 text-xs font-mono font-bold rounded-lg border border-zinc-300 dark:border-zinc-700 bg-white dark:bg-zinc-900 text-black dark:text-white placeholder:text-zinc-400 focus:outline-hidden focus:border-black dark:focus:border-white transition-colors shadow-2xs"
                />
              </div>
              <p v-if="attemptStep1 && !isCompletePhone(formData.phone2)" class="mt-1 text-[11px] font-semibold text-red-600 dark:text-red-400">
                Telefon raqamini to'liq kiriting!
              </p>
            </div>

            <!-- Email -->
            <div class="sm:col-span-2">
              <label class="block text-xs font-bold uppercase tracking-wide text-black dark:text-white mb-1.5">
                Email manzil <span class="text-red-600">*</span>
              </label>
              <input
                v-model="formData.email"
                type="email"
                required
                placeholder="student@example.com"
                class="w-full px-3.5 py-2.5 text-xs font-mono font-bold rounded-lg border border-zinc-300 dark:border-zinc-700 bg-white dark:bg-zinc-900 text-black dark:text-white placeholder:text-zinc-400 focus:outline-hidden focus:border-black dark:focus:border-white transition-colors shadow-2xs"
              />
              <p v-if="attemptStep1 && !formData.email.trim()" class="mt-1 text-[11px] font-semibold text-red-600 dark:text-red-400">
                Email yozing!
              </p>
              <p v-else-if="attemptStep1 && !formData.email.includes('@')" class="mt-1 text-[11px] font-semibold text-red-600 dark:text-red-400">
                Email manzili noto'g'ri!
              </p>
            </div>
          </div>

          <!-- Bottom Next Button -->
          <div class="pt-5 border-t border-zinc-200 dark:border-zinc-850 flex justify-end">
            <button
              type="button"
              @click="goToStep2"
              :disabled="!isStep1Valid"
              class="inline-flex items-center gap-2 px-6 py-2.5 rounded-lg bg-black hover:bg-zinc-800 text-white dark:bg-white dark:hover:bg-zinc-200 dark:text-black text-xs font-bold shadow-xs transition-all cursor-pointer active:scale-98 disabled:opacity-40"
            >
              <span>Shartnomani o'qish va imzolash</span>
              <ArrowRight class="w-3.5 h-3.5" />
            </button>
          </div>
        </section>
      </div>

      <!-- STEP 2: CONTRACT READING & ELECTRONIC SIGNATURE -->
      <div v-else-if="currentStep === 2" class="space-y-6">
        <!-- 2.1 Complete Contract Reading -->
        <section class="bg-white dark:bg-zinc-900/60 border border-zinc-300 dark:border-zinc-800 rounded-xl p-6 sm:p-8 shadow-xs">
          <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-4 pb-4 border-b border-zinc-200 dark:border-zinc-850">
            <div>
              <h2 class="text-base font-bold text-black dark:text-white tracking-tight flex items-center gap-2">
                <span>Shartnoma bilan to'liq tanishish</span>
                <span v-if="hasReadFullContract" class="text-[10.5px] font-mono font-bold px-2 py-0.5 rounded-md bg-emerald-50 text-emerald-700 dark:bg-emerald-950/60 dark:text-emerald-400 border border-emerald-500/20">
                  ✓ O'qib chiqildi
                </span>
              </h2>
              <p class="text-xs text-zinc-700 dark:text-zinc-300 font-medium mt-0.5">
                Imzolashdan oldin shartnoma matnining barcha bandlari bilan tanishib chiqing
              </p>
            </div>

            <button
              type="button"
              @click="handleOpenFullContract"
              class="inline-flex items-center gap-1.5 px-3.5 py-2 rounded-lg bg-blue-600 hover:bg-blue-700 text-white text-xs font-bold border border-blue-700/20 dark:border-blue-500/20 shadow-xs hover:shadow-sm transition-all cursor-pointer self-start sm:self-center active:scale-98"
            >
              <BookOpen class="w-3.5 h-3.5 text-white" />
              <span>Shartnomani to'liq ochish</span>
            </button>
          </div>

          <!-- Quick Preview Box -->
          <div class="bg-zinc-50/70 dark:bg-zinc-850/50 border border-zinc-300 dark:border-zinc-800 rounded-lg p-4 sm:p-5 max-h-52 overflow-y-auto text-xs text-black dark:text-zinc-200 leading-relaxed font-sans">
            <h4 class="font-bold text-black dark:text-white mb-2">
              {{ selectedTariff?.name }} DASTURI BO'YICHA KONSALTING XIZMATLARI SHARTNOMASI
            </h4>
            <div class="space-y-1 text-xs text-zinc-800 dark:text-zinc-300">
              <p><strong>Mijoz (F.I.O):</strong> {{ (formData.fullName || '').toUpperCase() || '—' }}</p>
              <p><strong>Pasport raqami:</strong> {{ (formData.passportNumber || '').toUpperCase() || '—' }}</p>
              <p><strong>Ta'lim bosqichi:</strong> {{ formData.educationLevel || '—' }}</p>
              <p><strong>Qabul ofisi:</strong> {{ formData.office || '—' }}</p>
              <p><strong>Tug'ilgan sana:</strong> {{ formattedDob || '—' }}</p>
              <p><strong>Telefonlar:</strong> {{ displayPhone(formData.phone1) || '—' }} / {{ displayPhone(formData.phone2) || '—' }}</p>
              <p><strong>Xizmat to'lovi:</strong> {{ formatPrice(selectedTariff?.price) }}</p>
              <p class="pt-2 text-zinc-600 dark:text-zinc-400 italic">
                Shartnomaning barcha bandlari va yuridik kafolatlarini ko'rish uchun yuqoridagi "Shartnomani to'liq ochish" tugmasini bosing.
              </p>
            </div>
          </div>
        </section>

        <!-- 2.2 Contract Agreement Declarations -->
        <section class="bg-white dark:bg-zinc-900/60 border border-zinc-300 dark:border-zinc-800 rounded-xl p-6 sm:p-8 shadow-xs space-y-4">
          <div class="pb-3 border-b border-zinc-200 dark:border-zinc-850">
            <h3 class="text-sm font-bold text-black dark:text-white tracking-tight">
              Shartnoma roziliklari va tasdiqlash
            </h3>
            <p class="text-xs text-zinc-700 dark:text-zinc-300 font-medium">
              Quyidagi bandlarni belgilash orqali shartnoma shartlariga to'liq rozilik bildirasiz
            </p>
          </div>

          <div class="space-y-3">
            <label class="flex items-start gap-3 cursor-pointer select-none p-2.5 rounded-lg border border-transparent hover:border-zinc-200 dark:hover:border-zinc-800 transition-colors">
              <input
                type="checkbox"
                v-model="declarations.readFullContract"
                class="mt-0.5 w-4 h-4 rounded border-zinc-400 dark:border-zinc-600 text-black focus:ring-black"
              />
              <span class="text-xs font-semibold text-black dark:text-white leading-snug">
                Shartnomani to'liq o'qib chiqdim va barcha bandlariga roziman
              </span>
            </label>
            <p v-if="attemptStep2 && !declarations.readFullContract" class="text-[11px] font-semibold text-red-600 dark:text-red-400 pl-2.5">
              Shartnomani o'qib chiqqaningizni tasdiqlang!
            </p>

            <label class="flex items-start gap-3 cursor-pointer select-none p-2.5 rounded-lg border border-transparent hover:border-zinc-200 dark:hover:border-zinc-800 transition-colors">
              <input
                type="checkbox"
                v-model="declarations.voluntarySign"
                class="mt-0.5 w-4 h-4 rounded border-zinc-400 dark:border-zinc-600 text-black focus:ring-black"
              />
              <span class="text-xs font-semibold text-black dark:text-white leading-snug">
                Shartnomani o'z erkin xohishim bilan imzoladim
              </span>
            </label>
            <p v-if="attemptStep2 && !declarations.voluntarySign" class="text-[11px] font-semibold text-red-600 dark:text-red-400 pl-2.5">
              Ushbu bandni tasdiqlang!
            </p>

            <label class="flex items-start gap-3 cursor-pointer select-none p-2.5 rounded-lg border border-transparent hover:border-zinc-200 dark:hover:border-zinc-800 transition-colors">
              <input
                type="checkbox"
                v-model="declarations.confirmationCodeMeaning"
                class="mt-0.5 w-4 h-4 rounded border-zinc-400 dark:border-zinc-600 text-black focus:ring-black"
              />
              <span class="text-xs font-semibold text-black dark:text-white leading-snug">
                Kiritiladigan tasdiqlash kodi ushbu shartnomani rasman tasdiqlashimni bildiradi
              </span>
            </label>
            <p v-if="attemptStep2 && !declarations.confirmationCodeMeaning" class="text-[11px] font-semibold text-red-600 dark:text-red-400 pl-2.5">
              Ushbu bandni tasdiqlang!
            </p>

            <label class="flex items-start gap-3 cursor-pointer select-none p-2.5 rounded-lg border border-transparent hover:border-zinc-200 dark:hover:border-zinc-800 transition-colors">
              <input
                type="checkbox"
                v-model="declarations.legalBasisAcknowledged"
                class="mt-0.5 w-4 h-4 rounded border-zinc-400 dark:border-zinc-600 text-black focus:ring-black"
              />
              <span class="text-xs font-semibold text-black dark:text-white leading-snug">
                Telefon, planshet va kompyuterlarda imzo qo'yib tasdiqlash
                <button
                  type="button"
                  @click.prevent="isLegalBasisModalOpen = true"
                  class="text-blue-600 dark:text-blue-400 underline underline-offset-2 hover:text-blue-700 dark:hover:text-blue-300 font-bold"
                >ushbu</button>
                qonunchilik moddalariga to'g'ri kelishidan xabarim bor, imzo rasmiy kuchga ega
              </span>
            </label>
            <p v-if="attemptStep2 && !declarations.legalBasisAcknowledged" class="text-[11px] font-semibold text-red-600 dark:text-red-400 pl-2.5">
              Ushbu bandni tasdiqlang!
            </p>
          </div>

          <!-- Guardian (kafil) consent: only for a student under 18 at signing time -->
          <div v-if="isMinor" class="space-y-4 pt-4 border-t border-zinc-200 dark:border-zinc-850">
            <div>
              <h4 class="text-sm font-bold text-black dark:text-white tracking-tight flex items-center gap-2">
                Kafil (ota-ona/vasiy) ma'lumotlari
                <span class="px-2 py-0.5 rounded-full bg-amber-100 dark:bg-amber-950/60 text-amber-800 dark:text-amber-300 text-[10px] font-bold">18 yoshdan kichik</span>
              </h4>
              <p class="text-xs text-zinc-600 dark:text-zinc-400 font-medium mt-0.5">
                Fuqarolik kodeksining 27-moddasiga ko'ra, voyaga yetmagan talaba nomidan tuzilgan shartnoma
                ota-ona yoki vasiyning yozma roziligi va imzosi bilangina yuridik kuchga ega bo'ladi.
              </p>
            </div>

            <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <div>
                <label class="text-[11px] font-bold uppercase tracking-wider text-zinc-500 dark:text-zinc-400 block mb-1">F.I.O</label>
                <input
                  v-model="guardianData.fullName"
                  type="text"
                  placeholder="ABDULLAYEV VALI"
                  class="w-full h-9 px-3 text-xs rounded-lg border border-zinc-300 dark:border-zinc-700 bg-white dark:bg-zinc-900 text-black dark:text-white focus:outline-none focus:ring-1 focus:ring-black dark:focus:ring-white"
                />
                <p v-if="attemptStep2 && guardianData.fullName.trim().length < 3" class="mt-1 text-[11px] font-semibold text-red-600 dark:text-red-400">
                  Kafil F.I.O sini kiriting!
                </p>
              </div>
              <div>
                <label class="text-[11px] font-bold uppercase tracking-wider text-zinc-500 dark:text-zinc-400 block mb-1">Pasport raqami</label>
                <input
                  v-model="guardianData.passportNumber"
                  type="text"
                  placeholder="AB1234567"
                  class="w-full h-9 px-3 text-xs rounded-lg border border-zinc-300 dark:border-zinc-700 bg-white dark:bg-zinc-900 text-black dark:text-white focus:outline-none focus:ring-1 focus:ring-black dark:focus:ring-white"
                />
                <p v-if="attemptStep2 && guardianData.passportNumber.trim().length < 6" class="mt-1 text-[11px] font-semibold text-red-600 dark:text-red-400">
                  Kafil pasport raqamini kiriting!
                </p>
              </div>
              <div>
                <label class="text-[11px] font-bold uppercase tracking-wider text-zinc-500 dark:text-zinc-400 block mb-1">Talabaga qarindoshligi</label>
                <select
                  v-model="guardianRelationOption"
                  class="w-full h-9 px-3 text-xs rounded-lg border border-zinc-300 dark:border-zinc-700 bg-white dark:bg-zinc-900 text-black dark:text-white focus:outline-none focus:ring-1 focus:ring-black dark:focus:ring-white cursor-pointer"
                >
                  <option value="" disabled>Tanlang</option>
                  <option v-for="opt in GUARDIAN_RELATION_OPTIONS" :key="opt" :value="opt">{{ opt }}</option>
                  <option value="Other">Boshqa (qo'lda yozish)</option>
                </select>
                <input
                  v-if="guardianRelationOption === 'Other'"
                  v-model="guardianData.relation"
                  type="text"
                  placeholder="Masalan: Tog'a, Vasiy"
                  class="w-full h-9 px-3 mt-1.5 text-xs rounded-lg border border-zinc-300 dark:border-zinc-700 bg-white dark:bg-zinc-900 text-black dark:text-white focus:outline-none focus:ring-1 focus:ring-black dark:focus:ring-white"
                />
                <p v-if="attemptStep2 && !guardianData.relation.trim()" class="mt-1 text-[11px] font-semibold text-red-600 dark:text-red-400">
                  Qarindoshlikni tanlang!
                </p>
              </div>
              <div class="sm:col-span-2">
                <label class="text-[11px] font-bold uppercase tracking-wider text-zinc-500 dark:text-zinc-400 block mb-1">
                  Telefon raqami
                  <span class="ml-1 text-[10px] font-normal text-zinc-500 normal-case">(SMS orqali tasdiqlanadi)</span>
                </label>

                <!-- reCAPTCHA invisible container -->
                <div id="recaptcha-guardian"></div>

                <!-- Phone input row -->
                <div class="flex items-stretch gap-2">
                  <div class="flex-1">
                    <input
                      :value="guardianData.phone"
                      @input="onGuardianPhoneInput"
                      type="tel"
                      :disabled="guardianIsVerified"
                      placeholder="+998 90-123-45-67"
                      class="w-full h-9 px-3 text-xs rounded-lg border border-zinc-300 dark:border-zinc-700 bg-white dark:bg-zinc-900 text-black dark:text-white focus:outline-none focus:ring-1 focus:ring-black dark:focus:ring-white disabled:opacity-60"
                    />
                  </div>

                  <!-- Verified badge -->
                  <template v-if="guardianIsVerified">
                    <div class="inline-flex items-center gap-1.5 px-3 py-2 rounded-lg bg-emerald-50 dark:bg-emerald-950/60 border border-emerald-400/50 text-emerald-700 dark:text-emerald-300 text-xs font-bold whitespace-nowrap">
                      <CheckCircle2 class="w-3.5 h-3.5" />
                      Tasdiqlandi
                    </div>
                  </template>

                  <!-- Send OTP button -->
                  <template v-else-if="guardianStep === 'idle' || guardianStep === 'sending'">
                    <button
                      type="button"
                      @click="sendGuardianOtp"
                      :disabled="!isCompletePhone(guardianData.phone) || guardianLoading"
                      class="h-9 px-3 rounded-lg bg-zinc-900 hover:bg-zinc-700 dark:bg-zinc-100 dark:hover:bg-white text-white dark:text-black text-xs font-bold transition-all disabled:opacity-40 whitespace-nowrap cursor-pointer inline-flex items-center gap-1.5"
                    >
                      <Loader2 v-if="guardianLoading" class="w-3.5 h-3.5 animate-spin" />
                      <Phone v-else class="w-3.5 h-3.5" />
                      SMS
                    </button>
                  </template>

                  <!-- Resend button -->
                  <template v-else>
                    <button
                      type="button"
                      @click="sendGuardianOtp"
                      :disabled="guardianLoading"
                      class="h-9 px-3 rounded-lg border border-zinc-300 dark:border-zinc-700 text-xs font-bold text-zinc-700 dark:text-zinc-300 hover:bg-zinc-100 dark:hover:bg-zinc-800 transition-all disabled:opacity-40 whitespace-nowrap cursor-pointer"
                    >
                      Qayta
                    </button>
                  </template>
                </div>

                <!-- OTP code input -->
                <div v-if="guardianStep === 'code_sent' || guardianStep === 'verifying'" class="mt-2 flex items-stretch gap-2">
                  <div class="relative flex-1">
                    <KeyRound class="w-3.5 h-3.5 text-zinc-400 absolute left-3 top-1/2 -translate-y-1/2 pointer-events-none" />
                    <input
                      v-model="guardianOtpCode"
                      type="text"
                      maxlength="6"
                      placeholder="6 xonali SMS kod"
                      class="w-full pl-9 pr-3 h-9 text-xs font-mono tracking-widest text-center rounded-lg border border-zinc-300 dark:border-zinc-700 bg-white dark:bg-zinc-900 text-black dark:text-white focus:outline-none focus:ring-1 focus:ring-black dark:focus:ring-white"
                    />
                  </div>
                  <button
                    type="button"
                    @click="confirmGuardianOtp"
                    :disabled="guardianOtpCode.length < 6 || guardianLoading"
                    class="h-9 px-4 rounded-lg bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-bold transition-all disabled:opacity-40 cursor-pointer inline-flex items-center gap-1.5"
                  >
                    <Loader2 v-if="guardianLoading" class="w-3.5 h-3.5 animate-spin" />
                    <Check v-else class="w-3.5 h-3.5" />
                    OK
                  </button>
                </div>

                <!-- Error -->
                <p v-if="guardianError" class="mt-1 text-[11px] font-semibold text-red-600 dark:text-red-400 flex items-center gap-1">
                  <AlertCircle class="w-3 h-3 shrink-0" />
                  {{ guardianError }}
                </p>
                <p v-if="attemptStep2 && !guardianIsVerified && isCompletePhone(guardianData.phone)" class="mt-1 text-[11px] font-semibold text-amber-600 dark:text-amber-400">
                  ⚠️ Kafil telefon raqamini SMS orqali tasdiqlang!
                </p>
                <p v-if="attemptStep2 && !isCompletePhone(guardianData.phone)" class="mt-1 text-[11px] font-semibold text-red-600 dark:text-red-400">
                  Kafil telefon raqamini to'liq kiriting!
                </p>
              </div>
              <div class="sm:col-span-2">
                <label class="text-[11px] font-bold uppercase tracking-wider text-zinc-500 dark:text-zinc-400 block mb-1">Yashash manzili</label>
                <input
                  v-model="guardianData.address"
                  type="text"
                  placeholder="Toshkent sh., ..."
                  class="w-full h-9 px-3 text-xs rounded-lg border border-zinc-300 dark:border-zinc-700 bg-white dark:bg-zinc-900 text-black dark:text-white focus:outline-none focus:ring-1 focus:ring-black dark:focus:ring-white"
                />
                <p v-if="attemptStep2 && guardianData.address.trim().length < 3" class="mt-1 text-[11px] font-semibold text-red-600 dark:text-red-400">
                  Yashash manzilini kiriting!
                </p>
              </div>
            </div>

            <div class="flex flex-col sm:flex-row items-stretch sm:items-center gap-2.5">
              <button
                v-if="tenantInfo?.guardian_contract_text"
                type="button"
                @click="isGuardianContractViewerOpen = true"
                class="inline-flex items-center justify-center gap-1.5 px-3.5 py-2 rounded-lg border border-zinc-300 dark:border-zinc-700 bg-white hover:bg-zinc-50 dark:bg-zinc-800 dark:hover:bg-zinc-750 text-xs font-bold text-black dark:text-white transition-colors cursor-pointer shadow-2xs"
              >
                <Eye class="w-3.5 h-3.5 text-zinc-600 dark:text-zinc-400" />
                <span>Kafillik shartnomasini ko'rish</span>
              </button>

              <button
                type="button"
                @click="isGuardianSignatureModalOpen = true"
                class="inline-flex items-center justify-center gap-1.5 px-3.5 py-2 rounded-lg text-xs font-bold transition-colors cursor-pointer shadow-2xs"
                :class="guardianSignatureData
                  ? 'border border-emerald-300 dark:border-emerald-800 bg-emerald-50 dark:bg-emerald-950/40 text-emerald-700 dark:text-emerald-400'
                  : 'border border-zinc-300 dark:border-zinc-700 bg-white hover:bg-zinc-50 dark:bg-zinc-800 dark:hover:bg-zinc-750 text-black dark:text-white'"
              >
                <CheckCircle2 v-if="guardianSignatureData" class="w-3.5 h-3.5" />
                <span>{{ guardianSignatureData ? 'Kafil imzolandi (qayta chizish)' : 'Kafil imzosini qo\'yish' }}</span>
              </button>
            </div>
            <p v-if="!guardianSignatureData" class="text-[11px] font-semibold text-red-600 dark:text-red-400">
              Kafilning imzosi kutilmoqda!
            </p>
          </div>

          <!-- Actions: Back & Continue to Review -->
          <div class="pt-5 border-t border-zinc-200 dark:border-zinc-850 flex items-center justify-between">
            <button
              type="button"
              @click="currentStep = 1"
              class="inline-flex items-center gap-1.5 px-3.5 py-2 rounded-lg border border-zinc-300 dark:border-zinc-700 bg-white hover:bg-zinc-50 dark:bg-zinc-900 dark:hover:bg-zinc-850 text-xs font-bold text-black dark:text-white transition-colors shadow-2xs cursor-pointer"
            >
              <ArrowLeft class="w-3.5 h-3.5" />
              <span>Orqaga</span>
            </button>

            <button
              type="button"
              @click="handleProceedToReview"
              :disabled="!isStep2DeclarationsValid || !isGuardianInfoValid"
              class="inline-flex items-center gap-2 px-6 py-2.5 rounded-lg bg-black hover:bg-zinc-800 text-white dark:bg-white dark:hover:bg-zinc-200 dark:text-black text-xs font-bold shadow-xs transition-all cursor-pointer active:scale-98 disabled:opacity-40"
            >
              <span>Tekshirish sahifasiga o'tish</span>
              <ArrowRight class="w-3.5 h-3.5" />
            </button>
          </div>
        </section>
      </div>

      <!-- STEP 3: FINAL REVIEW BEFORE SIGNING -->
      <div v-else-if="currentStep === 3" class="space-y-6">
        <section class="bg-white dark:bg-zinc-900/60 border border-zinc-300 dark:border-zinc-800 rounded-xl p-6 sm:p-8 shadow-xs space-y-6">
          <div class="flex items-center justify-between pb-4 border-b border-zinc-200 dark:border-zinc-850">
            <div>
              <h2 class="text-base font-bold text-black dark:text-white tracking-tight">
                Yakuniy ma'lumotlarni tekshirish
              </h2>
              <p class="text-xs text-zinc-700 dark:text-zinc-300 font-medium">
                Imzolashdan oldin barcha kiritilgan ma'lumotlarni qayta ko'rib chiqing
              </p>
            </div>

            <button
              type="button"
              @click="currentStep = 1"
              class="text-xs font-mono font-bold text-black dark:text-white hover:underline underline-offset-4 cursor-pointer"
            >
              Tahrirlash
            </button>
          </div>

          <!-- Review Grid -->
          <div class="grid grid-cols-1 sm:grid-cols-2 gap-3.5 text-xs">
            <div class="p-3.5 bg-zinc-50/70 dark:bg-zinc-850/50 rounded-lg border border-zinc-200 dark:border-zinc-800">
              <span class="text-xs font-bold uppercase tracking-wide text-zinc-700 dark:text-zinc-300 block mb-1">Tanlangan tarif</span>
              <strong class="text-xs font-bold text-black dark:text-white">{{ selectedTariff?.name }}</strong>
            </div>

            <div class="p-3.5 bg-zinc-50/70 dark:bg-zinc-850/50 rounded-lg border border-zinc-200 dark:border-zinc-800">
              <span class="text-xs font-bold uppercase tracking-wide text-zinc-700 dark:text-zinc-300 block mb-1">Shartnoma to'lovi</span>
              <strong class="text-xs font-bold font-mono text-black dark:text-white">{{ formatPrice(selectedTariff?.price) }}</strong>
            </div>

            <div class="p-3.5 bg-zinc-50/70 dark:bg-zinc-850/50 rounded-lg border border-zinc-200 dark:border-zinc-800">
              <span class="text-xs font-bold uppercase tracking-wide text-zinc-700 dark:text-zinc-300 block mb-1">To'liq ism-sharif (F.I.O)</span>
              <strong class="text-xs font-bold text-black dark:text-white uppercase">{{ (formData.fullName || '').toUpperCase() }}</strong>
            </div>

            <div class="p-3.5 bg-zinc-50/70 dark:bg-zinc-850/50 rounded-lg border border-zinc-200 dark:border-zinc-800">
              <span class="text-xs font-bold uppercase tracking-wide text-zinc-700 dark:text-zinc-300 block mb-1">Pasport raqami</span>
              <strong class="text-xs font-mono font-bold text-black dark:text-white uppercase">{{ (formData.passportNumber || '').toUpperCase() }}</strong>
            </div>

            <div class="p-3.5 bg-zinc-50/70 dark:bg-zinc-850/50 rounded-lg border border-zinc-200 dark:border-zinc-800">
              <span class="text-xs font-bold uppercase tracking-wide text-zinc-700 dark:text-zinc-300 block mb-1">Tug'ilgan sana</span>
              <strong class="text-xs font-bold text-black dark:text-white">{{ formattedDob }}</strong>
            </div>

            <div class="p-3.5 bg-zinc-50/70 dark:bg-zinc-850/50 rounded-lg border border-zinc-200 dark:border-zinc-800">
              <span class="text-xs font-bold uppercase tracking-wide text-zinc-700 dark:text-zinc-300 block mb-1">Ta'lim bosqichi</span>
              <strong class="text-xs font-bold text-black dark:text-white">{{ formData.educationLevel }}</strong>
            </div>

            <div class="p-3.5 bg-zinc-50/70 dark:bg-zinc-850/50 rounded-lg border border-zinc-200 dark:border-zinc-800">
              <span class="text-xs font-bold uppercase tracking-wide text-zinc-700 dark:text-zinc-300 block mb-1">Qabul ofisi</span>
              <strong class="text-xs font-bold text-black dark:text-white">{{ formData.office }}</strong>
            </div>

            <div class="p-3.5 bg-zinc-50/70 dark:bg-zinc-850/50 rounded-lg border border-zinc-200 dark:border-zinc-800">
              <span class="text-xs font-bold uppercase tracking-wide text-zinc-700 dark:text-zinc-300 block mb-1">Telefon raqamlari</span>
              <strong class="text-xs font-mono font-bold text-black dark:text-white">{{ displayPhone(formData.phone1) }} / {{ displayPhone(formData.phone2) }}</strong>
            </div>
          </div>

          <!-- Electronic Signature Preview -->
          <div class="p-4 bg-zinc-50/70 dark:bg-zinc-850/50 rounded-lg border border-zinc-200 dark:border-zinc-800">
            <div class="flex items-center justify-between mb-2">
              <span class="text-xs font-bold uppercase tracking-wide text-zinc-700 dark:text-zinc-300">Elektron imzo namunasi</span>
              <button
                type="button"
                @click="isSignatureModalOpen = true"
                class="text-xs font-mono font-bold text-black dark:text-white hover:underline cursor-pointer"
              >
                Imzoni o'zgartirish
              </button>
            </div>
            <div class="w-full h-24 bg-white dark:bg-zinc-950 border border-dashed border-zinc-300 dark:border-zinc-700 rounded-lg flex items-center justify-center p-2">
              <img
                v-if="formData.signatureData"
                :src="formData.signatureData"
                alt="Imzo"
                class="max-h-full object-contain"
              />
              <span v-else class="text-xs font-semibold text-zinc-500">Imzo qo'yilmagan</span>
            </div>
          </div>

          <!-- Declarations Summary -->
          <div class="p-3.5 rounded-lg bg-emerald-50 dark:bg-emerald-950/40 border border-emerald-500/20 text-xs text-emerald-900 dark:text-emerald-200 space-y-1">
            <div class="font-bold flex items-center gap-1.5">
              <Check class="w-3.5 h-3.5 shrink-0 text-emerald-700 dark:text-emerald-400" />
              <span>Barcha talab etilgan shartnoma roziliklari tasdiqlangan:</span>
            </div>
            <ul class="list-disc list-inside space-y-0.5 text-[11px] font-medium text-emerald-800 dark:text-emerald-300 pl-5">
              <li>Shartnoma to'liq o'qib chiqildi</li>
              <li>O'z xohishi bilan imzolandi</li>
              <li>Tasdiqlash kodi haqiqiyligi e'tirof etildi</li>
            </ul>
          </div>

          <!-- Bottom Action Buttons -->
          <div class="pt-5 border-t border-zinc-200 dark:border-zinc-850 flex items-center justify-between">
            <button
              type="button"
              @click="currentStep = 2"
              class="inline-flex items-center gap-1.5 px-3.5 py-2 rounded-lg border border-zinc-300 dark:border-zinc-700 bg-white hover:bg-zinc-50 dark:bg-zinc-900 dark:hover:bg-zinc-850 text-xs font-bold text-black dark:text-white transition-colors shadow-2xs cursor-pointer"
            >
              <ArrowLeft class="w-3.5 h-3.5" />
              <span>Orqaga</span>
            </button>

            <button
              type="button"
              @click="openPasswordModal"
              class="inline-flex items-center gap-2 px-6 py-2.5 rounded-lg bg-black hover:bg-zinc-800 text-white dark:bg-white dark:hover:bg-zinc-200 dark:text-black text-xs font-bold shadow-xs transition-all cursor-pointer active:scale-98"
            >
              <ShieldCheck class="w-3.5 h-3.5" />
              <span>Shartnomani tasdiqlash & imzolash</span>
            </button>
          </div>
        </section>
      </div>
    </div>

    <!-- Password Confirmation Modal (Section 13) -->
    <div
      v-if="isPasswordModalOpen"
      class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-xs animate-in fade-in duration-150"
      @click.self="isPasswordModalOpen = false"
    >
      <div class="bg-white dark:bg-zinc-900 rounded-xl shadow-xl w-full max-w-sm border border-zinc-300 dark:border-zinc-800 p-6 space-y-4">
        <div class="text-center">
          <div class="w-10 h-10 rounded-lg bg-zinc-100 dark:bg-zinc-800 border border-zinc-300 dark:border-zinc-700 text-black dark:text-white flex items-center justify-center mx-auto mb-3 font-mono font-bold text-sm">
            <Lock class="w-5 h-5" />
          </div>
          <h3 class="text-sm font-bold text-black dark:text-white tracking-tight">
            Parolni tasdiqlang
          </h3>
          <p class="text-xs text-zinc-700 dark:text-zinc-300 font-medium mt-1">
            Shartnomani rasman imzolash uchun profilingiz parolini kiriting.
          </p>
        </div>

        <div
          v-if="submitError"
          class="p-3 rounded-lg bg-red-50 dark:bg-red-950/40 border border-red-200 dark:border-red-900/60 text-xs text-red-700 dark:text-red-300 flex items-start gap-2"
        >
          <AlertCircle class="w-4 h-4 shrink-0 mt-0.5" />
          <span>{{ submitError }}</span>
        </div>

        <div>
          <label class="block text-xs font-bold uppercase tracking-wide text-black dark:text-white mb-1.5">
            Profil paroli
          </label>
          <div class="relative">
            <Lock class="w-3.5 h-3.5 text-zinc-600 dark:text-zinc-400 absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              v-model="accountPassword"
              :type="showAccountPassword ? 'text' : 'password'"
              required
              placeholder="Parolingizni kiriting"
              class="w-full pl-9 pr-9 py-2 text-xs font-bold rounded-lg border border-zinc-300 dark:border-zinc-700 bg-white dark:bg-zinc-900 text-black dark:text-white focus:outline-hidden focus:border-black dark:focus:border-white transition-colors shadow-2xs"
              @keydown.enter="handleFinalSubmit"
            />
            <button
              type="button"
              @click="showAccountPassword = !showAccountPassword"
              class="absolute right-3 top-1/2 -translate-y-1/2 text-zinc-500 dark:text-zinc-400 hover:text-zinc-700 dark:hover:text-zinc-200 transition-colors cursor-pointer"
              tabindex="-1"
              :title="showAccountPassword ? 'Parolni yashirish' : 'Parolni ko\'rsatish'"
            >
              <EyeOff v-if="showAccountPassword" class="w-3.5 h-3.5" />
              <Eye v-else class="w-3.5 h-3.5" />
            </button>
          </div>
        </div>

        <div class="flex items-center justify-end gap-2 pt-2">
          <button
            type="button"
            @click="isPasswordModalOpen = false"
            class="px-3.5 py-2 rounded-lg border border-zinc-300 dark:border-zinc-700 bg-white hover:bg-zinc-50 dark:bg-zinc-900 dark:hover:bg-zinc-850 text-xs font-bold text-black dark:text-white transition-colors shadow-2xs cursor-pointer"
          >
            Bekor qilish
          </button>

          <button
            type="button"
            @click="handleFinalSubmit"
            :disabled="isSubmitting || !accountPassword"
            class="inline-flex items-center gap-1.5 px-4 py-2 rounded-lg bg-black hover:bg-zinc-800 text-white dark:bg-white dark:hover:bg-zinc-200 dark:text-black text-xs font-bold shadow-xs transition-all cursor-pointer active:scale-98 disabled:opacity-40"
          >
            <Loader2 v-if="isSubmitting" class="w-3.5 h-3.5 animate-spin" />
            <span v-else>Tasdiqlash & Imzolash</span>
          </button>
        </div>
      </div>
    </div>

    <!-- Full Contract Viewer Modal -->
    <FullContractViewerModal
      :is-open="isViewerModalOpen"
      :contract-title="selectedTariff?.name ? `${selectedTariff.name} Shartnomasi` : 'Shartnoma to\'liq matni'"
      :content="effectiveContractText"
      :variable-values="variableValues"
      @confirm-read="handleConfirmReadContract"
      @close="isViewerModalOpen = false"
    />

    <!-- 500px Signature Modal -->
    <OnlineContractSignatureModal
      :is-open="isSignatureModalOpen"
      :model-value="formData.signatureData"
      role="student"
      @confirm="handleSignatureConfirmed"
      @close="isSignatureModalOpen = false"
    />

    <!-- Legal Basis Modal -->
    <LegalBasisModal
      :is-open="isLegalBasisModalOpen"
      @close="isLegalBasisModalOpen = false"
    />

    <!-- Guardian (kafil) Contract Viewer -->
    <FullContractViewerModal
      v-if="tenantInfo?.guardian_contract_text"
      :is-open="isGuardianContractViewerOpen"
      contract-title="Kafillik to'g'risida shartnoma"
      :content="tenantInfo.guardian_contract_text"
      :variable-values="variableValues"
      read-only
      @close="isGuardianContractViewerOpen = false"
    />

    <!-- Guardian (kafil) Signature Modal -->
    <OnlineContractSignatureModal
      :is-open="isGuardianSignatureModalOpen"
      :model-value="guardianSignatureData"
      role="guardian"
      @confirm="handleGuardianSignatureConfirmed"
      @close="isGuardianSignatureModalOpen = false"
    />
  </OnlineContractLayout>
</template>
