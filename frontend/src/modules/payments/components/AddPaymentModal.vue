<script setup lang="ts">
import { ref, watch, computed } from 'vue'
import BaseModal from '@/components/common/BaseModal.vue'
import { useCurrency } from '@/composables/useCurrency'
import { CreditCard, AlertCircle, Plus, Check } from 'lucide-vue-next'

const props = defineProps<{
  isOpen: boolean
  preselectedStudentId?: string | null
  studentsList?: { id: string; full_name: string }[]
}>()

const emit = defineEmits<{
  (e: 'close'): void
  (e: 'submit', data: any): void
}>()

const { formatAmountInput, parseAmount } = useCurrency()

const PAYMENT_METHODS = ['Karta J.A', 'Karta Abdulaziz', 'Naqd', 'Karta M.A', 'Bank', 'Discount']
const RECEIVED_BY_OPTIONS = ['ABDULAZIZ', 'MUSLIHIDDIN', 'BAXTIYOR', 'MUHAMMADALI', 'JASUR', 'ADMIN']
const NOTE_PILLS = ['Shartnoma uchun', 'Qarz', 'Elchixona uchun', 'Appfee', 'DISCOUNT']

const studentId = ref('')
const amountInput = ref('')
const method = ref(PAYMENT_METHODS[0])
const receivedBy = ref(RECEIVED_BY_OPTIONS[0])
const notes = ref('')
const isDiscount = ref(false)
const error = ref<string | null>(null)
const isSubmitting = ref(false)

watch(() => props.isOpen, (newVal) => {
  if (newVal) {
    studentId.value = props.preselectedStudentId || ''
    amountInput.value = ''
    method.value = PAYMENT_METHODS[0]
    receivedBy.value = RECEIVED_BY_OPTIONS[0]
    notes.value = ''
    isDiscount.value = false
    error.value = null
  }
})

const onAmountChange = (e: Event) => {
  const target = e.target as HTMLInputElement
  amountInput.value = formatAmountInput(target.value)
}

const togglePill = (pill: string) => {
  if (pill === 'DISCOUNT') {
    isDiscount.value = true
    method.value = 'Discount'
  }
  if (!notes.value.includes(pill)) {
    notes.value = notes.value ? `${notes.value}, ${pill}` : pill
  }
}

const handleSubmit = () => {
  const numericAmount = parseAmount(amountInput.value)
  if (!numericAmount || numericAmount <= 0) {
    error.value = 'Please enter a valid payment amount.'
    return
  }
  if (!method.value) {
    error.value = 'Please select a payment method.'
    return
  }

  isSubmitting.value = true
  emit('submit', {
    student_id: studentId.value ? studentId.value.trim().toUpperCase() : null,
    amount: numericAmount,
    method: method.value,
    received_by: receivedBy.value,
    notes: notes.value.trim(),
    is_discount: isDiscount.value || notes.value.toUpperCase().includes('DISCOUNT')
  })
}
</script>

<template>
  <BaseModal
    :is-open="isOpen"
    title="Record Payment / Discount"
    subtitle="Record a transaction directly into the student financial ledger."
    max-width="max-w-md"
    @close="emit('close')"
  >
    <form @submit.prevent="handleSubmit" class="space-y-4 text-xs">
      <!-- Error Alert -->
      <div v-if="error" class="p-3 rounded-xl bg-rose-50 dark:bg-rose-950/50 border border-rose-200 dark:border-rose-800 text-rose-700 dark:text-rose-300 flex items-center gap-2 font-semibold">
        <AlertCircle class="w-4 h-4 shrink-0" />
        <span>{{ error }}</span>
      </div>

      <!-- Student ID Selection -->
      <div>
        <label class="block font-bold text-zinc-700 dark:text-zinc-300 mb-1">Student ID (Optional if General)</label>
        <input
          v-model="studentId"
          type="text"
          placeholder="e.g. UB120"
          class="w-full px-3 py-2 rounded-xl border border-zinc-300 dark:border-zinc-700 bg-white dark:bg-zinc-800 font-mono font-bold uppercase focus:ring-2 focus:ring-brand-500/20 focus:border-brand-500 outline-none"
        />
      </div>

      <!-- Amount in UZS -->
      <div>
        <label class="block font-bold text-zinc-700 dark:text-zinc-300 mb-1">
          Amount (UZS) <span class="text-rose-500">*</span>
        </label>
        <div class="relative">
          <input
            :value="amountInput"
            @input="onAmountChange"
            type="text"
            placeholder="0"
            required
            class="w-full px-3 py-2 pr-12 rounded-xl border border-zinc-300 dark:border-zinc-700 bg-white dark:bg-zinc-800 font-mono font-bold text-base text-brand-600 dark:text-brand-400 focus:ring-2 focus:ring-brand-500/20 focus:border-brand-500 outline-none"
          />
          <span class="absolute right-3.5 top-1/2 -translate-y-1/2 text-[11px] font-bold text-zinc-400">UZS</span>
        </div>
      </div>

      <!-- Method & Received By -->
      <div class="grid grid-cols-2 gap-3">
        <div>
          <label class="block font-bold text-zinc-700 dark:text-zinc-300 mb-1">Payment Method</label>
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

      <!-- Quick Note Pills -->
      <div>
        <label class="block font-bold text-[10.5px] uppercase tracking-wider text-zinc-400 mb-1.5">Quick Notes</label>
        <div class="flex flex-wrap gap-1.5">
          <button
            v-for="pill in NOTE_PILLS"
            :key="pill"
            type="button"
            @click="togglePill(pill)"
            class="px-2.5 py-1 rounded-lg text-[10.5px] font-bold border border-zinc-200 dark:border-zinc-700 bg-zinc-50 dark:bg-zinc-800 text-zinc-700 dark:text-zinc-300 hover:bg-zinc-100 transition-colors cursor-pointer"
          >
            + {{ pill }}
          </button>
        </div>
      </div>

      <!-- Notes Textarea -->
      <div>
        <label class="block font-bold text-zinc-700 dark:text-zinc-300 mb-1">Notes / Description</label>
        <textarea
          v-model="notes"
          rows="2"
          placeholder="Optional payment notes..."
          class="w-full px-3 py-2 rounded-xl border border-zinc-300 dark:border-zinc-700 bg-white dark:bg-zinc-800 font-medium focus:ring-2 focus:ring-brand-500/20 focus:border-brand-500 outline-none resize-none"
        />
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
          class="px-5 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white font-bold transition-all shadow-md shadow-emerald-600/25 cursor-pointer disabled:opacity-50 flex items-center gap-1.5"
        >
          <CreditCard class="w-4 h-4" />
          <span>Save Payment</span>
        </button>
      </div>
    </form>
  </BaseModal>
</template>
