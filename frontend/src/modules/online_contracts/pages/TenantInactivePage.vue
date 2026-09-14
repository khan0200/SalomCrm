<script setup lang="ts">
import { AlertTriangle, Clock } from 'lucide-vue-next'

defineProps<{
  companyName?: string
}>()
</script>

<template>
  <div class="min-h-screen flex items-center justify-center bg-zinc-50 dark:bg-zinc-950 p-4">
    <div class="max-w-md w-full text-center bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 rounded-3xl p-8 shadow-xl">
      <div class="w-16 h-16 rounded-2xl bg-amber-100 dark:bg-amber-950/60 text-amber-600 dark:text-amber-400 flex items-center justify-center mx-auto mb-5 shadow-xs">
        <Clock class="w-8 h-8" />
      </div>

      <h1 class="text-xl font-extrabold text-zinc-900 dark:text-white mb-2">
        Shartnoma portali vaqtincha faol emas
      </h1>

      <p class="text-xs text-zinc-500 leading-relaxed mb-6">
        <strong class="text-zinc-800 dark:text-zinc-200">{{ companyName || 'Ushbu kompaniya' }}</strong> uchun onlayn shartnomalar xizmati ayni damda mavjud emas yoki texnik xizmat ko'rsatish rejimida.
      </p>

      <div class="p-3 bg-amber-50 dark:bg-amber-950/30 border border-amber-200 dark:border-amber-900/50 rounded-xl text-xs text-amber-700 dark:text-amber-300 mb-6">
        Online contracts are currently unavailable for this consulting company.
      </div>

      <p class="text-xs text-zinc-400">
        Iltimos, qo'shimcha ma'lumot olish uchun kompaniya ma'muriyati bilan bog'laning.
      </p>
    </div>
  </div>
</template>
