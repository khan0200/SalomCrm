<script setup lang="ts">
import { ref, watch } from 'vue'
import BaseModal from '@/components/common/BaseModal.vue'
import { Plus, UserPlus, AlertCircle } from 'lucide-vue-next'

const props = defineProps<{
  isOpen: boolean
  options: {
    tariffs: { name: string; price: number }[]
    levels: string[]
    groups: string[]
    leads: string[]
    coordinators: string[]
    offices: string[]
  }
}>()

const emit = defineEmits<{
  (e: 'close'): void
  (e: 'submit', data: any): void
}>()

const form = ref({
  id: '',
  full_name: '',
  office: '',
  tariff: '',
  level: '',
  university_1: '',
  student_group: '',
  lead_by: '',
  coordinator: '',
})

const isSubmitting = ref(false)
const error = ref<string | null>(null)

watch(() => props.isOpen, (newVal) => {
  if (newVal) {
    form.value = {
      id: '',
      full_name: '',
      office: props.options.offices[0] || 'ANDIJON OFFIS',
      tariff: props.options.tariffs[0]?.name || 'STANDART',
      level: props.options.levels[0] || 'BACHELOR',
      university_1: '',
      student_group: props.options.groups[0] || '',
      lead_by: props.options.leads[0] || '',
      coordinator: props.options.coordinators[0] || '',
    }
    error.value = null
  }
})

const handleSubmit = async () => {
  if (!form.value.id.trim()) {
    error.value = 'Student ID is required (e.g. UB120).'
    return
  }
  if (!form.value.full_name.trim()) {
    error.value = 'Full name is required.'
    return
  }

  isSubmitting.value = true
  error.value = null
  try {
    emit('submit', {
      id: form.value.id.trim().toUpperCase(),
      full_name: form.value.full_name.trim().toUpperCase(),
      office: form.value.office || null,
      tariff: form.value.tariff || null,
      level: form.value.level || null,
      university_1: form.value.university_1 ? form.value.university_1.trim().toUpperCase() : null,
      student_group: form.value.student_group || null,
      lead_by: form.value.lead_by || null,
      coordinator: form.value.coordinator || null,
    })
  } catch (err: any) {
    error.value = err.message || 'Failed to submit form'
  } finally {
    isSubmitting.value = false
  }
}
</script>

<template>
  <BaseModal
    :is-open="isOpen"
    title="Register New Student"
    subtitle="Quickly register a new student into the CRM database."
    max-width="max-w-xl"
    @close="emit('close')"
  >
    <form @submit.prevent="handleSubmit" class="space-y-4 text-xs">
      <!-- Error Alert -->
      <div v-if="error" class="p-3 rounded-xl bg-rose-50 dark:bg-rose-950/50 border border-rose-200 dark:border-rose-800 text-rose-700 dark:text-rose-300 flex items-center gap-2 font-semibold">
        <AlertCircle class="w-4 h-4 shrink-0" />
        <span>{{ error }}</span>
      </div>

      <!-- ID & Full Name -->
      <div class="grid grid-cols-1 sm:grid-cols-3 gap-3">
        <div>
          <label class="block font-bold text-zinc-700 dark:text-zinc-300 mb-1">
            Student ID <span class="text-rose-500">*</span>
          </label>
          <input
            v-model="form.id"
            type="text"
            placeholder="e.g. UB120"
            required
            class="w-full px-3 py-2 rounded-xl border border-zinc-300 dark:border-zinc-700 bg-white dark:bg-zinc-800 font-mono font-bold uppercase focus:ring-2 focus:ring-brand-500/20 focus:border-brand-500 outline-none transition-all"
          />
        </div>
        <div class="sm:col-span-2">
          <label class="block font-bold text-zinc-700 dark:text-zinc-300 mb-1">
            Full Name <span class="text-rose-500">*</span>
          </label>
          <input
            v-model="form.full_name"
            type="text"
            placeholder="e.g. KARIMOV SHOHRUH"
            required
            class="w-full px-3 py-2 rounded-xl border border-zinc-300 dark:border-zinc-700 bg-white dark:bg-zinc-800 font-semibold uppercase focus:ring-2 focus:ring-brand-500/20 focus:border-brand-500 outline-none transition-all"
          />
        </div>
      </div>

      <!-- Office & Tariff -->
      <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
        <div>
          <label class="block font-bold text-zinc-700 dark:text-zinc-300 mb-1">Branch / Office</label>
          <select
            v-model="form.office"
            class="w-full px-3 py-2 rounded-xl border border-zinc-300 dark:border-zinc-700 bg-white dark:bg-zinc-800 font-medium focus:ring-2 focus:ring-brand-500/20 focus:border-brand-500 outline-none cursor-pointer"
          >
            <option v-for="o in options.offices" :key="o" :value="o">{{ o }}</option>
          </select>
        </div>
        <div>
          <label class="block font-bold text-zinc-700 dark:text-zinc-300 mb-1">Tariff Package</label>
          <select
            v-model="form.tariff"
            class="w-full px-3 py-2 rounded-xl border border-zinc-300 dark:border-zinc-700 bg-white dark:bg-zinc-800 font-medium focus:ring-2 focus:ring-brand-500/20 focus:border-brand-500 outline-none cursor-pointer"
          >
            <option v-for="t in options.tariffs" :key="t.name" :value="t.name">{{ t.name }}</option>
          </select>
        </div>
      </div>

      <!-- Education Level & Group -->
      <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
        <div>
          <label class="block font-bold text-zinc-700 dark:text-zinc-300 mb-1">Education Level</label>
          <select
            v-model="form.level"
            class="w-full px-3 py-2 rounded-xl border border-zinc-300 dark:border-zinc-700 bg-white dark:bg-zinc-800 font-medium focus:ring-2 focus:ring-brand-500/20 focus:border-brand-500 outline-none cursor-pointer"
          >
            <option v-for="l in options.levels" :key="l" :value="l">{{ l }}</option>
          </select>
        </div>
        <div>
          <label class="block font-bold text-zinc-700 dark:text-zinc-300 mb-1">Student Group</label>
          <select
            v-model="form.student_group"
            class="w-full px-3 py-2 rounded-xl border border-zinc-300 dark:border-zinc-700 bg-white dark:bg-zinc-800 font-medium focus:ring-2 focus:ring-brand-500/20 focus:border-brand-500 outline-none cursor-pointer"
          >
            <option value="">No Group</option>
            <option v-for="g in options.groups" :key="g" :value="g">{{ g }}</option>
          </select>
        </div>
      </div>

      <!-- University 1 -->
      <div>
        <label class="block font-bold text-zinc-700 dark:text-zinc-300 mb-1">University 1 (Initial Choice)</label>
        <input
          v-model="form.university_1"
          type="text"
          placeholder="e.g. SEJONG UNIVERSITY"
          class="w-full px-3 py-2 rounded-xl border border-zinc-300 dark:border-zinc-700 bg-white dark:bg-zinc-800 font-semibold uppercase focus:ring-2 focus:ring-brand-500/20 focus:border-brand-500 outline-none transition-all"
        />
      </div>

      <!-- Lead By & Coordinator -->
      <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
        <div>
          <label class="block font-bold text-zinc-700 dark:text-zinc-300 mb-1">Lead Source</label>
          <select
            v-model="form.lead_by"
            class="w-full px-3 py-2 rounded-xl border border-zinc-300 dark:border-zinc-700 bg-white dark:bg-zinc-800 font-medium focus:ring-2 focus:ring-brand-500/20 focus:border-brand-500 outline-none cursor-pointer"
          >
            <option value="">Select source...</option>
            <option v-for="lead in options.leads" :key="lead" :value="lead">{{ lead }}</option>
          </select>
        </div>
        <div>
          <label class="block font-bold text-zinc-700 dark:text-zinc-300 mb-1">Coordinator</label>
          <select
            v-model="form.coordinator"
            class="w-full px-3 py-2 rounded-xl border border-zinc-300 dark:border-zinc-700 bg-white dark:bg-zinc-800 font-medium focus:ring-2 focus:ring-brand-500/20 focus:border-brand-500 outline-none cursor-pointer"
          >
            <option value="">Select coordinator...</option>
            <option v-for="c in options.coordinators" :key="c" :value="c">{{ c }}</option>
          </select>
        </div>
      </div>

      <!-- Actions -->
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
          <UserPlus class="w-4 h-4" />
          <span>{{ isSubmitting ? 'Registering...' : 'Register Student' }}</span>
        </button>
      </div>
    </form>
  </BaseModal>
</template>
