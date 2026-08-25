<script setup lang="ts">
import { ref, computed } from 'vue'
import { useQuery, useMutation, useQueryClient } from '@tanstack/vue-query'
import { tenantsApi } from '@/api/tenants'
import { useAuthStore } from '@/stores/auth'
import { useUiStore } from '@/stores/ui'
import type { Tenant } from '@/types'
import {
  ShieldAlert, Building2, Plus, Users, GraduationCap,
  CheckCircle2, XCircle, ArrowRight, Loader2,
  Pencil, Trash2, Power, PowerOff, Check, AlertTriangle, LogOut
} from 'lucide-vue-next'

import CreateTenantModal from './components/CreateTenantModal.vue'
import BaseModal from '@/components/common/BaseModal.vue'

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

// The tenant whose data the CRM is currently showing. Super Admins have no
// tenant of their own, so this is purely the impersonation context.
const activeTenantId = computed(() => authStore.activeTenantId)

const switchTenant = (t: Tenant) => {
  if (t.id === activeTenantId.value) return
  authStore.setActiveTenant(t.id)
}

const exitTenantContext = () => {
  authStore.setActiveTenant(null)
}

// ── Edit ──────────────────────────────────────────────────────────────
const editingTenant = ref<Tenant | null>(null)
const editForm = ref({ name: '', branding_color: '#007aff', description: '' })

const openEdit = (t: Tenant) => {
  editingTenant.value = t
  editForm.value = {
    name: t.name || '',
    branding_color: t.branding_color || '#007aff',
    description: t.description || '',
  }
}

const updateTenantMutation = useMutation({
  mutationFn: (data: any) => tenantsApi.updateTenant(editingTenant.value!.id, data),
  onSuccess: (updated) => {
    queryClient.invalidateQueries({ queryKey: ['tenants'] })
    editingTenant.value = null
    uiStore.addToast({
      type: 'success',
      title: 'Tenant Updated',
      message: `"${updated.name}" has been updated.`
    })
  },
  onError: (err: any) => {
    uiStore.addToast({
      type: 'error',
      title: 'Update Failed',
      message: err.response?.data?.detail || err.message || 'Could not update tenant'
    })
  }
})

const submitEdit = () => {
  if (!editForm.value.name.trim()) {
    uiStore.addToast({ type: 'error', title: 'Name Required', message: 'Tenant name cannot be empty.' })
    return
  }
  updateTenantMutation.mutate({
    name: editForm.value.name.trim(),
    branding_color: editForm.value.branding_color,
    description: editForm.value.description,
  })
}

// ── Activate / Deactivate ─────────────────────────────────────────────
const togglingId = ref<string | null>(null)

const toggleActiveMutation = useMutation({
  mutationFn: (t: Tenant) =>
    t.is_active ? tenantsApi.deactivateTenant(t.id) : tenantsApi.activateTenant(t.id),
  onSuccess: (_res, t) => {
    queryClient.invalidateQueries({ queryKey: ['tenants'] })
    togglingId.value = null
    uiStore.addToast({
      type: t.is_active ? 'warning' : 'success',
      title: t.is_active ? 'Tenant Suspended' : 'Tenant Activated',
      message: `"${t.name}" is now ${t.is_active ? 'suspended' : 'active'}.`
    })
  },
  onError: (err: any) => {
    togglingId.value = null
    uiStore.addToast({
      type: 'error',
      title: 'Action Failed',
      message: err.response?.data?.detail || err.message || 'Could not change tenant status'
    })
  }
})

const toggleActive = (t: Tenant) => {
  togglingId.value = t.id
  toggleActiveMutation.mutate(t)
}

// ── Delete ────────────────────────────────────────────────────────────
const deletingTenant = ref<Tenant | null>(null)
const deleteConfirmText = ref('')

const deleteTenantMutation = useMutation({
  mutationFn: (id: string) => tenantsApi.deleteTenant(id),
  onSuccess: () => {
    const name = deletingTenant.value?.name || 'Tenant'
    // If we were viewing the tenant we just deleted, drop that context.
    if (deletingTenant.value?.id === activeTenantId.value) {
      authStore.setActiveTenant(null)
      return
    }
    queryClient.invalidateQueries({ queryKey: ['tenants'] })
    deletingTenant.value = null
    deleteConfirmText.value = ''
    uiStore.addToast({
      type: 'success',
      title: 'Tenant Deleted',
      message: `"${name}" and all its data have been removed.`
    })
  },
  onError: (err: any) => {
    uiStore.addToast({
      type: 'error',
      title: 'Delete Failed',
      message: err.response?.data?.detail || err.message || 'Could not delete tenant'
    })
  }
})

const openDelete = (t: Tenant) => {
  deletingTenant.value = t
  deleteConfirmText.value = ''
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

    <!-- Active tenant context banner: switching is otherwise invisible, since
         the page looks identical after the reload. -->
    <div
      v-if="activeTenantId"
      class="flex items-center justify-between gap-3 px-4 py-2.5 rounded-xl bg-brand-500/10 border border-brand-500/25 text-xs"
    >
      <div class="flex items-center gap-2 min-w-0">
        <Check class="w-4 h-4 shrink-0 text-brand-500" />
        <span class="text-zinc-700 dark:text-zinc-300">
          Viewing the CRM as
          <strong class="text-zinc-900 dark:text-zinc-100">
            {{ tenants.find(t => t.id === activeTenantId)?.name || activeTenantId }}
          </strong>
          — all pages show this agency's data.
        </span>
      </div>
      <button
        @click="exitTenantContext"
        class="shrink-0 inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-white dark:bg-zinc-800 border border-zinc-200 dark:border-zinc-700 font-bold text-zinc-700 dark:text-zinc-300 hover:bg-zinc-100 dark:hover:bg-zinc-750 transition-colors cursor-pointer"
      >
        <LogOut class="w-3.5 h-3.5" />
        <span>Exit</span>
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
        class="p-5 rounded-2xl border bg-white dark:bg-zinc-900 shadow-xs flex flex-col justify-between gap-4 transition-all text-xs"
        :class="t.id === activeTenantId
          ? 'border-brand-500 ring-1 ring-brand-500/30'
          : 'border-zinc-200 dark:border-zinc-800 hover:border-brand-500/50'"
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

        <div class="flex flex-col gap-2">
          <!-- Switch Context Button -->
          <button
            v-if="t.id !== activeTenantId"
            @click="switchTenant(t)"
            class="w-full py-2 px-3 rounded-xl border border-zinc-200 dark:border-zinc-700 hover:border-brand-500 hover:bg-brand-50/50 dark:hover:bg-brand-950/20 text-zinc-800 dark:text-zinc-200 font-bold flex items-center justify-between transition-all cursor-pointer"
          >
            <span>Switch to this Tenant</span>
            <ArrowRight class="w-3.5 h-3.5 text-brand-500" />
          </button>
          <div
            v-else
            class="w-full py-2 px-3 rounded-xl bg-brand-500/10 border border-brand-500/30 text-brand-700 dark:text-brand-300 font-bold flex items-center justify-between"
          >
            <span>Currently viewing</span>
            <Check class="w-3.5 h-3.5" />
          </div>

          <!-- Manage Actions -->
          <div class="flex items-center gap-1.5">
            <button
              @click="openEdit(t)"
              class="flex-1 py-1.5 px-2 rounded-lg bg-zinc-100 dark:bg-zinc-800 hover:bg-zinc-200 dark:hover:bg-zinc-750 text-zinc-700 dark:text-zinc-300 font-bold flex items-center justify-center gap-1.5 transition-colors cursor-pointer"
              title="Edit tenant"
            >
              <Pencil class="w-3.5 h-3.5" />
              <span>Edit</span>
            </button>

            <button
              @click="toggleActive(t)"
              :disabled="togglingId === t.id"
              class="flex-1 py-1.5 px-2 rounded-lg font-bold flex items-center justify-center gap-1.5 transition-colors cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed"
              :class="t.is_active
                ? 'bg-amber-500/10 hover:bg-amber-500/20 text-amber-700 dark:text-amber-400'
                : 'bg-emerald-500/10 hover:bg-emerald-500/20 text-emerald-700 dark:text-emerald-400'"
              :title="t.is_active ? 'Suspend tenant' : 'Activate tenant'"
            >
              <Loader2 v-if="togglingId === t.id" class="w-3.5 h-3.5 animate-spin" />
              <PowerOff v-else-if="t.is_active" class="w-3.5 h-3.5" />
              <Power v-else class="w-3.5 h-3.5" />
              <span>{{ t.is_active ? 'Suspend' : 'Activate' }}</span>
            </button>

            <button
              @click="openDelete(t)"
              class="py-1.5 px-2.5 rounded-lg bg-rose-500/10 hover:bg-rose-500/20 text-rose-600 dark:text-rose-400 font-bold flex items-center justify-center transition-colors cursor-pointer"
              title="Delete tenant permanently"
            >
              <Trash2 class="w-3.5 h-3.5" />
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Create Tenant Modal -->
    <CreateTenantModal
      :is-open="isCreateModalOpen"
      @close="isCreateModalOpen = false"
      @submit="data => createTenantMutation.mutate(data)"
    />

    <!-- Edit Tenant -->
    <BaseModal
      :is-open="!!editingTenant"
      title="Edit Tenant"
      subtitle="Update this agency's name, branding, or description."
      max-width="max-w-md"
      @close="editingTenant = null"
    >
      <form @submit.prevent="submitEdit" class="space-y-4 text-xs">
        <div>
          <label class="block font-bold text-zinc-700 dark:text-zinc-300 mb-1">
            Tenant Name <span class="text-rose-500">*</span>
          </label>
          <input
            v-model="editForm.name"
            type="text"
            required
            class="w-full px-3 py-2 rounded-xl border border-zinc-300 dark:border-zinc-700 bg-white dark:bg-zinc-800 font-semibold focus:ring-2 focus:ring-brand-500/20 focus:border-brand-500 outline-none"
          />
        </div>

        <div>
          <label class="block font-bold text-zinc-700 dark:text-zinc-300 mb-1">Slug (identifier)</label>
          <input
            :value="editingTenant?.slug"
            type="text"
            disabled
            class="w-full px-3 py-2 rounded-xl border border-zinc-200 dark:border-zinc-800 bg-zinc-100 dark:bg-zinc-850 font-mono font-bold text-zinc-500 cursor-not-allowed"
          />
          <p class="text-[11px] text-zinc-500 dark:text-zinc-400 mt-1">
            The slug is permanent — existing records reference it.
          </p>
        </div>

        <div>
          <label class="block font-bold text-zinc-700 dark:text-zinc-300 mb-1">Branding Color</label>
          <div class="flex items-center gap-2">
            <input v-model="editForm.branding_color" type="color" class="w-8 h-8 rounded-lg border-0 cursor-pointer p-0 bg-transparent" />
            <input v-model="editForm.branding_color" type="text" class="flex-1 px-3 py-2 rounded-xl border border-zinc-300 dark:border-zinc-700 bg-white dark:bg-zinc-800 font-mono" />
          </div>
        </div>

        <div>
          <label class="block font-bold text-zinc-700 dark:text-zinc-300 mb-1">Description</label>
          <input
            v-model="editForm.description"
            type="text"
            placeholder="Optional agency note..."
            class="w-full px-3 py-2 rounded-xl border border-zinc-300 dark:border-zinc-700 bg-white dark:bg-zinc-800"
          />
        </div>

        <div class="pt-4 flex items-center justify-end gap-2.5 border-t border-zinc-100 dark:border-zinc-800">
          <button
            type="button"
            @click="editingTenant = null"
            class="px-4 py-2 rounded-xl border border-zinc-300 dark:border-zinc-700 font-bold text-zinc-700 dark:text-zinc-300 hover:bg-zinc-100 dark:hover:bg-zinc-800 transition-colors cursor-pointer"
          >
            Cancel
          </button>
          <button
            type="submit"
            :disabled="updateTenantMutation.isPending.value"
            class="px-4 py-2 rounded-xl bg-brand-500 hover:bg-brand-600 disabled:opacity-60 disabled:cursor-not-allowed text-white font-bold shadow-md shadow-brand-500/25 transition-all cursor-pointer flex items-center gap-1.5"
          >
            <Loader2 v-if="updateTenantMutation.isPending.value" class="w-4 h-4 animate-spin" />
            <Check v-else class="w-4 h-4" />
            <span>Save</span>
          </button>
        </div>
      </form>
    </BaseModal>

    <!-- Delete Tenant -->
    <BaseModal
      :is-open="!!deletingTenant"
      title="Delete Tenant"
      subtitle="This permanently removes the agency and everything in it."
      max-width="max-w-md"
      @close="deletingTenant = null"
    >
      <div class="space-y-4 text-xs">
        <div class="p-3 rounded-xl bg-rose-50 dark:bg-rose-950/50 border border-rose-200 dark:border-rose-800 text-rose-700 dark:text-rose-300 flex items-start gap-2">
          <AlertTriangle class="w-4 h-4 shrink-0 mt-0.5" />
          <div class="space-y-1">
            <p class="font-bold">Delete {{ deletingTenant?.name }}?</p>
            <p>
              This deletes its
              <strong>{{ deletingTenant?.user_count || 0 }} user(s)</strong> and
              <strong>{{ deletingTenant?.student_count || 0 }} student(s)</strong>,
              along with all payments and documents. This cannot be undone.
            </p>
            <p class="pt-1">
              To keep the data but block access, use <strong>Suspend</strong> instead.
            </p>
          </div>
        </div>

        <div>
          <label class="block font-bold text-zinc-700 dark:text-zinc-300 mb-1">
            Type <span class="font-mono text-rose-600">{{ deletingTenant?.slug }}</span> to confirm
          </label>
          <input
            v-model="deleteConfirmText"
            type="text"
            :placeholder="deletingTenant?.slug"
            class="w-full px-3 py-2 rounded-xl border border-zinc-300 dark:border-zinc-700 bg-white dark:bg-zinc-800 font-mono font-bold focus:ring-2 focus:ring-rose-500/20 focus:border-rose-500 outline-none"
          />
        </div>

        <div class="pt-3 flex items-center justify-end gap-2.5 border-t border-zinc-100 dark:border-zinc-800">
          <button
            type="button"
            @click="deletingTenant = null"
            class="px-4 py-2 rounded-xl border border-zinc-300 dark:border-zinc-700 font-bold text-zinc-700 dark:text-zinc-300 hover:bg-zinc-100 dark:hover:bg-zinc-800 transition-colors cursor-pointer"
          >
            Cancel
          </button>
          <button
            type="button"
            :disabled="deleteConfirmText !== deletingTenant?.slug || deleteTenantMutation.isPending.value"
            @click="deletingTenant && deleteTenantMutation.mutate(deletingTenant.id)"
            class="px-4 py-2 rounded-xl bg-rose-600 hover:bg-rose-700 disabled:opacity-50 disabled:cursor-not-allowed text-white font-bold shadow-md shadow-rose-600/25 transition-all cursor-pointer flex items-center gap-1.5"
          >
            <Loader2 v-if="deleteTenantMutation.isPending.value" class="w-4 h-4 animate-spin" />
            <Trash2 v-else class="w-4 h-4" />
            <span>Delete Permanently</span>
          </button>
        </div>
      </div>
    </BaseModal>
  </div>
</template>
