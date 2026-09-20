<script setup lang="ts">
import { ref, computed } from 'vue'
import {
  KeyRound,
  Lock,
  CheckCircle2,
  AlertCircle,
  Clock,
  Loader2,
  Download,
  Eye,
  EyeOff,
} from 'lucide-vue-next'
import { onlineContractsApi, type OnlineContractSummary } from '@/api/onlineContracts'
import { downloadContractAsPdf } from '@/modules/contracts/utils/contractPdf'
import { buildVariableValues } from '@/modules/contracts/utils/contractVariables'
import BaseModal from '@/components/common/BaseModal.vue'

const props = defineProps<{
  isOpen: boolean
  contract: OnlineContractSummary | null
}>()

const emit = defineEmits<{
  close: []
  verified: [contractId: string]
}>()

const verificationCode = ref('')
const password = ref('')
const showPassword = ref(false)
const isSubmitting = ref(false)
const errorMessage = ref('')
const isVerifiedSuccess = ref(false)
const verifiedContractData = ref<any>(null)
const isDownloadingPdf = ref(false)

const canSubmit = computed(() => {
  return verificationCode.value.trim().length >= 6 && password.value.length > 0
})

const modalSubtitle = computed(() => {
  return props.contract ? `Shartnoma raqami: ${props.contract.contract_number}` : ''
})

// Normalize input automatically
function handleCodeInput(e: Event) {
  const target = e.target as HTMLInputElement
  verificationCode.value = target.value.toUpperCase().trim()
}

async function handleVerify() {
  if (!props.contract || !canSubmit.value) return
  isSubmitting.value = true
  errorMessage.value = ''

  try {
    const res = await onlineContractsApi.verifyContract(props.contract.id, {
      code: verificationCode.value.trim().toUpperCase(),
      password: password.value,
    })
    isVerifiedSuccess.value = true
    verifiedContractData.value = res
    emit('verified', props.contract.id)
  } catch (err: any) {
    errorMessage.value = err?.response?.data?.detail || "Tasdiqlashda xatolik yuz berdi. Kod yoki parolni tekshiring."
  } finally {
    isSubmitting.value = false
  }
}

async function handleDownloadPdf() {
  if (!props.contract) return
  isDownloadingPdf.value = true
  try {
    const detail = await onlineContractsApi.getContractDetail(props.contract.id)
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
      verificationMeta,
      detail.is_minor && detail.guardian_contract_text
        ? { content: detail.guardian_contract_text, variableValues }
        : undefined
    )
  } catch (err) {
    console.error('Failed to download PDF:', err)
  } finally {
    isDownloadingPdf.value = false
  }
}

function handleClose() {
  isVerifiedSuccess.value = false
  verificationCode.value = ''
  password.value = ''
  showPassword.value = false
  errorMessage.value = ''
  emit('close')
}
</script>

<template>
  <BaseModal
    :is-open="isOpen"
    title="Shartnomani Yakuniy Tasdiqlash"
    :subtitle="modalSubtitle"
    max-width="max-w-lg"
    @close="handleClose"
  >
    <!-- Success State -->
    <div v-if="isVerifiedSuccess" class="text-center">
      <div class="w-14 h-14 rounded-2xl bg-emerald-50 dark:bg-emerald-950/60 text-emerald-600 dark:text-emerald-400 flex items-center justify-center mx-auto mb-4 border border-emerald-500/20">
        <CheckCircle2 class="w-7 h-7" />
      </div>

      <h4 class="text-base font-bold text-zinc-900 dark:text-white mb-1.5">
        Shartnoma Muvaffaqiyatli Tasdiqlandi!
      </h4>

      <p class="text-xs text-zinc-500 dark:text-zinc-400 leading-relaxed max-w-sm mx-auto mb-5">
        Shartnoma qonuniy kuchga kirdi va o'zgarmas holatda saqlandi. Rasmiy PDF nusxasini istalgan vaqtda yuklab olishingiz mumkin.
      </p>

      <div class="bg-zinc-50/70 dark:bg-zinc-850/50 p-4 rounded-xl border border-zinc-200 dark:border-zinc-800 text-xs space-y-1.5 mb-5 text-left max-w-sm mx-auto">
        <div class="flex justify-between">
          <span class="text-zinc-500">Shartnoma Raqami:</span>
          <strong class="text-zinc-900 dark:text-white font-mono">{{ verifiedContractData?.contract_number || contract?.contract_number }}</strong>
        </div>
        <div class="flex justify-between">
          <span class="text-zinc-500">Talaba ID (Student ID):</span>
          <strong class="text-zinc-900 dark:text-white font-mono">{{ verifiedContractData?.student_id || contract?.student_id_assigned }}</strong>
        </div>
        <div class="flex justify-between">
          <span class="text-zinc-500">Holati:</span>
          <span class="font-bold text-emerald-600 dark:text-emerald-400 uppercase">VERIFIED</span>
        </div>
      </div>

      <div class="flex items-center justify-center gap-2.5">
        <button
          type="button"
          @click="handleClose"
          class="px-4 py-2.5 rounded-lg border border-zinc-200 dark:border-zinc-700 bg-white hover:bg-zinc-50 dark:bg-zinc-900 dark:hover:bg-zinc-850 text-xs font-semibold text-zinc-700 dark:text-zinc-300 transition-colors cursor-pointer"
        >
          Yopish
        </button>

        <button
          type="button"
          @click="handleDownloadPdf"
          :disabled="isDownloadingPdf"
          class="inline-flex items-center gap-2 px-5 py-2.5 rounded-lg bg-zinc-900 hover:bg-zinc-800 text-white dark:bg-zinc-100 dark:hover:bg-white dark:text-zinc-950 text-xs font-medium shadow-xs transition-all cursor-pointer active:scale-98 disabled:opacity-50"
        >
          <Loader2 v-if="isDownloadingPdf" class="w-3.5 h-3.5 animate-spin" />
          <Download v-else class="w-3.5 h-3.5" />
          <span>Rasmiy PDF yuklab olish</span>
        </button>
      </div>
    </div>

    <!-- Verification Form -->
    <form v-else @submit.prevent="handleVerify" class="space-y-4">
      <div class="text-xs text-zinc-600 dark:text-zinc-400 leading-relaxed bg-zinc-50/70 dark:bg-zinc-850/50 border border-zinc-200 dark:border-zinc-800 p-3.5 rounded-lg">
        Kompaniya bergan bir martalik <strong class="text-zinc-900 dark:text-zinc-100">Tasdiqlash Kodi</strong>ni va profil parolingizni kiriting.
      </div>

      <!-- Error display -->
      <div
        v-if="errorMessage"
        class="p-3 rounded-lg bg-red-50 dark:bg-red-950/40 border border-red-200 dark:border-red-900/60 text-xs text-red-700 dark:text-red-300 flex items-start gap-2"
      >
        <AlertCircle class="w-4 h-4 shrink-0 mt-0.5" />
        <span>{{ errorMessage }}</span>
      </div>

      <!-- Verification Code Input -->
      <div>
        <label class="block text-xs font-medium text-zinc-700 dark:text-zinc-300 mb-1.5">
          Tasdiqlash Kodi (Verification Code)
        </label>
        <div class="relative">
          <KeyRound class="w-3.5 h-3.5 text-zinc-400 absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            :value="verificationCode"
            @input="handleCodeInput"
            type="text"
            required
            placeholder="Masalan: 7K4P-92MX-G108"
            class="w-full pl-9 pr-3 py-2 rounded-lg border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-950 text-xs font-mono tracking-wider text-zinc-900 dark:text-zinc-100 uppercase placeholder:text-zinc-400 focus:outline-hidden focus:border-zinc-400 dark:focus:border-zinc-600 transition-colors"
          />
        </div>
        <span class="block text-[11px] text-zinc-400 mt-1">
          Format: XXXX-XXXX-{{ contract?.student_id_assigned || 'STUDENTID' }}
        </span>
      </div>

      <!-- Account Password Input -->
      <div>
        <label class="block text-xs font-medium text-zinc-700 dark:text-zinc-300 mb-1.5">
          Profil Paroli (Account Password)
        </label>
        <div class="relative">
          <Lock class="w-3.5 h-3.5 text-zinc-400 absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            v-model="password"
            :type="showPassword ? 'text' : 'password'"
            required
            placeholder="Shaxsiy profilingiz paroli"
            class="w-full pl-9 pr-9 py-2 rounded-lg border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-950 text-xs text-zinc-900 dark:text-zinc-100 placeholder:text-zinc-400 focus:outline-hidden focus:border-zinc-400 dark:focus:border-zinc-600 transition-colors"
          />
          <button
            type="button"
            @click="showPassword = !showPassword"
            class="absolute right-3 top-1/2 -translate-y-1/2 text-zinc-400 hover:text-zinc-600 dark:hover:text-zinc-300 transition-colors cursor-pointer"
            tabindex="-1"
            :title="showPassword ? 'Parolni yashirish' : 'Parolni ko\'rsatish'"
          >
            <EyeOff v-if="showPassword" class="w-3.5 h-3.5" />
            <Eye v-else class="w-3.5 h-3.5" />
          </button>
        </div>
      </div>

      <!-- Expiration reminder -->
      <div class="flex items-center gap-1.5 text-[11px] text-amber-600 dark:text-amber-400">
        <Clock class="w-3.5 h-3.5" />
        <span>Kod berilgandan 24 soat amal qiladi.</span>
      </div>

      <!-- Submit Button -->
      <div class="pt-1 flex items-center justify-end gap-2.5">
        <button
          type="button"
          @click="handleClose"
          class="px-3.5 py-2 rounded-lg border border-zinc-200 dark:border-zinc-800 bg-white hover:bg-zinc-50 dark:bg-zinc-900 dark:hover:bg-zinc-850 text-xs font-medium text-zinc-700 dark:text-zinc-300 transition-colors cursor-pointer"
        >
          Bekor qilish
        </button>

        <button
          type="submit"
          :disabled="isSubmitting"
          class="inline-flex items-center gap-2 px-5 py-2 rounded-lg bg-zinc-900 hover:bg-zinc-800 text-white dark:bg-zinc-100 dark:hover:bg-white dark:text-zinc-950 text-xs font-medium shadow-xs transition-all cursor-pointer active:scale-98 disabled:opacity-50"
        >
          <Loader2 v-if="isSubmitting" class="w-3.5 h-3.5 animate-spin" />
          <span v-else>Shartnomani tasdiqlash</span>
        </button>
      </div>
    </form>
  </BaseModal>
</template>
