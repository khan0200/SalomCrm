<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import {
  CheckCircle2,
  Clock,
  AlertCircle,
  XCircle,
  FileText,
  Loader2,
  Download,
  ShieldCheck,
  ShieldQuestion,
  Building2,
  Scale,
} from 'lucide-vue-next'
import { onlineContractsApi, type PublicContractVerifyResponse } from '@/api/onlineContracts'
import { buildVariableValues } from '@/modules/contracts/utils/contractVariables'

const route = useRoute()
const code = computed(() => (route.params.code as string) || '')

const isLoading = ref(true)
const isNotFound = ref(false)
const data = ref<PublicContractVerifyResponse | null>(null)
const isDownloading = ref(false)

async function load() {
  isLoading.value = true
  isNotFound.value = false
  try {
    data.value = await onlineContractsApi.verifyPublicContract(code.value)
  } catch (err: any) {
    isNotFound.value = true
  } finally {
    isLoading.value = false
  }
}

const statusInfo = computed(() => {
  const s = data.value?.status
  if (s === 'verified') return { label: 'Rasman tasdiqlangan', icon: CheckCircle2, cls: 'bg-emerald-100 text-emerald-900 dark:bg-emerald-950/60 dark:text-emerald-300 border-emerald-500/30' }
  if (s === 'pending') return { label: 'Agentlik ko\'rib chiqmoqda', icon: Clock, cls: 'bg-amber-100 text-amber-900 dark:bg-amber-950/60 dark:text-amber-300 border-amber-500/30' }
  if (s === 'rejected') return { label: 'Rad etilgan', icon: AlertCircle, cls: 'bg-red-100 text-red-900 dark:bg-red-950/60 dark:text-red-300 border-red-500/30' }
  if (s === 'cancelled') return { label: 'Bekor qilingan', icon: XCircle, cls: 'bg-violet-100 text-violet-900 dark:bg-violet-950/60 dark:text-violet-300 border-violet-500/30' }
  return { label: s || 'Noma\'lum', icon: ShieldQuestion, cls: 'bg-zinc-100 text-zinc-700 dark:bg-zinc-800 dark:text-zinc-300 border-zinc-300 dark:border-zinc-700' }
})

function formatDate(val?: string | null): string {
  if (!val) return '—'
  const d = new Date(val)
  if (isNaN(d.getTime())) return val
  const day = String(d.getDate()).padStart(2, '0')
  const month = String(d.getMonth() + 1).padStart(2, '0')
  return `${day}.${month}.${d.getFullYear()}`
}

function formatPrice(val: number | undefined): string {
  if (!val) return '0 UZS'
  return val.toLocaleString('uz-UZ') + ' UZS'
}

async function handleDownload() {
  if (!data.value) return
  isDownloading.value = true
  try {
    const { downloadContractAsPdf } = await import('@/modules/contracts/utils/contractPdf')
    const title = `SHARTNOMA_${data.value.contract_number}_${data.value.full_name || ''}`
    const variableValues = buildVariableValues(data.value, {
      contractNumber: data.value.contract_number,
      price: data.value.tariff_price,
      discount: data.value.discount,
      signatureData: data.value.signature_data,
      verificationCode: data.value.verification_code,
    })
    await downloadContractAsPdf(
      title,
      data.value.content,
      { top: 15, right: 15, bottom: 15, left: 15 },
      variableValues,
      data.value.signature_data,
      {
        contractNumber: data.value.contract_number,
        studentId: data.value.contract_number,
        studentName: data.value.full_name,
        verifiedAt: data.value.verified_at ? formatDate(data.value.verified_at) : undefined,
        status: data.value.status,
      },
      data.value.is_minor && data.value.guardian_contract_text
        ? { content: data.value.guardian_contract_text, variableValues }
        : undefined
    )
  } catch (err) {
    console.error('Failed to download PDF:', err)
  } finally {
    isDownloading.value = false
  }
}

onMounted(() => {
  load()
})
</script>

<template>
  <div class="min-h-screen flex flex-col items-center bg-[#fafafa] dark:bg-[#09090b] text-zinc-900 dark:text-zinc-100 px-4 py-10 sm:py-16">
    <div class="w-full max-w-lg">
      <!-- Loading -->
      <div v-if="isLoading" class="flex flex-col items-center justify-center py-20 text-zinc-400">
        <Loader2 class="w-6 h-6 animate-spin text-zinc-900 dark:text-white mb-2" />
        <span class="text-xs font-mono">Tekshirilmoqda...</span>
      </div>

      <!-- Not found -->
      <div v-else-if="isNotFound" class="bg-white dark:bg-zinc-900/60 border border-zinc-200 dark:border-zinc-800 rounded-2xl p-8 text-center shadow-xs">
        <div class="w-14 h-14 rounded-2xl bg-red-50 dark:bg-red-950/50 border border-red-200 dark:border-red-900/50 text-red-500 flex items-center justify-center mx-auto mb-4">
          <ShieldQuestion class="w-7 h-7" />
        </div>
        <h1 class="text-base font-bold text-zinc-900 dark:text-white mb-1.5">
          Shartnoma topilmadi
        </h1>
        <p class="text-xs text-zinc-500 dark:text-zinc-400 leading-relaxed">
          Ushbu tasdiqlash kodi bo'yicha hech qanday shartnoma topilmadi. Havolani yoki QR-kodni qaytadan tekshiring.
        </p>
        <p class="mt-4 text-[11px] font-mono text-zinc-400 break-all">{{ code }}</p>
      </div>

      <!-- Found -->
      <div v-else-if="data" class="space-y-5">
        <!-- Header: tenant + trust badge -->
        <div class="flex items-center justify-between">
          <div class="flex items-center gap-2.5">
            <div
              v-if="data.tenant.logo_url"
              class="w-9 h-9 rounded-lg overflow-hidden bg-white border border-zinc-200 dark:border-zinc-800 p-0.5 flex items-center justify-center shrink-0"
            >
              <img :src="data.tenant.logo_url" :alt="data.tenant.name" class="w-full h-full object-contain" />
            </div>
            <div v-else class="w-9 h-9 rounded-lg bg-zinc-900 dark:bg-zinc-100 text-white dark:text-zinc-950 flex items-center justify-center shrink-0">
              <Building2 class="w-4 h-4" />
            </div>
            <span class="text-sm font-semibold tracking-tight">{{ data.tenant.name }}</span>
          </div>
          <div class="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full border border-emerald-500/20 bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 text-[10.5px] font-mono">
            <ShieldCheck class="w-3.5 h-3.5" />
            <span>Rasmiy tekshirish</span>
          </div>
        </div>

        <!-- Status card -->
        <div class="bg-white dark:bg-zinc-900/60 border border-zinc-200 dark:border-zinc-800 rounded-2xl p-6 sm:p-8 shadow-xs space-y-6">
          <div class="flex items-center justify-between flex-wrap gap-3">
            <span
              class="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full text-sm font-bold border"
              :class="statusInfo.cls"
            >
              <component :is="statusInfo.icon" class="w-4 h-4" />
              <span>{{ statusInfo.label }}</span>
            </span>
            <span class="text-xs font-mono font-bold text-zinc-900 dark:text-white px-2.5 py-1 rounded-md bg-zinc-100 dark:bg-zinc-800 border border-zinc-200 dark:border-zinc-700">
              № {{ data.contract_number }}
            </span>
          </div>

          <div class="grid grid-cols-1 sm:grid-cols-2 gap-3.5 text-xs">
            <div class="p-3.5 bg-zinc-50/70 dark:bg-zinc-850/50 rounded-lg border border-zinc-200 dark:border-zinc-800">
              <span class="font-bold uppercase tracking-wide text-zinc-500 dark:text-zinc-400 block mb-1">Mijoz</span>
              <strong class="text-zinc-900 dark:text-white">{{ data.full_name || '—' }}</strong>
            </div>
            <div class="p-3.5 bg-zinc-50/70 dark:bg-zinc-850/50 rounded-lg border border-zinc-200 dark:border-zinc-800">
              <span class="font-bold uppercase tracking-wide text-zinc-500 dark:text-zinc-400 block mb-1">Xizmat</span>
              <strong class="text-zinc-900 dark:text-white">{{ data.tariff_name || '—' }}</strong>
            </div>
            <div class="p-3.5 bg-zinc-50/70 dark:bg-zinc-850/50 rounded-lg border border-zinc-200 dark:border-zinc-800">
              <span class="font-bold uppercase tracking-wide text-zinc-500 dark:text-zinc-400 block mb-1">Shartnoma to'lovi</span>
              <strong class="font-mono text-zinc-900 dark:text-white">{{ formatPrice(data.tariff_price) }}</strong>
            </div>
            <div class="p-3.5 bg-zinc-50/70 dark:bg-zinc-850/50 rounded-lg border border-zinc-200 dark:border-zinc-800">
              <span class="font-bold uppercase tracking-wide text-zinc-500 dark:text-zinc-400 block mb-1">
                {{ data.status === 'verified' ? 'Tasdiqlangan sana' : 'Imzolangan sana' }}
              </span>
              <strong class="text-zinc-900 dark:text-white">{{ formatDate(data.verified_at || data.signed_at || data.created_at) }}</strong>
            </div>
          </div>

          <div v-if="data.status === 'rejected'" class="p-3.5 rounded-xl bg-red-50 dark:bg-red-950/30 border border-red-200 dark:border-red-900/50 text-xs text-red-700 dark:text-red-300">
            Ushbu shartnoma agentlik tomonidan rad etilgan. Batafsil ma'lumot uchun konsalting kompaniyasiga murojaat qiling.
          </div>
          <div v-else-if="data.status === 'cancelled'" class="p-3.5 rounded-xl bg-violet-50/80 dark:bg-violet-950/30 border border-violet-500/20 text-xs text-violet-800 dark:text-violet-300">
            Ushbu shartnoma bekor qilingan.
          </div>

          <div class="p-3.5 rounded-xl bg-zinc-50 dark:bg-zinc-850/60 border border-zinc-200 dark:border-zinc-800 flex items-start gap-2.5">
            <Scale class="w-4 h-4 text-zinc-500 dark:text-zinc-400 shrink-0 mt-0.5" />
            <p class="text-[11.5px] text-zinc-600 dark:text-zinc-400 leading-relaxed font-medium">
              Tomonlar shartnoma va uning ilovalari Korxonaning axborot tizimi orqali elektron shaklda tuzilishi va Mijozning grafik (qo'lda chizilgan) imzosi, elektron pochta orqali tasdiqlash kodi hamda tizim tomonidan qayd etilgan sana, IP-manzil va qurilma ma'lumotlari birgalikda qo'lyozma imzoga tenglashtirilishini tan oladilar. Elektron nusxa qog'oz nusxa bilan bir xil yuridik kuchga ega.
            </p>
          </div>

          <button
            type="button"
            @click="handleDownload"
            :disabled="isDownloading"
            class="w-full inline-flex items-center justify-center gap-2 py-2.5 px-4 rounded-lg bg-zinc-900 hover:bg-zinc-800 text-white dark:bg-zinc-100 dark:hover:bg-white dark:text-zinc-950 text-xs font-medium transition-all cursor-pointer disabled:opacity-50 active:scale-98 shadow-xs"
          >
            <Loader2 v-if="isDownloading" class="w-3.5 h-3.5 animate-spin" />
            <Download v-else class="w-3.5 h-3.5" />
            <span>Rasmiy PDF nusxasini yuklab olish</span>
          </button>
        </div>

        <div class="flex items-center gap-2 justify-center text-[11px] text-zinc-400">
          <FileText class="w-3.5 h-3.5" />
          <span>Ushbu sahifa shartnomaning joriy holatini real vaqtda ko'rsatadi.</span>
        </div>
      </div>
    </div>
  </div>
</template>
