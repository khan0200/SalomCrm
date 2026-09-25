<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import BaseModal from '@/components/common/BaseModal.vue'
import {
  AlertCircle, UserPlus, Loader2, User, Mail, Building2, KeyRound, Globe, Lock
} from 'lucide-vue-next'
import type { UserRole, UserProfile, DataScope } from '@/types'
import { useOffices } from '@/composables/useOffices'

const props = defineProps<{
  isOpen: boolean
  isSubmitting?: boolean
  member?: UserProfile | null
}>()

const emit = defineEmits<{
  (e: 'close'): void
  (e: 'submit', data: { full_name: string; email: string; role: UserRole; password: string; branch: string | null; data_scope: DataScope }): void
}>()

const { officesRegistry, fetchOffices } = useOffices()

const blankForm = () => ({
  full_name: '',
  email: '',
  role: 'STAFF' as UserRole,
  password: '',
  branch: '' as string,
  data_scope: 'ALL' as DataScope,
})

const form = ref(blankForm())
const error = ref<string | null>(null)

// A Head Manager may only delegate roles at or below their own level.
const roleOptions: { value: UserRole; label: string; hint: string }[] = [
  { value: 'STAFF', label: 'Staff', hint: 'Day-to-day access to students' },
  { value: 'MANAGER', label: 'Manager', hint: 'Can also access payments and settings' },
  { value: 'HEAD_MANAGER', label: 'Head Manager', hint: 'Full control, including staff management' },
]

const isEditing = computed(() => !!props.member)

watch(() => props.isOpen, (open) => {
  if (open) {
    error.value = null
    fetchOffices()
    if (props.member) {
      form.value = {
        full_name: props.member.full_name,
        email: props.member.email,
        role: props.member.role,
        password: '',
        // GET /users/ (the list this modal's `member` prop comes from) returns
        // `branch` as a plain FK id, not the nested {id,name} object the
        // UserProfile type declares - that shape only matches the login
        // response. Guard with a plain truthy/String() cast either way.
        branch: (props.member as any).branch ? String((props.member as any).branch) : '',
        data_scope: ((props.member as any).data_scope as DataScope) || 'ALL',
      }
    } else {
      form.value = blankForm()
    }
  }
})

const handleSubmit = () => {
  error.value = null

  if (!form.value.full_name.trim()) {
    error.value = 'Full name is required.'
    return
  }
  if (!form.value.email.trim()) {
    error.value = 'Email is required.'
    return
  }
  // On edit, a blank password means "leave unchanged".
  if (!isEditing.value && form.value.password.length < 6) {
    error.value = 'Password must be at least 6 characters.'
    return
  }
  if (isEditing.value && form.value.password && form.value.password.length < 6) {
    error.value = 'Password must be at least 6 characters.'
    return
  }
  if (form.value.data_scope === 'BRANCH_ONLY' && !form.value.branch) {
    error.value = 'Select a branch before restricting access to it.'
    return
  }

  const payload: Record<string, unknown> = {
    full_name: form.value.full_name.trim(),
    email: form.value.email.trim().toLowerCase(),
    role: form.value.role,
    branch: form.value.branch || null,
    data_scope: form.value.data_scope,
  }
  if (form.value.password) {
    payload.password = form.value.password
  }
  emit('submit', payload as any)
}
</script>

<template>
  <BaseModal
    :is-open="isOpen"
    :title="isEditing ? 'Edit Staff Member' : 'Add New Staff Member'"
    :subtitle="isEditing
      ? 'Update the details, role, or password for this team member.'
      : 'The new account is created inside your agency automatically.'"
    max-width="max-w-2xl"
    @close="emit('close')"
  >
    <form @submit.prevent="handleSubmit" class="space-y-5 text-xs">
      <div v-if="error" class="p-3 rounded-xl bg-rose-50 dark:bg-rose-950/50 border border-rose-200 dark:border-rose-800 text-rose-700 dark:text-rose-300 flex items-center gap-2 font-semibold">
        <AlertCircle class="w-4 h-4 shrink-0" />
        <span>{{ error }}</span>
      </div>

      <!-- Basic info -->
      <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <div>
          <label class="block font-bold text-zinc-700 dark:text-zinc-300 mb-1">Full Name <span class="text-rose-500">*</span></label>
          <div class="relative">
            <User class="absolute left-3 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-zinc-400 pointer-events-none" />
            <input
              v-model="form.full_name"
              type="text"
              placeholder="e.g. Aziz Karimov"
              required
              class="w-full pl-9 pr-3 py-2 rounded-xl border border-zinc-300 dark:border-zinc-700 bg-white dark:bg-zinc-800 font-semibold focus:ring-2 focus:ring-brand-500/20 focus:border-brand-500 outline-none"
            />
          </div>
        </div>

        <div>
          <label class="block font-bold text-zinc-700 dark:text-zinc-300 mb-1">Email <span class="text-rose-500">*</span></label>
          <div class="relative">
            <Mail class="absolute left-3 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-zinc-400 pointer-events-none" />
            <input
              v-model="form.email"
              type="email"
              placeholder="staff@agency.com"
              required
              class="w-full pl-9 pr-3 py-2 rounded-xl border border-zinc-300 dark:border-zinc-700 bg-white dark:bg-zinc-800 font-medium focus:ring-2 focus:ring-brand-500/20 focus:border-brand-500 outline-none"
            />
          </div>
        </div>
      </div>

      <!-- Role & Branch -->
      <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <div>
          <label class="block font-bold text-zinc-700 dark:text-zinc-300 mb-1">Role <span class="text-rose-500">*</span></label>
          <select
            v-model="form.role"
            class="w-full px-3 py-2 rounded-xl border border-zinc-300 dark:border-zinc-700 bg-white dark:bg-zinc-800 font-semibold focus:ring-2 focus:ring-brand-500/20 focus:border-brand-500 outline-none cursor-pointer"
          >
            <option v-for="opt in roleOptions" :key="opt.value" :value="opt.value">
              {{ opt.label }}
            </option>
          </select>
          <p class="text-[11px] text-zinc-500 dark:text-zinc-400 mt-1">
            {{ roleOptions.find(o => o.value === form.role)?.hint }}
          </p>
        </div>

        <div>
          <label class="block font-bold text-zinc-700 dark:text-zinc-300 mb-1">Branch / Office</label>
          <div class="relative">
            <Building2 class="absolute left-3 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-zinc-400 pointer-events-none z-10" />
            <select
              v-model="form.branch"
              class="w-full pl-9 pr-3 py-2 rounded-xl border border-zinc-300 dark:border-zinc-700 bg-white dark:bg-zinc-800 font-semibold focus:ring-2 focus:ring-brand-500/20 focus:border-brand-500 outline-none cursor-pointer"
            >
              <option value="">Not assigned</option>
              <option v-for="office in officesRegistry" :key="office.id" :value="String(office.id)">
                {{ office.name }}
              </option>
            </select>
          </div>
          <p class="text-[11px] text-zinc-500 dark:text-zinc-400 mt-1">
            Which office this team member works out of.
          </p>
        </div>
      </div>

      <!-- Access to Data -->
      <div>
        <label class="block font-bold text-zinc-700 dark:text-zinc-300 mb-1.5">Access to Data</label>
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
          <button
            type="button"
            @click="form.data_scope = 'ALL'"
            class="text-left p-3 rounded-xl border-2 transition-all cursor-pointer"
            :class="form.data_scope === 'ALL'
              ? 'border-sky-500 bg-sky-50 dark:bg-sky-950/40'
              : 'border-zinc-200 dark:border-zinc-700 hover:border-zinc-300 dark:hover:border-zinc-600'"
          >
            <div class="flex items-center gap-1.5 mb-1">
              <Globe class="w-3.5 h-3.5 shrink-0" :class="form.data_scope === 'ALL' ? 'text-sky-600 dark:text-sky-400' : 'text-zinc-400'" />
              <span class="font-bold" :class="form.data_scope === 'ALL' ? 'text-sky-700 dark:text-sky-300' : 'text-zinc-700 dark:text-zinc-300'">All Data</span>
            </div>
            <p class="text-[10px] text-zinc-500 dark:text-zinc-400 leading-snug">
              Every branch's students, payments, and contracts.
            </p>
          </button>

          <button
            type="button"
            @click="form.data_scope = 'BRANCH_ONLY'"
            class="text-left p-3 rounded-xl border-2 transition-all cursor-pointer"
            :class="form.data_scope === 'BRANCH_ONLY'
              ? 'border-amber-500 bg-amber-50 dark:bg-amber-950/40'
              : 'border-zinc-200 dark:border-zinc-700 hover:border-zinc-300 dark:hover:border-zinc-600'"
          >
            <div class="flex items-center gap-1.5 mb-1">
              <Lock class="w-3.5 h-3.5 shrink-0" :class="form.data_scope === 'BRANCH_ONLY' ? 'text-amber-600 dark:text-amber-400' : 'text-zinc-400'" />
              <span class="font-bold" :class="form.data_scope === 'BRANCH_ONLY' ? 'text-amber-700 dark:text-amber-300' : 'text-zinc-700 dark:text-zinc-300'">Branch Only</span>
            </div>
            <p class="text-[10px] text-zinc-500 dark:text-zinc-400 leading-snug">
              Only the branch selected above - regardless of role.
            </p>
          </button>
        </div>
      </div>

      <!-- Password -->
      <div>
        <label class="block font-bold text-zinc-700 dark:text-zinc-300 mb-1">
          {{ isEditing ? 'New Password' : 'Temporary Password' }}
          <span v-if="!isEditing" class="text-rose-500">*</span>
        </label>
        <div class="relative">
          <KeyRound class="absolute left-3 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-zinc-400 pointer-events-none" />
          <input
            v-model="form.password"
            type="password"
            placeholder="••••••••"
            :required="!isEditing"
            class="w-full pl-9 pr-3 py-2 rounded-xl border border-zinc-300 dark:border-zinc-700 bg-white dark:bg-zinc-800 font-medium focus:ring-2 focus:ring-brand-500/20 focus:border-brand-500 outline-none"
          />
        </div>
        <p class="text-[11px] text-zinc-500 dark:text-zinc-400 mt-1">
          {{ isEditing
            ? 'Leave blank to keep the current password.'
            : 'Share this with the staff member so they can sign in.' }}
        </p>
      </div>

      <div class="pt-4 flex items-center justify-end gap-2.5 border-t border-zinc-100 dark:border-zinc-800">
        <button
          type="button"
          @click="emit('close')"
          class="px-4 py-2 rounded-xl border border-zinc-300 dark:border-zinc-700 font-bold text-zinc-700 dark:text-zinc-300 hover:bg-zinc-100 dark:hover:bg-zinc-800 transition-colors cursor-pointer"
        >
          Cancel
        </button>
        <button
          type="submit"
          :disabled="isSubmitting"
          class="px-4 py-2 rounded-xl bg-brand-500 hover:bg-brand-600 disabled:opacity-60 disabled:cursor-not-allowed text-white font-bold shadow-md shadow-brand-500/25 transition-all cursor-pointer flex items-center gap-1.5"
        >
          <Loader2 v-if="isSubmitting" class="w-4 h-4 animate-spin" />
          <UserPlus v-else class="w-4 h-4" />
          <span>Save</span>
        </button>
      </div>
    </form>
  </BaseModal>
</template>
