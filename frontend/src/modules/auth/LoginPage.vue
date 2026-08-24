<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useUiStore } from '@/stores/ui'
import {
  Lock, Mail, ArrowRight, AlertCircle, Sun, Moon,
  Eye, EyeOff, ShieldCheck, Sparkles
} from 'lucide-vue-next'

const router = useRouter()
const authStore = useAuthStore()
const uiStore = useUiStore()

const email = ref('')
const password = ref('')
const showPassword = ref(false)
const rememberMe = ref(true)
const isLoading = ref(false)
const error = ref<string | null>(null)

const handleLogin = async () => {
  if (!email.value.trim() || !password.value) {
    error.value = 'Iltimos, email va parolni kiriting.'
    return
  }

  isLoading.value = true
  error.value = null
  try {
    await authStore.login({
      email: email.value.trim(),
      password: password.value
    })
    uiStore.addToast({
      type: 'success',
      title: 'Xush kelibsiz!',
      message: `Tizimga kirdingiz: ${authStore.user?.full_name || authStore.user?.email}`
    })
    router.push('/students')
  } catch (err: any) {
    error.value = err.response?.data?.detail || 'Email yoki parol noto\'g\'ri kiritildi.'
  } finally {
    isLoading.value = false
  }
}
</script>

<template>
  <div class="min-h-screen w-screen flex items-center justify-center p-4 bg-slate-50 dark:bg-[#0c0e12] select-none relative overflow-hidden font-sans">
    <!-- Ambient Background Gradients -->
    <div class="absolute -top-40 -left-40 w-96 h-96 bg-blue-500/15 dark:bg-blue-600/10 rounded-full blur-[120px] pointer-events-none" />
    <div class="absolute -bottom-40 -right-40 w-96 h-96 bg-emerald-500/15 dark:bg-emerald-600/10 rounded-full blur-[120px] pointer-events-none" />
    <div class="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] bg-indigo-500/5 dark:bg-indigo-500/5 rounded-full blur-[140px] pointer-events-none" />

    <!-- Subtle Dot Grid Background Pattern -->
    <div class="absolute inset-0 bg-[radial-gradient(#cbd5e1_1px,transparent_1px)] dark:bg-[radial-gradient(#1e293b_1px,transparent_1px)] [background-size:24px_24px] opacity-40 pointer-events-none" />

    <!-- Top Right Theme Toggle -->
    <div class="absolute top-6 right-6 z-20 flex items-center gap-2">
      <button
        @click="uiStore.toggleTheme"
        class="flex items-center gap-2 px-3 py-2 rounded-xl border border-slate-200/80 dark:border-zinc-800 bg-white/80 dark:bg-zinc-900/80 backdrop-blur-md text-slate-700 dark:text-zinc-300 shadow-xs hover:bg-slate-100 dark:hover:bg-zinc-800/80 transition-all cursor-pointer text-xs font-semibold"
        title="Mavzuni o'zgartirish"
      >
        <Sun v-if="uiStore.isDark" class="w-4 h-4 text-amber-400" />
        <Moon v-else class="w-4 h-4 text-slate-600" />
        <span>{{ uiStore.isDark ? 'Dark' : 'Light' }}</span>
      </button>
    </div>

    <!-- Login Card -->
    <div class="relative w-full max-w-[420px] bg-white/90 dark:bg-[#13161c]/90 backdrop-blur-xl border border-slate-200/80 dark:border-zinc-800/80 rounded-3xl shadow-2xl shadow-slate-200/50 dark:shadow-black/60 p-8 sm:p-9 z-10 space-y-6 transition-all">
      
      <!-- Brand & Header -->
      <div class="text-center space-y-3">
        <!-- Modern App Icon Badge -->
        <div class="inline-flex relative items-center justify-center">
          <div class="w-14 h-14 rounded-2xl bg-gradient-to-tr from-blue-600 to-indigo-500 text-white flex items-center justify-center shadow-lg shadow-blue-500/25 ring-4 ring-blue-500/10">
            <Sparkles class="w-7 h-7 stroke-[2.2]" />
          </div>
        </div>

        <div class="space-y-1">
          <h1 class="text-2xl font-black tracking-tight text-slate-900 dark:text-white uppercase">
            Salom CRM
          </h1>
          <p class="text-xs text-slate-500 dark:text-zinc-400 font-medium">
            Agency Management &amp; Visa Platform
          </p>
        </div>
      </div>

      <!-- Error Notification Alert -->
      <Transition
        enter-active-class="transition duration-200 ease-out"
        enter-from-class="opacity-0 -translate-y-2 scale-95"
        enter-to-class="opacity-100 translate-y-0 scale-100"
        leave-active-class="transition duration-150 ease-in"
        leave-from-class="opacity-100 translate-y-0 scale-100"
        leave-to-class="opacity-0 -translate-y-2 scale-95"
      >
        <div
          v-if="error"
          class="p-3.5 rounded-2xl bg-rose-50 dark:bg-rose-950/50 border border-rose-200 dark:border-rose-800/60 text-rose-700 dark:text-rose-300 text-xs font-semibold flex items-center gap-2.5 shadow-xs"
        >
          <AlertCircle class="w-4 h-4 shrink-0 text-rose-500" />
          <span class="flex-1 leading-snug">{{ error }}</span>
        </div>
      </Transition>

      <!-- Login Form -->
      <form @submit.prevent="handleLogin" class="space-y-4">
        <!-- Email Input -->
        <div class="space-y-1.5">
          <label class="block text-xs font-bold text-slate-700 dark:text-zinc-300">
            Email manzil
          </label>
          <div class="relative flex items-center">
            <Mail class="w-4 h-4 text-slate-400 dark:text-zinc-500 absolute left-3.5 pointer-events-none" />
            <input
              v-model="email"
              type="email"
              placeholder="example@unibridge.uz"
              required
              autocomplete="email"
              class="w-full pl-10 pr-4 py-2.5 rounded-xl border border-slate-200 dark:border-zinc-700/80 bg-slate-50/60 dark:bg-zinc-900/60 text-xs font-semibold text-slate-900 dark:text-white placeholder:text-slate-400 dark:placeholder:text-zinc-500 focus:bg-white dark:focus:bg-zinc-900 focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 dark:focus:border-blue-500 outline-none transition-all shadow-2xs"
            />
          </div>
        </div>

        <!-- Password Input with Show/Hide Toggle -->
        <div class="space-y-1.5">
          <div class="flex items-center justify-between">
            <label class="block text-xs font-bold text-slate-700 dark:text-zinc-300">
              Parol
            </label>
          </div>
          <div class="relative flex items-center">
            <Lock class="w-4 h-4 text-slate-400 dark:text-zinc-500 absolute left-3.5 pointer-events-none" />
            <input
              v-model="password"
              :type="showPassword ? 'text' : 'password'"
              placeholder="••••••••"
              required
              autocomplete="current-password"
              class="w-full pl-10 pr-10 py-2.5 rounded-xl border border-slate-200 dark:border-zinc-700/80 bg-slate-50/60 dark:bg-zinc-900/60 text-xs font-semibold text-slate-900 dark:text-white placeholder:text-slate-400 dark:placeholder:text-zinc-500 focus:bg-white dark:focus:bg-zinc-900 focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 dark:focus:border-blue-500 outline-none transition-all shadow-2xs"
            />
            <button
              type="button"
              @click="showPassword = !showPassword"
              class="absolute right-3 p-1 rounded-md text-slate-400 hover:text-slate-600 dark:text-zinc-500 dark:hover:text-zinc-300 transition-colors cursor-pointer"
              tabindex="-1"
              :title="showPassword ? 'Parolni yashirish' : 'Parolni ko\'rsatish'"
            >
              <EyeOff v-if="showPassword" class="w-4 h-4" />
              <Eye v-else class="w-4 h-4" />
            </button>
          </div>
        </div>

        <!-- Remember Me Checkbox -->
        <div class="flex items-center justify-between pt-1">
          <label class="inline-flex items-center gap-2 cursor-pointer select-none">
            <input
              v-model="rememberMe"
              type="checkbox"
              class="size-4 rounded border-slate-300 dark:border-zinc-700 text-blue-600 focus:ring-blue-500 focus:ring-offset-0 transition-colors cursor-pointer"
            />
            <span class="text-xs text-slate-600 dark:text-zinc-400 font-medium">Eslab qolish</span>
          </label>
        </div>

        <!-- Submit Button -->
        <button
          type="submit"
          :disabled="isLoading"
          class="w-full py-3 px-4 rounded-xl bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white font-bold text-xs shadow-lg shadow-blue-500/25 active:scale-[0.98] transition-all cursor-pointer flex items-center justify-center gap-2 disabled:opacity-60 disabled:cursor-not-allowed mt-2"
        >
          <span v-if="isLoading" class="inline-block size-3.5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
          <span>{{ isLoading ? 'Kirilmoqda...' : 'Tizimga kirish' }}</span>
          <ArrowRight v-if="!isLoading" class="w-4 h-4" />
        </button>
      </form>

      <!-- Security / Trust Note Footer -->
      <div class="pt-4 border-t border-slate-100 dark:border-zinc-800/80 flex items-center justify-center gap-1.5 text-[11px] text-slate-400 dark:text-zinc-500 font-medium">
        <ShieldCheck class="w-4 h-4 text-emerald-500" />
        <span>Xavfsiz va shifrlangan ulanish</span>
      </div>
    </div>
  </div>
</template>
