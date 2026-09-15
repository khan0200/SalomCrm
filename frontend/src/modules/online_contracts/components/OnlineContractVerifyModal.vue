<script setup lang="ts">
import { ref, computed } from 'vue'
import {
  X,
  KeyRound,
  Lock,
  CheckCircle2,
  AlertCircle,
  Clock,
  Loader2,
  Download,
  Eye,
  FileCheck,
} from 'lucide-vue-next'
import { onlineContractsApi, type OnlineContractSummary } from '@/api/onlineContracts'
import { downloadContractAsPdf } from '@/modules/contracts/utils/contractPdf'
import { buildVariableValues } from '@/modules/contracts/utils/contractVariables'

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
const isSubmitting = ref(false)
const errorMessage = ref('')
const isVerifiedSuccess = ref(false)
const verifiedContractData = ref<any>(null)
const isDownloadingPdf = ref(false)

const canSubmit = computed(() => {
  return verificationCode.value.trim().length >= 6 && password.value.length > 0
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
      verificationMeta
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
  errorMessage.value = ''
  emit('close')
}
</script>

<template>
  <div
    v-if="isOpen"
    class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-xs animate-in fade-in duration-200"
    @click.self="handleClose"
  >
    <div
      class="bg-white dark:bg-zinc-900 rounded-3xl shadow-2xl w-full max-w-lg border border-zinc-200 dark:border-zinc-800 overflow-hidden"
    >
      <!-- Modal Header -->
      <div class="px-6 py-4 border-b border-zinc-200 dark:border-zinc-800 flex items-center justify-between bg-zinc-50 dark:bg-zinc-850">
        <div class="flex items-center gap-2.5">
          <div class="w-8 h-8 rounded-xl bg-blue-100 dark:bg-blue-950/60 text-blue-600 flex items-center justify-center font-bold">
            <KeyRound class="w-4 h-4" />
          </div>
          <div>
            <h3 class="text-sm font-bold text-zinc-900 dark:text-white">
              Shartnomani Yakuniy Tasdiqlash
            </h3>
            <p class="text-[11px] text-zinc-500">
              Contract No: <strong>{{ contract?.contract_number }}</strong>
            </p>
          </div>
        </div>

        <button
          type="button"
          @click="handleClose"
          class="p-1.5 rounded-lg text-zinc-400 hover:text-zinc-600 dark:hover:text-zinc-200 hover:bg-zinc-100 dark:hover:bg-zinc-800 transition-colors"
        >
          <X class="w-5 h-5" />
        </button>
      </div>

      <!-- Success State -->
      <div v-if="isVerifiedSuccess" class="p-8 text-center animate-in fade-in">
        <div class="w-16 h-16 rounded-full bg-emerald-100 dark:bg-emerald-950/60 text-emerald-600 dark:text-emerald-400 flex items-center justify-center mx-auto mb-4">
          <CheckCircle2 class="w-10 h-10" />
        </div>

        <h3 class="text-lg font-extrabold text-zinc-900 dark:text-white mb-2">
          Shartnoma Muvaffaqiyatli Tasdiqlandi!
        </h3>

        <p class="text-xs text-zinc-500 leading-relaxed max-w-sm mx-auto mb-6">
          Shartnoma to'liq qonuniy kuchga kirdi va o'zgarmas holatda tizimda ro'yxatga olindi.
          Siz shartnoma raqami orqali istalgan vaqtda rasmiy PDF nusxasini yuklab olishingiz mumkin.
        </p>

        <div class="bg-zinc-50 dark:bg-zinc-800/60 p-4 rounded-2xl border border-zinc-200 dark:border-zinc-700/60 text-xs space-y-1.5 mb-6 text-left max-w-sm mx-auto">
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

        <div class="flex items-center justify-center gap-3">
          <button
            type="button"
            @click="handleDownloadPdf"
            :disabled="isDownloadingPdf"
            class="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-blue-600 hover:bg-blue-700 text-white text-xs font-bold shadow-md shadow-blue-500/20 transition-all cursor-pointer disabled:opacity-50"
          >
            <Loader2 v-if="isDownloadingPdf" class="w-4 h-4 animate-spin" />
            <Download v-else class="w-4 h-4" />
            <span>Rasmiy PDF yuklab olish</span>
          </button>

          <button
            type="button"
            @click="handleClose"
            class="px-4 py-2.5 rounded-xl border border-zinc-200 dark:border-zinc-700 text-xs font-semibold text-zinc-700 dark:text-zinc-300 hover:bg-zinc-100 dark:hover:bg-zinc-800"
          >
            Yopish
          </button>
        </div>
      </div>

      <!-- Verification Form -->
      <form v-else @submit.prevent="handleVerify" class="p-6 space-y-5">
        <div class="text-xs text-zinc-600 dark:text-zinc-400 leading-relaxed bg-blue-50 dark:bg-blue-950/30 border border-blue-200 dark:border-blue-900/40 p-3.5 rounded-xl">
          Konsalting kompaniyasi sizga taqdim etgan bir martalik <strong>Tasdiqlash Kodi</strong>ni va hisobingiz parolini kiriting.
        </div>

        <!-- Error display -->
        <div
          v-if="errorMessage"
          class="p-3 rounded-xl bg-red-50 dark:bg-red-950/40 border border-red-200 dark:border-red-900/60 text-xs text-red-700 dark:text-red-300 flex items-start gap-2"
        >
          <AlertCircle class="w-4 h-4 shrink-0 mt-0.5" />
          <span>{{ errorMessage }}</span>
        </div>

        <!-- Verification Code Input -->
        <div>
          <label class="block text-xs font-semibold text-zinc-700 dark:text-zinc-300 mb-1.5">
            Tasdiqlash Kodi (Verification Code)
          </label>
          <div class="relative">
            <KeyRound class="w-4 h-4 text-zinc-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
            <input
              :value="verificationCode"
              @input="handleCodeInput"
              type="text"
              required
              placeholder="Masalan: 7K4P-92MX-G108"
              class="w-full pl-10 pr-3.5 py-2.5 rounded-xl border border-zinc-300 dark:border-zinc-700 bg-white dark:bg-zinc-800 text-sm font-mono tracking-wider text-zinc-900 dark:text-white uppercase focus:ring-2 focus:ring-blue-500 outline-hidden transition-all"
            />
          </div>
          <span class="block text-[11px] text-zinc-400 mt-1">
            Format: XXXX-XXXX-{{ contract?.student_id_assigned || 'STUDENTID' }}
          </span>
        </div>

        <!-- Account Password Input -->
        <div>
          <label class="block text-xs font-semibold text-zinc-700 dark:text-zinc-300 mb-1.5">
            Hisobingiz Paroli (Account Password)
          </label>
          <div class="relative">
            <Lock class="w-4 h-4 text-zinc-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
            <input
              v-model="password"
              type="password"
              required
              placeholder="Shaxsiy profilingiz paroli"
              class="w-full pl-10 pr-3.5 py-2.5 rounded-xl border border-zinc-300 dark:border-zinc-700 bg-white dark:bg-zinc-800 text-xs text-zinc-900 dark:text-white focus:ring-2 focus:ring-blue-500 outline-hidden transition-all"
            />
          </div>
        </div>

        <!-- Expiration reminder -->
        <div class="flex items-center gap-1.5 text-[11px] text-amber-600 dark:text-amber-400">
          <Clock class="w-3.5 h-3.5" />
          <span>Tasdiqlash kodi berilgan vaqtdan boshlab 24 soat davomida amal qiladi.</span>
        </div>

        <!-- Submit Button -->
        <div class="pt-2 flex items-center justify-end gap-3">
          <button
            type="button"
            @click="handleClose"
            class="px-4 py-2.5 rounded-xl border border-zinc-200 dark:border-zinc-700 text-xs font-semibold text-zinc-700 dark:text-zinc-300 hover:bg-zinc-100 dark:hover:bg-zinc-800 transition-colors"
          >
            Bekor qilish
          </button>

          <button
            type="submit"
            :disabled="isSubmitting"
            class="inline-flex items-center gap-2 px-6 py-2.5 rounded-xl bg-blue-600 hover:bg-blue-700 text-white text-xs font-bold shadow-md shadow-blue-500/20 transition-all cursor-pointer disabled:opacity-50"
          >
            <Loader2 v-if="isSubmitting" class="w-4 h-4 animate-spin" />
            <span v-else>Shartnomani tasdiqlash</span>
          </button>
        </div>
      </form>
    </div>
  </div>
</template>
