<script setup lang="ts">
import { ref, watch } from 'vue'
import BaseModal from '@/components/common/BaseModal.vue'
import { Building2, AlertCircle, Plus } from 'lucide-vue-next'

const props = defineProps<{
  isOpen: boolean
}>()

const emit = defineEmits<{
  (e: 'close'): void
  (e: 'submit', data: any): void
}>()

const form = ref({
  name: '',
  slug: '',
  branding_color: '#007aff',
  description: '',
  admin_email: '',
  admin_full_name: '',
  admin_password: '',
})

const error = ref<string | null>(null)
const isSubmitting = ref(false)

watch(() => props.isOpen, (newVal) => {
  if (newVal) {
    form.value = {
      name: '',
      slug: '',
      branding_color: '#007aff',
      description: '',
      admin_email: '',
      admin_full_name: '',
      admin_password: '',
    }
    error.value = null
  }
})

const onNameChange = () => {
  if (!form.value.slug) {
    form.value.slug = form.value.name.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/(^-|-$)/g, '')
  }
}

const handleSubmit = () => {
  if (!form.value.name.trim() || !form.value.slug.trim()) {
    error.value = 'Tenant name and slug are required.'
    return
  }
  if (!form.value.admin_email.trim() || !form.value.admin_password.trim()) {
    error.value = 'Initial Head Manager email and password are required.'
    return
  }

  isSubmitting.value = true
  emit('submit', { ...form.value })
}
</script>

<template>
  <BaseModal
    :is-open="isOpen"
    title="Create New Tenant Agency"
    subtitle="Provision an isolated CRM environment with dedicated admin credentials."
    max-width="max-w-lg"
    @close="emit('close')"
  >
    <form @submit.prevent="handleSubmit" class="space-y-4 text-xs">
      <div v-if="error" class="p-3 rounded-xl bg-rose-50 dark:bg-rose-950/50 border border-rose-200 dark:border-rose-800 text-rose-700 dark:text-rose-300 flex items-center gap-2 font-semibold">
        <AlertCircle class="w-4 h-4 shrink-0" />
        <span>{{ error }}</span>
      </div>

      <div class="grid grid-cols-2 gap-3">
        <div>
          <label class="block font-bold text-zinc-700 dark:text-zinc-300 mb-1">Tenant Name <span class="text-rose-500">*</span></label>
          <input
            v-model="form.name"
            @input="onNameChange"
            type="text"
            placeholder="e.g. Apex Global Consulting"
            required
            class="w-full px-3 py-2 rounded-xl border border-zinc-300 dark:border-zinc-700 bg-white dark:bg-zinc-800 font-semibold focus:ring-2 focus:ring-brand-500/20 focus:border-brand-500 outline-none"
          />
        </div>
        <div>
          <label class="block font-bold text-zinc-700 dark:text-zinc-300 mb-1">Tenant Slug (Identifier) <span class="text-rose-500">*</span></label>
          <input
            v-model="form.slug"
            type="text"
            placeholder="e.g. apex-global"
            required
            class="w-full px-3 py-2 rounded-xl border border-zinc-300 dark:border-zinc-700 bg-white dark:bg-zinc-800 font-mono font-bold focus:ring-2 focus:ring-brand-500/20 focus:border-brand-500 outline-none"
          />
        </div>
      </div>

      <div class="grid grid-cols-2 gap-3">
        <div>
          <label class="block font-bold text-zinc-700 dark:text-zinc-300 mb-1">Branding Color</label>
          <div class="flex items-center gap-2">
            <input
              v-model="form.branding_color"
              type="color"
              class="w-8 h-8 rounded-lg border-0 cursor-pointer p-0 bg-transparent"
            />
            <input
              v-model="form.branding_color"
              type="text"
              class="flex-1 px-3 py-2 rounded-xl border border-zinc-300 dark:border-zinc-700 bg-white dark:bg-zinc-800 font-mono"
            />
          </div>
        </div>
        <div>
          <label class="block font-bold text-zinc-700 dark:text-zinc-300 mb-1">Description</label>
          <input
            v-model="form.description"
            type="text"
            placeholder="Optional agency note..."
            class="w-full px-3 py-2 rounded-xl border border-zinc-300 dark:border-zinc-700 bg-white dark:bg-zinc-800"
          />
        </div>
      </div>

      <div class="pt-3 border-t border-zinc-100 dark:border-zinc-800 space-y-3">
        <h4 class="font-bold text-zinc-800 dark:text-zinc-200">Initial Head Manager Account</h4>

        <div>
          <label class="block font-bold text-zinc-700 dark:text-zinc-300 mb-1">Head Manager Full Name</label>
          <input
            v-model="form.admin_full_name"
            type="text"
            placeholder="e.g. Alisher Head Manager"
            required
            class="w-full px-3 py-2 rounded-xl border border-zinc-300 dark:border-zinc-700 bg-white dark:bg-zinc-800 font-medium"
          />
        </div>

        <div class="grid grid-cols-2 gap-3">
          <div>
            <label class="block font-bold text-zinc-700 dark:text-zinc-300 mb-1">Admin Email</label>
            <input
              v-model="form.admin_email"
              type="email"
              placeholder="admin@agency.com"
              required
              class="w-full px-3 py-2 rounded-xl border border-zinc-300 dark:border-zinc-700 bg-white dark:bg-zinc-800 font-medium"
            />
          </div>
          <div>
            <label class="block font-bold text-zinc-700 dark:text-zinc-300 mb-1">Admin Password</label>
            <input
              v-model="form.admin_password"
              type="password"
              placeholder="••••••••"
              required
              class="w-full px-3 py-2 rounded-xl border border-zinc-300 dark:border-zinc-700 bg-white dark:bg-zinc-800 font-medium"
            />
          </div>
        </div>
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
          class="px-5 py-2 rounded-xl bg-brand-500 hover:bg-brand-600 text-white font-bold transition-all shadow-md shadow-brand-500/25 cursor-pointer disabled:opacity-50 flex items-center gap-1.5"
        >
          <Building2 class="w-4 h-4" />
          <span>Create Tenant</span>
        </button>
      </div>
    </form>
  </BaseModal>
</template>
