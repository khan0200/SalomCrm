<script setup lang="ts">
import { ref, computed } from 'vue'
import { useQuery, useMutation, useQueryClient } from '@tanstack/vue-query'
import { tenantsApi } from '@/api/tenants'
import { useAuthStore } from '@/stores/auth'
import { useUiStore } from '@/stores/ui'
import type { Tenant } from '@/types'
import {
  ShieldAlert, Building2, Plus, Users, GraduationCap,
  CheckCircle2, XCircle, ArrowRight, Loader2
} from 'lucide-vue-next'

import CreateTenantModal from './components/CreateTenantModal.vue'

const queryClient = useQueryClient()
const authStore = useAuthStore()
const uiStore = useUiStore()

const isCreateModalOpen = ref(false)

// Query: Tenants
const { data: tenantsData, isLoading } = useQuery({
  queryKey: ['tenants'],
  queryFn: () => tenantsApi.getTenants(),
})

const tenants = computed(() => {
  const data = tenantsData.value
  return Array.isArray(data) ? data : (data?.results || [])
})

// Mutations
const createTenantMutation = useMutation({
  mutationFn: (data: any) => tenantsApi.createTenant(data),
  onSuccess: (newTenant) => {
    queryClient.invalidateQueries({ queryKey: ['tenants'] })
    isCreateModalOpen.value = false
    uiStore.addToast({
      type: 'success',
      title: 'Tenant Provisioned',
      message: `Tenant "${newTenant.name}" has been initialized.`
    })
  },
  onError: (err: any) => {
    uiStore.addToast({
      type: 'error',
      title: 'Failed to Create Tenant',
      message: err.response?.data?.detail || err.message || 'Tenant creation failed'
    })
  }
})

const switchTenant = (t: Tenant) => {
  authStore.setActiveTenant(t.id)
}
</script>

<template>
  <div class="space-y-4">
    <!-- Header -->
    <div class="flex flex-col md:flex-row md:items-center justify-between gap-4">
      <div>
        <h1 class="text-xl font-bold text-zinc-900 dark:text-zinc-100 flex items-center gap-2">
          <ShieldAlert class="w-5 h-5 text-brand-500" />
          <span>Platform Multi-Tenancy Management</span>
        </h1>
        <p class="text-xs text-zinc-500 dark:text-zinc-400 mt-0.5">
          Super Admin controls for provisioning, managing, and inspecting isolated agency environments.
        </p>
      </div>

      <button
        @click="isCreateModalOpen = true"
        class="px-4 py-2 rounded-xl bg-brand-500 hover:bg-brand-600 text-white text-xs font-bold shadow-md shadow-brand-500/25 transition-all cursor-pointer flex items-center gap-1.5"
      >
        <Plus class="w-4 h-4" />
        <span>Create Tenant</span>
      </button>
    </div>

    <!-- Tenants Grid -->
    <div v-if="isLoading" class="p-12 text-center text-zinc-400">
      <Loader2 class="w-6 h-6 animate-spin mx-auto text-brand-500 mb-2" />
      <span>Loading tenant agencies...</span>
    </div>

    <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      <div
        v-for="t in tenants"
        :key="t.id"
        class="p-5 rounded-2xl border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-900 shadow-xs flex flex-col justify-between gap-4 hover:border-brand-500/50 transition-all text-xs"
      >
        <div>
          <!-- Header with Color & Status -->
          <div class="flex items-center justify-between mb-2">
            <div class="flex items-center gap-2.5">
              <div
                class="w-3.5 h-3.5 rounded-full shadow-2xs"
                :style="{ backgroundColor: t.branding_color || '#007aff' }"
              />
              <span class="font-mono font-bold text-zinc-400 uppercase text-[11px]">{{ t.slug }}</span>
            </div>

            <span
              class="px-2 py-0.5 rounded-full text-[10px] font-bold"
              :class="t.is_active ? 'bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300' : 'bg-rose-100 text-rose-800 dark:bg-rose-950 dark:text-rose-300'"
            >
              {{ t.is_active ? 'Active' : 'Suspended' }}
            </span>
          </div>

          <h3 class="font-bold text-base text-zinc-900 dark:text-zinc-100">{{ t.name }}</h3>
          <p v-if="t.description" class="text-zinc-500 text-xs mt-1">{{ t.description }}</p>
        </div>

        <!-- Metrics -->
        <div class="grid grid-cols-2 gap-2 pt-3 border-t border-zinc-100 dark:border-zinc-800">
          <div class="p-2.5 rounded-xl bg-zinc-50 dark:bg-zinc-800/50 border border-zinc-100 dark:border-zinc-800">
            <div class="flex items-center gap-1.5 text-zinc-400 font-bold text-[10px] uppercase">
              <Users class="w-3 h-3" />
              <span>Users</span>
            </div>
            <div class="font-bold text-base text-zinc-800 dark:text-zinc-200 mt-0.5">{{ t.user_count || 0 }}</div>
          </div>

          <div class="p-2.5 rounded-xl bg-zinc-50 dark:bg-zinc-800/50 border border-zinc-100 dark:border-zinc-800">
            <div class="flex items-center gap-1.5 text-zinc-400 font-bold text-[10px] uppercase">
              <GraduationCap class="w-3 h-3" />
              <span>Students</span>
            </div>
            <div class="font-bold text-base text-zinc-800 dark:text-zinc-200 mt-0.5">{{ t.student_count || 0 }}</div>
          </div>
        </div>

        <!-- Switch Context Button -->
        <button
          @click="switchTenant(t)"
          class="w-full py-2 px-3 rounded-xl border border-zinc-200 dark:border-zinc-700 hover:border-brand-500 hover:bg-brand-50/50 dark:hover:bg-brand-950/20 text-zinc-800 dark:text-zinc-200 font-bold flex items-center justify-between transition-all cursor-pointer"
        >
          <span>Switch to this Tenant</span>
          <ArrowRight class="w-3.5 h-3.5 text-brand-500" />
        </button>
      </div>
    </div>

    <!-- Create Tenant Modal -->
    <CreateTenantModal
      :is-open="isCreateModalOpen"
      @close="isCreateModalOpen = false"
      @submit="data => createTenantMutation.mutate(data)"
    />
  </div>
</template>
