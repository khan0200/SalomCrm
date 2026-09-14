<script setup lang="ts">
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { FileSignature, User, LogOut, ShieldCheck } from 'lucide-vue-next'
import type { TenantInfoResponse } from '@/api/onlineContracts'

const props = defineProps<{
  tenantInfo: TenantInfoResponse | null
  isLoading?: boolean
}>()

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()

const tenantSlug = computed(() => (route.params.tenantname as string) || props.tenantInfo?.slug || '')
const isStudentAuthenticated = computed(() => authStore.isAuthenticated && authStore.user?.role === 'STUDENT')
const studentFullName = computed(() => authStore.user?.full_name || authStore.user?.email || 'Talaba')

function handleSignOut() {
  authStore.logout()
  router.push({ name: 'online-landing', params: { tenantname: tenantSlug.value } })
}

/**
 * Handle smooth scrolling for in-page anchors
 */
function handleNavClick(sectionId: string, e: MouseEvent) {
  if (route.name === 'online-landing') {
    e.preventDefault()
    const target = document.getElementById(sectionId)
    if (target) {
      target.scrollIntoView({ behavior: 'smooth', block: 'start' })
      history.pushState(null, '', `#${sectionId}`)
    }
  } else {
    // If on a sub-route, navigate back to landing page with anchor
    router.push({
      name: 'online-landing',
      params: { tenantname: tenantSlug.value },
      hash: `#${sectionId}`,
    })
  }
}
</script>

<template>
  <div class="min-h-screen flex flex-col bg-[#fafafa] dark:bg-[#09090b] text-zinc-900 dark:text-zinc-100 font-sans antialiased selection:bg-zinc-900 selection:text-white dark:selection:bg-white dark:selection:text-zinc-900">
    <!-- Resend-style Top Navigation Header -->
    <header class="sticky top-0 z-40 w-full bg-white/90 dark:bg-zinc-950/90 backdrop-blur-md border-b border-zinc-200/80 dark:border-zinc-800/80 transition-all">
      <div class="max-w-6xl mx-auto px-3.5 sm:px-6 h-14 sm:h-16 flex items-center justify-between gap-2">
        <!-- Brand / Tenant -->
        <router-link
          :to="{ name: 'online-landing', params: { tenantname: tenantSlug } }"
          class="flex items-center gap-2.5 sm:gap-3 group min-w-0"
        >
          <div
            v-if="tenantInfo?.logo_url"
            class="w-8 h-8 rounded-lg overflow-hidden bg-white border border-zinc-200 dark:border-zinc-800 p-0.5 flex items-center justify-center shrink-0 transition-transform group-hover:scale-105"
          >
            <img :src="tenantInfo.logo_url" :alt="tenantInfo.name" class="w-full h-full object-contain" />
          </div>
          <div
            v-else
            class="w-8 h-8 rounded-lg bg-zinc-900 dark:bg-zinc-100 text-white dark:text-zinc-950 flex items-center justify-center font-mono font-bold text-xs tracking-tight shrink-0 transition-transform group-hover:scale-105"
          >
            {{ (tenantInfo?.name || 'U')[0] }}
          </div>

          <span class="font-semibold text-xs sm:text-sm tracking-tight text-zinc-900 dark:text-zinc-100 truncate max-w-[120px] xs:max-w-[160px] sm:max-w-none">
            {{ tenantInfo?.name || 'Onlayn Shartnoma' }}
          </span>
        </router-link>

        <!-- Center Nav Links (Desktop) with Smooth Scrolling -->
        <nav class="hidden md:flex items-center gap-6 text-xs font-semibold text-zinc-900 dark:text-zinc-100">
          <a
            href="#tariffs-section"
            @click="handleNavClick('tariffs-section', $event)"
            class="hover:text-black dark:hover:text-white transition-colors cursor-pointer"
          >
            Tariflar
          </a>
          <a
            href="#process-section"
            @click="handleNavClick('process-section', $event)"
            class="hover:text-black dark:hover:text-white transition-colors cursor-pointer"
          >
            Jarayon
          </a>
          <a
            href="#security-section"
            @click="handleNavClick('security-section', $event)"
            class="hover:text-black dark:hover:text-white transition-colors cursor-pointer flex items-center gap-1"
          >
            <ShieldCheck class="w-3.5 h-3.5 text-emerald-600 dark:text-emerald-400" />
            <span>Xavfsizlik</span>
          </a>
          <a
            href="#offices-section"
            @click="handleNavClick('offices-section', $event)"
            class="hover:text-black dark:hover:text-white transition-colors cursor-pointer"
          >
            Filiallar
          </a>
        </nav>

        <!-- Right Side Nav Actions -->
        <div class="flex items-center gap-1.5 sm:gap-2.5 shrink-0">
          <template v-if="isStudentAuthenticated">
            <router-link
              :to="{ name: 'online-profile', params: { tenantname: tenantSlug } }"
              class="inline-flex items-center gap-1.5 px-2.5 sm:px-3 py-1.5 rounded-lg border border-zinc-300 dark:border-zinc-700 bg-white dark:bg-zinc-900 hover:bg-zinc-50 dark:hover:bg-zinc-850 text-xs font-semibold text-zinc-900 dark:text-zinc-100 transition-colors shadow-2xs"
            >
              <User class="w-3.5 h-3.5 text-zinc-700 dark:text-zinc-300" />
              <span class="hidden sm:inline">{{ studentFullName }}</span>
              <span class="sm:hidden text-[11px]">Profil</span>
            </router-link>

            <button
              type="button"
              @click="handleSignOut"
              class="inline-flex items-center gap-1 px-2 sm:px-2.5 py-1.5 rounded-lg border border-zinc-200 dark:border-zinc-800 hover:bg-red-50 dark:hover:bg-red-950/40 text-zinc-500 hover:text-red-600 dark:hover:text-red-400 text-xs font-medium transition-colors cursor-pointer"
              title="Chiqish"
            >
              <LogOut class="w-3.5 h-3.5" />
            </button>
          </template>

          <template v-else>
            <router-link
              :to="{ name: 'online-sign-in', params: { tenantname: tenantSlug } }"
              class="px-2.5 sm:px-3 py-1.5 rounded-lg text-xs font-semibold text-zinc-900 dark:text-zinc-100 hover:text-black dark:hover:text-white transition-colors"
            >
              Kirish
            </router-link>

            <router-link
              :to="{ name: 'online-sign-up', params: { tenantname: tenantSlug } }"
              class="inline-flex items-center gap-1 sm:gap-1.5 px-2.5 sm:px-3.5 py-1.5 rounded-lg bg-zinc-900 hover:bg-zinc-800 text-white dark:bg-zinc-100 dark:hover:bg-white dark:text-zinc-950 text-xs font-medium transition-all shadow-xs active:scale-98"
            >
              <FileSignature class="w-3.5 h-3.5" />
              <span class="hidden sm:inline">Shartnoma tuzish</span>
              <span class="sm:hidden text-[11px]">Tuzish</span>
            </router-link>
          </template>
        </div>
      </div>

      <!-- Mobile Horizontal Nav Pills with Sleek Floating Design -->
      <div class="md:hidden flex items-center gap-1.5 overflow-x-auto px-3.5 py-2 border-t border-zinc-100 dark:border-zinc-850/80 text-[11px] font-semibold text-zinc-900 dark:text-zinc-100 no-scrollbar">
        <a
          href="#tariffs-section"
          @click="handleNavClick('tariffs-section', $event)"
          class="shrink-0 px-2.5 py-1 rounded-full border border-zinc-300 dark:border-zinc-700 bg-white dark:bg-zinc-900 hover:bg-zinc-50 dark:hover:bg-zinc-800 transition-colors shadow-2xs text-zinc-900 dark:text-zinc-100"
        >
          Tariflar
        </a>
        <a
          href="#process-section"
          @click="handleNavClick('process-section', $event)"
          class="shrink-0 px-2.5 py-1 rounded-full border border-zinc-300 dark:border-zinc-700 bg-white dark:bg-zinc-900 hover:bg-zinc-50 dark:hover:bg-zinc-800 transition-colors shadow-2xs text-zinc-900 dark:text-zinc-100"
        >
          Jarayon
        </a>
        <a
          href="#security-section"
          @click="handleNavClick('security-section', $event)"
          class="shrink-0 px-2.5 py-1 rounded-full border border-zinc-300 dark:border-zinc-700 bg-white dark:bg-zinc-900 hover:bg-zinc-50 dark:hover:bg-zinc-800 transition-colors shadow-2xs flex items-center gap-1 text-zinc-900 dark:text-zinc-100"
        >
          <ShieldCheck class="w-3 h-3 text-emerald-600 dark:text-emerald-400" />
          <span>Xavfsizlik</span>
        </a>
        <a
          href="#offices-section"
          @click="handleNavClick('offices-section', $event)"
          class="shrink-0 px-2.5 py-1 rounded-full border border-zinc-300 dark:border-zinc-700 bg-white dark:bg-zinc-900 hover:bg-zinc-50 dark:hover:bg-zinc-800 transition-colors shadow-2xs text-zinc-900 dark:text-zinc-100"
        >
          Filiallar
        </a>
      </div>
    </header>

    <!-- Main Content Area -->
    <main class="flex-1 w-full relative">
      <div class="max-w-6xl mx-auto px-4 sm:px-6 py-6 sm:py-12">
        <slot />
      </div>
    </main>

    <!-- Resend-style Minimal Footer -->
    <footer class="mt-auto border-t border-zinc-200/80 dark:border-zinc-850 py-6 sm:py-8 bg-white/50 dark:bg-zinc-950/50 backdrop-blur-xs text-xs text-zinc-500">
      <div class="max-w-6xl mx-auto px-4 sm:px-6 flex flex-col sm:flex-row items-center justify-between gap-3 text-center sm:text-left">
        <div class="text-[11px] text-zinc-400 dark:text-zinc-500">
          © {{ new Date().getFullYear() }} {{ tenantInfo?.name || 'UniApp' }}. Barcha huquqlar himoyalangan.
        </div>

        <div class="text-[11px] text-zinc-400 dark:text-zinc-500">
          O'zbekiston Respublikasi Qonunchiligiga Muvofiq
        </div>
      </div>
    </footer>
  </div>
</template>
