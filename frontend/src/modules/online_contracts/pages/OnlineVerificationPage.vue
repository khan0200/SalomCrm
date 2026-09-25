<script setup lang="ts">
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  BookUser,
  CreditCard,
  ScanFace,
  ArrowRight,
  ArrowLeft,
  Loader2,
  CheckCircle2,
  AlertCircle,
  ExternalLink,
  RotateCw,
  ShieldCheck,
} from 'lucide-vue-next'
import {
  onlineContractsApi,
  type TenantInfoResponse,
  type IdentityVerificationStatus,
} from '@/api/onlineContracts'
import OnlineContractLayout from '../layouts/OnlineContractLayout.vue'

const route = useRoute()
const router = useRouter()
const tenantSlug = computed(() => (route.params.tenantname as string) || '')

const isLoadingTenant = ref(true)
const tenantInfo = ref<TenantInfoResponse | null>(null)

const documentType = ref<'PASSPORT' | 'ID_CARD'>('PASSPORT')
const status = ref<IdentityVerificationStatus>('NOT_STARTED')
const sessionUrl = ref('')
const isStarting = ref(false)
const errorMessage = ref('')
let pollTimer: ReturnType<typeof setInterval> | null = null

const extracted = ref({ full_name: '', document_number: '', date_of_birth: '' })
const isConfirming = ref(false)
const confirmError = ref('')

function goNext() {
  const pendingTariffId = sessionStorage.getItem('selected_tariff_id')
  if (pendingTariffId) {
    router.replace({
      name: 'online-contract-sign',
      params: { tenantname: tenantSlug.value },
      query: { tariffId: pendingTariffId },
    })
  } else {
    router.replace({ name: 'online-profile', params: { tenantname: tenantSlug.value } })
  }
}

function stopPolling() {
  if (pollTimer) clearInterval(pollTimer)
  pollTimer = null
}

async function refreshStatus() {
  try {
    const res = await onlineContractsApi.getVerificationStatus()
    status.value = res.status
    if (res.status === 'PENDING_REVIEW' && res.extracted) {
      extracted.value = { ...res.extracted }
      stopPolling()
    } else if (res.status === 'VERIFIED') {
      stopPolling()
      goNext()
    }
  } catch {
    // Transient poll errors are ignored - the next tick tries again.
  }
}

function startPolling() {
  stopPolling()
  pollTimer = setInterval(refreshStatus, 4000)
}

async function handleStart() {
  errorMessage.value = ''
  isStarting.value = true
  try {
    const res = await onlineContractsApi.startVerification(documentType.value)
    status.value = res.status
    sessionUrl.value = res.url
    window.open(res.url, '_blank', 'noopener')
    startPolling()
  } catch (err: any) {
    errorMessage.value = err?.response?.data?.detail
      || "Tekshiruv xizmatini boshlab bo'lmadi. Birozdan so'ng qayta urinib ko'ring."
  } finally {
    isStarting.value = false
  }
}

function handleReopen() {
  if (sessionUrl.value) {
    window.open(sessionUrl.value, '_blank', 'noopener')
  }
}

function handleRetry() {
  status.value = 'NOT_STARTED'
  sessionUrl.value = ''
  errorMessage.value = ''
  stopPolling()
}

async function handleConfirm() {
  confirmError.value = ''
  if (!extracted.value.full_name.trim() || !extracted.value.document_number.trim() || !extracted.value.date_of_birth.trim()) {
    confirmError.value = "Barcha maydonlarni to'ldiring."
    return
  }
  isConfirming.value = true
  try {
    await onlineContractsApi.confirmVerification(extracted.value)
    goNext()
  } catch (err: any) {
    confirmError.value = err?.response?.data?.detail || 'Tasdiqlashda xatolik yuz berdi.'
  } finally {
    isConfirming.value = false
  }
}

onMounted(async () => {
  try {
    tenantInfo.value = await onlineContractsApi.getTenantInfo(tenantSlug.value)
  } finally {
    isLoadingTenant.value = false
  }
  await refreshStatus()
  if (status.value === 'IN_PROGRESS') startPolling()
})

onBeforeUnmount(() => stopPolling())
</script>

<template>
  <OnlineContractLayout :tenant-info="tenantInfo" :is-loading="isLoadingTenant">
    <div class="max-w-lg mx-auto py-6">
      <!-- Back link -->
      <router-link
        :to="{ name: 'online-profile', params: { tenantname: tenantSlug } }"
        class="inline-flex items-center gap-1.5 text-xs font-mono text-zinc-500 hover:text-zinc-900 dark:hover:text-zinc-100 transition-colors mb-4"
      >
        <ArrowLeft class="w-3.5 h-3.5" />
        <span>Profilga qaytish</span>
      </router-link>

      <div class="bg-white dark:bg-zinc-900/60 border border-zinc-200/80 dark:border-zinc-800 rounded-xl p-8 shadow-xs">
        <div class="mb-6">
          <div class="w-10 h-10 rounded-xl bg-zinc-900 dark:bg-zinc-100 text-white dark:text-zinc-950 flex items-center justify-center mb-3">
            <ShieldCheck class="w-5 h-5" />
          </div>
          <h1 class="text-xl font-semibold tracking-tight text-zinc-900 dark:text-zinc-100">
            Shaxsni tasdiqlash
          </h1>
          <p class="text-xs text-zinc-500 dark:text-zinc-400 mt-1.5 leading-relaxed">
            Birinchi shartnomangizni tuzishdan oldin, hujjatingiz va yuzingizni bir marta tasdiqlashingiz kerak.
            Bu jarayon keyingi barcha shartnomalar uchun qayta talab qilinmaydi.
          </p>
        </div>

        <!-- STATE: not started / declined / abandoned -->
        <template v-if="status === 'NOT_STARTED' || status === 'DECLINED' || status === 'ABANDONED'">
          <div
            v-if="status === 'DECLINED'"
            class="mb-4 p-3 rounded-lg bg-red-50 dark:bg-red-950/40 border border-red-200 dark:border-red-900/60 text-xs text-red-700 dark:text-red-300 flex items-start gap-2"
          >
            <AlertCircle class="w-4 h-4 shrink-0 mt-0.5 text-red-500" />
            <span>Tekshiruv rad etildi. Hujjatingiz aniq va yorug'likda suratga olinganiga ishonch hosil qilib, qayta urinib ko'ring.</span>
          </div>
          <div
            v-else-if="status === 'ABANDONED'"
            class="mb-4 p-3 rounded-lg bg-amber-50 dark:bg-amber-950/40 border border-amber-200 dark:border-amber-900/60 text-xs text-amber-700 dark:text-amber-300 flex items-start gap-2"
          >
            <AlertCircle class="w-4 h-4 shrink-0 mt-0.5 text-amber-500" />
            <span>Tekshiruv jarayoni yakunlanmadi. Qaytadan boshlang.</span>
          </div>
          <div
            v-if="errorMessage"
            class="mb-4 p-3 rounded-lg bg-red-50 dark:bg-red-950/40 border border-red-200 dark:border-red-900/60 text-xs text-red-700 dark:text-red-300 flex items-start gap-2"
          >
            <AlertCircle class="w-4 h-4 shrink-0 mt-0.5 text-red-500" />
            <span>{{ errorMessage }}</span>
          </div>

          <label class="block text-xs font-medium text-zinc-700 dark:text-zinc-300 mb-2">
            Hujjat turini tanlang
          </label>
          <div class="grid grid-cols-2 gap-2.5 mb-6">
            <button
              type="button"
              @click="documentType = 'PASSPORT'"
              class="p-3 rounded-lg border-2 text-left transition-all cursor-pointer"
              :class="documentType === 'PASSPORT'
                ? 'border-zinc-900 dark:border-zinc-100 bg-zinc-50 dark:bg-zinc-800/60'
                : 'border-zinc-200 dark:border-zinc-800 hover:border-zinc-300 dark:hover:border-zinc-700'"
            >
              <BookUser class="w-4 h-4 mb-1.5" :class="documentType === 'PASSPORT' ? 'text-zinc-900 dark:text-zinc-100' : 'text-zinc-400'" />
              <div class="text-xs font-semibold text-zinc-900 dark:text-zinc-100">Xalqaro pasport</div>
            </button>
            <button
              type="button"
              @click="documentType = 'ID_CARD'"
              class="p-3 rounded-lg border-2 text-left transition-all cursor-pointer"
              :class="documentType === 'ID_CARD'
                ? 'border-zinc-900 dark:border-zinc-100 bg-zinc-50 dark:bg-zinc-800/60'
                : 'border-zinc-200 dark:border-zinc-800 hover:border-zinc-300 dark:hover:border-zinc-700'"
            >
              <CreditCard class="w-4 h-4 mb-1.5" :class="documentType === 'ID_CARD' ? 'text-zinc-900 dark:text-zinc-100' : 'text-zinc-400'" />
              <div class="text-xs font-semibold text-zinc-900 dark:text-zinc-100">ID karta</div>
            </button>
          </div>

          <button
            type="button"
            @click="handleStart"
            :disabled="isStarting"
            class="w-full inline-flex items-center justify-center gap-2 py-2.5 px-4 rounded-lg bg-zinc-900 hover:bg-zinc-800 text-white dark:bg-zinc-100 dark:hover:bg-white dark:text-zinc-950 text-xs font-medium transition-all cursor-pointer disabled:opacity-50 active:scale-98 shadow-xs"
          >
            <Loader2 v-if="isStarting" class="w-3.5 h-3.5 animate-spin" />
            <ScanFace v-else class="w-3.5 h-3.5" />
            <span>Tasdiqlashni boshlash</span>
            <ArrowRight v-if="!isStarting" class="w-3.5 h-3.5" />
          </button>
        </template>

        <!-- STATE: in progress (waiting for the hosted flow / webhook) -->
        <template v-else-if="status === 'IN_PROGRESS'">
          <div class="flex flex-col items-center text-center py-6">
            <Loader2 class="w-6 h-6 animate-spin text-zinc-900 dark:text-white mb-3" />
            <p class="text-xs font-medium text-zinc-700 dark:text-zinc-300 mb-1">
              Tekshiruv oynasida davom eting
            </p>
            <p class="text-[11px] text-zinc-500 dark:text-zinc-400 max-w-xs leading-relaxed mb-5">
              Yangi ochilgan oynada hujjatingizni skanerlab, selfie oling. Yakunlaganingizdan so'ng bu sahifa avtomatik yangilanadi.
            </p>
            <button
              type="button"
              @click="handleReopen"
              class="inline-flex items-center gap-1.5 text-xs font-medium text-zinc-700 dark:text-zinc-300 hover:text-zinc-900 dark:hover:text-white underline transition-colors cursor-pointer"
            >
              <ExternalLink class="w-3.5 h-3.5" />
              <span>Oynani qayta ochish</span>
            </button>
          </div>
        </template>

        <!-- STATE: pending review - student confirms/edits extracted fields -->
        <template v-else-if="status === 'PENDING_REVIEW'">
          <div class="mb-4 p-3 rounded-lg bg-emerald-50 dark:bg-emerald-950/40 border border-emerald-200 dark:border-emerald-900/60 text-xs text-emerald-700 dark:text-emerald-300 flex items-start gap-2">
            <CheckCircle2 class="w-4 h-4 shrink-0 mt-0.5 text-emerald-500" />
            <span>Hujjatingiz tasdiqlandi. Quyidagi ma'lumotlar to'g'ri ekanini tekshiring.</span>
          </div>

          <div
            v-if="confirmError"
            class="mb-4 p-3 rounded-lg bg-red-50 dark:bg-red-950/40 border border-red-200 dark:border-red-900/60 text-xs text-red-700 dark:text-red-300 flex items-start gap-2"
          >
            <AlertCircle class="w-4 h-4 shrink-0 mt-0.5 text-red-500" />
            <span>{{ confirmError }}</span>
          </div>

          <form @submit.prevent="handleConfirm" class="space-y-4">
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
              :disabled="isConfirming"
              class="w-full inline-flex items-center justify-center gap-2 py-2.5 px-4 rounded-lg bg-zinc-900 hover:bg-zinc-800 text-white dark:bg-zinc-100 dark:hover:bg-white dark:text-zinc-950 text-xs font-medium transition-all cursor-pointer disabled:opacity-50 active:scale-98 shadow-xs"
            >
              <Loader2 v-if="isConfirming" class="w-3.5 h-3.5 animate-spin" />
              <span v-else>Ma'lumotlar to'g'ri, tasdiqlayman</span>
            </button>
          </form>
        </template>

        <!-- STATE: verified (brief, redirects immediately) -->
        <template v-else-if="status === 'VERIFIED'">
          <div class="flex flex-col items-center text-center py-6">
            <CheckCircle2 class="w-8 h-8 text-emerald-500 mb-3" />
            <p class="text-xs font-medium text-zinc-700 dark:text-zinc-300">Shaxsingiz tasdiqlandi</p>
          </div>
        </template>
      </div>

      <button
        v-if="status !== 'NOT_STARTED'"
        type="button"
        @click="handleRetry"
        class="mt-4 mx-auto flex items-center gap-1.5 text-[11px] text-zinc-400 hover:text-zinc-600 dark:hover:text-zinc-300 transition-colors cursor-pointer"
      >
        <RotateCw class="w-3 h-3" />
        <span>Boshqa hujjat bilan qaytadan boshlash</span>
      </button>
    </div>
  </OnlineContractLayout>
</template>
