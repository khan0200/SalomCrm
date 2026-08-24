<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import BaseModal from '@/components/common/BaseModal.vue'
import { AlertCircle, UserPlus, Loader2 } from 'lucide-vue-next'
import type { UserRole, UserProfile } from '@/types'

const props = defineProps<{
  isOpen: boolean
  isSubmitting?: boolean
  member?: UserProfile | null
}>()

const emit = defineEmits<{
  (e: 'close'): void
  (e: 'submit', data: { full_name: string; email: string; role: UserRole; password: string }): void
}>()

const blankForm = () => ({
  full_name: '',
  email: '',
  role: 'STAFF' as UserRole,
  password: '',
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
    if (props.member) {
      form.value = {
        full_name: props.member.full_name,
        email: props.member.email,
        role: props.member.role,
        password: '',
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

  const payload: Record<string, unknown> = {
    full_name: form.value.full_name.trim(),
    email: form.value.email.trim().toLowerCase(),
    role: form.value.role,
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
    max-width="max-w-md"
    @close="emit('close')"
  >
    <form @submit.prevent="handleSubmit" class="space-y-4 text-xs">
      <div v-if="error" class="p-3 rounded-xl bg-rose-50 dark:bg-rose-950/50 border border-rose-200 dark:border-rose-800 text-rose-700 dark:text-rose-300 flex items-center gap-2 font-semibold">
        <AlertCircle class="w-4 h-4 shrink-0" />
        <span>{{ error }}</span>
      </div>

      <div>
        <label class="block font-bold text-zinc-700 dark:text-zinc-300 mb-1">Full Name <span class="text-rose-500">*</span></label>
        <input
          v-model="form.full_name"
          type="text"
          placeholder="e.g. Aziz Karimov"
          required
          class="w-full px-3 py-2 rounded-xl border border-zinc-300 dark:border-zinc-700 bg-white dark:bg-zinc-800 font-semibold focus:ring-2 focus:ring-brand-500/20 focus:border-brand-500 outline-none"
        />
      </div>

      <div>
        <label class="block font-bold text-zinc-700 dark:text-zinc-300 mb-1">Email <span class="text-rose-500">*</span></label>
        <input
          v-model="form.email"
          type="email"
          placeholder="staff@agency.com"
          required
          class="w-full px-3 py-2 rounded-xl border border-zinc-300 dark:border-zinc-700 bg-white dark:bg-zinc-800 font-medium focus:ring-2 focus:ring-brand-500/20 focus:border-brand-500 outline-none"
        />
      </div>

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
        <label class="block font-bold text-zinc-700 dark:text-zinc-300 mb-1">
          {{ isEditing ? 'New Password' : 'Temporary Password' }}
          <span v-if="!isEditing" class="text-rose-500">*</span>
        </label>
        <input
          v-model="form.password"
          type="password"
          placeholder="••••••••"
          :required="!isEditing"
          class="w-full px-3 py-2 rounded-xl border border-zinc-300 dark:border-zinc-700 bg-white dark:bg-zinc-800 font-medium focus:ring-2 focus:ring-brand-500/20 focus:border-brand-500 outline-none"
        />
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
