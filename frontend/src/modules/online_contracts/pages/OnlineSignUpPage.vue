<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { onlineContractsApi } from '@/api/onlineContracts'
import {
  Mail,
  Lock,
  KeyRound,
  ArrowRight,
  ArrowLeft,
  Loader2,
  CheckCircle2,
  AlertCircle,
  Clock,
  Eye,
  EyeOff,
} from 'lucide-vue-next'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()

onMounted(() => {
  if (authStore.isAuthenticated && authStore.user?.role === 'STUDENT') {
    const pendingTariffId = sessionStorage.getItem('selected_tariff_id')
    if (pendingTariffId) {
      router.replace({
        name: 'online-contract-sign',
        params: { tenantname: tenantSlug.value },
        query: { tariffId: pendingTariffId },
      })
    } else {
      router.replace({
        name: 'online-profile',
        params: { tenantname: tenantSlug.value },
      })
    }
  }
})

const tenantSlug = computed(() => (route.params.tenantname as string) || '')

const email = ref('')
const password = ref('')
const confirmPassword = ref('')
const showPassword = ref(false)
const showConfirmPassword = ref(false)
const otpCode = ref('')

const isOtpSent = ref(false)
const isSendingOtp = ref(false)
const isVerifying = ref(false)
const errorMessage = ref('')
const successMessage = ref('')
const countdown = ref(0)
let timerInterval: any = null

function startCountdown(seconds: number = 600) {
  countdown.value = seconds
  if (timerInterval) clearInterval(timerInterval)
  timerInterval = setInterval(() => {
    if (countdown.value > 0) {
      countdown.value--
    } else {
      clearInterval(timerInterval)
    }
  }, 1000)
}

const formattedCountdown = computed(() => {
  const m = Math.floor(countdown.value / 60)
  const s = countdown.value % 60
  return `${m}:${s.toString().padStart(2, '0')}`
})

async function handleSendOtp() {
  errorMessage.value = ''
  successMessage.value = ''

  if (!email.value || !email.value.includes('@')) {
    errorMessage.value = "Iltimos, to'g'ri email manzilini kiriting."
    return
  }

  if (!password.value || password.value.length < 6) {
    errorMessage.value = "Parol kamida 6 ta belgidan iborat bo'lishi kerak."
    return
  }

  if (password.value !== confirmPassword.value) {
    errorMessage.value = "Kiritilgan parollar bir-biriga mos kelmadi."
    return
  }

  isSendingOtp.value = true
  try {
    const res = await onlineContractsApi.sendOtp(email.value, tenantSlug.value)
    isOtpSent.value = true
    successMessage.value = `Tasdiqlash kodi ${email.value} manziliga yuborildi.`
    startCountdown(res.expires_in_seconds || 600)
  } catch (err: any) {
    errorMessage.value = err?.response?.data?.detail || "Kodni yuborishda xatolik yuz berdi. Qayta urinib ko'ring."
  } finally {
    isSendingOtp.value = false
  }
}

async function handleVerifyAndRegister() {
  errorMessage.value = ''
  if (!otpCode.value || otpCode.value.length < 6) {
    errorMessage.value = 'Iltimos, 6 xonali tasdiqlash kodini to\'liq kiriting.'
    return
  }

  isVerifying.value = true
  try {
    const data = await onlineContractsApi.signUp({
      email: email.value,
      password: password.value,
      code: otpCode.value.trim().toUpperCase(),
      tenant_slug: tenantSlug.value,
    })

    // Save tokens and user session
    localStorage.setItem('access_token', data.access)
    localStorage.setItem('refresh_token', data.refresh)
    localStorage.setItem('user_profile', JSON.stringify(data.user))
    if (data.user?.tenant?.id) {
      localStorage.setItem('active_tenant_id', data.user.tenant.id)
    }

    // Update pinia auth store
    authStore.token = data.access
    authStore.user = data.user as any

    successMessage.value = 'Muvaffaqiyatli ro\'yxatdan o\'tdingiz!'

    // Redirect to pending contract signing if tariff was selected from landing page
    setTimeout(() => {
      const pendingTariffId = sessionStorage.getItem('selected_tariff_id')
      if (pendingTariffId) {
        router.push({
          name: 'online-contract-sign',
          params: { tenantname: tenantSlug.value },
          query: { tariffId: pendingTariffId },
        })
      } else {
        router.push({
          name: 'online-profile',
          params: { tenantname: tenantSlug.value },
        })
      }
    }, 1000)
  } catch (err: any) {
    errorMessage.value = err?.response?.data?.detail || "Tasdiqlashda xatolik. Kod noto'g'ri yoki muddati o'tgan."
  } finally {
    isVerifying.value = false
  }
}
</script>

<template>
  <div class="min-h-screen flex flex-col items-center justify-center bg-[#fafafa] dark:bg-[#09090b] text-zinc-900 dark:text-zinc-100 p-4 selection:bg-zinc-900 selection:text-white dark:selection:bg-white dark:selection:text-zinc-900">
    <!-- Back to landing breadcrumb -->
    <div class="max-w-md w-full mb-4">
      <router-link
        :to="{ name: 'online-landing', params: { tenantname: tenantSlug } }"
        class="inline-flex items-center gap-1.5 text-xs font-mono text-zinc-500 hover:text-zinc-900 dark:hover:text-zinc-100 transition-colors"
      >
        <ArrowLeft class="w-3.5 h-3.5" />
        <span>{{ tenantSlug.toUpperCase() }} shartnomalariga qaytish</span>
      </router-link>
    </div>

    <!-- Minimalist Resend-style card -->
    <div class="max-w-md w-full bg-white dark:bg-zinc-900/60 border border-zinc-200/80 dark:border-zinc-800 rounded-xl p-8 shadow-xs">
      <!-- Header -->
      <div class="mb-6">
        <h1 class="text-xl font-semibold tracking-tight text-zinc-900 dark:text-zinc-100">
          Onlayn shartnoma tuzish
        </h1>
        <p class="text-xs text-zinc-500 dark:text-zinc-400 mt-1.5 leading-relaxed">
          Shartnoma imzolash uchun profilingizni yarating.
        </p>
      </div>

      <!-- Error / Success Alerts -->
      <div
        v-if="errorMessage"
        class="mb-4 p-3 rounded-lg bg-red-50 dark:bg-red-950/40 border border-red-200 dark:border-red-900/60 text-xs text-red-700 dark:text-red-300 flex items-start gap-2"
      >
        <AlertCircle class="w-4 h-4 shrink-0 mt-0.5 text-red-500" />
        <span>{{ errorMessage }}</span>
      </div>

      <div
        v-if="successMessage"
        class="mb-4 p-3 rounded-lg bg-emerald-50 dark:bg-emerald-950/40 border border-emerald-200 dark:border-emerald-900/60 text-xs text-emerald-700 dark:text-emerald-300 flex items-start gap-2"
      >
        <CheckCircle2 class="w-4 h-4 shrink-0 mt-0.5 text-emerald-500" />
        <span>{{ successMessage }}</span>
      </div>

      <!-- Step 1: Email & Password -->
      <form v-if="!isOtpSent" @submit.prevent="handleSendOtp" class="space-y-4">
        <div>
          <label class="block text-xs font-medium text-zinc-700 dark:text-zinc-300 mb-1.5">
            Email manzilingiz
          </label>
          <div class="relative">
            <Mail class="w-3.5 h-3.5 text-zinc-400 absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              v-model="email"
              type="email"
              required
              placeholder="talaba@example.com"
              class="w-full pl-9 pr-3 py-2 rounded-lg border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-950 text-xs text-zinc-900 dark:text-zinc-100 placeholder:text-zinc-400 focus:outline-hidden focus:border-zinc-400 dark:focus:border-zinc-600 transition-colors"
            />
          </div>
        </div>

        <div>
          <label class="block text-xs font-medium text-zinc-700 dark:text-zinc-300 mb-1.5">
            Parol yarating
          </label>
          <div class="relative">
            <Lock class="w-3.5 h-3.5 text-zinc-400 absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              v-model="password"
              :type="showPassword ? 'text' : 'password'"
              required
              minlength="6"
              placeholder="Kamida 6 ta belgi"
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

        <div>
          <label class="block text-xs font-medium text-zinc-700 dark:text-zinc-300 mb-1.5">
            Parolni tasdiqlang
          </label>
          <div class="relative">
            <Lock class="w-3.5 h-3.5 text-zinc-400 absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              v-model="confirmPassword"
              :type="showConfirmPassword ? 'text' : 'password'"
              required
              minlength="6"
              placeholder="Parolni qayta kiriting"
              class="w-full pl-9 pr-9 py-2 rounded-lg border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-950 text-xs text-zinc-900 dark:text-zinc-100 placeholder:text-zinc-400 focus:outline-hidden focus:border-zinc-400 dark:focus:border-zinc-600 transition-colors"
            />
            <button
              type="button"
              @click="showConfirmPassword = !showConfirmPassword"
              class="absolute right-3 top-1/2 -translate-y-1/2 text-zinc-400 hover:text-zinc-600 dark:hover:text-zinc-300 transition-colors cursor-pointer"
              tabindex="-1"
              :title="showConfirmPassword ? 'Parolni yashirish' : 'Parolni ko\'rsatish'"
            >
              <EyeOff v-if="showConfirmPassword" class="w-3.5 h-3.5" />
              <Eye v-else class="w-3.5 h-3.5" />
            </button>
          </div>
        </div>

        <button
          type="submit"
          :disabled="isSendingOtp"
          class="w-full inline-flex items-center justify-center gap-2 py-2.5 px-4 rounded-lg bg-zinc-900 hover:bg-zinc-800 text-white dark:bg-zinc-100 dark:hover:bg-white dark:text-zinc-950 text-xs font-medium transition-all cursor-pointer disabled:opacity-50 active:scale-98 shadow-xs"
        >
          <Loader2 v-if="isSendingOtp" class="w-3.5 h-3.5 animate-spin" />
          <span v-else>Tasdiqlash kodini yuborish</span>
          <ArrowRight v-if="!isSendingOtp" class="w-3.5 h-3.5" />
        </button>
      </form>

      <!-- Step 2: Enter Email Verification OTP -->
      <form v-else @submit.prevent="handleVerifyAndRegister" class="space-y-4 animate-in fade-in">
        <div class="p-3 bg-zinc-50 dark:bg-zinc-850/60 border border-zinc-200 dark:border-zinc-800 rounded-lg text-xs text-zinc-700 dark:text-zinc-300 flex items-center justify-between">
          <span>Kod yuborildi: <strong>{{ email }}</strong></span>
          <button
            type="button"
            @click="isOtpSent = false"
            class="text-[11px] underline font-medium text-zinc-900 dark:text-white hover:text-zinc-600"
          >
            O'zgartirish
          </button>
        </div>

        <div>
          <div class="flex items-center justify-between mb-1.5">
            <label class="text-xs font-medium text-zinc-700 dark:text-zinc-300">
              Email Tasdiqlash Kodi
            </label>
            <span v-if="countdown > 0" class="text-[11px] font-mono text-zinc-500 flex items-center gap-1">
              <Clock class="w-3 h-3 text-amber-500" />
              <span>{{ formattedCountdown }}</span>
            </span>
          </div>

          <div class="relative">
            <KeyRound class="w-3.5 h-3.5 text-zinc-400 absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              v-model="otpCode"
              type="text"
              required
              maxlength="6"
              placeholder="6 xonali kod"
              class="w-full pl-9 pr-3 py-2 rounded-lg border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-950 text-xs font-mono tracking-widest text-center text-zinc-900 dark:text-zinc-100 focus:outline-hidden focus:border-zinc-400 dark:focus:border-zinc-600 transition-colors uppercase"
            />
          </div>
        </div>

        <button
          type="submit"
          :disabled="isVerifying"
          class="w-full inline-flex items-center justify-center gap-2 py-2.5 px-4 rounded-lg bg-zinc-900 hover:bg-zinc-800 text-white dark:bg-zinc-100 dark:hover:bg-white dark:text-zinc-950 text-xs font-medium transition-all cursor-pointer disabled:opacity-50 active:scale-98 shadow-xs"
        >
          <Loader2 v-if="isVerifying" class="w-3.5 h-3.5 animate-spin" />
          <span v-else>Emailni tasdiqlash va profilga kirish</span>
        </button>

        <div class="text-center pt-2">
          <button
            type="button"
            @click="handleSendOtp"
            :disabled="countdown > 540 || isSendingOtp"
            class="text-xs text-zinc-500 hover:text-zinc-900 dark:hover:text-zinc-100 font-medium transition-colors disabled:opacity-50"
          >
            Kodni qayta yuborish
          </button>
        </div>
      </form>

      <!-- Bottom link to Sign In -->
      <div class="mt-6 pt-5 border-t border-zinc-100 dark:border-zinc-850 text-center text-xs text-zinc-500">
        <span>Hisobingiz bormi? </span>
        <router-link
          :to="{ name: 'online-sign-in', params: { tenantname: tenantSlug } }"
          class="font-medium text-zinc-900 dark:text-zinc-100 hover:underline"
        >
          Tizimga kirish
        </router-link>
      </div>
    </div>
  </div>
</template>
