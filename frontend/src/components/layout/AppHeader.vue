<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { useUiStore } from '@/stores/ui'
import { tenantsApi } from '@/api/tenants'
import type { Tenant } from '@/types'
import {
  Sun, Moon, Building2, User, LogOut, ShieldCheck, ChevronDown, Check
} from 'lucide-vue-next'
import BaseModal from '@/components/common/BaseModal.vue'

const authStore = useAuthStore()
const uiStore = useUiStore()

const isTenantModalOpen = ref(false)
const availableTenants = ref<Tenant[]>([])
const isLoadingTenants = ref(false)

const loadTenants = async () => {
  if (!authStore.isSuperAdmin) return
  isLoadingTenants.value = true
  try {
    const res = await tenantsApi.getTenants()
    availableTenants.value = Array.isArray(res) ? res : (res.results || [])
  } catch (err) {
    console.error('Failed to load tenants:', err)
  } finally {
    isLoadingTenants.value = false
  }
}

const selectTenant = (tenantId: string | null) => {
  authStore.setActiveTenant(tenantId)
  isTenantModalOpen.value = false
}

onMounted(() => {
  if (authStore.isSuperAdmin) {
    loadTenants()
  }
})
</script>

<template>
  <header class="h-16 bg-white dark:bg-zinc-900 border-b border-zinc-200 dark:border-zinc-800 px-6 flex items-center justify-between z-10 select-none">
    <!-- Left: Tenant Indicator & Switcher -->
    <div class="flex items-center gap-3">
      <!-- Tenant Badge -->
      <div
        v-if="authStore.isSuperAdmin"
        @click="isTenantModalOpen = true"
        class="flex items-center gap-2 px-3 py-1.5 rounded-xl border border-zinc-200 dark:border-zinc-700 bg-zinc-50 dark:bg-zinc-800 text-xs font-bold text-zinc-800 dark:text-zinc-200 hover:border-brand-500 transition-all cursor-pointer shadow-2xs"
        title="Click to switch tenant view"
      >
        <Building2 class="w-3.5 h-3.5 text-brand-500" />
        <span>{{ authStore.currentTenant?.name || (authStore.activeTenantId ? `Tenant: ${authStore.activeTenantId}` : 'All Tenants (Global View)') }}</span>
        <ChevronDown class="w-3 h-3 text-zinc-400" />
      </div>

      <div
        v-else-if="authStore.currentTenant"
        class="flex items-center gap-2 px-3 py-1.5 rounded-xl border border-zinc-200 dark:border-zinc-800 bg-zinc-50 dark:bg-zinc-800/60 text-xs font-bold text-zinc-700 dark:text-zinc-300"
      >
        <Building2 class="w-3.5 h-3.5 text-brand-500" />
        <span>{{ authStore.currentTenant.name }}</span>
      </div>
    </div>

    <!-- Right: Theme toggle & User Menu -->
    <div class="flex items-center gap-3.5">
      <!-- Theme Switcher -->
      <button
        @click="uiStore.toggleTheme"
        class="p-2 rounded-xl border border-zinc-200 dark:border-zinc-800 bg-zinc-50 dark:bg-zinc-800 text-zinc-600 dark:text-zinc-300 hover:bg-zinc-100 dark:hover:bg-zinc-700 transition-colors cursor-pointer"
        :title="uiStore.isDark ? 'Switch to Light Mode' : 'Switch to Dark Mode'"
      >
        <Sun v-if="uiStore.isDark" class="w-4 h-4 text-amber-400" />
        <Moon v-else class="w-4 h-4 text-zinc-600" />
      </button>

      <!-- User Profile Badge -->
      <div class="flex items-center gap-2.5 pl-3 border-l border-zinc-200 dark:border-zinc-800">
        <div class="w-8 h-8 rounded-full bg-brand-500/10 border border-brand-500/20 text-brand-600 dark:text-brand-400 flex items-center justify-center font-bold text-xs">
          {{ authStore.user?.full_name?.charAt(0) || 'U' }}
        </div>
        <div class="hidden sm:flex flex-col">
          <span class="text-xs font-bold text-zinc-900 dark:text-zinc-100 leading-tight">
            {{ authStore.user?.full_name || 'User' }}
          </span>
          <span class="text-[10px] font-semibold text-zinc-500 dark:text-zinc-400 leading-tight flex items-center gap-1 mt-0.5">
            <ShieldCheck class="w-2.5 h-2.5 text-brand-500" />
            {{ authStore.user?.role?.replace('_', ' ') || 'Staff' }}
          </span>
        </div>

        <!-- Logout Button -->
        <button
          @click="authStore.logout"
          class="ml-2 p-2 rounded-xl text-zinc-400 hover:text-rose-600 hover:bg-rose-50 dark:hover:bg-rose-950/30 transition-colors cursor-pointer"
          title="Sign Out"
        >
          <LogOut class="w-4 h-4" />
        </button>
      </div>
    </div>

    <!-- Super Admin Tenant Switcher Modal -->
    <BaseModal
      :is-open="isTenantModalOpen"
      title="Switch Tenant Context"
      subtitle="Select a tenant to manage or view platform-wide global data."
      max-width="max-w-md"
      @close="isTenantModalOpen = false"
    >
      <div class="space-y-2">
        <button
          @click="selectTenant(null)"
          class="w-full flex items-center justify-between p-3.5 rounded-xl border text-xs font-bold transition-all text-left cursor-pointer"
          :class="!authStore.activeTenantId ? 'border-brand-500 bg-brand-50/50 dark:bg-brand-950/20 text-brand-600 dark:text-brand-400' : 'border-zinc-200 dark:border-zinc-800 hover:bg-zinc-50 dark:hover:bg-zinc-800 text-zinc-800 dark:text-zinc-200'"
        >
          <div class="flex items-center gap-2.5">
            <Building2 class="w-4 h-4" />
            <div>
              <div>All Tenants (Global Platform View)</div>
              <div class="text-[10px] text-zinc-400 font-normal mt-0.5">View cross-tenant aggregated analytics and roster</div>
            </div>
          </div>
          <Check v-if="!authStore.activeTenantId" class="w-4 h-4 text-brand-500" />
        </button>

        <div class="py-1 text-[11px] font-bold text-zinc-400 uppercase tracking-wider">Tenants:</div>

        <button
          v-for="t in availableTenants"
          :key="t.id"
          @click="selectTenant(t.id)"
          class="w-full flex items-center justify-between p-3.5 rounded-xl border text-xs font-bold transition-all text-left cursor-pointer"
          :class="authStore.activeTenantId === t.id ? 'border-brand-500 bg-brand-50/50 dark:bg-brand-950/20 text-brand-600 dark:text-brand-400' : 'border-zinc-200 dark:border-zinc-800 hover:bg-zinc-50 dark:hover:bg-zinc-800 text-zinc-800 dark:text-zinc-200'"
        >
          <div class="flex items-center gap-2.5">
            <div class="w-3 h-3 rounded-full" :style="{ backgroundColor: t.branding_color || '#007aff' }" />
            <div>
              <div>{{ t.name }}</div>
              <div class="text-[10px] text-zinc-400 font-normal mt-0.5">Slug: {{ t.slug }} &bull; Students: {{ t.student_count || 0 }}</div>
            </div>
          </div>
          <Check v-if="authStore.activeTenantId === t.id" class="w-4 h-4 text-brand-500" />
        </button>
      </div>
    </BaseModal>
  </header>
</template>
