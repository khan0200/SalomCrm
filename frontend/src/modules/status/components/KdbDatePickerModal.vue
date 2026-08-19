<script setup lang="ts">
import { ref, watch } from 'vue'
import BaseModal from '@/components/common/BaseModal.vue'
import type { Student } from '@/types'
import { Calendar, Clock, Save } from 'lucide-vue-next'

const props = defineProps<{
  isOpen: boolean
  student: Student | null
}>()

const emit = defineEmits<{
  (e: 'close'): void
  (e: 'save', data: { kdb_put_date: string | null; kdb_take_date: string | null }): void
}>()

const putDate = ref('')
const takeDate = ref('')

watch(() => props.student, (newVal) => {
  if (newVal) {
    putDate.value = newVal.kdb_put_date || ''
    takeDate.value = newVal.kdb_take_date || ''
  }
}, { immediate: true })

const setPreset = (days: number) => {
  const base = putDate.value ? new Date(putDate.value) : new Date()
  base.setDate(base.getDate() + days)
  takeDate.value = base.toISOString().split('T')[0]
}

const handleSave = () => {
  emit('save', {
    kdb_put_date: putDate.value || null,
    kdb_take_date: takeDate.value || null
  })
}
</script>

<template>
  <BaseModal
    :is-open="isOpen"
    title="Set KDB Deposit Dates"
    :subtitle="`Student: ${student?.full_name || ''} (ID: ${student?.id || ''})`"
    max-width="max-w-md"
    @close="emit('close')"
  >
    <form @submit.prevent="handleSave" class="space-y-4 text-xs">
      <!-- KDB PUT Date -->
      <div>
        <label class="block font-bold text-zinc-700 dark:text-zinc-300 mb-1">
          KDB PUT Date (Qo'yilgan sana)
        </label>
        <input
          v-model="putDate"
          type="date"
          class="w-full px-3 py-2 rounded-xl border border-zinc-300 dark:border-zinc-700 bg-white dark:bg-zinc-800 font-medium focus:ring-2 focus:ring-brand-500/20 focus:border-brand-500 outline-none cursor-pointer"
        />
      </div>

      <!-- KDB TAKE Date -->
      <div>
        <label class="block font-bold text-zinc-700 dark:text-zinc-300 mb-1">
          KDB TAKE Date (Olinadigan sana)
        </label>
        <input
          v-model="takeDate"
          type="date"
          class="w-full px-3 py-2 rounded-xl border border-zinc-300 dark:border-zinc-700 bg-white dark:bg-zinc-800 font-medium focus:ring-2 focus:ring-brand-500/20 focus:border-brand-500 outline-none cursor-pointer"
        />
      </div>

      <!-- Quick Date Presets -->
      <div>
        <label class="block font-bold text-[10.5px] uppercase tracking-wider text-zinc-400 mb-1.5">Quick Presets</label>
        <div class="flex items-center gap-1.5 flex-wrap">
          <button
            type="button"
            @click="setPreset(5)"
            class="px-2.5 py-1 rounded-lg border border-zinc-200 dark:border-zinc-700 bg-zinc-50 dark:bg-zinc-800 text-zinc-700 dark:text-zinc-300 hover:bg-zinc-100 font-bold cursor-pointer"
          >
            +5 Days
          </button>
          <button
            type="button"
            @click="setPreset(7)"
            class="px-2.5 py-1 rounded-lg border border-zinc-200 dark:border-zinc-700 bg-zinc-50 dark:bg-zinc-800 text-zinc-700 dark:text-zinc-300 hover:bg-zinc-100 font-bold cursor-pointer"
          >
            +7 Days
          </button>
          <button
            type="button"
            @click="setPreset(10)"
            class="px-2.5 py-1 rounded-lg border border-zinc-200 dark:border-zinc-700 bg-zinc-50 dark:bg-zinc-800 text-zinc-700 dark:text-zinc-300 hover:bg-zinc-100 font-bold cursor-pointer"
          >
            +10 Days
          </button>
          <button
            type="button"
            @click="setPreset(15)"
            class="px-2.5 py-1 rounded-lg border border-zinc-200 dark:border-zinc-700 bg-zinc-50 dark:bg-zinc-800 text-zinc-700 dark:text-zinc-300 hover:bg-zinc-100 font-bold cursor-pointer"
          >
            +15 Days
          </button>
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
          class="px-5 py-2 rounded-xl bg-brand-500 hover:bg-brand-600 text-white font-bold transition-all shadow-md shadow-brand-500/25 cursor-pointer flex items-center gap-1.5"
        >
          <Save class="w-4 h-4" />
          <span>Save KDB Dates</span>
        </button>
      </div>
    </form>
  </BaseModal>
</template>
