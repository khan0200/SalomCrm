<script setup lang="ts">
import { ref, computed } from 'vue'
import { useQuery, useMutation, useQueryClient } from '@tanstack/vue-query'
import { staffApi } from '@/api/staff'
import { tenantsApi } from '@/api/tenants'
import { useAuthStore } from '@/stores/auth'
import { useUiStore } from '@/stores/ui'
import type { UserProfile, UserRole } from '@/types'
import {
  Users, Plus, Loader2, Mail, ShieldCheck, Pencil, Trash2, AlertTriangle,
  ShieldAlert, CheckCircle2, XCircle, Eye, Edit3, Trash, CreditCard,
  UserCog, BarChart2, Settings, BookOpen, FolderOpen, Crown, Shield, User
} from 'lucide-vue-next'

import AddStaffModal from './components/AddStaffModal.vue'
import BaseModal from '@/components/common/BaseModal.vue'

const queryClient = useQueryClient()
const authStore = useAuthStore()
const uiStore = useUiStore()

// ─── Tab state ─────────────────────────────────────────────────────────────
const activeTab = ref<'staff' | 'roles'>('staff')

// ─── Staff tab ─────────────────────────────────────────────────────────────
const isAddModalOpen = ref(false)
const editingMember = ref<UserProfile | null>(null)
const deletingMember = ref<UserProfile | null>(null)

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

const canEdit = (member: UserProfile) => {
  if (member.role === 'SUPER_ADMIN' && !isSuperAdmin.value) return false
  return true
}

const canDelete = (member: UserProfile) => {
  if (member.id === authStore.user?.id) return false
  if (member.role === 'SUPER_ADMIN' && !isSuperAdmin.value) return false
  return true
}

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
    if (editingMember.value && editingMember.value.id === authStore.user?.id) {
      authStore.fetchUser()
    }
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

// ─── Roles tab data ─────────────────────────────────────────────────────────
// Permission levels: 'full' | 'view' | 'none'
type PermLevel = 'full' | 'view' | 'none'

interface PermRow {
  label: string
  headManager: PermLevel
  manager: PermLevel
  staff: PermLevel
  note?: string
}

interface PermGroup {
  category: string
  icon: any
  color: string
  rows: PermRow[]
}

const permissionGroups: PermGroup[] = [
  {
    category: 'Talabalar (Students)',
    icon: BookOpen,
    color: 'blue',
    rows: [
      { label: "Talaba ro'yxatini ko'rish", headManager: 'full', manager: 'full', staff: 'full' },
      { label: "Talaba qo'shish", headManager: 'full', manager: 'full', staff: 'none', note: "Staff faqat ko'ra oladi" },
      { label: 'Talaba ma\'lumotlarini tahrirlash', headManager: 'full', manager: 'full', staff: 'none' },
      { label: "Talabani o'chirish", headManager: 'full', manager: 'full', staff: 'none' },
      { label: 'Talaba to\'liq ma\'lumotlar (drawer)', headManager: 'full', manager: 'full', staff: 'full' },
      { label: "Custom tag qo'shish/tahrirlash", headManager: 'full', manager: 'full', staff: 'none' },
      { label: 'Excel export', headManager: 'full', manager: 'full', staff: 'none' },
      { label: "Papkaga qo'shish/olib tashlash", headManager: 'full', manager: 'full', staff: 'none' },
    ],
  },
  {
    category: "To'lovlar (Payments)",
    icon: CreditCard,
    color: 'emerald',
    rows: [
      { label: "To'lovlar sahifasini ko'rish", headManager: 'full', manager: 'full', staff: 'none', note: "Staff kira olmaydi" },
      { label: "To'lov qo'shish", headManager: 'full', manager: 'full', staff: 'none' },
      { label: "To'lovni tahrirlash", headManager: 'full', manager: 'full', staff: 'none' },
      { label: "To'lovni o'chirish", headManager: 'full', manager: 'none', staff: 'none', note: 'Faqat Head Manager' },
      { label: "Hisobot / statistikani ko'rish", headManager: 'full', manager: 'full', staff: 'none' },
      { label: "Pul chiqarish (Withdraw)", headManager: 'full', manager: 'full', staff: 'none' },
    ],
  },
  {
    category: 'Status Board (Visa)',
    icon: BarChart2,
    color: 'violet',
    rows: [
      { label: "Visa status jadvalini ko'rish", headManager: 'full', manager: 'full', staff: 'full' },
      { label: 'Status tahrirlash', headManager: 'full', manager: 'full', staff: 'none' },
      { label: 'KDB sanasini o\'rnatish', headManager: 'full', manager: 'full', staff: 'none' },
      { label: 'Embassy hujjatlarini boshqarish', headManager: 'full', manager: 'full', staff: 'none' },
    ],
  },
  {
    category: 'Papkalar (Folders)',
    icon: FolderOpen,
    color: 'amber',
    rows: [
      { label: "Papkalarni ko'rish", headManager: 'full', manager: 'full', staff: 'full' },
      { label: "Papka yaratish", headManager: 'full', manager: 'full', staff: 'none' },
      { label: "Papkani o'chirish", headManager: 'full', manager: 'full', staff: 'none' },
      { label: 'KDB papkasini boshqarish', headManager: 'full', manager: 'full', staff: 'none' },
    ],
  },
  {
    category: 'Sozlamalar (Settings)',
    icon: Settings,
    color: 'rose',
    rows: [
      { label: "Sozlamalar sahifasini ko'rish", headManager: 'full', manager: 'full', staff: 'none', note: 'Faqat Manager+' },
      { label: "Tarif rejalarini boshqarish", headManager: 'full', manager: 'full', staff: 'none' },
      { label: "Custom taglarni boshqarish", headManager: 'full', manager: 'full', staff: 'none' },
      { label: "Universitetlarni boshqarish", headManager: 'full', manager: 'full', staff: 'none' },
      { label: "Ofislarni boshqarish", headManager: 'full', manager: 'none', staff: 'none', note: 'Faqat Head Manager' },
      { label: "Koordinatorlarni boshqarish", headManager: 'full', manager: 'full', staff: 'none' },
    ],
  },
  {
    category: 'Xodimlar (Staff)',
    icon: UserCog,
    color: 'indigo',
    rows: [
      { label: "Xodimlar sahifasini ko'rish", headManager: 'full', manager: 'full', staff: 'none' },
      { label: "Yangi xodim qo'shish", headManager: 'full', manager: 'none', staff: 'none', note: 'Faqat Head Manager' },
      { label: "Xodim ma'lumotlarini tahrirlash", headManager: 'full', manager: 'none', staff: 'none', note: 'Faqat Head Manager' },
      { label: "Xodimni o'chirish", headManager: 'full', manager: 'none', staff: 'none', note: 'Faqat Head Manager' },
      { label: "O'z profilini tahrirlash", headManager: 'full', manager: 'full', staff: 'full' },
    ],
  },
]

const colorMap: Record<string, { bg: string; text: string; border: string; icon: string }> = {
  blue:    { bg: 'bg-blue-50 dark:bg-blue-950/30',    text: 'text-blue-700 dark:text-blue-300',    border: 'border-blue-200 dark:border-blue-800',    icon: 'text-blue-500' },
  emerald: { bg: 'bg-emerald-50 dark:bg-emerald-950/30', text: 'text-emerald-700 dark:text-emerald-300', border: 'border-emerald-200 dark:border-emerald-800', icon: 'text-emerald-500' },
  violet:  { bg: 'bg-violet-50 dark:bg-violet-950/30',  text: 'text-violet-700 dark:text-violet-300',  border: 'border-violet-200 dark:border-violet-800',  icon: 'text-violet-500' },
  amber:   { bg: 'bg-amber-50 dark:bg-amber-950/30',   text: 'text-amber-700 dark:text-amber-300',   border: 'border-amber-200 dark:border-amber-800',   icon: 'text-amber-500' },
  rose:    { bg: 'bg-rose-50 dark:bg-rose-950/30',     text: 'text-rose-700 dark:text-rose-300',     border: 'border-rose-200 dark:border-rose-800',     icon: 'text-rose-500' },
  indigo:  { bg: 'bg-indigo-50 dark:bg-indigo-950/30',  text: 'text-indigo-700 dark:text-indigo-300',  border: 'border-indigo-200 dark:border-indigo-800',  icon: 'text-indigo-500' },
}
</script>

<template>
  <div class="space-y-4">

    <!-- ── Header ─────────────────────────────────────────────────────── -->
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

      <!-- Add staff button — only visible on Xodimlar tab -->
      <button
        v-if="activeTab === 'staff'"
        @click="openAdd()"
        :disabled="!canAddStaff"
        :title="canAddStaff ? 'Add a staff member' : 'Switch into a tenant first'"
        class="px-4 py-2 rounded-xl bg-brand-500 hover:bg-brand-600 disabled:opacity-50 disabled:cursor-not-allowed text-white text-xs font-bold shadow-md shadow-brand-500/25 transition-all cursor-pointer flex items-center gap-1.5"
      >
        <Plus class="w-4 h-4" />
        <span>Add New Staff</span>
      </button>
    </div>

    <!-- ── Tabs ───────────────────────────────────────────────────────── -->
    <div class="flex items-center gap-1 p-1 bg-zinc-100 dark:bg-zinc-800/60 rounded-xl w-fit">
      <button
        @click="activeTab = 'staff'"
        :class="[
          'flex items-center gap-1.5 px-4 py-1.5 rounded-lg text-xs font-bold transition-all cursor-pointer',
          activeTab === 'staff'
            ? 'bg-white dark:bg-zinc-900 text-zinc-900 dark:text-zinc-100 shadow-sm'
            : 'text-zinc-500 dark:text-zinc-400 hover:text-zinc-700 dark:hover:text-zinc-200'
        ]"
      >
        <Users class="w-3.5 h-3.5" />
        Xodimlar
        <span
          class="px-1.5 py-0.5 rounded text-[9px] font-bold"
          :class="activeTab === 'staff'
            ? 'bg-brand-100 text-brand-700 dark:bg-brand-950/60 dark:text-brand-300'
            : 'bg-zinc-200 dark:bg-zinc-700 text-zinc-500 dark:text-zinc-400'"
        >
          {{ staff.length }}
        </span>
      </button>
      <button
        @click="activeTab = 'roles'"
        :class="[
          'flex items-center gap-1.5 px-4 py-1.5 rounded-lg text-xs font-bold transition-all cursor-pointer',
          activeTab === 'roles'
            ? 'bg-white dark:bg-zinc-900 text-zinc-900 dark:text-zinc-100 shadow-sm'
            : 'text-zinc-500 dark:text-zinc-400 hover:text-zinc-700 dark:hover:text-zinc-200'
        ]"
      >
        <ShieldCheck class="w-3.5 h-3.5" />
        Roles & Permissions
      </button>
    </div>

    <!-- ═══════════════════════════════════════════════════════════════════ -->
    <!-- TAB 1 — Xodimlar                                                   -->
    <!-- ═══════════════════════════════════════════════════════════════════ -->
    <template v-if="activeTab === 'staff'">
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
                    <div class="flex items-center gap-1.5">
                      <span class="font-bold text-zinc-900 dark:text-zinc-100">{{ member.full_name }}</span>
                      <span
                        v-if="member.id === authStore.user?.id"
                        class="px-1.5 py-0.5 rounded text-[9px] font-bold bg-brand-50 text-brand-600 dark:bg-brand-950/50 dark:text-brand-400 border border-brand-200 dark:border-brand-800"
                      >
                        You
                      </span>
                    </div>
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
                    <button
                      v-if="canEdit(member)"
                      @click="openEdit(member)"
                      :title="member.id === authStore.user?.id ? 'Edit your profile & password' : 'Edit staff member & password'"
                      class="p-1.5 rounded-lg text-zinc-500 hover:text-brand-600 hover:bg-brand-50 dark:hover:bg-brand-950/30 transition-colors cursor-pointer"
                    >
                      <Pencil class="w-3.5 h-3.5" />
                    </button>
                    <button
                      v-if="canDelete(member)"
                      @click="deletingMember = member"
                      title="Delete staff member"
                      class="p-1.5 rounded-lg text-zinc-500 hover:text-rose-600 hover:bg-rose-50 dark:hover:bg-rose-950/30 transition-colors cursor-pointer"
                    >
                      <Trash2 class="w-3.5 h-3.5" />
                    </button>
                    <span v-if="!canEdit(member) && !canDelete(member)" class="text-[10px] text-zinc-400 italic pr-1">
                      Protected
                    </span>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </template>

    <!-- ═══════════════════════════════════════════════════════════════════ -->
    <!-- TAB 2 — Roles & Permissions                                        -->
    <!-- ═══════════════════════════════════════════════════════════════════ -->
    <template v-if="activeTab === 'roles'">

      <!-- Role cards legend -->
      <div class="grid grid-cols-3 gap-3">
        <!-- Head Manager -->
        <div class="rounded-2xl border border-blue-200 dark:border-blue-800 bg-gradient-to-br from-blue-50 to-indigo-50 dark:from-blue-950/40 dark:to-indigo-950/30 p-4">
          <div class="flex items-center gap-2 mb-2">
            <div class="w-8 h-8 rounded-xl bg-blue-500 shadow-md shadow-blue-500/30 flex items-center justify-center">
              <Crown class="w-4 h-4 text-white" />
            </div>
            <div>
              <p class="text-xs font-bold text-blue-900 dark:text-blue-100">Head Manager</p>
              <p class="text-[10px] text-blue-600 dark:text-blue-400">To'liq huquqlar</p>
            </div>
          </div>
          <p class="text-[10px] text-blue-700 dark:text-blue-300 leading-relaxed">
            Barcha sahifalar va amallar uchun to'liq kirish. Xodimlarni boshqarish, to'lovlarni o'chirish va sozlamalarni tahrirlash imkoniyatiga ega.
          </p>
        </div>
        <!-- Manager -->
        <div class="rounded-2xl border border-amber-200 dark:border-amber-800 bg-gradient-to-br from-amber-50 to-orange-50 dark:from-amber-950/40 dark:to-orange-950/30 p-4">
          <div class="flex items-center gap-2 mb-2">
            <div class="w-8 h-8 rounded-xl bg-amber-500 shadow-md shadow-amber-500/30 flex items-center justify-center">
              <Shield class="w-4 h-4 text-white" />
            </div>
            <div>
              <p class="text-xs font-bold text-amber-900 dark:text-amber-100">Manager</p>
              <p class="text-[10px] text-amber-600 dark:text-amber-400">Kengaytirilgan huquqlar</p>
            </div>
          </div>
          <p class="text-[10px] text-amber-700 dark:text-amber-300 leading-relaxed">
            Talabalar, to'lovlar va sozlamalarni boshqara oladi. Lekin xodimlarni qo'sha olmaydi va to'lovlarni o'chira olmaydi.
          </p>
        </div>
        <!-- Staff -->
        <div class="rounded-2xl border border-zinc-200 dark:border-zinc-700 bg-gradient-to-br from-zinc-50 to-slate-50 dark:from-zinc-800/40 dark:to-slate-800/30 p-4">
          <div class="flex items-center gap-2 mb-2">
            <div class="w-8 h-8 rounded-xl bg-zinc-500 shadow-md shadow-zinc-500/30 flex items-center justify-center">
              <User class="w-4 h-4 text-white" />
            </div>
            <div>
              <p class="text-xs font-bold text-zinc-900 dark:text-zinc-100">Staff</p>
              <p class="text-[10px] text-zinc-500 dark:text-zinc-400">Asosiy kirish</p>
            </div>
          </div>
          <p class="text-[10px] text-zinc-600 dark:text-zinc-400 leading-relaxed">
            Faqat talabalar ro'yxatini ko'rish va o'z profilini tahrirlash imkoniyatiga ega. To'lovlar va sozlamalarga kirish yo'q.
          </p>
        </div>
      </div>

      <!-- Legend for icons -->
      <div class="flex items-center gap-4 text-[10px] text-zinc-500 dark:text-zinc-400 bg-zinc-50 dark:bg-zinc-800/50 rounded-xl px-4 py-2 border border-zinc-200 dark:border-zinc-800 w-fit">
        <span class="flex items-center gap-1.5">
          <CheckCircle2 class="w-3.5 h-3.5 text-emerald-500" />
          <span>To'liq ruxsat</span>
        </span>
        <span class="flex items-center gap-1.5">
          <Eye class="w-3.5 h-3.5 text-blue-500" />
          <span>Faqat ko'rish</span>
        </span>
        <span class="flex items-center gap-1.5">
          <XCircle class="w-3.5 h-3.5 text-rose-400" />
          <span>Ruxsat yo'q</span>
        </span>
      </div>

      <!-- Permission groups -->
      <div class="space-y-4">
        <div
          v-for="group in permissionGroups"
          :key="group.category"
          class="rounded-2xl border overflow-hidden"
          :class="colorMap[group.color].border"
        >
          <!-- Group header -->
          <div
            class="px-4 py-3 flex items-center gap-2.5 border-b"
            :class="[colorMap[group.color].bg, colorMap[group.color].border]"
          >
            <component :is="group.icon" class="w-4 h-4" :class="colorMap[group.color].icon" />
            <h3 class="text-xs font-bold" :class="colorMap[group.color].text">
              {{ group.category }}
            </h3>
          </div>

          <!-- Table -->
          <div class="overflow-x-auto bg-white dark:bg-zinc-900">
            <table class="w-full text-xs">
              <thead class="bg-zinc-50 dark:bg-zinc-800/50 border-b border-zinc-100 dark:border-zinc-800">
                <tr class="text-[10px] uppercase font-bold text-zinc-400">
                  <th class="px-4 py-2.5 text-left w-1/2">Amal / Permission</th>
                  <th class="px-4 py-2.5 text-center w-[17%]">
                    <span class="inline-flex items-center gap-1 text-blue-600 dark:text-blue-400">
                      <Crown class="w-3 h-3" />Head Manager
                    </span>
                  </th>
                  <th class="px-4 py-2.5 text-center w-[17%]">
                    <span class="inline-flex items-center gap-1 text-amber-600 dark:text-amber-400">
                      <Shield class="w-3 h-3" />Manager
                    </span>
                  </th>
                  <th class="px-4 py-2.5 text-center w-[17%]">
                    <span class="inline-flex items-center gap-1 text-zinc-500 dark:text-zinc-400">
                      <User class="w-3 h-3" />Staff
                    </span>
                  </th>
                </tr>
              </thead>
              <tbody class="divide-y divide-zinc-100 dark:divide-zinc-800/60">
                <tr
                  v-for="row in group.rows"
                  :key="row.label"
                  class="hover:bg-zinc-50/80 dark:hover:bg-zinc-800/30 transition-colors"
                >
                  <td class="px-4 py-2.5">
                    <div class="flex items-center gap-2">
                      <span class="text-zinc-700 dark:text-zinc-300 font-medium">{{ row.label }}</span>
                      <span
                        v-if="row.note"
                        class="px-1.5 py-0.5 rounded text-[9px] font-semibold bg-amber-100 text-amber-700 dark:bg-amber-950/50 dark:text-amber-400 border border-amber-200 dark:border-amber-800"
                      >
                        {{ row.note }}
                      </span>
                    </div>
                  </td>
                  <!-- Head Manager -->
                  <td class="px-4 py-2.5 text-center">
                    <span v-if="row.headManager === 'full'" class="inline-flex items-center justify-center">
                      <CheckCircle2 class="w-4 h-4 text-emerald-500" />
                    </span>
                    <span v-else-if="row.headManager === 'view'" class="inline-flex items-center justify-center">
                      <Eye class="w-4 h-4 text-blue-500" />
                    </span>
                    <span v-else class="inline-flex items-center justify-center">
                      <XCircle class="w-4 h-4 text-zinc-300 dark:text-zinc-600" />
                    </span>
                  </td>
                  <!-- Manager -->
                  <td class="px-4 py-2.5 text-center">
                    <span v-if="row.manager === 'full'" class="inline-flex items-center justify-center">
                      <CheckCircle2 class="w-4 h-4 text-emerald-500" />
                    </span>
                    <span v-else-if="row.manager === 'view'" class="inline-flex items-center justify-center">
                      <Eye class="w-4 h-4 text-blue-500" />
                    </span>
                    <span v-else class="inline-flex items-center justify-center">
                      <XCircle class="w-4 h-4 text-zinc-300 dark:text-zinc-600" />
                    </span>
                  </td>
                  <!-- Staff -->
                  <td class="px-4 py-2.5 text-center">
                    <span v-if="row.staff === 'full'" class="inline-flex items-center justify-center">
                      <CheckCircle2 class="w-4 h-4 text-emerald-500" />
                    </span>
                    <span v-else-if="row.staff === 'view'" class="inline-flex items-center justify-center">
                      <Eye class="w-4 h-4 text-blue-500" />
                    </span>
                    <span v-else class="inline-flex items-center justify-center">
                      <XCircle class="w-4 h-4 text-zinc-300 dark:text-zinc-600" />
                    </span>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </template>

    <!-- ── Add / Edit Staff Modal ─────────────────────────────────────── -->
    <AddStaffModal
      :is-open="isAddModalOpen"
      :member="editingMember"
      :is-submitting="saveStaffMutation.isPending.value"
      @close="closeModal()"
      @submit="data => saveStaffMutation.mutate(data)"
    />

    <!-- ── Delete Confirmation ────────────────────────────────────────── -->
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
