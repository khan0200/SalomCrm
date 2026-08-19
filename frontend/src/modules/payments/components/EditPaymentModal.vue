<script setup lang="ts">
import { ref, watch } from 'vue'
import BaseModal from '@/components/common/BaseModal.vue'
import { useCurrency } from '@/composables/useCurrency'
import type { Payment } from '@/types'
import { Edit3, AlertCircle } from 'lucide-vue-next'

const props = defineProps<{
  isOpen: boolean
  payment: Payment | null
}>()

const emit = defineEmits<{
  (e: 'close'): void
  (e: 'submit', data: any): void
}>()

const { formatAmount, formatAmountInput, parseAmount } = useCurrency()

const PAYMENT_METHODS = ['Karta J.A', 'Karta Abdulaziz', 'Naqd', 'Karta M.A', 'Bank', 'Discount']
const RECEIVED_BY_OPTIONS = ['ABDULAZIZ', 'MUSLIHIDDIN', 'BAXTIYOR', 'MUHAMMADALI', 'JASUR', 'ADMIN']

const amountInput = ref('')
const method = ref('')
const receivedBy = ref('')
const notes = ref('')
const error = ref<string | null>(null)
const isSubmitting = ref(false)

watch(() => props.payment, (newVal) => {
  if (newVal) {
    amountInput.value = formatAmount(Math.abs(newVal.amount))
    method.value = newVal.method || PAYMENT_METHODS[0]
    receivedBy.value = newVal.received_by || RECEIVED_BY_OPTIONS[0]
    notes.value = newVal.notes || ''
    error.value = null
  }
}, { immediate: true })

const onAmountChange = (e: Event) => {
  const target = e.target as HTMLInputElement
  amountInput.value = formatAmountInput(target.value)
}

const handleSubmit = () => {
  const numericAmount = parseAmount(amountInput.value)
  if (!numericAmount || numericAmount <= 0) {
    error.value = 'Please enter a valid amount.'
    return
  }

  isSubmitting.value = true
  emit('submit', {
    amount: numericAmount,
    method: method.value,
    received_by: receivedBy.value,
    notes: notes.value.trim() || null
  })
}
</script>

<template>
  <BaseModal
    :is-open="isOpen"
    title="Edit Payment Record"
    :subtitle="`Editing payment for: ${payment?.student_full_name || payment?.student_name || 'General'}`"
    max-width="max-w-md"
    @close="emit('close')"
  >
    <form @submit.prevent="handleSubmit" class="space-y-4 text-xs">
      <div v-if="error" class="p-3 rounded-xl bg-rose-50 dark:bg-rose-950/50 border border-rose-200 dark:border-rose-800 text-rose-700 dark:text-rose-300 flex items-center gap-2 font-semibold">
        <AlertCircle class="w-4 h-4 shrink-0" />
        <span>{{ error }}</span>
      </div>

      <div>
        <label class="block font-bold text-zinc-700 dark:text-zinc-300 mb-1">Amount (UZS)</label>
        <div class="relative">
          <input
            :value="amountInput"
            @input="onAmountChange"
            type="text"
            required
            class="w-full px-3 py-2 pr-12 rounded-xl border border-zinc-300 dark:border-zinc-700 bg-white dark:bg-zinc-800 font-mono font-bold text-base text-zinc-900 dark:text-zinc-100 focus:ring-2 focus:ring-brand-500/20 focus:border-brand-500 outline-none"
          />
          <span class="absolute right-3.5 top-1/2 -translate-y-1/2 text-[11px] font-bold text-zinc-400">UZS</span>
        </div>
      </div>

      <div class="grid grid-cols-2 gap-3">
        <div>
          <label class="block font-bold text-zinc-700 dark:text-zinc-300 mb-1">Method</label>
          <select
            v-model="method"
            class="w-full px-3 py-2 rounded-xl border border-zinc-300 dark:border-zinc-700 bg-white dark:bg-zinc-800 font-medium focus:ring-2 focus:ring-brand-500/20 focus:border-brand-500 outline-none cursor-pointer"
          >
            <option v-for="m in PAYMENT_METHODS" :key="m" :value="m">{{ m }}</option>
          </select>
        </div>
        <div>
          <label class="block font-bold text-zinc-700 dark:text-zinc-300 mb-1">Received By</label>
          <select
            v-model="receivedBy"
            class="w-full px-3 py-2 rounded-xl border border-zinc-300 dark:border-zinc-700 bg-white dark:bg-zinc-800 font-medium focus:ring-2 focus:ring-brand-500/20 focus:border-brand-500 outline-none cursor-pointer"
          >
            <option v-for="r in RECEIVED_BY_OPTIONS" :key="r" :value="r">{{ r }}</option>
          </select>
        </div>
      </div>

      <div>
        <label class="block font-bold text-zinc-700 dark:text-zinc-300 mb-1">Notes</label>
        <textarea
          v-model="notes"
          rows="2"
          class="w-full px-3 py-2 rounded-xl border border-zinc-300 dark:border-zinc-700 bg-white dark:bg-zinc-800 font-medium focus:ring-2 focus:ring-brand-500/20 focus:border-brand-500 outline-none resize-none"
        />
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
          <Edit3 class="w-4 h-4" />
          <span>Update Payment</span>
        </button>
      </div>
    </form>
  </BaseModal>
</template>
