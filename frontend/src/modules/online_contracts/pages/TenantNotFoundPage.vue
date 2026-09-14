<script setup lang="ts">
import { Building2, Search, ArrowLeft } from 'lucide-vue-next'
</script>

<template>
  <div class="min-h-screen flex items-center justify-center bg-zinc-50 dark:bg-zinc-950 p-4">
    <div class="max-w-md w-full text-center bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 rounded-3xl p-8 shadow-xl">
      <div class="w-16 h-16 rounded-2xl bg-amber-100 dark:bg-amber-950/60 text-amber-600 dark:text-amber-400 flex items-center justify-center mx-auto mb-5 shadow-xs">
        <Building2 class="w-8 h-8" />
      </div>

      <h1 class="text-xl font-extrabold text-zinc-900 dark:text-white mb-2">
        Kompaniya topilmadi / Tenant Not Found
      </h1>

      <p class="text-xs text-zinc-500 leading-relaxed mb-6">
        Siz so'ragan konsalting kompaniyasi tizimda mavjud emas yoki havola manzili noto'g'ri kiritilgan.
        Iltimos, kompaniya nomini tekshirib qayta urinib ko'ring.
      </p>

      <div class="p-3 bg-zinc-50 dark:bg-zinc-800/50 rounded-xl text-xs text-zinc-600 dark:text-zinc-400 font-mono mb-6">
        /contracts/online/:tenantname
      </div>

      <a
        href="/login"
        class="inline-flex items-center justify-center gap-2 w-full py-2.5 px-4 rounded-xl bg-zinc-900 hover:bg-zinc-800 text-white dark:bg-white dark:text-zinc-900 dark:hover:bg-zinc-100 text-xs font-bold transition-all"
      >
        <ArrowLeft class="w-4 h-4" />
        <span>Bosh sahifaga qaytish</span>
      </a>
    </div>
  </div>
</template>
