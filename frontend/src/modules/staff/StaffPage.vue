<script setup lang="ts">
import { ref, computed } from 'vue'
import { useQuery, useMutation, useQueryClient } from '@tanstack/vue-query'
import { staffApi } from '@/api/staff'
import { tenantsApi } from '@/api/tenants'
import { useAuthStore } from '@/stores/auth'
import { useUiStore } from '@/stores/ui'
import type { UserProfile, UserRole } from '@/types'
import { Users, Plus, Loader2, Mail, ShieldCheck, Pencil, Trash2, AlertTriangle } from 'lucide-vue-next'

import AddStaffModal from './components/AddStaffModal.vue'
import BaseModal from '@/components/common/BaseModal.vue'

const queryClient = useQueryClient()
const authStore = useAuthStore()
const uiStore = useUiStore()

const isAddModalOpen = ref(false)
const editingMember = ref<UserProfile | null>(null)
const deletingMember = ref<UserProfile | null>(null)

// A Super Admin has no tenant of their own; staff are created into whichever
// tenant they have switched into, so the page needs to name it and refuse to
// add staff when no tenant is selected.
const isSuperAdmin = computed(() => authStore.isSuperAdmin)
const activeTenantId = computed(() => authStore.activeTenantId)

const { data: tenantsData } = useQuery({
  queryKey: ['tenants'],
  queryFn: () => tenantsApi.getTenants(),
  enabled: isSuperAdmin,
  staleTime: 1000 * 60 * 5,
})

const activeTenantName = computed(() => {
  if (authStore.user?.tenant?.name) return authStore.user.tenant.name
  const list: any = tenantsData.value
  const arr = Array.isArray(list) ? list : (list?.results || [])
  return arr.find((t: any) => t.id === activeTenantId.value)?.name || null
})

// Super Admins can only add staff while viewing a specific tenant.
const canAddStaff = computed(() => !isSuperAdmin.value || !!activeTenantId.value)

const openAdd = () => {
  editingMember.value = null
  isAddModalOpen.value = true
}

const openEdit = (member: UserProfile) => {
  editingMember.value = member
  isAddModalOpen.value = true
}

const closeModal = () => {
  isAddModalOpen.value = false
  editingMember.value = null
}

// A head manager manages managers and staff, not other head managers or
// themselves; the backend enforces this too.
const canManage = (member: UserProfile) =>
  member.id !== authStore.user?.id &&
  member.role !== 'SUPER_ADMIN' &&
  member.role !== 'HEAD_MANAGER'

const { data: staffData, isLoading } = useQuery({
  queryKey: ['staff'],
  queryFn: () => staffApi.getStaff(),
})

const staff = computed<UserProfile[]>(() => {
  const data = staffData.value as any
  return Array.isArray(data) ? data : (data?.results || [])
})

const roleLabels: Record<UserRole, string> = {
  SUPER_ADMIN: 'Super Admin',
  HEAD_MANAGER: 'Head Manager',
  MANAGER: 'Manager',
  STAFF: 'Staff',
}

const roleClasses: Record<UserRole, string> = {
  SUPER_ADMIN: 'bg-violet-100 text-violet-800 dark:bg-violet-950 dark:text-violet-300',
  HEAD_MANAGER: 'bg-blue-100 text-blue-800 dark:bg-blue-950 dark:text-blue-300',
  MANAGER: 'bg-amber-100 text-amber-800 dark:bg-amber-950 dark:text-amber-300',
  STAFF: 'bg-zinc-100 text-zinc-700 dark:bg-zinc-800 dark:text-zinc-300',
}

const initials = (name: string) => (name || 'U').slice(0, 2).toUpperCase()

const describeError = (err: any, fallback: string) => {
  const data = err.response?.data
  const fieldError = data && typeof data === 'object'
    ? Object.entries(data).map(([k, v]) => `${k}: ${Array.isArray(v) ? v[0] : v}`)[0]
    : null
  return fieldError || data?.detail || err.message || fallback
}

const saveStaffMutation = useMutation({
  mutationFn: (data: any) =>
    editingMember.value
      ? staffApi.updateStaff(editingMember.value.id, data)
      : staffApi.createStaff(data),
  onSuccess: (saved) => {
    const wasEditing = !!editingMember.value
    queryClient.invalidateQueries({ queryKey: ['staff'] })
    closeModal()
    uiStore.addToast({
      type: 'success',
      title: wasEditing ? 'Staff Updated' : 'Staff Added',
      message: wasEditing
        ? `${saved.full_name}'s details have been updated.`
        : `${saved.full_name} can now sign in to your agency.`
    })
  },
  onError: (err: any) => {
    uiStore.addToast({
      type: 'error',
      title: 'Could Not Save Staff',
      message: describeError(err, 'Staff save failed')
    })
  }
})

const deleteStaffMutation = useMutation({
  mutationFn: (id: string) => staffApi.deleteStaff(id),
  onSuccess: () => {
    const name = deletingMember.value?.full_name || 'Staff member'
    queryClient.invalidateQueries({ queryKey: ['staff'] })
    deletingMember.value = null
    uiStore.addToast({
      type: 'success',
      title: 'Staff Removed',
      message: `${name} no longer has access to your agency.`
    })
  },
  onError: (err: any) => {
    uiStore.addToast({
      type: 'error',
      title: 'Could Not Remove Staff',
      message: describeError(err, 'Staff deletion failed')
    })
  }
})
</script>

<template>
  <div class="space-y-4">
    <!-- Header -->
    <div class="flex flex-col md:flex-row md:items-center justify-between gap-4">
      <div>
        <h1 class="text-xl font-bold text-zinc-900 dark:text-zinc-100 flex items-center gap-2">
          <Users class="w-5 h-5 text-brand-500" />
          <span>Staff Management</span>
        </h1>
        <p class="text-xs text-zinc-500 dark:text-zinc-400 mt-0.5">
          <template v-if="activeTenantName">
            Team members of
            <span class="font-semibold text-zinc-700 dark:text-zinc-300">{{ activeTenantName }}</span>.
          </template>
          <template v-else-if="isSuperAdmin">
            No tenant selected — switch into one on the Tenants page to manage its staff.
          </template>
          <template v-else>Team members of your agency.</template>
        </p>
      </div>

      <button
        @click="openAdd()"
        :disabled="!canAddStaff"
        :title="canAddStaff ? 'Add a staff member' : 'Switch into a tenant first'"
        class="px-4 py-2 rounded-xl bg-brand-500 hover:bg-brand-600 disabled:opacity-50 disabled:cursor-not-allowed text-white text-xs font-bold shadow-md shadow-brand-500/25 transition-all cursor-pointer flex items-center gap-1.5"
      >
        <Plus class="w-4 h-4" />
        <span>Add New Staff</span>
      </button>
    </div>

    <!-- Loading -->
    <div v-if="isLoading" class="p-12 text-center text-zinc-400 text-xs">
      <Loader2 class="w-6 h-6 animate-spin mx-auto text-brand-500 mb-2" />
      <span>Loading staff...</span>
    </div>

    <!-- Empty -->
    <div
      v-else-if="!staff.length"
      class="p-12 text-center rounded-2xl border border-dashed border-zinc-300 dark:border-zinc-700 text-xs"
    >
      <Users class="w-8 h-8 mx-auto text-zinc-300 dark:text-zinc-600 mb-2" />
      <p class="font-bold text-zinc-700 dark:text-zinc-300">No staff yet</p>
      <p class="text-zinc-500 dark:text-zinc-400 mt-1">Add your first team member to get started.</p>
    </div>

    <!-- Staff list -->
    <div v-else class="rounded-2xl border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-900 overflow-hidden">
      <div class="overflow-x-auto">
        <table class="w-full text-xs">
          <thead class="bg-zinc-50 dark:bg-zinc-800/50 border-b border-zinc-200 dark:border-zinc-800">
            <tr class="text-left text-[10px] uppercase font-bold text-zinc-400">
              <th class="px-4 py-3">Name</th>
              <th class="px-4 py-3">Email</th>
              <th class="px-4 py-3">Role</th>
              <th class="px-4 py-3">Status</th>
              <th class="px-4 py-3 text-right">Actions</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-zinc-100 dark:divide-zinc-800">
            <tr
              v-for="member in staff"
              :key="member.id"
              class="hover:bg-zinc-50 dark:hover:bg-zinc-800/40 transition-colors"
            >
              <td class="px-4 py-3">
                <div class="flex items-center gap-2.5">
                  <div
                    class="flex h-7 w-7 shrink-0 items-center justify-center rounded-full text-[10px] font-bold text-white select-none"
                    style="background: linear-gradient(135deg, #3b7ff5, #6366f1)"
                  >
                    {{ initials(member.full_name) }}
                  </div>
                  <span class="font-bold text-zinc-900 dark:text-zinc-100">{{ member.full_name }}</span>
                </div>
              </td>
              <td class="px-4 py-3">
                <span class="flex items-center gap-1.5 text-zinc-600 dark:text-zinc-400">
                  <Mail class="w-3 h-3 shrink-0" />
                  {{ member.email }}
                </span>
              </td>
              <td class="px-4 py-3">
                <span
                  class="px-2 py-0.5 rounded-full text-[10px] font-bold inline-flex items-center gap-1"
                  :class="roleClasses[member.role]"
                >
                  <ShieldCheck class="w-3 h-3" />
                  {{ roleLabels[member.role] || member.role }}
                </span>
              </td>
              <td class="px-4 py-3">
                <span
                  class="px-2 py-0.5 rounded-full text-[10px] font-bold"
                  :class="(member as any).is_active !== false
                    ? 'bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300'
                    : 'bg-rose-100 text-rose-800 dark:bg-rose-950 dark:text-rose-300'"
                >
                  {{ (member as any).is_active !== false ? 'Active' : 'Disabled' }}
                </span>
              </td>
              <td class="px-4 py-3">
                <div class="flex items-center justify-end gap-1.5">
                  <template v-if="canManage(member)">
                    <button
                      @click="openEdit(member)"
                      title="Edit staff member"
                      class="p-1.5 rounded-lg text-zinc-500 hover:text-brand-600 hover:bg-brand-50 dark:hover:bg-brand-950/30 transition-colors cursor-pointer"
                    >
                      <Pencil class="w-3.5 h-3.5" />
                    </button>
                    <button
                      @click="deletingMember = member"
                      title="Delete staff member"
                      class="p-1.5 rounded-lg text-zinc-500 hover:text-rose-600 hover:bg-rose-50 dark:hover:bg-rose-950/30 transition-colors cursor-pointer"
                    >
                      <Trash2 class="w-3.5 h-3.5" />
                    </button>
                  </template>
                  <span v-else class="text-[10px] text-zinc-400 italic pr-1">
                    {{ member.id === authStore.user?.id ? 'You' : 'Protected' }}
                  </span>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Add / Edit Staff Modal -->
    <AddStaffModal
      :is-open="isAddModalOpen"
      :member="editingMember"
      :is-submitting="saveStaffMutation.isPending.value"
      @close="closeModal()"
      @submit="data => saveStaffMutation.mutate(data)"
    />

    <!-- Delete Confirmation -->
    <BaseModal
      :is-open="!!deletingMember"
      title="Remove Staff Member"
      subtitle="This permanently revokes their access to your agency."
      max-width="max-w-sm"
      @close="deletingMember = null"
    >
      <div class="space-y-4 text-xs">
        <div class="p-3 rounded-xl bg-rose-50 dark:bg-rose-950/50 border border-rose-200 dark:border-rose-800 text-rose-700 dark:text-rose-300 flex items-start gap-2">
          <AlertTriangle class="w-4 h-4 shrink-0 mt-0.5" />
          <div>
            <p class="font-bold">Delete {{ deletingMember?.full_name }}?</p>
            <p class="mt-0.5">{{ deletingMember?.email }} will no longer be able to sign in. This cannot be undone.</p>
          </div>
        </div>

        <div class="pt-3 flex items-center justify-end gap-2.5 border-t border-zinc-100 dark:border-zinc-800">
          <button
            type="button"
            @click="deletingMember = null"
            class="px-4 py-2 rounded-xl border border-zinc-300 dark:border-zinc-700 font-bold text-zinc-700 dark:text-zinc-300 hover:bg-zinc-100 dark:hover:bg-zinc-800 transition-colors cursor-pointer"
          >
            Cancel
          </button>
          <button
            type="button"
            :disabled="deleteStaffMutation.isPending.value"
            @click="deletingMember && deleteStaffMutation.mutate(deletingMember.id)"
            class="px-4 py-2 rounded-xl bg-rose-600 hover:bg-rose-700 disabled:opacity-60 disabled:cursor-not-allowed text-white font-bold shadow-md shadow-rose-600/25 transition-all cursor-pointer flex items-center gap-1.5"
          >
            <Loader2 v-if="deleteStaffMutation.isPending.value" class="w-4 h-4 animate-spin" />
            <Trash2 v-else class="w-4 h-4" />
            <span>Delete</span>
          </button>
        </div>
      </div>
    </BaseModal>
  </div>
</template>
