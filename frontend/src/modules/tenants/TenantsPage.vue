<script setup lang="ts">
import { ref, computed } from 'vue'
import { useQuery, useMutation, useQueryClient } from '@tanstack/vue-query'
import { tenantsApi, type TenantAdmin } from '@/api/tenants'
import { useAuthStore } from '@/stores/auth'
import { useUiStore } from '@/stores/ui'
import type { Tenant } from '@/types'
import {
  ShieldAlert, Building2, Plus, Users, GraduationCap,
  CheckCircle2, XCircle, ArrowRight, Loader2,
  Pencil, Trash2, Power, PowerOff, Check, AlertTriangle, LogOut,
  Eye, EyeOff
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
const editForm = ref({ name: '', description: '', telegram_bot_token: '', telegram_chat_id: '' })
const showBotToken = ref(false)
const showChatId = ref(false)
const editBotToken = ref(false)
const editChatId = ref(false)

// Login credentials live on the tenant's Head Manager users, not on the
// Tenant row. A tenant can have several, so the admin to edit is picked
// explicitly rather than guessed.
const tenantAdmins = ref<TenantAdmin[]>([])
const isLoadingAdmins = ref(false)
const selectedAdminId = ref('')
const credForm = ref({ email: '', full_name: '', password: '' })

const selectedAdmin = computed(() =>
  tenantAdmins.value.find(a => a.id === selectedAdminId.value) || null
)

const loadAdmins = async (tenantId: string) => {
  isLoadingAdmins.value = true
  tenantAdmins.value = []
  selectedAdminId.value = ''
  credForm.value = { email: '', full_name: '', password: '' }
  try {
    tenantAdmins.value = await tenantsApi.getTenantAdmins(tenantId)
    if (tenantAdmins.value.length === 1) {
      selectAdmin(tenantAdmins.value[0].id)
    }
  } catch (err: any) {
    uiStore.addToast({
      type: 'error',
      title: 'Could Not Load Admins',
      message: err.response?.data?.detail || err.message || 'Failed to load tenant admins'
    })
  } finally {
    isLoadingAdmins.value = false
  }
}

const selectAdmin = (id: string) => {
  selectedAdminId.value = id
  const a = tenantAdmins.value.find(x => x.id === id)
  credForm.value = {
    email: a?.email || '',
    full_name: a?.full_name || '',
    password: '',
  }
}

const updateCredentialsMutation = useMutation({
  mutationFn: (payload: any) =>
    tenantsApi.updateTenantAdminCredentials(editingTenant.value!.id, payload),
  onSuccess: (res: any) => {
    credForm.value.password = ''
    if (editingTenant.value) loadAdmins(editingTenant.value.id)
    queryClient.invalidateQueries({ queryKey: ['staff'] })
    uiStore.addToast({
      type: 'success',
      title: 'Credentials Updated',
      message: `Updated ${(res?.updated || []).join(', ')} for ${res?.user?.email || 'admin'}.`
    })
  },
  onError: (err: any) => {
    uiStore.addToast({
      type: 'error',
      title: 'Update Failed',
      message: err.response?.data?.detail || err.message || 'Could not update credentials'
    })
  }
})

const submitCredentials = () => {
  if (!selectedAdminId.value) {
    uiStore.addToast({ type: 'error', title: 'Select an Admin', message: 'Choose which admin to update.' })
    return
  }
  const payload: Record<string, string> = { user_id: selectedAdminId.value }
  const a = selectedAdmin.value
  if (credForm.value.email.trim() && credForm.value.email.trim() !== a?.email) {
    payload.email = credForm.value.email.trim()
  }
  if (credForm.value.full_name.trim() && credForm.value.full_name.trim() !== a?.full_name) {
    payload.full_name = credForm.value.full_name.trim()
  }
  if (credForm.value.password) {
    payload.password = credForm.value.password
  }
  if (Object.keys(payload).length === 1) {
    uiStore.addToast({ type: 'error', title: 'Nothing Changed', message: 'Change an email, name, or password first.' })
    return
  }
  updateCredentialsMutation.mutate(payload)
}

const openEdit = (t: Tenant) => {
  editingTenant.value = t
  editForm.value = {
    name: t.name || '',
    description: t.description || '',
    telegram_bot_token: t.settings?.telegram_bot_token || '',
    telegram_chat_id: t.settings?.telegram_chat_id || '',
  }
  showBotToken.value = false
  showChatId.value = false
  editBotToken.value = false
  editChatId.value = false
  loadAdmins(t.id)
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
    description: editForm.value.description,
    settings: {
      telegram_bot_token: editForm.value.telegram_bot_token.trim(),
      telegram_chat_id: editForm.value.telegram_chat_id.trim(),
    },
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

    <div v-else class="grid gap-3.5" style="grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));">
      <div
        v-for="t in tenants"
        :key="t.id"
        class="rounded-2xl border bg-white dark:bg-zinc-900 shadow-xs overflow-hidden transition-all text-xs"
        :class="t.id === activeTenantId
          ? 'border-brand-500 ring-1 ring-brand-500/30'
          : 'border-zinc-200 dark:border-zinc-800 hover:border-brand-500/50'"
      >
        <!-- Header -->
        <div class="px-4 pt-3.5 pb-3 flex items-start justify-between gap-2">
          <div class="min-w-0">
            <span class="font-mono font-semibold text-zinc-400 uppercase text-[10px] tracking-wide">{{ t.slug }}</span>
            <h3 class="font-bold text-[15px] text-zinc-900 dark:text-zinc-100 truncate leading-tight mt-0.5">{{ t.name }}</h3>
            <p v-if="t.description" class="text-zinc-500 text-[11px] truncate mt-0.5">{{ t.description }}</p>
          </div>

          <span
            class="shrink-0 px-2 py-0.5 rounded-full text-[10px] font-bold"
            :class="t.is_active ? 'bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300' : 'bg-rose-100 text-rose-800 dark:bg-rose-950 dark:text-rose-300'"
          >
            {{ t.is_active ? 'Active' : 'Suspended' }}
          </span>
        </div>

        <!-- Metrics -->
        <div class="flex border-t border-b border-zinc-100 dark:border-zinc-800">
          <div class="flex-1 px-4 py-2.5 flex flex-col gap-0.5">
            <div class="flex items-center gap-1.5 text-zinc-400 font-bold text-[10px] uppercase tracking-wide">
              <Users class="w-3 h-3" />
              <span>Users</span>
            </div>
            <div class="font-extrabold text-[17px] text-zinc-800 dark:text-zinc-200 tabular-nums">{{ t.user_count || 0 }}</div>
          </div>
          <div class="w-px bg-zinc-100 dark:bg-zinc-800" />
          <div class="flex-1 px-4 py-2.5 flex flex-col gap-0.5">
            <div class="flex items-center gap-1.5 text-zinc-400 font-bold text-[10px] uppercase tracking-wide">
              <GraduationCap class="w-3 h-3" />
              <span>Students</span>
            </div>
            <div class="font-extrabold text-[17px] text-zinc-800 dark:text-zinc-200 tabular-nums">{{ t.student_count || 0 }}</div>
          </div>
        </div>

        <!-- Actions -->
        <div class="px-3 py-2.5 flex items-center gap-1.5">
          <button
            v-if="t.id !== activeTenantId"
            @click="switchTenant(t)"
            class="flex-1 py-2 px-3 rounded-xl bg-zinc-100 dark:bg-zinc-800 hover:bg-brand-50 dark:hover:bg-brand-950/40 text-zinc-700 dark:text-zinc-300 hover:text-brand-700 dark:hover:text-brand-300 font-bold text-[12px] flex items-center justify-center gap-1.5 transition-colors cursor-pointer"
          >
            <span>Switch</span>
            <ArrowRight class="w-3.5 h-3.5" />
          </button>
          <div
            v-else
            class="flex-1 py-2 px-3 rounded-xl bg-brand-500/10 text-brand-700 dark:text-brand-300 font-bold text-[12px] flex items-center justify-center gap-1.5"
          >
            <Check class="w-3.5 h-3.5" />
            <span>Viewing</span>
          </div>

          <button
            @click="openEdit(t)"
            class="w-8 h-8 shrink-0 rounded-xl text-zinc-400 hover:text-zinc-700 hover:bg-zinc-100 dark:hover:text-zinc-200 dark:hover:bg-zinc-800 flex items-center justify-center transition-colors cursor-pointer"
            title="Edit tenant"
          >
            <Pencil class="w-3.5 h-3.5" />
          </button>

          <button
            @click="toggleActive(t)"
            :disabled="togglingId === t.id"
            class="w-8 h-8 shrink-0 rounded-xl flex items-center justify-center transition-colors cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed"
            :class="t.is_active
              ? 'text-amber-500 hover:text-amber-700 hover:bg-amber-500/10 dark:hover:text-amber-400'
              : 'text-emerald-500 hover:text-emerald-700 hover:bg-emerald-500/10 dark:hover:text-emerald-400'"
            :title="t.is_active ? 'Suspend tenant' : 'Activate tenant'"
          >
            <Loader2 v-if="togglingId === t.id" class="w-3.5 h-3.5 animate-spin" />
            <PowerOff v-else-if="t.is_active" class="w-3.5 h-3.5" />
            <Power v-else class="w-3.5 h-3.5" />
          </button>

          <button
            @click="openDelete(t)"
            class="w-8 h-8 shrink-0 rounded-xl text-zinc-400 hover:text-rose-600 hover:bg-rose-500/10 dark:hover:text-rose-400 flex items-center justify-center transition-colors cursor-pointer"
            title="Delete tenant permanently"
          >
            <Trash2 class="w-3.5 h-3.5" />
          </button>
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
      max-width="max-w-xl"
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
          <label class="block font-bold text-zinc-700 dark:text-zinc-300 mb-1">Description</label>
          <input
            v-model="editForm.description"
            type="text"
            placeholder="Optional agency note..."
            class="w-full px-3 py-2 rounded-xl border border-zinc-300 dark:border-zinc-700 bg-white dark:bg-zinc-800"
          />
        </div>

        <div class="pt-3 border-t border-zinc-100 dark:border-zinc-800 space-y-3">
          <div class="flex items-center justify-between gap-2">
            <div>
              <h4 class="font-bold text-zinc-800 dark:text-zinc-200">Telegram Notifications</h4>
              <p class="text-[11px] text-zinc-500 dark:text-zinc-400 mt-0.5">
                This agency's own bot and chat. Registrations, payments, and withdrawals for this tenant only are sent here — never mixed with another agency's chat.
              </p>
            </div>
            <button
              v-if="editForm.telegram_bot_token || editForm.telegram_chat_id"
              type="button"
              @click="editForm.telegram_bot_token = ''; editForm.telegram_chat_id = ''"
              class="shrink-0 px-2.5 py-1.5 rounded-lg bg-rose-500/10 hover:bg-rose-500/20 text-rose-600 dark:text-rose-400 font-bold text-[11px] transition-colors cursor-pointer"
              title="Clear Telegram settings (Save to apply)"
            >
              Clear
            </button>
          </div>

          <div>
            <label class="block font-bold text-zinc-700 dark:text-zinc-300 mb-1">Bot Token</label>
            <div class="relative">
              <input
                v-model="editForm.telegram_bot_token"
                :type="showBotToken ? 'text' : 'password'"
                :readonly="!editBotToken"
                placeholder="123456789:AAExampleBotTokenHere"
                autocomplete="off"
                class="w-full px-3 py-2 pr-16 rounded-xl border border-zinc-300 dark:border-zinc-700 font-mono"
                :class="editBotToken ? 'bg-white dark:bg-zinc-800' : 'bg-zinc-100 dark:bg-zinc-850 cursor-default'"
              />
              <div class="absolute right-2 top-1/2 -translate-y-1/2 flex items-center gap-1">
                <button
                  type="button"
                  @click="showBotToken = !showBotToken"
                  class="p-1 text-zinc-400 hover:text-zinc-600 dark:hover:text-zinc-300 cursor-pointer"
                  :title="showBotToken ? 'Hide' : 'Show'"
                >
                  <EyeOff v-if="showBotToken" class="w-4 h-4" />
                  <Eye v-else class="w-4 h-4" />
                </button>
                <button
                  type="button"
                  @click="editBotToken = !editBotToken"
                  class="p-1 cursor-pointer"
                  :class="editBotToken ? 'text-brand-500' : 'text-zinc-400 hover:text-zinc-600 dark:hover:text-zinc-300'"
                  :title="editBotToken ? 'Editing' : 'Edit'"
                >
                  <Pencil class="w-3.5 h-3.5" />
                </button>
              </div>
            </div>
          </div>

          <div>
            <label class="block font-bold text-zinc-700 dark:text-zinc-300 mb-1">Chat ID</label>
            <div class="relative">
              <input
                v-model="editForm.telegram_chat_id"
                :type="showChatId ? 'text' : 'password'"
                :readonly="!editChatId"
                placeholder="-1001234567890 (or several, comma-separated)"
                autocomplete="off"
                class="w-full px-3 py-2 pr-16 rounded-xl border border-zinc-300 dark:border-zinc-700 font-mono"
                :class="editChatId ? 'bg-white dark:bg-zinc-800' : 'bg-zinc-100 dark:bg-zinc-850 cursor-default'"
              />
              <div class="absolute right-2 top-1/2 -translate-y-1/2 flex items-center gap-1">
                <button
                  type="button"
                  @click="showChatId = !showChatId"
                  class="p-1 text-zinc-400 hover:text-zinc-600 dark:hover:text-zinc-300 cursor-pointer"
                  :title="showChatId ? 'Hide' : 'Show'"
                >
                  <EyeOff v-if="showChatId" class="w-4 h-4" />
                  <Eye v-else class="w-4 h-4" />
                </button>
                <button
                  type="button"
                  @click="editChatId = !editChatId"
                  class="p-1 cursor-pointer"
                  :class="editChatId ? 'text-brand-500' : 'text-zinc-400 hover:text-zinc-600 dark:hover:text-zinc-300'"
                  :title="editChatId ? 'Editing' : 'Edit'"
                >
                  <Pencil class="w-3.5 h-3.5" />
                </button>
              </div>
            </div>
          </div>
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

      <!-- Admin login credentials (separate from the tenant record above) -->
      <div class="mt-5 pt-4 border-t border-zinc-100 dark:border-zinc-800 space-y-3 text-xs">
        <div>
          <h4 class="font-bold text-zinc-800 dark:text-zinc-200">Admin Login</h4>
          <p class="text-[11px] text-zinc-500 dark:text-zinc-400 mt-0.5">
            Email and password belong to a person, not the agency. Pick which admin to update.
          </p>
        </div>

        <div v-if="isLoadingAdmins" class="flex items-center gap-2 text-zinc-500 py-2">
          <Loader2 class="w-4 h-4 animate-spin" />
          <span>Loading admins...</span>
        </div>

        <div v-else-if="!tenantAdmins.length" class="p-3 rounded-xl bg-amber-50 dark:bg-amber-950/40 border border-amber-200 dark:border-amber-800 text-amber-700 dark:text-amber-300 flex items-start gap-2">
          <AlertTriangle class="w-4 h-4 shrink-0 mt-0.5" />
          <span>This tenant has no head manager, so nobody can sign in to it.</span>
        </div>

        <template v-else>
          <div>
            <label class="block font-bold text-zinc-700 dark:text-zinc-300 mb-1">
              Admin <span class="text-rose-500">*</span>
            </label>
            <select
              :value="selectedAdminId"
              @change="selectAdmin(($event.target as HTMLSelectElement).value)"
              class="w-full px-3 py-2 rounded-xl border border-zinc-300 dark:border-zinc-700 bg-white dark:bg-zinc-800 font-semibold focus:ring-2 focus:ring-brand-500/20 focus:border-brand-500 outline-none cursor-pointer"
            >
              <option value="" disabled>Select an admin...</option>
              <option v-for="a in tenantAdmins" :key="a.id" :value="a.id">
                {{ a.full_name || 'Unnamed' }} — {{ a.email }}
              </option>
            </select>
            <p v-if="tenantAdmins.length > 1" class="text-[11px] text-zinc-500 dark:text-zinc-400 mt-1">
              {{ tenantAdmins.length }} head managers on this tenant.
            </p>
          </div>

          <template v-if="selectedAdminId">
            <div>
              <label class="block font-bold text-zinc-700 dark:text-zinc-300 mb-1">Full Name</label>
              <input
                v-model="credForm.full_name"
                type="text"
                class="w-full px-3 py-2 rounded-xl border border-zinc-300 dark:border-zinc-700 bg-white dark:bg-zinc-800 font-medium focus:ring-2 focus:ring-brand-500/20 focus:border-brand-500 outline-none"
              />
            </div>

            <div>
              <label class="block font-bold text-zinc-700 dark:text-zinc-300 mb-1">Login Email</label>
              <input
                v-model="credForm.email"
                type="email"
                class="w-full px-3 py-2 rounded-xl border border-zinc-300 dark:border-zinc-700 bg-white dark:bg-zinc-800 font-medium focus:ring-2 focus:ring-brand-500/20 focus:border-brand-500 outline-none"
              />
            </div>

            <div>
              <label class="block font-bold text-zinc-700 dark:text-zinc-300 mb-1">New Password</label>
              <input
                v-model="credForm.password"
                type="password"
                placeholder="••••••••"
                autocomplete="new-password"
                class="w-full px-3 py-2 rounded-xl border border-zinc-300 dark:border-zinc-700 bg-white dark:bg-zinc-800 font-medium focus:ring-2 focus:ring-brand-500/20 focus:border-brand-500 outline-none"
              />
              <p class="text-[11px] text-zinc-500 dark:text-zinc-400 mt-1">
                Leave blank to keep the current password. Changing it signs this person out of nothing — they keep working until their token expires.
              </p>
            </div>

            <div class="flex items-center justify-end pt-1">
              <button
                type="button"
                :disabled="updateCredentialsMutation.isPending.value"
                @click="submitCredentials"
                class="px-4 py-2 rounded-xl bg-zinc-900 dark:bg-zinc-100 text-white dark:text-zinc-900 font-bold hover:bg-zinc-800 dark:hover:bg-white disabled:opacity-60 disabled:cursor-not-allowed transition-all cursor-pointer flex items-center gap-1.5"
              >
                <Loader2 v-if="updateCredentialsMutation.isPending.value" class="w-4 h-4 animate-spin" />
                <Check v-else class="w-4 h-4" />
                <span>Update Login</span>
              </button>
            </div>
          </template>
        </template>
      </div>
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
