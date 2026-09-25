<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  FileCheck,
  ShieldCheck,
  CheckCircle2,
  ArrowRight,
  Eye,
  Building2,
  Sparkles,
  Loader2,
  Download,
  Check,
  Search,
  MapPin,
  FileSignature,
  Layers,
  Scale,
  Lock,
  QrCode,
  KeyRound,
  FileCheck2,
} from 'lucide-vue-next'
import { onlineContractsApi, type TenantInfoResponse, type OnlineTariff } from '@/api/onlineContracts'
import { downloadContractAsPdf } from '@/modules/contracts/utils/contractPdf'
import { getTariffSampleContractHtml } from '../utils/sampleContract'
import { useAuthStore } from '@/stores/auth'
import OnlineContractLayout from '../layouts/OnlineContractLayout.vue'
import TenantNotFoundPage from './TenantNotFoundPage.vue'
import TenantInactivePage from './TenantInactivePage.vue'
import FullContractViewerModal from '../components/FullContractViewerModal.vue'
import { vReveal } from '@/directives/reveal'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()

const tenantSlug = computed(() => (route.params.tenantname as string) || '')
const isStudentAuthenticated = computed(() => authStore.isAuthenticated && authStore.user?.role === 'STUDENT')

const isLoading = ref(true)
const isNotFound = ref(false)
const isInactive = ref(false)
const tenantInfo = ref<TenantInfoResponse | null>(null)

// Search query for instant real-time filtering of tariffs
const searchQuery = ref('')

// PDF download states per tariff
const downloadingTariffId = ref<string | null>(null)
const downloadSuccessTariffId = ref<string | null>(null)

// Preview modal state
const isPreviewModalOpen = ref(false)
const previewContractTitle = ref('')
const previewContractContent = ref('')

const filteredTariffs = computed(() => {
  const list = tenantInfo.value?.tariffs || []
  if (!searchQuery.value.trim()) return list
  const query = searchQuery.value.toLowerCase().trim()
  return list.filter((t) => t.name.toLowerCase().includes(query))
})

function scrollToSection(sectionId: string) {
  const target = document.getElementById(sectionId)
  if (target) {
    target.scrollIntoView({ behavior: 'smooth', block: 'start' })
    history.pushState(null, '', `#${sectionId}`)
  }
}

async function fetchTenantData() {
  if (!tenantSlug.value) return
  isLoading.value = true
  isNotFound.value = false
  isInactive.value = false

  try {
    const data = await onlineContractsApi.getTenantInfo(tenantSlug.value)
    if (!data.active) {
      isInactive.value = true
      tenantInfo.value = data
      return
    }
    tenantInfo.value = data
  } catch (err: any) {
    if (err?.response?.status === 404) {
      isNotFound.value = true
    } else {
      console.error('Failed to load tenant info:', err)
      isNotFound.value = true
    }
  } finally {
    isLoading.value = false
  }
}

function formatPrice(val: number | string | undefined): string {
  if (!val) return '0 UZS'
  const num = typeof val === 'number' ? val : parseFloat(String(val))
  return num.toLocaleString('uz-UZ') + ' UZS'
}

/**
 * Handle direct sample PDF download for a tariff
 */
async function fetchTariffContractText(tariff: OnlineTariff): Promise<string | undefined> {
  // getTenantInfo's list doesn't carry contract_text (see backend
  // TenantInfoView) - fetched lazily here, only for the one tariff the
  // visitor actually acted on.
  if (tariff.contract_text) return tariff.contract_text
  try {
    const res = await onlineContractsApi.getTariffContractText(tariff.id)
    return res.contract_text
  } catch {
    return undefined
  }
}

async function handleDownloadSamplePdf(tariff: OnlineTariff) {
  const tariffIdStr = String(tariff.id)
  if (downloadingTariffId.value) return

  downloadingTariffId.value = tariffIdStr
  try {
    const companyName = tenantInfo.value?.name || 'Konsalting Kompaniyasi'
    const contractText = await fetchTariffContractText(tariff)
    const contractHtml = getTariffSampleContractHtml(companyName, { ...tariff, contract_text: contractText })
    const safeTitle = `${companyName}_${tariff.name}_Shartnoma`.replace(/[^a-zA-Z0-9_\u0400-\u04FF]/g, '_')

    await downloadContractAsPdf(
      safeTitle,
      contractHtml,
      { top: 18, right: 15, bottom: 18, left: 20 }
    )

    downloadSuccessTariffId.value = tariffIdStr
    setTimeout(() => {
      if (downloadSuccessTariffId.value === tariffIdStr) {
        downloadSuccessTariffId.value = null
      }
    }, 2500)
  } catch (err) {
    console.error('PDF yuklab olishda xatolik:', err)
  } finally {
    downloadingTariffId.value = null
  }
}

const isLoadingPreview = ref<string | null>(null)

async function handleViewContract(tariff: OnlineTariff) {
  if (isLoadingPreview.value) return
  isLoadingPreview.value = String(tariff.id)
  try {
    const companyName = tenantInfo.value?.name || 'Konsalting Kompaniyasi'
    const contractText = await fetchTariffContractText(tariff)
    previewContractTitle.value = `${tariff.name} — Namunaviy Shartnoma`
    previewContractContent.value = getTariffSampleContractHtml(companyName, { ...tariff, contract_text: contractText })
    isPreviewModalOpen.value = true
  } finally {
    isLoadingPreview.value = null
  }
}

function handleSelectTariffToSign(tariff: OnlineTariff) {
  sessionStorage.setItem('selected_tariff_id', String(tariff.id))
  sessionStorage.setItem('selected_tariff_name', tariff.name)
  sessionStorage.setItem('selected_tariff_price', String(tariff.price))

  router.push({
    name: 'online-contract-sign',
    params: { tenantname: tenantSlug.value },
    query: { tariffId: String(tariff.id) },
  })
}

onMounted(() => {
  fetchTenantData()
})
</script>

<template>
  <Transition name="page-fade" mode="out-in">
  <div v-if="isLoading" key="loading" class="min-h-screen flex items-center justify-center bg-[#fafafa] dark:bg-[#09090b]">
    <div class="flex flex-col items-center gap-3 text-zinc-400">
      <Loader2 class="w-6 h-6 animate-spin text-zinc-900 dark:text-white" />
      <span class="text-xs font-mono tracking-tight">Yuklanmoqda...</span>
    </div>
  </div>

  <TenantNotFoundPage v-else-if="isNotFound" key="not-found" />
  <TenantInactivePage v-else-if="isInactive" key="inactive" :company-name="tenantInfo?.name" />

  <OnlineContractLayout v-else key="content" :tenant-info="tenantInfo">
    <!-- Resend-style Minimalist Hero Section (Mobile Optimized) -->
    <section class="pt-2 sm:pt-6 pb-10 sm:pb-14 border-b border-zinc-200/80 dark:border-zinc-800/80">
      <div class="max-w-3xl">
        <!-- Status Pill -->
        <div class="inline-flex items-center gap-1.5 sm:gap-2 px-2.5 py-1 rounded-full border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-900 text-zinc-600 dark:text-zinc-400 text-[10.5px] sm:text-xs font-mono mb-4 sm:mb-6 shadow-2xs">
          <span class="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse shrink-0" />
          <span class="truncate">{{ tenantInfo?.name }} • Rasmiy Onlayn Shartnomalar</span>
        </div>

        <!-- High-Impact Responsive Headline -->
        <h1 class="text-2xl xs:text-3xl sm:text-5xl font-bold tracking-tight text-zinc-900 dark:text-zinc-50 mb-3 sm:mb-4 leading-tight sm:leading-[1.15]">
          {{ tenantInfo?.name }} bilan onlayn shartnomalar va tariflar
        </h1>

        <!-- Subtitle -->
        <p class="text-xs sm:text-base text-zinc-500 dark:text-zinc-400 leading-relaxed mb-6 sm:mb-8 max-w-2xl">
          Uydan chiqmasdan namunaviy shartnomalar bilan tanishing, rasmiy PDF nusxasini yuklab oling yoki elektron imzo orqali onlayn rasmiylashtiring.
        </p>

        <!-- Responsive Action Buttons (Thumb-friendly on mobile) -->
        <div class="flex flex-col xs:flex-row items-stretch xs:items-center gap-2.5 sm:gap-3">
          <a
            v-if="isStudentAuthenticated"
            href="#tariffs-section"
            @click.prevent="scrollToSection('tariffs-section')"
            class="inline-flex items-center justify-center gap-2 px-4 py-2.5 rounded-lg bg-zinc-900 hover:bg-zinc-800 text-white dark:bg-zinc-100 dark:hover:bg-white dark:text-zinc-950 text-xs font-medium transition-all shadow-xs active:scale-98 text-center cursor-pointer"
          >
            <span>Tarif tanlash va shartnoma tuzish</span>
            <ArrowRight class="w-3.5 h-3.5" />
          </a>

          <router-link
            v-else
            :to="{ name: 'online-sign-up', params: { tenantname: tenantSlug } }"
            class="inline-flex items-center justify-center gap-2 px-4 py-2.5 rounded-lg bg-zinc-900 hover:bg-zinc-800 text-white dark:bg-zinc-100 dark:hover:bg-white dark:text-zinc-950 text-xs font-medium transition-all shadow-xs active:scale-98 text-center"
          >
            <span>Shartnoma tuzish</span>
            <ArrowRight class="w-3.5 h-3.5" />
          </router-link>

          <a
            href="#tariffs-section"
            @click.prevent="scrollToSection('tariffs-section')"
            class="inline-flex items-center justify-center gap-2 px-4 py-2.5 rounded-lg border border-zinc-200 dark:border-zinc-800 bg-white hover:bg-zinc-50 dark:bg-zinc-900 dark:hover:bg-zinc-850 text-zinc-700 dark:text-zinc-300 text-xs font-medium transition-colors shadow-2xs cursor-pointer text-center"
          >
            <span>Mavjud tariflarni ko'rish</span>
          </a>
        </div>
      </div>

      <!-- Hero Trust Ribbon -->
      <div class="grid grid-cols-1 sm:grid-cols-3 gap-3 sm:gap-4 pt-6 sm:pt-10 mt-6 sm:mt-10 border-t border-zinc-200/80 dark:border-zinc-850">
        <div class="flex items-start gap-3">
          <div class="w-8 h-8 rounded-lg bg-zinc-100 dark:bg-zinc-850 flex items-center justify-center text-zinc-800 dark:text-zinc-200 shrink-0 border border-zinc-200/60 dark:border-zinc-800">
            <ShieldCheck class="w-4 h-4 text-emerald-500" />
          </div>
          <div>
            <div class="text-xs font-semibold text-zinc-900 dark:text-zinc-100">100% Qonuniy Asosda</div>
            <div class="text-[11px] text-zinc-500 leading-normal mt-0.5">O'zR Fuqarolik kodeksi talablariga muvofiq</div>
          </div>
        </div>

        <div class="flex items-start gap-3">
          <div class="w-8 h-8 rounded-lg bg-zinc-100 dark:bg-zinc-850 flex items-center justify-center text-zinc-800 dark:text-zinc-200 shrink-0 border border-zinc-200/60 dark:border-zinc-800">
            <FileCheck class="w-4 h-4 text-zinc-600 dark:text-zinc-300" />
          </div>
          <div>
            <div class="text-xs font-semibold text-zinc-900 dark:text-zinc-100">O'zgarmas Snapshot</div>
            <div class="text-[11px] text-zinc-500 leading-normal mt-0.5">Shartnoma matni va tarif narxlari qat'iy kafolatlangan</div>
          </div>
        </div>

        <div class="flex items-start gap-3">
          <div class="w-8 h-8 rounded-lg bg-zinc-100 dark:bg-zinc-850 flex items-center justify-center text-zinc-800 dark:text-zinc-200 shrink-0 border border-zinc-200/60 dark:border-zinc-800">
            <CheckCircle2 class="w-4 h-4 text-zinc-600 dark:text-zinc-300" />
          </div>
          <div>
            <div class="text-xs font-semibold text-zinc-900 dark:text-zinc-100">Tezkor Tasdiqlash</div>
            <div class="text-[11px] text-zinc-500 leading-normal mt-0.5">Agentlik tasdiq kodi orqali haqiqiylikni tekshirish</div>
          </div>
        </div>
      </div>
    </section>

    <!-- 1. Tariffs Catalog Section (Mobile Optimized) -->
    <section id="tariffs-section" class="scroll-mt-20 py-10 sm:py-12 border-b border-zinc-200/80 dark:border-zinc-800/80">
      <!-- Section Header with Integrated Compact Search Filter -->
      <div class="flex flex-col sm:flex-row sm:items-end justify-between gap-4 mb-6 sm:mb-8">
        <div>
          <div class="text-[10px] sm:text-[11px] font-mono uppercase tracking-wider text-zinc-400 mb-1">
            Xizmatlar Katalogi
          </div>
          <h2 class="text-lg sm:text-2xl font-bold tracking-tight text-zinc-900 dark:text-zinc-100">
            Mavjud Tariflar va Namunaviy Shartnomalar
          </h2>
          <p class="text-xs text-zinc-500 dark:text-zinc-400 mt-0.5">
            Kerakli tarif bo'yicha shartnomani bir zumda PDF formatida yuklab oling.
          </p>
        </div>

        <!-- Mobile-first integrated search input with count badge -->
        <div class="relative w-full sm:w-72">
          <Search class="w-3.5 h-3.5 text-zinc-400 absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            v-model="searchQuery"
            type="text"
            placeholder="Tarif qidirish..."
            class="w-full pl-8 pr-16 py-2 text-xs rounded-lg border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-900 text-zinc-900 dark:text-zinc-100 placeholder:text-zinc-400 focus:outline-hidden focus:border-zinc-400 dark:focus:border-zinc-600 transition-colors shadow-2xs"
          />
          <span class="absolute right-2.5 top-1/2 -translate-y-1/2 text-[10px] font-mono text-zinc-500 dark:text-zinc-400 bg-zinc-100 dark:bg-zinc-800 px-1.5 py-0.5 rounded border border-zinc-200/60 dark:border-zinc-700/60">
            {{ filteredTariffs.length }} ta
          </span>
        </div>
      </div>

      <!-- Tariffs Grid -->
      <div v-if="filteredTariffs.length > 0" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 sm:gap-5">
        <div
          v-for="(tariff, tariffIdx) in filteredTariffs"
          :key="tariff.id"
          v-reveal="Math.min(tariffIdx, 6) * 40"
          class="group relative bg-white dark:bg-zinc-900/40 border border-zinc-200/80 dark:border-zinc-800/80 hover:border-zinc-400 dark:hover:border-zinc-600 rounded-xl p-5 sm:p-6 transition-all duration-200 flex flex-col justify-between shadow-2xs hover:shadow-xs"
        >
          <div>
            <!-- Card Meta Row -->
            <div class="flex items-center justify-between gap-2 mb-2.5">
              <span class="text-[10px] font-mono font-medium uppercase tracking-wider px-2 py-0.5 rounded-md bg-zinc-100 dark:bg-zinc-800 text-zinc-600 dark:text-zinc-400 border border-zinc-200/60 dark:border-zinc-700/60">
                Konsalting
              </span>
              <span class="text-[10.5px] font-mono text-zinc-400">
                PDF • Namunaviy
              </span>
            </div>

            <!-- Tariff Title -->
            <h3 class="text-base font-semibold text-zinc-900 dark:text-zinc-100 mb-1 tracking-tight group-hover:text-black dark:group-hover:text-white transition-colors">
              {{ tariff.name }}
            </h3>

            <!-- Description -->
            <p class="text-xs text-zinc-500 dark:text-zinc-400 line-clamp-2 leading-relaxed mb-5">
              {{ tariff.name }} dasturi bo'yicha konsalting xizmati va rasmiy shartnoma shartlari to'plami.
            </p>
          </div>

          <div>
            <!-- Price Display -->
            <div class="pt-3.5 border-t border-zinc-100 dark:border-zinc-850 mb-3.5 flex items-baseline justify-between">
              <span class="text-[11px] font-mono uppercase text-zinc-400 tracking-wider">
                Shartnoma to'lovi
              </span>
              <span class="text-lg font-bold tracking-tight text-zinc-900 dark:text-zinc-50 font-mono">
                {{ formatPrice(tariff.price) }}
              </span>
            </div>

            <!-- Single Minimal Action Button: Shartnomani yuklab olish -->
            <button
              type="button"
              @click="handleDownloadSamplePdf(tariff)"
              :disabled="downloadingTariffId === String(tariff.id)"
              class="w-full inline-flex items-center justify-center gap-2 px-3.5 py-2.5 rounded-lg border border-zinc-200 dark:border-zinc-700 bg-zinc-50 hover:bg-zinc-100 dark:bg-zinc-800/80 dark:hover:bg-zinc-800 text-xs font-medium text-zinc-900 dark:text-zinc-100 transition-all cursor-pointer active:scale-98 shadow-2xs disabled:opacity-60"
            >
              <!-- Loading state -->
              <template v-if="downloadingTariffId === String(tariff.id)">
                <Loader2 class="w-3.5 h-3.5 animate-spin text-zinc-900 dark:text-white" />
                <span>PDF tayyorlanmoqda...</span>
              </template>

              <!-- Success state -->
              <template v-else-if="downloadSuccessTariffId === String(tariff.id)">
                <Check class="w-3.5 h-3.5 text-emerald-500" />
                <span class="text-emerald-600 dark:text-emerald-400 font-semibold">Yuklab olindi ✓</span>
              </template>

              <!-- Idle download state -->
              <template v-else>
                <Download class="w-3.5 h-3.5 text-zinc-500 group-hover:text-zinc-900 dark:group-hover:text-white transition-colors" />
                <span>Shartnomani yuklab olish</span>
              </template>
            </button>

            <!-- Subtle secondary action for signing online -->
            <div class="mt-2 flex items-center justify-between text-[11px] text-zinc-400 px-1">
              <button
                type="button"
                @click="handleViewContract(tariff)"
                :disabled="isLoadingPreview === String(tariff.id)"
                class="hover:text-zinc-700 dark:hover:text-zinc-200 transition-colors cursor-pointer flex items-center gap-1 py-1 disabled:opacity-60"
              >
                <Loader2 v-if="isLoadingPreview === String(tariff.id)" class="w-3 h-3 animate-spin" />
                <Eye v-else class="w-3 h-3" />
                <span>Ko'rish</span>
              </button>

              <button
                type="button"
                @click="handleSelectTariffToSign(tariff)"
                class="hover:text-zinc-900 dark:hover:text-zinc-100 transition-colors cursor-pointer font-medium py-1"
              >
                Onlayn imzolash →
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- Empty Search State -->
      <div v-else class="text-center py-12 sm:py-16 border border-dashed border-zinc-200 dark:border-zinc-800 rounded-xl bg-zinc-50/50 dark:bg-zinc-900/20">
        <Layers class="w-7 h-7 text-zinc-300 dark:text-zinc-700 mx-auto mb-2" />
        <p class="text-xs font-semibold text-zinc-700 dark:text-zinc-300">
          "{{ searchQuery }}" bo'yicha hech qanday tarif topilmadi
        </p>
        <button
          type="button"
          @click="searchQuery = ''"
          class="mt-2.5 text-xs text-zinc-500 hover:text-zinc-900 dark:hover:text-white underline cursor-pointer"
        >
          Qidiruvni tozalash
        </button>
      </div>
    </section>

    <!-- 2. Process Guide Section (Mobile Optimized) -->
    <section id="process-section" class="scroll-mt-20 py-10 sm:py-12 border-b border-zinc-200/80 dark:border-zinc-800/80">
      <div class="mb-6 sm:mb-8">
        <div class="text-[10px] sm:text-[11px] font-mono uppercase tracking-wider text-zinc-400 mb-1">
          Bosqichlar
        </div>
        <h2 class="text-lg sm:text-2xl font-bold tracking-tight text-zinc-900 dark:text-zinc-100">
          Onlayn shartnoma qanday ishlaydi?
        </h2>
        <p class="text-xs text-zinc-500 dark:text-zinc-400 mt-0.5">
          Atigi 3 ta oddiy qadam orqali rasmiy va qonuniy shartnomaga ega bo'ling.
        </p>
      </div>

      <div class="grid grid-cols-1 md:grid-cols-3 gap-3.5 sm:gap-6">
        <!-- Step 1 -->
        <div v-reveal="0" class="p-4 sm:p-5 rounded-xl border border-zinc-200/80 dark:border-zinc-800/80 bg-white dark:bg-zinc-900/40">
          <div class="font-mono text-xs font-bold text-zinc-400 mb-2 sm:mb-3">01</div>
          <h3 class="text-sm font-semibold text-zinc-900 dark:text-zinc-100 mb-1 sm:mb-1.5">
            Shartnomani tanlang va yuklab oling
          </h3>
          <p class="text-xs text-zinc-500 dark:text-zinc-400 leading-relaxed">
            Mavjud tariflar ro'yxatidan o'zingizga mos yo'nalishni tanlang, shartlari bilan tanishing va namunaviy PDF nusxasini oling.
          </p>
        </div>

        <!-- Step 2 -->
        <div v-reveal="60" class="p-4 sm:p-5 rounded-xl border border-zinc-200/80 dark:border-zinc-800/80 bg-white dark:bg-zinc-900/40">
          <div class="font-mono text-xs font-bold text-zinc-400 mb-2 sm:mb-3">02</div>
          <h3 class="text-sm font-semibold text-zinc-900 dark:text-zinc-100 mb-1 sm:mb-1.5">
            Ma'lumotlarni onlayn kiriting
          </h3>
          <p class="text-xs text-zinc-500 dark:text-zinc-400 leading-relaxed">
            Pasport va shaxsiy ma'lumotlaringizni xavfsiz shaklda to'ldiring hamda rasmiy tasdiqlash uchun yuboring.
          </p>
        </div>

        <!-- Step 3 -->
        <div v-reveal="120" class="p-4 sm:p-5 rounded-xl border border-zinc-200/80 dark:border-zinc-800/80 bg-white dark:bg-zinc-900/40">
          <div class="font-mono text-xs font-bold text-zinc-400 mb-2 sm:mb-3">03</div>
          <h3 class="text-sm font-semibold text-zinc-900 dark:text-zinc-100 mb-1 sm:mb-1.5">
            Elektron imzolang va tasdiqlang
          </h3>
          <p class="text-xs text-zinc-500 dark:text-zinc-400 leading-relaxed">
            Ekran orqali elektron imzo cheking, agentlik tasdiq kodi orqali tasdiqlang va yakuniy rasmiy PDF shartnomani qabul qiling.
          </p>
        </div>
      </div>
    </section>

    <!-- 3. Dedicated Security & Legal Compliance Section (Mobile Optimized) -->
    <section id="security-section" class="scroll-mt-20 py-10 sm:py-14 border-b border-zinc-200/80 dark:border-zinc-800/80">
      <div class="mb-6 sm:mb-10">
        <div class="inline-flex items-center gap-1.5 sm:gap-2 px-2.5 py-1 rounded-full border border-emerald-500/20 bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 text-[10.5px] sm:text-xs font-mono mb-2.5 sm:mb-3">
          <ShieldCheck class="w-3.5 h-3.5" />
          <span>Yuridik Kafolat va Himoya</span>
        </div>
        <h2 class="text-lg sm:text-3xl font-bold tracking-tight text-zinc-900 dark:text-zinc-100">
          100% Qonuniy Asosda va Kriptografik Himoyalangan Shartnomalar
        </h2>
        <p class="text-xs sm:text-sm text-zinc-500 dark:text-zinc-400 mt-1 sm:mt-2 max-w-2xl leading-relaxed">
          Ushbu portal orqali tuzilgan har bir onlayn shartnoma O'zbekiston Respublikasining amaldagi qonunchiligi asosida rasmiylashtiriladi va qog'oz shaklidagi muhrlangan shartnoma bilan to'liq teng yuridik kuchga ega.
        </p>
      </div>

      <!-- 4 Pillars Grid -->
      <div class="grid grid-cols-1 md:grid-cols-2 gap-3.5 sm:gap-5 mb-6 sm:mb-8">
        <!-- Pillar 1 -->
        <div v-reveal="0" class="p-4 sm:p-6 rounded-xl border border-zinc-200/80 dark:border-zinc-800/80 bg-white dark:bg-zinc-900/40">
          <div class="flex items-center justify-between mb-3 sm:mb-4">
            <div class="w-8 sm:w-9 h-8 sm:h-9 rounded-lg bg-zinc-100 dark:bg-zinc-850 flex items-center justify-center text-zinc-900 dark:text-zinc-100 border border-zinc-200/60 dark:border-zinc-800">
              <Scale class="w-4 h-4" />
            </div>
            <span class="text-[10px] font-mono px-2 py-0.5 rounded-md bg-zinc-100 dark:bg-zinc-800 text-zinc-600 dark:text-zinc-400 border border-zinc-200/60 dark:border-zinc-700/60">
              O'zR Qonunchiligi
            </span>
          </div>
          <h3 class="text-sm font-semibold text-zinc-900 dark:text-zinc-100 mb-1.5 sm:mb-2">
            To'liq Teng Yuridik Kuch
          </h3>
          <p class="text-xs text-zinc-500 dark:text-zinc-400 leading-relaxed">
            O'zbekiston Respublikasining <strong>«Elektron raqamli imzo to'g'risida»</strong> (O'RQ-793) va <strong>«Elektron hujjat aylanishi to'g'risida»</strong> (O'RQ-936)gi Qonunlariga to'liq asosan, portalda tasdiqlangan elektron shartnoma qog'ozdagi shartnoma bilan bir xil yuridik oqibatlarni keltirib chiqaradi.
          </p>
        </div>

        <!-- Pillar 2 -->
        <div v-reveal="60" class="p-4 sm:p-6 rounded-xl border border-zinc-200/80 dark:border-zinc-800/80 bg-white dark:bg-zinc-900/40">
          <div class="flex items-center justify-between mb-3 sm:mb-4">
            <div class="w-8 sm:w-9 h-8 sm:h-9 rounded-lg bg-zinc-100 dark:bg-zinc-850 flex items-center justify-center text-zinc-900 dark:text-zinc-100 border border-zinc-200/60 dark:border-zinc-800">
              <Lock class="w-4 h-4" />
            </div>
            <span class="text-[10px] font-mono px-2 py-0.5 rounded-md bg-zinc-100 dark:bg-zinc-800 text-zinc-600 dark:text-zinc-400 border border-zinc-200/60 dark:border-zinc-700/60">
              SHA-256 Snapshot
            </span>
          </div>
          <h3 class="text-sm font-semibold text-zinc-900 dark:text-zinc-100 mb-1.5 sm:mb-2">
            O'zgarmas Kriptografik Himoya
          </h3>
          <p class="text-xs text-zinc-500 dark:text-zinc-400 leading-relaxed">
            Shartnoma imzolangach, uning to'liq matni, narxi va shartlari o'zgarmas «Snapshot» holatiga o'tkazilib, kriptografik xesh bilan muhrlanadi. Hech kim uni keyinchalik bir tomonlama o'zgartira olmaydi.
          </p>
        </div>

        <!-- Pillar 3 -->
        <div v-reveal="120" class="p-4 sm:p-6 rounded-xl border border-zinc-200/80 dark:border-zinc-800/80 bg-white dark:bg-zinc-900/40">
          <div class="flex items-center justify-between mb-3 sm:mb-4">
            <div class="w-8 sm:w-9 h-8 sm:h-9 rounded-lg bg-zinc-100 dark:bg-zinc-850 flex items-center justify-center text-zinc-900 dark:text-zinc-100 border border-zinc-200/60 dark:border-zinc-800">
              <QrCode class="w-4 h-4" />
            </div>
            <span class="text-[10px] font-mono px-2 py-0.5 rounded-md bg-zinc-100 dark:bg-zinc-800 text-zinc-600 dark:text-zinc-400 border border-zinc-200/60 dark:border-zinc-700/60">
              QR-Kodli Verifikatsiya
            </span>
          </div>
          <h3 class="text-sm font-semibold text-zinc-900 dark:text-zinc-100 mb-1.5 sm:mb-2">
            Tezkor QR-Kod Orqali Tasdiqlash
          </h3>
          <p class="text-xs text-zinc-500 dark:text-zinc-400 leading-relaxed">
            Yuklab olingan har bir rasmiy PDF shartnomada noyob raqamli QR-kod mavjud. Elchixonalar, banklar, xorijiy universitetlar hujjatning asl holatini bir lahzada tekshirishi mumkin.
          </p>
        </div>

        <!-- Pillar 4 -->
        <div v-reveal="180" class="p-4 sm:p-6 rounded-xl border border-zinc-200/80 dark:border-zinc-800/80 bg-white dark:bg-zinc-900/40">
          <div class="flex items-center justify-between mb-3 sm:mb-4">
            <div class="w-8 sm:w-9 h-8 sm:h-9 rounded-lg bg-zinc-100 dark:bg-zinc-850 flex items-center justify-center text-zinc-900 dark:text-zinc-100 border border-zinc-200/60 dark:border-zinc-800">
              <KeyRound class="w-4 h-4" />
            </div>
            <span class="text-[10px] font-mono px-2 py-0.5 rounded-md bg-zinc-100 dark:bg-zinc-800 text-zinc-600 dark:text-zinc-400 border border-zinc-200/60 dark:border-zinc-700/60">
              Ikki Bosqichli Tasdiq
            </span>
          </div>
          <h3 class="text-sm font-semibold text-zinc-900 dark:text-zinc-100 mb-1.5 sm:mb-2">
            Shaxsiy Tasdiqlash Kodi
          </h3>
          <p class="text-xs text-zinc-500 dark:text-zinc-400 leading-relaxed">
            Soxtalashtirishlarning oldini olish maqsadida har bir shartnoma konsalting kompaniyasi bergan bir martalik tasdiqlash kodi va shaxsiy parol orqali qat'iy verifikatsiya qilinadi.
          </p>
        </div>
      </div>

      <!-- Verification Quick Check Box (Mobile Optimized) -->
      <div class="p-4 sm:p-6 rounded-xl border border-zinc-200/80 dark:border-zinc-800/80 bg-zinc-50/50 dark:bg-zinc-900/20 flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3 sm:gap-4">
        <div class="max-w-xl">
          <div class="text-xs font-semibold text-zinc-900 dark:text-zinc-100 flex items-center gap-2 mb-1">
            <FileCheck2 class="w-4 h-4 text-emerald-500 shrink-0" />
            <span>Shartnoma haqiqiyligini tekshirish</span>
          </div>
          <p class="text-[11px] text-zinc-500 leading-relaxed">
            Agar sizda avval tuzilgan shartnoma raqami yoki tasdiqlash kodi bo'lsa, uning rasmiy holati va haqiqiyligini tekshirishingiz mumkin.
          </p>
        </div>

        <router-link
          :to="{ name: 'online-sign-in', params: { tenantname: tenantSlug } }"
          class="shrink-0 inline-flex items-center justify-center gap-1.5 px-3.5 py-2.5 sm:py-2 rounded-lg border border-zinc-300 dark:border-zinc-700 bg-white hover:bg-zinc-100 dark:bg-zinc-800 dark:hover:bg-zinc-750 text-xs font-medium text-zinc-800 dark:text-zinc-200 transition-colors shadow-2xs text-center"
        >
          <KeyRound class="w-3.5 h-3.5 text-zinc-400" />
          <span>Shartnomani tekshirish</span>
        </router-link>
      </div>
    </section>

    <!-- 4. Company Offices / Filiallar Section (Mobile Optimized) -->
    <section id="offices-section" class="scroll-mt-20 py-10 sm:py-12">
      <div class="mb-5 sm:mb-6">
        <div class="text-[10px] sm:text-[11px] font-mono uppercase tracking-wider text-zinc-400 mb-1">
          Manzillar
        </div>
        <h2 class="text-lg sm:text-xl font-bold tracking-tight text-zinc-900 dark:text-zinc-100">
          Rasmiy Filiallar va Qabul Ofislari
        </h2>
      </div>

      <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3 sm:gap-4">
        <div
          v-for="(office, officeIdx) in tenantInfo?.offices || []"
          :key="office.id"
          v-reveal="Math.min(officeIdx, 6) * 40"
          class="p-3.5 sm:p-4 rounded-xl bg-white dark:bg-zinc-900/40 border border-zinc-200/80 dark:border-zinc-800/80 flex items-center gap-3 shadow-2xs"
        >
          <div class="w-8 h-8 rounded-lg bg-zinc-100 dark:bg-zinc-850 border border-zinc-200/60 dark:border-zinc-800 text-zinc-700 dark:text-zinc-300 flex items-center justify-center shrink-0">
            <MapPin class="w-4 h-4" />
          </div>
          <div class="min-w-0">
            <div class="text-xs font-semibold text-zinc-900 dark:text-zinc-100 truncate">
              {{ office.name }}
            </div>
            <div class="text-[11px] text-zinc-400 truncate">
              Rasmiy maslahat va qabul markazi
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- Full Contract Viewer Modal (for previewing) -->
    <FullContractViewerModal
      :is-open="isPreviewModalOpen"
      :contract-title="previewContractTitle"
      :content="previewContractContent"
      read-only
      @close="isPreviewModalOpen = false"
    />
  </OnlineContractLayout>
  </Transition>
</template>

<style scoped>
.page-fade-enter-active,
.page-fade-leave-active {
  transition: opacity 0.2s ease;
}
.page-fade-enter-from,
.page-fade-leave-to {
  opacity: 0;
}
</style>
