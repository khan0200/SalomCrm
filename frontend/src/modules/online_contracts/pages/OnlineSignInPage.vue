<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { onlineContractsApi } from '@/api/onlineContracts'
import { Mail, Lock, LogIn, Loader2, AlertCircle, ArrowLeft } from 'lucide-vue-next'

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
const isLoading = ref(false)
const errorMessage = ref('')

async function handleSignIn() {
  errorMessage.value = ''
  if (!email.value || !password.value) {
    errorMessage.value = 'Email va parolni kiriting.'
    return
  }

  isLoading.value = true
  try {
    const data = await onlineContractsApi.signIn({
      email: email.value,
      password: password.value,
      tenant_slug: tenantSlug.value,
    })

    // Store auth session
    localStorage.setItem('access_token', data.access)
    localStorage.setItem('refresh_token', data.refresh)
    localStorage.setItem('user_profile', JSON.stringify(data.user))
    if (data.user?.tenant?.id) {
      localStorage.setItem('active_tenant_id', data.user.tenant.id)
    }

    // Update store
    authStore.token = data.access
    authStore.user = data.user as any

    // Check if user was in the middle of signing a specific tariff
    const pendingTariffId = sessionStorage.getItem('selected_tariff_id')
    if (pendingTariffId) {
      router.push({
        name: 'online-contract-sign',
        params: { tenantname: tenantSlug.value },
        query: { tariffId: pendingTariffId }
      })
    } else {
      router.push({ name: 'online-profile', params: { tenantname: tenantSlug.value } })
    }
  } catch (err: any) {
    errorMessage.value = err?.response?.data?.detail || 'Email yoki parol noto\'g\'ri kiritildi.'
  } finally {
    isLoading.value = false
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
          Tizimga kirish
        </h1>
      </div>

      <!-- Error alert -->
      <div
        v-if="errorMessage"
        class="mb-4 p-3 rounded-lg bg-red-50 dark:bg-red-950/40 border border-red-200 dark:border-red-900/60 text-xs text-red-700 dark:text-red-300 flex items-start gap-2"
      >
        <AlertCircle class="w-4 h-4 shrink-0 mt-0.5 text-red-500" />
        <span>{{ errorMessage }}</span>
      </div>

      <form @submit.prevent="handleSignIn" class="space-y-4">
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
          <div class="flex items-center justify-between mb-1.5">
            <label class="text-xs font-medium text-zinc-700 dark:text-zinc-300">
              Parolingiz
            </label>
            <router-link
              :to="{ name: 'online-sign-up', params: { tenantname: tenantSlug } }"
              class="text-[11px] text-zinc-500 hover:text-zinc-900 dark:hover:text-zinc-200 transition-colors"
            >
              Parolni unutdingizmi?
            </router-link>
          </div>
          <div class="relative">
            <Lock class="w-3.5 h-3.5 text-zinc-400 absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              v-model="password"
              type="password"
              required
              placeholder="Parolingizni kiriting"
              class="w-full pl-9 pr-3 py-2 rounded-lg border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-950 text-xs text-zinc-900 dark:text-zinc-100 placeholder:text-zinc-400 focus:outline-hidden focus:border-zinc-400 dark:focus:border-zinc-600 transition-colors"
            />
          </div>
        </div>

        <button
          type="submit"
          :disabled="isLoading"
          class="w-full inline-flex items-center justify-center gap-2 py-2.5 px-4 rounded-lg bg-zinc-900 hover:bg-zinc-800 text-white dark:bg-zinc-100 dark:hover:bg-white dark:text-zinc-950 text-xs font-medium transition-all cursor-pointer disabled:opacity-50 active:scale-98 shadow-xs"
        >
          <Loader2 v-if="isLoading" class="w-3.5 h-3.5 animate-spin" />
          <LogIn v-else class="w-3.5 h-3.5" />
          <span>Tizimga kirish</span>
        </button>
      </form>

      <!-- Bottom link to Sign Up -->
      <div class="mt-6 pt-5 border-t border-zinc-100 dark:border-zinc-850 text-center text-xs text-zinc-500">
        <span>Hisobingiz yo'qmi? </span>
        <router-link
          :to="{ name: 'online-sign-up', params: { tenantname: tenantSlug } }"
          class="font-medium text-zinc-900 dark:text-zinc-100 hover:underline"
        >
          Shartnoma tuzish
        </router-link>
      </div>
    </div>
  </div>
</template>
