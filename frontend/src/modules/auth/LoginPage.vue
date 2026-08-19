<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useUiStore } from '@/stores/ui'
import {
  GraduationCap, Lock, Mail, ArrowRight,
  AlertCircle, Sun, Moon
} from 'lucide-vue-next'

const router = useRouter()
const authStore = useAuthStore()
const uiStore = useUiStore()

const email = ref('')
const password = ref('')
const isLoading = ref(false)
const error = ref<string | null>(null)

const handleLogin = async () => {
  if (!email.value.trim() || !password.value) {
    error.value = 'Please enter both email and password.'
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
      title: 'Welcome back!',
      message: `Signed in as ${authStore.user?.full_name}`
    })
    router.push('/students')
  } catch (err: any) {
    error.value = err.response?.data?.detail || 'Invalid email or password.'
  } finally {
    isLoading.value = false
  }
}

const fillCredentials = (e: string, p: string) => {
  email.value = e
  password.value = p
}
</script>

<template>
  <div class="min-h-screen w-screen flex items-center justify-center p-4 bg-zinc-100 dark:bg-zinc-950 select-none relative overflow-hidden">
    <!-- Subtle Background Glows -->
    <div class="absolute top-1/4 left-1/4 w-96 h-96 bg-brand-500/10 rounded-full blur-3xl pointer-events-none" />
    <div class="absolute bottom-1/4 right-1/4 w-96 h-96 bg-emerald-500/10 rounded-full blur-3xl pointer-events-none" />

    <!-- Theme Toggle at top right -->
    <div class="absolute top-6 right-6">
      <button
        @click="uiStore.toggleTheme"
        class="p-2.5 rounded-xl border border-zinc-200 dark:border-zinc-800 bg-white/80 dark:bg-zinc-900/80 backdrop-blur-xs text-zinc-600 dark:text-zinc-300 shadow-xs hover:bg-zinc-100 dark:hover:bg-zinc-800 transition-colors cursor-pointer"
      >
        <Sun v-if="uiStore.isDark" class="w-4 h-4 text-amber-400" />
        <Moon v-else class="w-4 h-4 text-zinc-600" />
      </button>
    </div>

    <!-- Login Card -->
    <div class="relative w-full max-w-md bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 rounded-3xl shadow-2xl p-8 z-10 space-y-6">
      <!-- Brand Header -->
      <div class="text-center space-y-2">
        <div class="w-12 h-12 mx-auto rounded-2xl bg-brand-500 text-white flex items-center justify-center shadow-lg shadow-brand-500/30">
          <GraduationCap class="w-6 h-6" />
        </div>
        <h1 class="text-2xl font-black text-zinc-900 dark:text-zinc-100 tracking-tight">UNIAPP CRM</h1>
        <p class="text-xs font-semibold text-zinc-500 dark:text-zinc-400">
          Educational Agency Multi-Tenant Platform &bull; v3.0
        </p>
      </div>

      <!-- Error Alert -->
      <div v-if="error" class="p-3.5 rounded-xl bg-rose-50 dark:bg-rose-950/60 border border-rose-200 dark:border-rose-800 text-rose-800 dark:text-rose-200 text-xs font-bold flex items-center gap-2">
        <AlertCircle class="w-4 h-4 shrink-0" />
        <span>{{ error }}</span>
      </div>

      <!-- Login Form -->
      <form @submit.prevent="handleLogin" class="space-y-4 text-xs">
        <div>
          <label class="block font-bold text-zinc-700 dark:text-zinc-300 mb-1">Email Address</label>
          <div class="relative">
            <Mail class="w-4 h-4 text-zinc-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
            <input
              v-model="email"
              type="email"
              placeholder="user@uniapp.com"
              required
              class="w-full pl-10 pr-4 py-2.5 rounded-xl border border-zinc-300 dark:border-zinc-700 bg-white dark:bg-zinc-800 font-medium text-zinc-900 dark:text-zinc-100 focus:ring-2 focus:ring-brand-500/20 focus:border-brand-500 outline-none transition-all"
            />
          </div>
        </div>

        <div>
          <label class="block font-bold text-zinc-700 dark:text-zinc-300 mb-1">Password</label>
          <div class="relative">
            <Lock class="w-4 h-4 text-zinc-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
            <input
              v-model="password"
              type="password"
              placeholder="••••••••"
              required
              class="w-full pl-10 pr-4 py-2.5 rounded-xl border border-zinc-300 dark:border-zinc-700 bg-white dark:bg-zinc-800 font-medium text-zinc-900 dark:text-zinc-100 focus:ring-2 focus:ring-brand-500/20 focus:border-brand-500 outline-none transition-all"
            />
          </div>
        </div>

        <button
          type="submit"
          :disabled="isLoading"
          class="w-full py-3 px-4 rounded-xl bg-brand-500 hover:bg-brand-600 text-white font-bold text-xs shadow-lg shadow-brand-500/30 transition-all cursor-pointer flex items-center justify-center gap-2 disabled:opacity-50"
        >
          <span>{{ isLoading ? 'Signing In...' : 'Sign In to Dashboard' }}</span>
          <ArrowRight class="w-4 h-4" />
        </button>
      </form>

      <!-- Quick Fill Demo Accounts -->
      <div class="pt-4 border-t border-zinc-100 dark:border-zinc-800 space-y-2">
        <span class="text-[10px] font-bold uppercase tracking-wider text-zinc-400 block text-center">
          Quick-Fill Demo Credentials
        </span>

        <div class="grid grid-cols-1 sm:grid-cols-2 gap-2 text-[11px]">
          <button
            type="button"
            @click="fillCredentials('admin@uniapp.com', 'admin123456')"
            class="p-2.5 rounded-xl border border-zinc-200 dark:border-zinc-800 hover:border-brand-500 hover:bg-zinc-50 dark:hover:bg-zinc-800/60 text-left transition-colors cursor-pointer"
          >
            <div class="font-bold text-zinc-800 dark:text-zinc-200">Platform Super Admin</div>
            <div class="text-[10px] text-zinc-400 font-mono truncate">admin@uniapp.com</div>
          </button>

          <button
            type="button"
            @click="fillCredentials('abdurazzakov_97@mail.ru', 'robocode2023@')"
            class="p-2.5 rounded-xl border border-zinc-200 dark:border-zinc-800 hover:border-brand-500 hover:bg-zinc-50 dark:hover:bg-zinc-800/60 text-left transition-colors cursor-pointer"
          >
            <div class="font-bold text-zinc-800 dark:text-zinc-200">Unibridge Head Manager</div>
            <div class="text-[10px] text-zinc-400 font-mono truncate">abdurazzakov_97@mail.ru</div>
          </button>
        </div>
      </div>
    </div>
  </div>
</template>
