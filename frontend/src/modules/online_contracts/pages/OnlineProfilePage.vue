<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  User,
  FileText,
  KeyRound,
  Eye,
  Download,
  AlertCircle,
  CheckCircle2,
  Clock,
  RotateCw,
  Loader2,
  FileSignature,
  Plus,
  ShieldAlert,
  Calendar,
  Trash2,
  XCircle,
  Scale,
} from 'lucide-vue-next'
import {
  onlineContractsApi,
  type StudentProfileResponse,
  type OnlineContractSummary,
  type TenantInfoResponse,
} from '@/api/onlineContracts'
import { downloadContractAsPdf } from '@/modules/contracts/utils/contractPdf'
import { buildVariableValues } from '@/modules/contracts/utils/contractVariables'
import OnlineContractLayout from '../layouts/OnlineContractLayout.vue'
import OnlineContractVerifyModal from '../components/OnlineContractVerifyModal.vue'
import FullContractViewerModal from '../components/FullContractViewerModal.vue'

const route = useRoute()
const router = useRouter()

const tenantSlug = computed(() => (route.params.tenantname as string) || '')

const isLoading = ref(true)
const isRefreshing = ref(false)
const profileData = ref<StudentProfileResponse | null>(null)
const tenantInfo = ref<TenantInfoResponse | null>(null)

// Modals state
const isVerifyModalOpen = ref(false)
const selectedContractForVerify = ref<OnlineContractSummary | null>(null)

const isViewerModalOpen = ref(false)
const viewerContractTitle = ref('')
const viewerContractContent = ref('')
const viewerVariableValues = ref<Record<string, string>>({})

const isCancelModalOpen = ref(false)
const selectedContractForCancel = ref<OnlineContractSummary | null>(null)
const cancelConfirmationInput = ref('')
const cancelReason = ref('')
const isCancelling = ref(false)
const cancelError = ref('')

const expectedContractName = computed(() => {
  return (selectedContractForCancel.value?.tariff_name || selectedContractForCancel.value?.title || '').trim()
})

const isCancelConfirmationMatching = computed(() => {
  if (!expectedContractName.value) return true
  return cancelConfirmationInput.value.trim().toUpperCase() === expectedContractName.value.toUpperCase()
})

function openCancelModal(contract: OnlineContractSummary) {
  selectedContractForCancel.value = contract
  cancelConfirmationInput.value = ''
  cancelReason.value = ''
  cancelError.value = ''
  isCancelModalOpen.value = true
}

async function handleConfirmCancel() {
  if (!selectedContractForCancel.value || !isCancelConfirmationMatching.value) return
  isCancelling.value = true
  cancelError.value = ''
  try {
    await onlineContractsApi.cancelContract(selectedContractForCancel.value.id, cancelReason.value)
    isCancelModalOpen.value = false
    await loadData(false)
  } catch (err: any) {
    console.error('Failed to cancel contract:', err)
    cancelError.value = err?.response?.data?.detail || "Shartnomani bekor qilishda xatolik yuz berdi."
  } finally {
    isCancelling.value = false
  }
}

const isDownloadingPdfId = ref<string | null>(null)
let pollTimer: any = null

async function loadData(silent: boolean = false) {
  if (!silent) {
    if (!profileData.value) {
      isLoading.value = true
    } else {
      isRefreshing.value = true
    }
  }

  try {
    const [prof, tInfo] = await Promise.all([
      onlineContractsApi.getProfile(),
      onlineContractsApi.getTenantInfo(tenantSlug.value),
    ])
    profileData.value = prof
    tenantInfo.value = tInfo
  } catch (err: any) {
    if (err?.response?.status === 401) {
      router.push({ name: 'online-sign-in', params: { tenantname: tenantSlug.value } })
    }
  } finally {
    isLoading.value = false
    isRefreshing.value = false
  }
}

onMounted(() => {
  loadData()

  // Background polling every 10 seconds without flickering
  pollTimer = setInterval(async () => {
    try {
      const prof = await onlineContractsApi.getProfile()
      if (profileData.value) {
        profileData.value.contracts = prof.contracts
        profileData.value.profile = prof.profile
      }
    } catch {
      // silent background refresh
    }
  }, 10000)
})

onBeforeUnmount(() => {
  if (pollTimer) clearInterval(pollTimer)
})

function formatPrice(val: number | string | undefined): string {
  if (!val) return '0 UZS'
  const num = typeof val === 'number' ? val : parseFloat(String(val))
  return num.toLocaleString('uz-UZ') + ' UZS'
}

function formatDate(val: string | undefined | null): string {
  if (!val) return ''
  const s = String(val).trim()
  if (!s) return ''
  if (/^\d{2}\.\d{2}\.\d{4}$/.test(s)) return s
  const isoMatch = s.match(/^(\d{4})[\-\/\.](\d{1,2})[\-\/\.](\d{1,2})/)
  if (isoMatch) {
    const y = isoMatch[1]
    const m = isoMatch[2].padStart(2, '0')
    const d = isoMatch[3].padStart(2, '0')
    return `${d}.${m}.${y}`
  }
  try {
    const d = new Date(val)
    if (isNaN(d.getTime())) return s
    const day = String(d.getDate()).padStart(2, '0')
    const month = String(d.getMonth() + 1).padStart(2, '0')
    const year = d.getFullYear()
    return `${day}.${month}.${year}`
  } catch {
    return s
  }
}

function formatDateTime(val: string | undefined | null): string {
  if (!val) return ''
  try {
    const d = new Date(val)
    if (isNaN(d.getTime())) return val
    const day = String(d.getDate()).padStart(2, '0')
    const month = String(d.getMonth() + 1).padStart(2, '0')
    const year = d.getFullYear()
    const hours = String(d.getHours()).padStart(2, '0')
    const mins = String(d.getMinutes()).padStart(2, '0')
    return `${day}.${month}.${year}, ${hours}:${mins}`
  } catch {
    return val
  }
}

function getContractNumberDisplay(contract: OnlineContractSummary): string {
  if (!contract.contract_number || contract.contract_number === 'Pending Student ID') {
    return '№ Raqam berilmoqda'
  }
  return `№ ${contract.contract_number}`
}

function openVerifyModal(contract: OnlineContractSummary) {
  selectedContractForVerify.value = contract
  isVerifyModalOpen.value = true
}

async function openViewContractModal(contract: OnlineContractSummary) {
  try {
    const detail = await onlineContractsApi.getContractDetail(contract.id)
    viewerContractTitle.value = `${detail.contract_number} — ${detail.title}`
    viewerContractContent.value = detail.content
    viewerVariableValues.value = buildVariableValues(detail, {
      contractNumber: detail.contract_number,
      price: detail.tariff_price,
      discount: detail.discount,
      signatureData: detail.signature_data,
      verificationCode: detail.has_verification_code ? detail.verification_code : undefined,
    })
    isViewerModalOpen.value = true
    await onlineContractsApi.logContractViewAudit(contract.id)
  } catch (err) {
    console.error('Failed to load contract detail:', err)
  }
}

async function handleDownloadPdf(contract: OnlineContractSummary) {
  isDownloadingPdfId.value = contract.id
  try {
    const detail = await onlineContractsApi.getContractDetail(contract.id)
    const title = `SHARTNOMA_${detail.contract_number}_${detail.full_name || 'TALABA'}`
    const variableValues = buildVariableValues(detail, {
      contractNumber: detail.contract_number,
      price: detail.tariff_price,
      discount: detail.discount,
      signatureData: detail.signature_data,
      verificationCode: detail.has_verification_code ? detail.verification_code : undefined,
    })
    const verificationMeta = {
      contractNumber: detail.contract_number,
      studentId: detail.student_id_assigned || undefined,
      studentName: detail.full_name,
      verifiedAt: detail.verified_at ? new Date(detail.verified_at).toLocaleDateString('uz-UZ') : undefined,
      status: detail.status,
    }
    await downloadContractAsPdf(
      title,
      detail.content,
      { top: 15, right: 15, bottom: 15, left: 15 },
      variableValues,
      detail.signature_data,
      verificationMeta
    )
  } catch (err) {
    console.error('Failed to download PDF:', err)
  } finally {
    isDownloadingPdfId.value = null
  }
}

function handleResubmit(contract: OnlineContractSummary) {
  router.push({
    name: 'online-contract-sign',
    params: { tenantname: tenantSlug.value },
    query: { resubmitContractId: contract.id }
  })
}
</script>

<template>
  <OnlineContractLayout :tenant-info="tenantInfo" :is-loading="isLoading">
    <!-- Initial Loading State -->
    <div v-if="isLoading" class="py-24 flex flex-col items-center justify-center text-zinc-400">
      <Loader2 class="w-6 h-6 animate-spin text-zinc-900 dark:text-white mb-2" />
      <span class="text-xs font-mono">Profil ma'lumotlari yuklanmoqda...</span>
    </div>

    <div v-else class="space-y-8">
      <!-- 1. MY PROFILE SECTION (Resend Minimalist Design) -->
      <section class="bg-white dark:bg-zinc-900/60 border border-zinc-200/80 dark:border-zinc-800 rounded-xl p-6 sm:p-8 shadow-xs">
        <div class="flex items-center justify-between mb-6 pb-5 border-b border-zinc-100 dark:border-zinc-850">
          <div class="flex items-center gap-3">
            <div class="w-10 h-10 rounded-lg bg-zinc-100 dark:bg-zinc-800 border border-zinc-200/60 dark:border-zinc-700 text-zinc-800 dark:text-zinc-200 flex items-center justify-center font-mono font-bold text-sm">
              <User class="w-5 h-5" />
            </div>
            <div>
              <h2 class="text-base font-semibold tracking-tight text-zinc-900 dark:text-zinc-100">
                Shaxsiy profil
              </h2>
              <p class="text-xs text-zinc-500 dark:text-zinc-400">
                Onlayn shartnomalarda ko'rsatiladigan rasmiy ma'lumotlaringiz
              </p>
            </div>
          </div>
        </div>

        <div class="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4">
          <div class="p-3.5 bg-zinc-50/70 dark:bg-zinc-850/50 rounded-lg border border-zinc-300 dark:border-zinc-800">
            <span class="text-xs font-bold uppercase tracking-wide text-black dark:text-white block mb-1">To'liq ism-sharif (F.I.O)</span>
            <span class="text-xs font-bold text-zinc-900 dark:text-zinc-100">
              {{ (profileData?.user.full_name || "Ko'rsatilmagan").toUpperCase() }}
            </span>
          </div>

          <div class="p-3.5 bg-zinc-50/70 dark:bg-zinc-850/50 rounded-lg border border-zinc-300 dark:border-zinc-800">
            <span class="text-xs font-bold uppercase tracking-wide text-black dark:text-white block mb-1">Email manzili</span>
            <span class="text-xs font-bold text-zinc-900 dark:text-zinc-100">
              {{ profileData?.user.email || "—" }}
            </span>
          </div>

          <div class="p-3.5 bg-zinc-50/70 dark:bg-zinc-850/50 rounded-lg border border-zinc-300 dark:border-zinc-800">
            <span class="text-xs font-bold uppercase tracking-wide text-black dark:text-white block mb-1">Pasport raqami</span>
            <span class="text-xs font-mono font-bold text-zinc-900 dark:text-zinc-100">
              {{ profileData?.profile.passport_number || "Hali kiritilmagan" }}
            </span>
          </div>

          <div class="p-3.5 bg-zinc-50/70 dark:bg-zinc-850/50 rounded-lg border border-zinc-300 dark:border-zinc-800">
            <span class="text-xs font-bold uppercase tracking-wide text-black dark:text-white block mb-1">Telefon raqami</span>
            <span class="text-xs font-mono font-bold text-zinc-900 dark:text-zinc-100">
              {{ profileData?.profile.phone1 || "Kiritilmagan" }}
            </span>
          </div>

          <div class="p-3.5 bg-zinc-50/70 dark:bg-zinc-850/50 rounded-lg border border-zinc-300 dark:border-zinc-800">
            <span class="text-xs font-bold uppercase tracking-wide text-black dark:text-white block mb-1">Tug'ilgan sana</span>
            <span class="text-xs font-bold text-zinc-900 dark:text-zinc-100">
              {{ formatDate(profileData?.profile.date_of_birth) || "—" }}
            </span>
          </div>

          <div class="p-3.5 bg-zinc-50/70 dark:bg-zinc-850/50 rounded-lg border border-zinc-300 dark:border-zinc-800">
            <span class="text-xs font-bold uppercase tracking-wide text-black dark:text-white block mb-1">Qabul ofisi</span>
            <span class="text-xs font-bold text-zinc-900 dark:text-zinc-100">
              {{ profileData?.profile.office || "Belgilanmagan" }}
            </span>
          </div>
        </div>
      </section>

      <!-- 2. MY CONTRACTS SECTION -->
      <section class="space-y-4">
        <div class="flex items-center justify-between gap-4">
          <div>
            <h2 class="text-base font-semibold tracking-tight text-zinc-900 dark:text-zinc-100 flex items-center gap-2">
              <span>Mening shartnomalarim</span>
              <span class="text-xs font-mono text-zinc-500 bg-zinc-100 dark:bg-zinc-850 px-2 py-0.5 rounded-md border border-zinc-200/60 dark:border-zinc-800">
                {{ profileData?.contracts?.length || 0 }} ta
              </span>
            </h2>
            <p class="text-xs text-zinc-500 dark:text-zinc-400 mt-0.5">
              Imzolangan va tasdiqlanishi kutilayotgan barcha shartnomalaringiz ro'yxati
            </p>
          </div>

          <div class="flex items-center gap-2">
            <button
              type="button"
              @click="loadData(false)"
              class="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-zinc-200 dark:border-zinc-800 bg-white hover:bg-zinc-50 dark:bg-zinc-900 dark:hover:bg-zinc-850 text-zinc-600 dark:text-zinc-400 hover:text-zinc-900 dark:hover:text-white text-xs font-medium transition-colors cursor-pointer shadow-2xs"
              title="Ro'yxatni yangilash"
            >
              <RotateCw class="w-3.5 h-3.5" :class="{ 'animate-spin': isRefreshing }" />
              <span class="hidden sm:inline">Yangilash</span>
            </button>

            <!-- New contract button -->
            <router-link
              :to="{ name: 'online-contract-sign', params: { tenantname: tenantSlug } }"
              class="inline-flex items-center gap-1 px-3 py-1.5 rounded-lg bg-zinc-900 hover:bg-zinc-800 text-white dark:bg-zinc-100 dark:hover:bg-white dark:text-zinc-950 text-xs font-medium transition-all shadow-xs active:scale-98"
            >
              <Plus class="w-3.5 h-3.5" />
              <span>Yangi shartnoma</span>
            </router-link>
          </div>
        </div>

        <!-- Contracts List -->
        <div v-if="profileData?.contracts?.length" class="space-y-4">
          <div
            v-for="contract in profileData.contracts"
            :key="contract.id"
            class="bg-white dark:bg-zinc-900 border border-zinc-300 dark:border-zinc-800 rounded-2xl p-5 sm:p-6 shadow-xs hover:shadow-md transition-all space-y-4"
          >
            <!-- Card Header: Status, Number, Date -->
            <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3.5 border-b border-zinc-200 dark:border-zinc-800">
              <div class="flex items-center gap-2.5 flex-wrap">
                <!-- Status Badge -->
                <span
                  v-if="contract.status === 'verified'"
                  class="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-emerald-100 text-emerald-900 dark:bg-emerald-950/60 dark:text-emerald-300 border border-emerald-500/30"
                >
                  <CheckCircle2 class="w-3.5 h-3.5 text-emerald-600 dark:text-emerald-400" />
                  <span>Rasman tasdiqlangan</span>
                </span>
                <span
                  v-else-if="contract.status === 'pending'"
                  class="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-amber-100 text-amber-900 dark:bg-amber-950/60 dark:text-amber-300 border border-amber-500/30"
                >
                  <Clock class="w-3.5 h-3.5 text-amber-600 dark:text-amber-400 animate-pulse" />
                  <span>Agentlik ko'rib chiqmoqda</span>
                </span>
                <span
                  v-else-if="contract.status === 'rejected'"
                  class="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-red-100 text-red-900 dark:bg-red-950/60 dark:text-red-300 border border-red-500/30"
                >
                  <AlertCircle class="w-3.5 h-3.5 text-red-600 dark:text-red-400" />
                  <span>Rad etilgan</span>
                </span>
                <span
                  v-else-if="contract.status === 'cancelled'"
                  class="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-violet-100 text-violet-900 dark:bg-violet-950/60 dark:text-violet-300 border border-violet-500/30"
                >
                  <XCircle class="w-3.5 h-3.5 text-violet-600 dark:text-violet-400" />
                  <span>Bekor qilingan</span>
                </span>
                <span
                  v-else
                  class="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-zinc-100 text-zinc-800 dark:bg-zinc-800 dark:text-zinc-200 border border-zinc-300 dark:border-zinc-700"
                >
                  <span>{{ contract.status }}</span>
                </span>

                <!-- Contract Number Badge -->
                <span class="text-xs font-mono font-bold text-black dark:text-white px-2.5 py-1 rounded-md bg-zinc-100 dark:bg-zinc-800 border border-zinc-200 dark:border-zinc-700">
                  {{ getContractNumberDisplay(contract) }}
                </span>
              </div>

              <!-- Signed / Created Date -->
              <div v-if="contract.signed_at || contract.created_at" class="text-xs font-medium text-zinc-600 dark:text-zinc-400 flex items-center gap-1.5">
                <Calendar class="w-3.5 h-3.5 text-zinc-500" />
                <span>Imzolangan: <strong class="text-black dark:text-white font-mono">{{ formatDateTime(contract.signed_at || contract.created_at) }}</strong></span>
              </div>
            </div>

            <!-- Card Body: Title & Grid info tiles -->
            <div class="space-y-3">
              <div>
                <h3 class="text-base sm:text-lg font-bold text-black dark:text-white tracking-tight">
                  {{ contract.tariff_name || contract.title }}
                </h3>
                <p class="text-xs text-zinc-600 dark:text-zinc-400 mt-0.5 font-medium">
                  Ta'lim konsalting xizmati ko'rsatish bo'yicha elektron shartnoma
                </p>
              </div>

              <!-- Details Tiles Grid -->
              <div class="grid grid-cols-1 sm:grid-cols-3 gap-3 pt-1">
                <!-- Tile 1: Price -->
                <div class="p-3.5 rounded-xl bg-zinc-50 dark:bg-zinc-850/60 border border-zinc-200 dark:border-zinc-800">
                  <span class="text-[11px] font-bold uppercase tracking-wider text-zinc-500 dark:text-zinc-400 block mb-1">
                    Xizmat to'lovi
                  </span>
                  <span class="text-sm font-bold font-mono text-black dark:text-white">
                    {{ formatPrice(contract.tariff_price) }}
                  </span>
                </div>

                <!-- Tile 2: Electronic Signature -->
                <div class="p-3.5 rounded-xl bg-zinc-50 dark:bg-zinc-850/60 border border-zinc-200 dark:border-zinc-800">
                  <span class="text-[11px] font-bold uppercase tracking-wider text-zinc-500 dark:text-zinc-400 block mb-1">
                    Mijoz imzosi
                  </span>
                  <div class="flex items-center gap-1.5 text-xs font-bold text-emerald-700 dark:text-emerald-400">
                    <CheckCircle2 class="w-3.5 h-3.5" />
                    <span>Elektron imzolangan</span>
                  </div>
                </div>

                <!-- Tile 3: Student ID / Verification -->
                <div class="p-3.5 rounded-xl bg-zinc-50 dark:bg-zinc-850/60 border border-zinc-200 dark:border-zinc-800">
                  <span class="text-[11px] font-bold uppercase tracking-wider text-zinc-500 dark:text-zinc-400 block mb-1">
                    Talaba ID
                  </span>
                  <span v-if="contract.student_id_assigned" class="text-sm font-bold font-mono text-blue-600 dark:text-blue-400">
                    {{ contract.student_id_assigned }}
                  </span>
                  <span v-else class="text-xs font-medium text-zinc-500">
                    Tasdiqlangach beriladi
                  </span>
                </div>
              </div>
            </div>

            <!-- Legal Basis Notice: electronic signature equivalence -->
            <div class="p-3.5 rounded-xl bg-zinc-50 dark:bg-zinc-850/60 border border-zinc-200 dark:border-zinc-800 flex items-start gap-2.5">
              <Scale class="w-4 h-4 text-zinc-500 dark:text-zinc-400 shrink-0 mt-0.5" />
              <p class="text-[11.5px] text-zinc-600 dark:text-zinc-400 leading-relaxed font-medium">
                Tomonlar shartnoma va uning ilovalari Korxonaning axborot tizimi orqali elektron shaklda tuzilishi va Mijozning grafik (qo'lda chizilgan) imzosi, elektron pochta orqali tasdiqlash kodi hamda tizim tomonidan qayd etilgan sana, IP-manzil va qurilma ma'lumotlari birgalikda qo'lyozma imzoga tenglashtirilishini tan oladilar. Elektron nusxa qog'oz nusxa bilan bir xil yuridik kuchga ega.
              </p>
            </div>

            <!-- Contextual Status Notice / Banner -->
            <!-- Pending without code banner -->
            <div
              v-if="contract.status === 'pending' && !contract.has_verification_code"
              class="p-3.5 rounded-xl bg-amber-50/80 dark:bg-amber-950/30 border border-amber-500/20 text-xs text-amber-950 dark:text-amber-200 flex items-start gap-3"
            >
              <Clock class="w-4 h-4 text-amber-600 dark:text-amber-400 shrink-0 mt-0.5" />
              <div>
                <strong class="font-bold text-amber-900 dark:text-amber-100">Kutilmoqda: Agentlik tekshiruvida</strong>
                <p class="text-amber-800/90 dark:text-amber-300/90 text-xs mt-0.5 leading-relaxed font-medium">
                  Shartnomangiz agentlikka muvaffaqiyatli yuborildi. Mas'ul xodimlar ma'lumotlaringizni tekshirib tasdiqlagach, ushbu sahifada tasdiqlash kodi paydo bo'ladi.
                </p>
              </div>
            </div>

            <!-- Pending WITH code banner -->
            <div
              v-if="contract.status === 'pending' && contract.has_verification_code"
              class="p-4 rounded-xl bg-blue-50 dark:bg-blue-950/40 border border-blue-500/30 text-xs text-blue-950 dark:text-blue-200 flex flex-col sm:flex-row sm:items-center justify-between gap-3 shadow-2xs"
            >
              <div class="flex items-start gap-2.5">
                <KeyRound class="w-4 h-4 text-blue-600 dark:text-blue-400 shrink-0 mt-0.5" />
                <div>
                  <strong class="font-bold text-blue-900 dark:text-blue-100">Tasdiqlash kodi tayyor!</strong>
                  <p class="text-blue-800/90 dark:text-blue-300/90 text-xs mt-0.5 leading-relaxed font-medium">
                    Agentlik shartnomangizni tasdiqlash uchun kod biriktirdi. Shartnomani rasman kuchga kiritish uchun tasdiqlash kodini kiriting.
                  </p>
                </div>
              </div>
              <button
                type="button"
                @click="openVerifyModal(contract)"
                class="inline-flex items-center justify-center gap-1.5 px-4 py-2 rounded-lg bg-blue-600 hover:bg-blue-700 text-white font-bold text-xs shadow-xs transition-all cursor-pointer shrink-0"
              >
                <KeyRound class="w-3.5 h-3.5" />
                <span>Kodni kiritish</span>
              </button>
            </div>

            <!-- Verified Banner -->
            <div
              v-if="contract.status === 'verified'"
              class="p-3 rounded-xl bg-emerald-50 dark:bg-emerald-950/30 border border-emerald-500/20 text-xs text-emerald-900 dark:text-emerald-200 flex items-center gap-2.5"
            >
              <CheckCircle2 class="w-4 h-4 text-emerald-600 dark:text-emerald-400 shrink-0" />
              <p class="text-xs font-semibold leading-relaxed">
                Shartnoma ikki tomonlama to'liq tasdiqlangan va rasmiy kuchga ega. PDF nusxasini yuklab olishingiz mumkin.
              </p>
            </div>

            <!-- Rejection Notice Banner -->
            <div
              v-if="contract.status === 'rejected'"
              class="p-3.5 rounded-xl bg-red-50 dark:bg-red-950/40 border border-red-300 dark:border-red-900/60 text-xs text-red-800 dark:text-red-200 space-y-1.5"
            >
              <div class="font-bold flex items-center gap-1.5 text-red-700 dark:text-red-400">
                <AlertCircle class="w-4 h-4 shrink-0" />
                <span>Agentlik tomonidan rad etilgan:</span>
              </div>
              <p class="text-xs text-red-600 dark:text-red-300 pl-5.5 font-medium">
                "{{ contract.rejection_reason || 'Sabab ko\'rsatilmadi' }}"
              </p>
            </div>

            <!-- Cancelled Banner -->
            <div
              v-if="contract.status === 'cancelled'"
              class="p-3.5 rounded-xl bg-violet-50/80 dark:bg-violet-950/30 border border-violet-500/20 text-xs text-violet-900 dark:text-violet-200 space-y-1"
            >
              <div class="font-bold flex items-center gap-1.5 text-violet-900 dark:text-violet-100">
                <XCircle class="w-4 h-4 text-violet-600 dark:text-violet-400" />
                <span>Ushbu shartnoma bekor qilingan</span>
              </div>
              <p class="text-xs text-violet-800/90 dark:text-violet-300/90 pl-5.5 font-medium">
                {{ contract.rejection_reason || "Shartnoma siz tomoningizdan bekor qilindi. Agar yangi shartnoma tuzmoqchi bo'lsangiz, yangi ariza topshirishingiz mumkin." }}
              </p>
            </div>

            <!-- Card Footer: Action Buttons -->
            <div class="pt-3 border-t border-zinc-200 dark:border-zinc-800 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
              <div class="text-[11.5px] text-zinc-500 font-medium">
                <span v-if="contract.status === 'verified'" class="text-emerald-700 dark:text-emerald-400 font-bold">
                  ✓ To'liq rasmiylashtirilgan
                </span>
                <span v-else-if="contract.status === 'pending'" class="text-zinc-600 dark:text-zinc-400">
                  Agentlik tasdiqlashini kuting
                </span>
              </div>

              <div class="flex items-center gap-2 flex-wrap">
                <!-- View Contract Preview -->
                <button
                  type="button"
                  @click="openViewContractModal(contract)"
                  class="inline-flex items-center gap-1.5 px-3.5 py-2 rounded-lg border border-zinc-300 dark:border-zinc-700 bg-white hover:bg-zinc-50 dark:bg-zinc-800 dark:hover:bg-zinc-750 text-xs font-bold text-black dark:text-white transition-colors cursor-pointer shadow-2xs"
                >
                  <Eye class="w-3.5 h-3.5 text-zinc-600 dark:text-zinc-400" />
                  <span>Ko'rish</span>
                </button>

                <!-- Verification Code Input button (if pending and has code) -->
                <button
                  v-if="contract.status === 'pending' && contract.has_verification_code"
                  type="button"
                  @click="openVerifyModal(contract)"
                  class="inline-flex items-center gap-1.5 px-4 py-2 rounded-lg bg-black hover:bg-zinc-800 text-white dark:bg-white dark:hover:bg-zinc-200 dark:text-black text-xs font-bold transition-all cursor-pointer shadow-xs active:scale-98"
                >
                  <KeyRound class="w-3.5 h-3.5" />
                  <span>Tasdiqlash kodi</span>
                </button>

                <!-- Resubmit if rejected -->
                <button
                  v-if="contract.status === 'rejected'"
                  type="button"
                  @click="handleResubmit(contract)"
                  class="inline-flex items-center gap-1.5 px-4 py-2 rounded-lg bg-red-600 hover:bg-red-700 text-white text-xs font-bold shadow-xs transition-all cursor-pointer"
                >
                  <span>Qayta yuborish</span>
                </button>

                <!-- If Cancelled: New Contract Link -->
                <router-link
                  v-if="contract.status === 'cancelled'"
                  :to="{ name: 'online-contract-sign', params: { tenantname: tenantSlug } }"
                  class="inline-flex items-center gap-1.5 px-3.5 py-2 rounded-lg bg-black hover:bg-zinc-800 text-white dark:bg-white dark:hover:bg-zinc-200 dark:text-black text-xs font-bold shadow-xs transition-all cursor-pointer"
                >
                  <Plus class="w-3.5 h-3.5" />
                  <span>Yangi shartnoma tuzish</span>
                </router-link>

                <!-- Cancel Contract Button -->
                <button
                  v-if="contract.status === 'pending' || contract.status === 'verified'"
                  type="button"
                  @click="openCancelModal(contract)"
                  class="flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-red-200 dark:border-red-900/50 text-red-600 dark:text-red-400 text-xs font-semibold hover:bg-red-50 dark:hover:bg-red-950/40 transition-colors shadow-2xs"
                >
                  <Trash2 class="w-3.5 h-3.5" />
                  <span>Bekor qilish</span>
                </button>

                <!-- PDF Download Button -->
                <button
                  type="button"
                  @click="handleDownloadPdf(contract)"
                  :disabled="isDownloadingPdfId === contract.id"
                  class="inline-flex items-center gap-1.5 px-3.5 py-2 rounded-lg border border-zinc-300 dark:border-zinc-700 bg-white hover:bg-zinc-50 dark:bg-zinc-800 dark:hover:bg-zinc-750 text-xs font-bold text-black dark:text-white transition-colors cursor-pointer shadow-2xs disabled:opacity-50"
                  title="Shartnomani PDF formatida yuklab olish"
                >
                  <Loader2 v-if="isDownloadingPdfId === contract.id" class="w-3.5 h-3.5 animate-spin text-zinc-500" />
                  <Download v-else class="w-3.5 h-3.5 text-zinc-700 dark:text-zinc-300" />
                  <span>PDF</span>
                </button>
              </div>
            </div>
          </div>
        </div>

        <!-- Empty State (No contracts yet) -->
        <div
          v-else
          class="bg-white dark:bg-zinc-900/60 border border-zinc-200/80 dark:border-zinc-800 rounded-xl p-10 sm:p-14 text-center shadow-xs"
        >
          <div class="w-12 h-12 rounded-xl bg-zinc-100 dark:bg-zinc-800 border border-zinc-200/60 dark:border-zinc-700 text-zinc-400 flex items-center justify-center mx-auto mb-3">
            <FileText class="w-6 h-6" />
          </div>
          <h4 class="text-sm font-semibold text-zinc-900 dark:text-zinc-100 mb-1">
            Sizda hozircha imzolangan shartnomalar mavjud emas
          </h4>
          <p class="text-xs text-zinc-500 dark:text-zinc-400 max-w-sm mx-auto mb-5 leading-relaxed">
            Mavjud konsalting tariflaridan birini tanlang va birinchi onlayn shartnomangizni rasmiylashtiring.
          </p>
          <div class="flex flex-col sm:flex-row items-center justify-center gap-3">
            <router-link
              :to="{ name: 'online-contract-sign', params: { tenantname: tenantSlug } }"
              class="inline-flex items-center gap-2 px-4 py-2.5 rounded-lg bg-zinc-900 hover:bg-zinc-800 text-white dark:bg-zinc-100 dark:hover:bg-white dark:text-zinc-950 text-xs font-medium shadow-xs transition-all active:scale-98"
            >
              <FileSignature class="w-3.5 h-3.5" />
              <span>Shartnoma tuzish</span>
            </router-link>

            <router-link
              :to="{ name: 'online-landing', params: { tenantname: tenantSlug }, hash: '#tariffs-section' }"
              class="inline-flex items-center gap-1.5 px-4 py-2.5 rounded-lg border border-zinc-200 dark:border-zinc-800 bg-white hover:bg-zinc-50 dark:bg-zinc-900 dark:hover:bg-zinc-850 text-xs font-medium text-zinc-700 dark:text-zinc-300 transition-colors shadow-2xs"
            >
              <span>Tariflarni ko'rish</span>
            </router-link>
          </div>
        </div>
      </section>
    </div>

    <!-- Student Verification Dialog -->
    <OnlineContractVerifyModal
      :is-open="isVerifyModalOpen"
      :contract="selectedContractForVerify"
      @close="isVerifyModalOpen = false"
      @verified="() => loadData()"
    />

    <!-- Full Contract Viewer Modal -->
    <FullContractViewerModal
      :is-open="isViewerModalOpen"
      :contract-title="viewerContractTitle"
      :content="viewerContractContent"
      :variable-values="viewerVariableValues"
      @close="isViewerModalOpen = false"
    />

    <!-- Cancel Contract Confirmation Modal -->
    <Teleport to="body">
      <div
        v-if="isCancelModalOpen"
        class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-xs"
        @click.self="isCancelModalOpen = false"
      >
        <div class="relative w-full max-w-md bg-white dark:bg-zinc-900 border border-zinc-300 dark:border-zinc-800 rounded-2xl shadow-2xl p-6 space-y-4 animate-in fade-in zoom-in-95 duration-200">
          <div class="flex items-start gap-3">
            <div class="w-10 h-10 rounded-xl bg-red-50 dark:bg-red-950/60 border border-red-500/20 text-red-600 dark:text-red-400 flex items-center justify-center shrink-0">
              <Trash2 class="w-5 h-5" />
            </div>
            <div>
              <h3 class="text-base font-bold text-black dark:text-white tracking-tight">
                Shartnomani bekor qilish
              </h3>
              <p class="text-xs text-zinc-600 dark:text-zinc-400 mt-1 leading-relaxed font-medium">
                Haqiqatan ham <strong>{{ selectedContractForCancel?.tariff_name || 'ushbu shartnoma' }}</strong> arizasini bekor qilmoqchimisiz?
                Bekor qilingach, xohlasangiz yangi ma'lumotlar bilan qaytadan shartnoma tuzishingiz mumkin.
              </p>
            </div>
          </div>

          <!-- Mandatory Contract Name Confirmation Input -->
          <div class="p-3.5 rounded-xl bg-zinc-50 dark:bg-zinc-850/80 border border-zinc-200 dark:border-zinc-800 space-y-2">
            <label class="block text-xs font-bold text-black dark:text-white leading-relaxed">
              Bekor qilishni tasdiqlash uchun quyidagi maydonga shartnoma nomini kiriting:
            </label>
            <div class="flex items-center gap-2">
              <span class="text-xs text-zinc-900 dark:text-zinc-100 font-mono font-bold select-all bg-white dark:bg-zinc-900 px-2.5 py-1 rounded-md border border-zinc-300 dark:border-zinc-700 shadow-2xs">
                {{ expectedContractName }}
              </span>
              <span class="text-[11px] text-zinc-500 font-medium">nomini aynan yozing</span>
            </div>

            <input
              v-model="cancelConfirmationInput"
              type="text"
              :placeholder="expectedContractName ? `«${expectedContractName}» deb yozing` : 'Shartnoma nomi'"
              class="w-full px-3 py-2 text-xs font-bold rounded-lg border bg-white dark:bg-zinc-900 text-black dark:text-white placeholder:text-zinc-400 focus:outline-hidden transition-colors shadow-2xs"
              :class="isCancelConfirmationMatching && cancelConfirmationInput.trim() ? 'border-emerald-500 ring-1 ring-emerald-500/30' : 'border-zinc-300 dark:border-zinc-700 focus:border-red-500 focus:ring-1 focus:ring-red-500/30'"
              @keydown.enter="isCancelConfirmationMatching ? handleConfirmCancel() : null"
            />

            <p v-if="cancelConfirmationInput && !isCancelConfirmationMatching" class="text-[11px] text-red-600 dark:text-red-400 font-medium">
              Kiritilgan nom shartnoma nomi bilan bir xil bo'lishi kerak.
            </p>
            <p v-else-if="isCancelConfirmationMatching && cancelConfirmationInput.trim()" class="text-[11px] text-emerald-600 dark:text-emerald-400 font-bold flex items-center gap-1">
              ✓ Nom to'g'ri kiritildi
            </p>
          </div>

          <!-- Optional Reason Textarea -->
          <div>
            <label class="block text-xs font-bold text-zinc-700 dark:text-zinc-300 mb-1.5">
              Bekor qilish sababi (ixtiyoriy)
            </label>
            <textarea
              v-model="cancelReason"
              rows="2"
              placeholder="Masalan: Ma'lumotlarni xato kiritdim yoki boshqa tarif tanlamoqchiman"
              class="w-full px-3 py-2 text-xs font-medium rounded-lg border border-zinc-300 dark:border-zinc-700 bg-white dark:bg-zinc-900 text-black dark:text-white placeholder:text-zinc-400 focus:outline-hidden focus:border-zinc-500 transition-colors resize-none"
            ></textarea>
          </div>

          <div v-if="cancelError" class="p-2.5 rounded-lg bg-red-50 text-red-700 border border-red-200 text-xs font-semibold">
            {{ cancelError }}
          </div>

          <!-- Actions -->
          <div class="pt-2 flex items-center justify-end gap-2 border-t border-zinc-200 dark:border-zinc-800">
            <button
              type="button"
              @click="isCancelModalOpen = false"
              :disabled="isCancelling"
              class="px-4 py-2 text-xs font-bold text-zinc-700 dark:text-zinc-300 hover:text-black dark:hover:text-white rounded-lg hover:bg-zinc-100 dark:hover:bg-zinc-800 transition-colors cursor-pointer"
            >
              Yo'q, qolsin
            </button>

            <button
              type="button"
              @click="handleConfirmCancel"
              :disabled="!isCancelConfirmationMatching || !cancelConfirmationInput.trim() || isCancelling"
              class="inline-flex items-center gap-1.5 px-4 py-2 rounded-lg bg-red-600 hover:bg-red-700 text-white font-bold text-xs shadow-xs transition-all cursor-pointer disabled:opacity-40 disabled:cursor-not-allowed"
            >
              <Loader2 v-if="isCancelling" class="w-3.5 h-3.5 animate-spin" />
              <span>Ha, bekor qilish</span>
            </button>
          </div>
        </div>
      </div>
    </Teleport>
  </OnlineContractLayout>
</template>
