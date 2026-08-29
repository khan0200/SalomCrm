<script setup lang="ts">
import { ref, watch, nextTick, onMounted, onUnmounted } from 'vue'
import { Lock, Eye, EyeOff, ShieldCheck, X, AlertCircle, Loader2 } from 'lucide-vue-next'

const props = defineProps<{
  isOpen: boolean
  isVerifying?: boolean
  errorMessage?: string | null
}>()

const emit = defineEmits<{
  (e: 'close'): void
  (e: 'submit', password: string): void
}>()

const password = ref('')
const showPassword = ref(false)
const inputRef = ref<HTMLInputElement | null>(null)

watch(() => props.isOpen, (open) => {
  if (open) {
    password.value = ''
    showPassword.value = false
    nextTick(() => {
      inputRef.value?.focus()
    })
  }
})

const handleKeydown = (e: KeyboardEvent) => {
  if (e.key === 'Escape' && props.isOpen && !props.isVerifying) {
    emit('close')
  }
}

onMounted(() => {
  window.addEventListener('keydown', handleKeydown)
})

onUnmounted(() => {
  window.removeEventListener('keydown', handleKeydown)
})

const handleSubmit = () => {
  if (!password.value.trim() || props.isVerifying) return
  emit('submit', password.value)
}
</script>

<template>
  <Teleport to="body">
    <div
      v-if="isOpen"
      class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-xs select-none animate-in fade-in duration-200"
    >
      <div
        class="relative w-full max-w-md rounded-2xl border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-[#15171a] p-6 shadow-2xl transition-all scale-100"
      >
        <!-- Close button -->
        <button
          type="button"
          @click="emit('close')"
          :disabled="isVerifying"
          class="absolute right-4 top-4 rounded-lg p-1.5 text-zinc-400 hover:bg-zinc-100 hover:text-zinc-700 dark:hover:bg-zinc-800 dark:hover:text-zinc-200 transition-colors disabled:opacity-50 cursor-pointer"
        >
          <X class="h-4 w-4" />
        </button>

        <!-- Header Icon & Title -->
        <div class="flex flex-col items-center text-center">
          <div class="mb-3.5 flex h-13 w-13 items-center justify-center rounded-2xl bg-amber-500/10 text-amber-600 dark:text-amber-400 border border-amber-500/20 shadow-inner">
            <Lock class="h-6 w-6 stroke-[2.2]" />
          </div>
          <h3 class="text-base font-bold text-zinc-900 dark:text-zinc-100">
            Head Manager Access
          </h3>
          <p class="mt-1 text-xs text-zinc-500 dark:text-zinc-400 max-w-xs leading-relaxed">
            The <span class="font-bold text-zinc-700 dark:text-zinc-300">Finance</span> dashboard contains sensitive revenue, collections, and debt data. Please enter the Head Manager password to unlock.
          </p>
        </div>

        <!-- Form -->
        <form @submit.prevent="handleSubmit" class="mt-5 space-y-4">
          <div>
            <label class="block text-[11px] font-bold uppercase tracking-wider text-zinc-500 dark:text-zinc-400 mb-1.5">
              Head Manager Password
            </label>
            <div class="relative">
              <input
                ref="inputRef"
                :type="showPassword ? 'text' : 'password'"
                v-model="password"
                placeholder="Enter password..."
                autocomplete="current-password"
                :disabled="isVerifying"
                class="w-full rounded-xl border border-zinc-300 dark:border-zinc-700 bg-zinc-50 dark:bg-zinc-850 px-3.5 py-2.5 pr-10 text-xs font-mono text-zinc-900 dark:text-zinc-100 placeholder:text-zinc-400 focus:border-blue-500 focus:bg-white dark:focus:bg-zinc-900 focus:outline-none transition-colors"
                :class="errorMessage ? 'border-red-500 dark:border-red-500' : ''"
              />
              <button
                type="button"
                @click="showPassword = !showPassword"
                tabindex="-1"
                class="absolute right-3 top-1/2 -translate-y-1/2 text-zinc-400 hover:text-zinc-600 dark:hover:text-zinc-200 cursor-pointer"
              >
                <EyeOff v-if="showPassword" class="h-4 w-4" />
                <Eye v-else class="h-4 w-4" />
              </button>
            </div>

            <!-- Error message -->
            <div v-if="errorMessage" class="mt-2 flex items-center gap-1.5 text-xs text-red-600 dark:text-red-400">
              <AlertCircle class="h-3.5 w-3.5 shrink-0" />
              <span>{{ errorMessage }}</span>
            </div>
          </div>

          <!-- Buttons -->
          <div class="flex items-center gap-2.5 pt-2">
            <button
              type="button"
              @click="emit('close')"
              :disabled="isVerifying"
              class="flex-1 rounded-xl border border-zinc-200 dark:border-zinc-700 bg-white dark:bg-zinc-850 py-2.5 text-xs font-bold text-zinc-700 dark:text-zinc-300 hover:bg-zinc-50 dark:hover:bg-zinc-800 transition-colors disabled:opacity-50 cursor-pointer"
            >
              Cancel
            </button>
            <button
              type="submit"
              :disabled="!password.trim() || isVerifying"
              class="flex-1 flex items-center justify-center gap-2 rounded-xl bg-blue-600 py-2.5 text-xs font-bold text-white hover:bg-blue-700 active:scale-[0.98] transition-all disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer shadow-sm shadow-blue-500/20"
            >
              <Loader2 v-if="isVerifying" class="h-4 w-4 animate-spin" />
              <ShieldCheck v-else class="h-4 w-4" />
              <span>{{ isVerifying ? 'Verifying...' : 'Unlock Finance' }}</span>
            </button>
          </div>
        </form>
      </div>
    </div>
  </Teleport>
</template>
